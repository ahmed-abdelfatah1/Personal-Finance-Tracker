"""Budget routes - CRUD operations for budgets."""

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Budget, Category

budget_bp = Blueprint('budget', __name__)


@budget_bp.route('/budgets')
@login_required
def budgets():
    now = datetime.now()

    user_budgets = Budget.query.filter_by(
        user_id=current_user.id
    ).order_by(Budget.year.desc(), Budget.month.desc()).all()

    expense_categories = Category.query.filter_by(
        user_id=current_user.id,
        category_type='Expense'
    ).all()

    return render_template(
        'budgets.html',
        budgets=user_budgets,
        categories=expense_categories,
        current_month=now.month,
        current_year=now.year
    )


@budget_bp.route('/set_budget', methods=['GET', 'POST'])
@login_required
def set_budget():
    if request.method == 'GET':
        now = datetime.now()
        categories = Category.query.filter_by(
            user_id=current_user.id,
            category_type='Expense'
        ).all()
        return render_template(
            'set_budget.html',
            categories=categories,
            current_month=now.month,
            current_year=now.year
        )

    try:
        data = _extract_budget_data()
        if not data:
            return redirect(url_for('budget.set_budget'))

        budget, action = _create_or_update_budget(data)
        db.session.commit()

        _flash_budget_result(budget, action, data['category_id'])
        return redirect(url_for('budget.budgets'))

    except ValueError:
        flash('Invalid number format', 'error')
        return redirect(url_for('budget.set_budget'))
    except Exception as e:
        flash(f'Error setting budget: {str(e)}', 'error')
        return redirect(url_for('budget.set_budget'))


def _extract_budget_data() -> dict | None:
    category_id = request.form.get('category_id')
    month = int(request.form.get('month'))
    year = int(request.form.get('year'))
    limit_amount = float(request.form.get('limit_amount'))

    if not all([category_id, month, year, limit_amount]):
        flash('All fields are required', 'error')
        return None

    if not 1 <= month <= 12:
        flash('Month must be between 1 and 12', 'error')
        return None

    if limit_amount <= 0:
        flash('Budget amount must be positive', 'error')
        return None

    return {
        'category_id': category_id,
        'month': month,
        'year': year,
        'limit_amount': limit_amount
    }


def _create_or_update_budget(data: dict) -> tuple[Budget, str]:
    existing = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=data['category_id'],
        month=data['month'],
        year=data['year']
    ).first()

    if existing:
        existing.limit_amount = data['limit_amount']
        existing.update_current_spent()
        return existing, 'updated'

    new_budget = Budget(
        user_id=current_user.id,
        category_id=data['category_id'],
        month=data['month'],
        year=data['year'],
        limit_amount=data['limit_amount']
    )
    new_budget.update_current_spent()
    db.session.add(new_budget)
    return new_budget, 'created'


def _flash_budget_result(budget: Budget, action: str, category_id: int) -> None:
    if budget.check_alert_threshold():
        category = Category.query.get(category_id)
        percentage = budget.get_percentage_used()
        flash(
            f'Budget {action} successfully! ⚠ Warning: {category.name} '
            f'budget is {percentage:.1f}% used.',
            'warning'
        )
    else:
        flash(f'Budget {action} successfully!', 'success')


@budget_bp.route('/delete_budget/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id: int):
    budget = Budget.query.filter_by(
        id=budget_id,
        user_id=current_user.id
    ).first()

    if not budget:
        flash('Budget not found', 'error')
        return redirect(url_for('budget.budgets'))

    try:
        category_name = budget.category.name if budget.category else 'Unknown'
        db.session.delete(budget)
        db.session.commit()
        flash(f'Budget for {category_name} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting budget: {str(e)}', 'error')

    return redirect(url_for('budget.budgets'))

