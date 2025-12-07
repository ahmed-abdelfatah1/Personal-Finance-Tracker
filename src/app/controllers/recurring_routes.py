"""Recurring transaction routes - manage and auto-generate recurring transactions."""

from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models import RecurringTransaction, Transaction, Account, Category

recurring_bp = Blueprint('recurring', __name__)


@recurring_bp.route('/recurring')
@login_required
def recurring_list():
    """Display all recurring transactions."""
    recurring_txns = RecurringTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(RecurringTransaction.next_due).all()
    
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

            new_recurring = RecurringTransaction(
                user_id=current_user.id,
                account_id=account_id,
                category_id=category_id,
                name=name,
                amount=amount,
                transaction_type=transaction_type,
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                next_due=next_due,
                description=description,
                is_active=True
            )

            db.session.add(new_recurring)
            db.session.commit()

            flash(f'Recurring transaction "{name}" created successfully!', 'success')
            return redirect(url_for('recurring.recurring_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating recurring transaction: {str(e)}', 'error')
            return redirect(url_for('recurring.add_recurring'))

    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('recurring_form.html', recurring=None, accounts=accounts, categories=categories)


@recurring_bp.route('/recurring/<int:recurring_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recurring(recurring_id):
    """Edit a recurring transaction."""
    recurring = RecurringTransaction.query.filter_by(
        id=recurring_id, user_id=current_user.id
    ).first_or_404()

    if request.method == 'POST':
        try:
            recurring.name = request.form.get('name')
            recurring.account_id = int(request.form.get('account_id'))
            recurring.category_id = int(request.form.get('category_id'))
            recurring.amount = Decimal(request.form.get('amount'))
            recurring.transaction_type = request.form.get('transaction_type')
            recurring.frequency = request.form.get('frequency')
            recurring.description = request.form.get('description')
            
            start_date_str = request.form.get('start_date')
            if start_date_str:
                recurring.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            
            end_date_str = request.form.get('end_date')
            if end_date_str:
                recurring.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                recurring.end_date = None

            db.session.commit()
            flash(f'Recurring transaction "{recurring.name}" updated!', 'success')
            return redirect(url_for('recurring.recurring_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating recurring transaction: {str(e)}', 'error')

    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('recurring_form.html', recurring=recurring, accounts=accounts, categories=categories)


@recurring_bp.route('/recurring/<int:recurring_id>/delete', methods=['POST'])
@login_required
def delete_recurring(recurring_id):
    """Delete a recurring transaction."""
    recurring = RecurringTransaction.query.filter_by(
        id=recurring_id, user_id=current_user.id
    ).first_or_404()
    
    try:
        name = recurring.name
        db.session.delete(recurring)
        db.session.commit()
        flash(f'Recurring transaction "{name}" deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting recurring transaction: {str(e)}', 'error')
    
    return redirect(url_for('recurring.recurring_list'))


@recurring_bp.route('/recurring/<int:recurring_id>/toggle', methods=['POST'])
@login_required
def toggle_recurring(recurring_id):
    """Toggle active status of a recurring transaction."""
    recurring = RecurringTransaction.query.filter_by(
        id=recurring_id, user_id=current_user.id
    ).first_or_404()
    
    try:
        recurring.is_active = not recurring.is_active
        db.session.commit()
        status = "activated" if recurring.is_active else "deactivated"
        flash(f'Recurring transaction "{recurring.name}" {status}!', 'success')
    except Exception as e:
        db.session.rollback()
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
    
    recurring_txns = RecurringTransaction.query.filter_by(
        user_id=user_id,
        is_active=True
    ).filter(
        RecurringTransaction.next_due <= today
    ).all()
    
    for recurring in recurring_txns:
        # Check if end date has passed
        if recurring.end_date and today > recurring.end_date:
            recurring.is_active = False
            continue
        
        # Create the transaction
        new_transaction = Transaction(
            user_id=recurring.user_id,
            account_id=recurring.account_id,
            category_id=recurring.category_id,
            date=recurring.next_due,
            amount=recurring.amount,
            transaction_type=recurring.transaction_type,
            description=f"{recurring.name} (Auto-generated)",
            notes=f"Generated from recurring transaction: {recurring.name}"
        )
        
        db.session.add(new_transaction)
        
        # Update account balance
        account = Account.query.get(recurring.account_id)
        if account:
            if recurring.transaction_type == 'Income':
                account.current_balance += recurring.amount
            else:
                account.current_balance -= recurring.amount
        
        # Update recurring transaction
        recurring.last_generated = recurring.next_due
        recurring.next_due = calculate_next_due(recurring.next_due, recurring.frequency)
        
        count += 1
    
    db.session.commit()
    return count
