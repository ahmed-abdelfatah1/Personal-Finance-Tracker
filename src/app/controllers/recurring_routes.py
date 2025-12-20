"""Recurring transaction routes - manage and auto-generate recurring transactions."""

from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..repositories import (
    RecurringTransactionRepository,
    TransactionRepository,
    AccountRepository,
    CategoryRepository
)

recurring_bp = Blueprint('recurring', __name__)


@recurring_bp.route('/recurring')
@login_required
def recurring_list():
    """Display all recurring transactions."""
    recurring_txns = RecurringTransactionRepository.get_all_by_user(current_user.id)
    
    return render_template('recurring.html', recurring_txns=recurring_txns)


@recurring_bp.route('/recurring/add', methods=['GET', 'POST'])
@login_required
def add_recurring():
    """Add a new recurring transaction."""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            account_id = int(request.form.get('account_id'))
            category_id = int(request.form.get('category_id'))
            amount = Decimal(request.form.get('amount'))
            transaction_type = request.form.get('transaction_type')
            frequency = request.form.get('frequency')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            description = request.form.get('description')

            # Validate
            if not all([name, account_id, category_id, amount, transaction_type, frequency, start_date_str]):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('recurring.add_recurring'))

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = None
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            # Calculate next due date
            next_due = calculate_next_due(start_date, frequency)

            RecurringTransactionRepository.create(
                user_id=current_user.id,
                account_id=account_id,
                category_id=category_id,
                name=name,
                amount=amount,
                transaction_type=transaction_type,
                frequency=frequency,
                start_date=start_date,
                next_due=next_due,
                end_date=end_date,
                description=description,
                is_active=True
            )

            flash(f'Recurring transaction "{name}" created successfully!', 'success')
            return redirect(url_for('recurring.recurring_list'))

        except Exception as e:
            RecurringTransactionRepository.rollback()
            flash(f'Error creating recurring transaction: {str(e)}', 'error')
            return redirect(url_for('recurring.add_recurring'))

    accounts = AccountRepository.get_all_by_user(current_user.id)
    categories = CategoryRepository.get_all_by_user(current_user.id)
    return render_template('recurring_form.html', recurring=None, accounts=accounts, categories=categories)


@recurring_bp.route('/recurring/<int:recurring_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recurring(recurring_id):
    """Edit a recurring transaction."""
    recurring = RecurringTransactionRepository.get_by_id_and_user_or_404(
        recurring_id, current_user.id
    )

    if request.method == 'POST':
        try:
            start_date_str = request.form.get('start_date')
            start_date = None
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
            end_date_str = request.form.get('end_date')
            end_date = None
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            RecurringTransactionRepository.update(
                recurring,
                name=request.form.get('name'),
                account_id=int(request.form.get('account_id')),
                category_id=int(request.form.get('category_id')),
                amount=Decimal(request.form.get('amount')),
                transaction_type=request.form.get('transaction_type'),
                frequency=request.form.get('frequency'),
                description=request.form.get('description'),
                start_date=start_date,
                end_date=end_date
            )
            flash(f'Recurring transaction "{recurring.name}" updated!', 'success')
            return redirect(url_for('recurring.recurring_list'))

        except Exception as e:
            RecurringTransactionRepository.rollback()
            flash(f'Error updating recurring transaction: {str(e)}', 'error')

    accounts = AccountRepository.get_all_by_user(current_user.id)
    categories = CategoryRepository.get_all_by_user(current_user.id)
    return render_template('recurring_form.html', recurring=recurring, accounts=accounts, categories=categories)


@recurring_bp.route('/recurring/<int:recurring_id>/delete', methods=['POST'])
@login_required
def delete_recurring(recurring_id):
    """Delete a recurring transaction."""
    recurring = RecurringTransactionRepository.get_by_id_and_user_or_404(
        recurring_id, current_user.id
    )
    
    try:
        name = recurring.name
        RecurringTransactionRepository.delete(recurring)
        flash(f'Recurring transaction "{name}" deleted!', 'success')
    except Exception as e:
        RecurringTransactionRepository.rollback()
        flash(f'Error deleting recurring transaction: {str(e)}', 'error')
    
    return redirect(url_for('recurring.recurring_list'))


@recurring_bp.route('/recurring/<int:recurring_id>/toggle', methods=['POST'])
@login_required
def toggle_recurring(recurring_id):
    """Toggle active status of a recurring transaction."""
    recurring = RecurringTransactionRepository.get_by_id_and_user_or_404(
        recurring_id, current_user.id
    )
    
    try:
        RecurringTransactionRepository.toggle_active(recurring)
        status = "activated" if recurring.is_active else "deactivated"
        flash(f'Recurring transaction "{recurring.name}" {status}!', 'success')
    except Exception as e:
        RecurringTransactionRepository.rollback()
        flash(f'Error toggling recurring transaction: {str(e)}', 'error')
    
    return redirect(url_for('recurring.recurring_list'))


@recurring_bp.route('/recurring/generate', methods=['POST'])
@login_required
def generate_transactions():
    """Manually trigger generation of due recurring transactions."""
    try:
        count = generate_due_transactions(current_user.id)
        flash(f'Generated {count} transaction(s) from recurring schedules!', 'success')
    except Exception as e:
        flash(f'Error generating transactions: {str(e)}', 'error')
    
    return redirect(url_for('recurring.recurring_list'))


def calculate_next_due(current_date, frequency):
    """Calculate the next due date based on frequency."""
    if frequency == 'daily':
        return current_date + timedelta(days=1)
    elif frequency == 'weekly':
        return current_date + timedelta(weeks=1)
    elif frequency == 'monthly':
        # Add one month
        month = current_date.month
        year = current_date.year
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        try:
            return current_date.replace(year=year, month=month)
        except ValueError:
            # Handle day overflow (e.g., Jan 31 -> Feb 28)
            return current_date.replace(year=year, month=month, day=1) + timedelta(days=27)
    elif frequency == 'yearly':
        return current_date.replace(year=current_date.year + 1)
    else:
        return current_date


def generate_due_transactions(user_id):
    """Generate transactions for all due recurring transactions."""
    today = datetime.now().date()
    count = 0
    
    recurring_txns = RecurringTransactionRepository.get_due(user_id, today)
    
    for recurring in recurring_txns:
        # Check if end date has passed
        if recurring.end_date and today > recurring.end_date:
            RecurringTransactionRepository.deactivate(recurring)
            continue
        
        # Create the transaction
        TransactionRepository.create(
            user_id=recurring.user_id,
            account_id=recurring.account_id,
            category_id=recurring.category_id,
            transaction_date=recurring.next_due,
            amount=recurring.amount,
            transaction_type=recurring.transaction_type,
            description=f"{recurring.name} (Auto-generated)",
            notes=f"Generated from recurring transaction: {recurring.name}"
        )
        
        # Update account balance
        account = AccountRepository.get_by_id(recurring.account_id)
        if account:
            AccountRepository.update_balance(
                account,
                recurring.amount,
                is_income=(recurring.transaction_type == 'Income')
            )
        
        # Update recurring transaction
        next_due = calculate_next_due(recurring.next_due, recurring.frequency)
        RecurringTransactionRepository.mark_generated(recurring, recurring.next_due, next_due)
        
        count += 1
    
    return count
