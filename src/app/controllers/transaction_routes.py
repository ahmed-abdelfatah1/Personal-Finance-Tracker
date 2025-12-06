"""Transaction routes - CRUD operations for transactions."""

import json
from datetime import date
from decimal import Decimal
from typing import Optional

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Transaction, Account, Category, Budget

transaction_bp = Blueprint('transaction', __name__)


@transaction_bp.route('/transactions')
@login_required
def transactions():
    query = Transaction.query.filter_by(user_id=current_user.id)
    query = _apply_filters(query)
    all_transactions = query.order_by(Transaction.date.desc()).all()

    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'transactions.html',
        transactions=all_transactions,
        accounts=accounts,
        categories=categories
    )


def _apply_filters(query):
    """Apply query filters for transactions based on request arguments."""
    account_id = request.args.get('account', type=int)
    category_id = request.args.get('category', type=int)
    transaction_type = request.args.get('type')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if account_id:
        query = query.filter_by(account_id=account_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if transaction_type in ['Income', 'Expense']:
        query = query.filter_by(transaction_type=transaction_type)
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
            query = query.filter(Transaction.date >= start_date)
        except (ValueError, TypeError):
            pass
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
            query = query.filter(Transaction.date <= end_date)
        except (ValueError, TypeError):
            pass

    return query


@transaction_bp.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'GET':
        return _render_transaction_form()

    return _create_transaction()


def _render_transaction_form():
    """Render the add transaction form with category limits data."""
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    category_limits = _build_category_limits_json(categories)

    return render_template(
        'add_transaction.html',
        accounts=accounts,
        categories=categories,
        category_limits=category_limits
    )


def _build_category_limits_json(categories: list) -> str:
    """Build JSON string of category IDs to their max_single_amount limits."""
    limits = {}
    for cat in categories:
        if cat.max_single_amount:
            limits[str(cat.id)] = float(cat.max_single_amount)
    return json.dumps(limits)


def _create_transaction():
    """Process new transaction form submission with limit checking."""
    try:
        data = _extract_transaction_data()
        if not data:
            return redirect(url_for('transaction.add_transaction'))

        limit_warning = _check_category_limit(data['category_id'], data['amount'])
        if limit_warning and not _is_limit_confirmed():
            flash(limit_warning, 'warning')
            return redirect(url_for('transaction.add_transaction'))

        new_transaction = Transaction(user_id=current_user.id, **data)
        db.session.add(new_transaction)

        _update_account_balance(data['account_id'], data['amount'], data['transaction_type'])
        _update_affected_budgets(data['category_id'], data['date'], data['transaction_type'])
        db.session.commit()

        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transaction.transactions'))

    except ValueError:
        flash('Invalid amount format', 'error')
        return redirect(url_for('transaction.add_transaction'))
    except Exception as e:
        flash(f'Error adding transaction: {str(e)}', 'error')
        return redirect(url_for('transaction.add_transaction'))


def _extract_transaction_data() -> dict | None:
    account_id = request.form.get('account_id')
    category_id = request.form.get('category_id')
    date_str = request.form.get('date')
    amount_str = request.form.get('amount')
    transaction_type = request.form.get('transaction_type')
    description = request.form.get('description', '')

    if not all([account_id, category_id, date_str, amount_str, transaction_type]):
        flash('All fields except description are required', 'error')
        return None

    if transaction_type not in ['Income', 'Expense']:
        flash('Invalid transaction type', 'error')
        return None

    try:
        amount = Decimal(str(amount_str))
        transaction_date = date.fromisoformat(date_str)
    except (ValueError, TypeError) as e:
        if isinstance(e, ValueError) and 'date' in str(e).lower():
            flash('Invalid date format', 'error')
        else:
            flash('Invalid amount format', 'error')
        return None

    return {
        'account_id': int(account_id),
        'category_id': int(category_id),
        'date': transaction_date,
        'amount': amount,
        'transaction_type': transaction_type,
        'description': description
    }


def _update_account_balance(account_id: int, amount: Decimal, transaction_type: str) -> None:
    """Update account balance based on transaction type."""
    account = Account.query.get(account_id)
    amount_decimal = Decimal(str(amount))
    if transaction_type == 'Income':
        account.current_balance += amount_decimal
    else:
        account.current_balance -= amount_decimal


def _update_affected_budgets(
    category_id: int,
    transaction_date: date,
    transaction_type: str
) -> None:
    """Update budgets affected by a transaction change."""
    if transaction_type != 'Expense':
        return

    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=category_id,
        month=transaction_date.month,
        year=transaction_date.year
    ).all()

    for budget in budgets:
        budget.update_current_spent()


def _check_category_limit(category_id: int, amount: Decimal) -> Optional[str]:
    """Check if amount exceeds category's max_single_amount limit."""
    category = Category.query.get(category_id)
    if not category or not category.max_single_amount:
        return None

    amount_decimal = Decimal(str(amount))
    if amount_decimal > category.max_single_amount:
        return (
            f'⚠️ This amount ({float(amount_decimal):.2f}) exceeds the limit '
            f'({float(category.max_single_amount):.2f}) set for "{category.name}". '
            f'Please confirm to proceed.'
        )
    return None


def _is_limit_confirmed() -> bool:
    """Check if user has confirmed the limit override."""
    return request.form.get('confirm_limit') == 'true'


@transaction_bp.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id: int):
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        user_id=current_user.id
    ).first()

    if not transaction:
        flash('Transaction not found', 'error')
        return redirect(url_for('transaction.transactions'))

    if request.method == 'GET':
        return _render_edit_form(transaction)

    return _update_transaction(transaction)


def _render_edit_form(transaction: Transaction):
    """Render the edit transaction form with category limits data."""
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    category_limits = _build_category_limits_json(categories)

    return render_template(
        'edit_transaction.html',
        transaction=transaction,
        accounts=accounts,
        categories=categories,
        category_limits=category_limits
    )


def _update_transaction(transaction: Transaction):
    """Process transaction update form submission with limit checking."""
    try:
        old_amount = Decimal(str(transaction.amount))
        old_type = transaction.transaction_type
        old_account_id = transaction.account_id
        old_category_id = transaction.category_id
        old_date = transaction.date

        new_category_id = int(request.form.get('category_id'))
        amount_str = request.form.get('amount')
        new_type = request.form.get('transaction_type')
        date_str = request.form.get('date')

        if new_type not in ['Income', 'Expense']:
            flash('Invalid transaction type', 'error')
            return redirect(
                url_for('transaction.edit_transaction', transaction_id=transaction.id)
            )

        try:
            new_amount = Decimal(str(amount_str))
            transaction_date = date.fromisoformat(date_str)
        except (ValueError, TypeError) as e:
            if isinstance(e, ValueError) and 'date' in str(e).lower():
                flash('Invalid date format', 'error')
            else:
                flash('Invalid amount format', 'error')
            return redirect(
                url_for('transaction.edit_transaction', transaction_id=transaction.id)
            )

        limit_warning = _check_category_limit(new_category_id, new_amount)
        if limit_warning and not _is_limit_confirmed():
            flash(limit_warning, 'warning')
            return redirect(
                url_for('transaction.edit_transaction', transaction_id=transaction.id)
            )

        _reverse_old_balance(old_account_id, old_amount, old_type)

        transaction.account_id = int(request.form.get('account_id'))
        transaction.category_id = new_category_id
        transaction.date = transaction_date
        transaction.amount = new_amount
        transaction.transaction_type = new_type
        transaction.description = request.form.get('description', '')

        _update_account_balance(
            transaction.account_id,
            transaction.amount,
            transaction.transaction_type
        )

        _update_affected_budgets(old_category_id, old_date, old_type)
        _update_affected_budgets(new_category_id, transaction_date, new_type)

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transaction.transactions'))

    except Exception as e:
        flash(f'Error updating transaction: {str(e)}', 'error')
        return redirect(
            url_for('transaction.edit_transaction', transaction_id=transaction.id)
        )


def _reverse_old_balance(account_id: int, amount: Decimal, transaction_type: str) -> None:
    """Reverse the account balance change from a transaction."""
    account = Account.query.get(account_id)
    amount_decimal = Decimal(str(amount))
    if transaction_type == 'Income':
        account.current_balance -= amount_decimal
    else:
        account.current_balance += amount_decimal


@transaction_bp.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id: int):
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        user_id=current_user.id
    ).first()

    if not transaction:
        flash('Transaction not found', 'error')
        return redirect(url_for('transaction.transactions'))

    try:
        category_id = transaction.category_id
        transaction_date = transaction.date
        transaction_type = transaction.transaction_type

        _reverse_old_balance(transaction.account_id, transaction.amount, transaction.transaction_type)
        db.session.delete(transaction)
        _update_affected_budgets(category_id, transaction_date, transaction_type)
        db.session.commit()
        flash('Transaction deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting transaction: {str(e)}', 'error')

    return redirect(url_for('transaction.transactions'))

