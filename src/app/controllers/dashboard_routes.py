"""Dashboard routes - main dashboard view."""

from datetime import datetime
from decimal import Decimal
from typing import List

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Transaction, Budget

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


def _get_recent_transactions() -> List[Transaction]:
    """Fetch the 5 most recent transactions for the current user."""
    return Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc()).limit(5).all()


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
    result = db.session.query(
        db.func.coalesce(db.func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == transaction_type,
        db.extract('month', Transaction.date) == month,
        db.extract('year', Transaction.date) == year
    ).scalar()

    return Decimal(str(result))


def _get_budget_alerts() -> List[dict]:
    """Get list of budgets that are over threshold or over budget."""
    now = datetime.now()

    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=now.month,
        year=now.year
    ).all()

    alerts = []
    for budget in budgets:
        budget.update_current_spent()

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

