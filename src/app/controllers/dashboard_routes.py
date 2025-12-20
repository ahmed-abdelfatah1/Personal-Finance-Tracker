"""Dashboard routes - main dashboard view."""

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..repositories import TransactionRepository, BudgetRepository

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Display the main dashboard with summary statistics and alerts."""
    total_balance = current_user.get_total_balance()
    recent_transactions = _get_recent_transactions()
    monthly_summary = _calculate_monthly_summary()
    budget_alerts = _get_budget_alerts()

    return render_template(
        'dashboard.html',
        user=current_user,
        total_balance=total_balance,
        recent_transactions=recent_transactions,
        monthly_summary=monthly_summary,
        budget_alerts=budget_alerts
    )


def _get_recent_transactions():
    """Fetch the 5 most recent transactions for the current user."""
    return TransactionRepository.get_recent(current_user.id, limit=5)


def _calculate_monthly_summary() -> dict:
    """Calculate income, expenses, and net for the current month."""
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    income = _get_monthly_total('Income', current_month, current_year)
    expenses = _get_monthly_total('Expense', current_month, current_year)

    return {
        'income': income,
        'expenses': expenses,
        'net': income - expenses
    }


def _get_monthly_total(
    transaction_type: str,
    month: int,
    year: int
) -> Decimal:
    """Get total amount for a transaction type in a specific month."""
    return TransactionRepository.get_monthly_total(
        current_user.id, transaction_type, month, year
    )


def _get_budget_alerts():
    """Get list of budgets that are over threshold or over budget."""
    now = datetime.now()

    budgets = BudgetRepository.get_by_month(current_user.id, now.month, now.year)

    alerts = []
    for budget in budgets:
        BudgetRepository.update_spent(budget)

        if budget.is_over_budget:
            alerts.append({
                'category': budget.category.name,
                'color': budget.category.color or '#ef4444',
                'percentage': budget.spent_percentage,
                'spent': budget.current_spent,
                'limit': budget.limit_amount,
                'severity': 'danger',
                'message': f'Over budget by {budget.current_spent - budget.limit_amount:.2f}'
            })
        elif budget.is_over_threshold:
            alerts.append({
                'category': budget.category.name,
                'color': budget.category.color or '#f59e0b',
                'percentage': budget.spent_percentage,
                'spent': budget.current_spent,
                'limit': budget.limit_amount,
                'severity': 'warning',
                'message': f'{budget.spent_percentage:.1f}% of budget used'
            })

    return sorted(alerts, key=lambda x: x['percentage'], reverse=True)

