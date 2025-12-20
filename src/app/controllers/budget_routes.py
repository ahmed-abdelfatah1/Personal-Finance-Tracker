"""Budget routes - CRUD operations for budgets."""

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user

from ..repositories import BudgetRepository, CategoryRepository

budget_bp = Blueprint('budget', __name__)


@budget_bp.route('/budgets')
@login_required
def budgets():
    now = datetime.now()

    user_budgets = BudgetRepository.get_all_by_user(current_user.id)
    expense_categories = CategoryRepository.get_expense_categories(current_user.id)

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
        categories = CategoryRepository.get_expense_categories(current_user.id)
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

        budget, action = BudgetRepository.create_or_update(
            user_id=current_user.id,
            category_id=data['category_id'],
            month=data['month'],
            year=data['year'],
            limit_amount=Decimal(str(data['limit_amount']))
        )

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




def _flash_budget_result(budget, action: str, category_id: int) -> None:
    if budget.check_alert_threshold():
        category = CategoryRepository.get_by_id(category_id)
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
    budget = BudgetRepository.get_by_id_and_user(budget_id, current_user.id)

    if not budget:
        flash('Budget not found', 'error')
        return redirect(url_for('budget.budgets'))

    try:
        category_name = budget.category.name if budget.category else 'Unknown'
        BudgetRepository.delete(budget)
        flash(f'Budget for {category_name} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting budget: {str(e)}', 'error')

    return redirect(url_for('budget.budgets'))

