"""Transaction routes - CRUD operations for transactions."""

import json
from decimal import Decimal
from typing import Optional

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Transaction, Account, Category

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
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if account_id:
        query = query.filter_by(account_id=account_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if transaction_type in ['Income', 'Expense']:
        query = query.filter_by(transaction_type=transaction_type)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

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
    date = request.form.get('date')
    amount = float(request.form.get('amount'))
    transaction_type = request.form.get('transaction_type')
    description = request.form.get('description', '')

    if not all([account_id, category_id, date, amount, transaction_type]):
        flash('All fields except description are required', 'error')
        return None

    if transaction_type not in ['Income', 'Expense']:
        flash('Invalid transaction type', 'error')
        return None

    return {
        'account_id': account_id,
        'category_id': category_id,
        'date': date,
        'amount': amount,
        'transaction_type': transaction_type,
        'description': description
    }


def _update_account_balance(account_id: int, amount: float, transaction_type: str) -> None:
    """Update account balance based on transaction type."""
    account = Account.query.get(account_id)
    if transaction_type == 'Income':
        account.current_balance += amount
    else:
        account.current_balance -= amount


def _check_category_limit(category_id: int, amount: float) -> Optional[str]:
    """Check if amount exceeds category's max_single_amount limit."""
    category = Category.query.get(category_id)
    if not category or not category.max_single_amount:
        return None

    if Decimal(str(amount)) > category.max_single_amount:
        return (
            f'⚠️ This amount ({amount:.2f}) exceeds the limit '
            f'({category.max_single_amount:.2f}) set for "{category.name}". '
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
        old_amount = float(transaction.amount)
        old_type = transaction.transaction_type
        old_account_id = transaction.account_id

        new_category_id = int(request.form.get('category_id'))
        new_amount = float(request.form.get('amount'))
        new_type = request.form.get('transaction_type')

        if new_type not in ['Income', 'Expense']:
            flash('Invalid transaction type', 'error')
            return redirect(
                url_for('transaction.edit_transaction', transaction_id=transaction.id)
            )

        limit_warning = _check_category_limit(new_category_id, new_amount)
        if limit_warning and not _is_limit_confirmed():
            flash(limit_warning, 'warning')
            return redirect(
                url_for('transaction.edit_transaction', transaction_id=transaction.id)
            )

        transaction.account_id = request.form.get('account_id')
        transaction.category_id = new_category_id
        transaction.date = request.form.get('date')
        transaction.amount = new_amount
        transaction.transaction_type = new_type
        transaction.description = request.form.get('description', '')

        _reverse_old_balance(old_account_id, old_amount, old_type)
        _update_account_balance(
            transaction.account_id,
            transaction.amount,
            transaction.transaction_type
        )

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transaction.transactions'))

    except Exception as e:
        flash(f'Error updating transaction: {str(e)}', 'error')
        return redirect(
            url_for('transaction.edit_transaction', transaction_id=transaction.id)
        )


def _reverse_old_balance(account_id: int, amount: float, transaction_type: str) -> None:
    account = Account.query.get(account_id)
    if transaction_type == 'Income':
        account.current_balance -= amount
    else:
        account.current_balance += amount


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
        _reverse_old_balance(transaction.account_id, transaction.amount, transaction.transaction_type)
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting transaction: {str(e)}', 'error')

    return redirect(url_for('transaction.transactions'))

