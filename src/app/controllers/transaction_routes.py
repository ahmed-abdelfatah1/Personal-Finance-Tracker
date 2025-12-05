"""Transaction routes - CRUD operations for transactions."""

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
    category_id = request.args.get('category', type=int)
    transaction_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

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
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template(
        'add_transaction.html',
        accounts=accounts,
        categories=categories
    )


def _create_transaction():
    try:
        data = _extract_transaction_data()
        if not data:
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
    account = Account.query.get(account_id)
    if transaction_type == 'Income':
        account.current_balance += amount
    else:
        account.current_balance -= amount


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
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template(
        'edit_transaction.html',
        transaction=transaction,
        accounts=accounts,
        categories=categories
    )


def _update_transaction(transaction: Transaction):
    try:
        old_amount = transaction.amount
        old_type = transaction.transaction_type
        old_account_id = transaction.account_id

        transaction.account_id = request.form.get('account_id')
        transaction.category_id = request.form.get('category_id')
        transaction.date = request.form.get('date')
        transaction.amount = float(request.form.get('amount'))
        transaction.transaction_type = request.form.get('transaction_type')
        transaction.description = request.form.get('description', '')

        if transaction.transaction_type not in ['Income', 'Expense']:
            flash('Invalid transaction type', 'error')
            return redirect(url_for('transaction.edit_transaction', transaction_id=transaction.id))

        _reverse_old_balance(old_account_id, old_amount, old_type)
        _update_account_balance(transaction.account_id, transaction.amount, transaction.transaction_type)

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transaction.transactions'))

    except Exception as e:
        flash(f'Error updating transaction: {str(e)}', 'error')
        return redirect(url_for('transaction.edit_transaction', transaction_id=transaction.id))


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

