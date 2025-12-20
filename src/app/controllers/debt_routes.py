"""Debt routes - CRUD operations for debts and loans."""

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..repositories import DebtRepository

debt_bp = Blueprint('debt', __name__)


@debt_bp.route('/debts')
@login_required
def debts():
    """Display all debts and loans for the current user."""
    all_debts = DebtRepository.get_all_by_user(current_user.id)
    debts_list = DebtRepository.get_debts(current_user.id)
    loans_list = DebtRepository.get_loans(current_user.id)
    total_debt = DebtRepository.get_total_debt(current_user.id)
    total_loan = DebtRepository.get_total_loan(current_user.id)

    return render_template(
        'debts.html',
        all_debts=all_debts,
        debts=debts_list,
        loans=loans_list,
        total_debt=total_debt,
        total_loan=total_loan
    )


@debt_bp.route('/debts/add', methods=['GET', 'POST'])
@login_required
def add_debt():
    """Add a new debt or loan."""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            debt_type = request.form.get('debt_type')
            principal_amount = Decimal(request.form.get('principal_amount', 0))
            remaining_amount_str = request.form.get('remaining_amount', '')
            interest_rate_str = request.form.get('interest_rate', '')
            minimum_payment_str = request.form.get('minimum_payment', '')
            due_date_str = request.form.get('due_date', '')
            lender_name = request.form.get('lender_name', '')
            description = request.form.get('description', '')

            if not name or not debt_type or principal_amount <= 0:
                flash('Name, type, and principal amount are required', 'error')
                return redirect(url_for('debt.add_debt'))

            if debt_type not in ['Debt', 'Loan']:
                flash('Invalid debt type', 'error')
                return redirect(url_for('debt.add_debt'))

            remaining_amount = None
            if remaining_amount_str:
                remaining_amount = Decimal(remaining_amount_str)

            interest_rate = None
            if interest_rate_str:
                interest_rate = Decimal(interest_rate_str)

            minimum_payment = None
            if minimum_payment_str:
                minimum_payment = Decimal(minimum_payment_str)

            due_date = None
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

            DebtRepository.create(
                user_id=current_user.id,
                name=name,
                debt_type=debt_type,
                principal_amount=principal_amount,
                remaining_amount=remaining_amount,
                interest_rate=interest_rate,
                minimum_payment=minimum_payment,
                due_date=due_date,
                lender_name=lender_name if lender_name else None,
                description=description if description else None
            )

            flash(f'{debt_type} "{name}" created successfully!', 'success')
            return redirect(url_for('debt.debts'))

        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('debt.add_debt'))
        except Exception as e:
            from ..extensions import db
            db.session.rollback()
            flash(f'Error creating debt: {str(e)}', 'error')
            return redirect(url_for('debt.add_debt'))

    return render_template('debt_form.html', debt=None)


@debt_bp.route('/debts/<int:debt_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_debt(debt_id: int):
    """Edit an existing debt."""
    debt = DebtRepository.get_by_id_and_user_or_404(debt_id, current_user.id)

    if request.method == 'POST':
        try:
            due_date_str = request.form.get('due_date', '')
            due_date = None
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

            interest_rate_str = request.form.get('interest_rate', '')
            interest_rate = None
            if interest_rate_str:
                interest_rate = Decimal(interest_rate_str)

            minimum_payment_str = request.form.get('minimum_payment', '')
            minimum_payment = None
            if minimum_payment_str:
                minimum_payment = Decimal(minimum_payment_str)

            DebtRepository.update(
                debt,
                name=request.form.get('name'),
                debt_type=request.form.get('debt_type'),
                principal_amount=Decimal(request.form.get('principal_amount', 0)),
                remaining_amount=Decimal(request.form.get('remaining_amount', 0)),
                interest_rate=interest_rate,
                minimum_payment=minimum_payment,
                due_date=due_date,
                lender_name=request.form.get('lender_name') or None,
                description=request.form.get('description') or None
            )

            flash(f'Debt "{debt.name}" updated successfully!', 'success')
            return redirect(url_for('debt.debts'))

        except ValueError as e:
            from ..extensions import db
            db.session.rollback()
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('debt.edit_debt', debt_id=debt_id))
        except Exception as e:
            from ..extensions import db
            db.session.rollback()
            flash(f'Error updating debt: {str(e)}', 'error')
            return redirect(url_for('debt.edit_debt', debt_id=debt_id))

    return render_template('debt_form.html', debt=debt)


@debt_bp.route('/debts/<int:debt_id>/delete', methods=['POST'])
@login_required
def delete_debt(debt_id: int):
    """Delete a debt."""
    debt = DebtRepository.get_by_id_and_user_or_404(debt_id, current_user.id)

    try:
        debt_name = debt.name
        DebtRepository.delete(debt)
        flash(f'Debt "{debt_name}" deleted successfully!', 'success')
    except Exception as e:
        from ..extensions import db
        db.session.rollback()
        flash(f'Error deleting debt: {str(e)}', 'error')

    return redirect(url_for('debt.debts'))


@debt_bp.route('/debts/<int:debt_id>/payment', methods=['POST'])
@login_required
def make_payment(debt_id: int):
    """Record a payment on a debt."""
    debt = DebtRepository.get_by_id_and_user_or_404(debt_id, current_user.id)

    try:
        payment_amount = Decimal(request.form.get('payment_amount', 0))

        if payment_amount <= 0:
            flash('Payment amount must be positive', 'error')
            return redirect(url_for('debt.debts'))

        DebtRepository.make_payment(debt, payment_amount)

        if debt.is_paid_off:
            flash(f'Payment recorded! Debt "{debt.name}" is now fully paid off!', 'success')
        else:
            flash(f'Payment of {payment_amount} EGP recorded for "{debt.name}"', 'success')

    except ValueError:
        flash('Invalid payment amount', 'error')
    except Exception as e:
        from ..extensions import db
        db.session.rollback()
        flash(f'Error recording payment: {str(e)}', 'error')

    return redirect(url_for('debt.debts'))

