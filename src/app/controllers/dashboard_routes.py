"""Dashboard routes - main dashboard view."""

from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..repositories import (
    TransactionRepository,
    BudgetRepository,
    CurrencyRepository,
    AccountRepository
)
from ..utils.currency_utils import convert_transaction_to_base

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Display the main dashboard with summary statistics and alerts."""
    from flask import request
    
    # Get selected currency from query parameter or use user's default
    selected_currency_code = request.args.get('currency', current_user.default_currency or 'EGP')
    
    # Validate currency exists and get currency object
    selected_currency_obj = CurrencyRepository.get_by_code(selected_currency_code)
    if not selected_currency_obj:
        selected_currency_code = current_user.default_currency or 'EGP'
        selected_currency_obj = CurrencyRepository.get_by_code(selected_currency_code)
    
    # Fallback to EGP if still not found
    if not selected_currency_obj:
        selected_currency_code = 'EGP'
        selected_currency_obj = CurrencyRepository.get_by_code('EGP')
    
    # Calculate total balance with currency conversion
    total_balance = _calculate_total_balance_converted(selected_currency_code)
    recent_transactions = _get_recent_transactions_with_conversion(selected_currency_code)
    monthly_summary = _calculate_monthly_summary(selected_currency_code)
    budget_alerts = _get_budget_alerts()
    
    # Get account currency breakdown
    accounts = AccountRepository.get_all_by_user(current_user.id)
    user_currency_obj = CurrencyRepository.get_by_code(current_user.default_currency or 'EGP')
    if not user_currency_obj:
        user_currency_obj = CurrencyRepository.get_by_code('EGP')
    
    account_breakdown = []
    for account in accounts:
        account_currency_obj = CurrencyRepository.get_by_code(account.currency)
        converted_balance = CurrencyRepository.convert_amount(
            account.current_balance,
            account.currency,
            selected_currency_code
        )
        account_breakdown.append({
            'name': account.name,
            'currency_code': account.currency,
            'currency_symbol': account_currency_obj.symbol if account_currency_obj and account_currency_obj.symbol else account.currency,
            'original_balance': account.current_balance,
            'converted_balance': converted_balance,
            'needs_conversion': account.currency != selected_currency_code
        })
    
    # Get all available currencies for the selector
    all_currencies = CurrencyRepository.get_all()

    return render_template(
        'dashboard.html',
        user=current_user,
        total_balance=total_balance,
        recent_transactions=recent_transactions,
        monthly_summary=monthly_summary,
        budget_alerts=budget_alerts,
        account_breakdown=account_breakdown,
        selected_currency=selected_currency_obj,
        selected_currency_code=selected_currency_code,
        currencies=all_currencies
    )


def _calculate_total_balance_converted(target_currency: str = None) -> Decimal:
    """Calculate total balance across all accounts, converting to target currency."""
    accounts = AccountRepository.get_all_by_user(current_user.id)
    if target_currency is None:
        target_currency = current_user.default_currency or 'EGP'
    
    total = Decimal('0.00')
    for account in accounts:
        converted_balance = CurrencyRepository.convert_amount(
            account.current_balance,
            account.currency,
            target_currency
        )
        total += converted_balance
    
    return total


def _get_recent_transactions():
    """Fetch the 5 most recent transactions for the current user."""
    return TransactionRepository.get_recent(current_user.id, limit=5)

def _get_recent_transactions_with_conversion(target_currency: str = None):
    """Fetch recent transactions with currency conversion info."""
    from ..repositories import CurrencyRepository
    
    transactions = TransactionRepository.get_recent(current_user.id, limit=5)
    if target_currency is None:
        target_currency = current_user.default_currency or 'EGP'
    
    target_currency_obj = CurrencyRepository.get_by_code(target_currency)
    if not target_currency_obj:
        target_currency_obj = CurrencyRepository.get_by_code('EGP')
    
    transactions_with_conversion = []
    for txn in transactions:
        original_currency_obj = CurrencyRepository.get_by_code(txn.account.currency)
        converted_amount = CurrencyRepository.convert_amount(
            txn.amount,
            txn.account.currency,
            target_currency
        )
        transactions_with_conversion.append({
            'transaction': txn,
            'original_amount': txn.amount,
            'original_currency_code': txn.account.currency,
            'original_currency_symbol': original_currency_obj.symbol if original_currency_obj and original_currency_obj.symbol else txn.account.currency,
            'converted_amount': converted_amount,
            'converted_currency_code': target_currency,
            'converted_currency_symbol': target_currency_obj.symbol if target_currency_obj and target_currency_obj.symbol else target_currency,
            'needs_conversion': txn.account.currency != target_currency
        })
    
    return transactions_with_conversion


def _calculate_monthly_summary(target_currency: str = None) -> dict:
    """Calculate income, expenses, and net for the current month."""
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    income = _get_monthly_total('Income', current_month, current_year, target_currency)
    expenses = _get_monthly_total('Expense', current_month, current_year, target_currency)

    return {
        'income': income,
        'expenses': expenses,
        'net': income - expenses
    }


def _get_monthly_total(
    transaction_type: str,
    month: int,
    year: int,
    target_currency: str = None
) -> Decimal:
    """
    Get total amount for a transaction type in a specific month.
    Converts all amounts to target currency.
    """
    if target_currency is None:
        target_currency = current_user.default_currency or 'EGP'
    
    # Calculate start and end dates for the month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Get all transactions for the month
    transactions = TransactionRepository.get_by_date_range(
        current_user.id,
        start_date,
        end_date
    )
    
    # Filter by type and convert to target currency
    total = Decimal('0.00')
    
    for txn in transactions:
        if txn.transaction_type == transaction_type:
            # Convert transaction amount to target currency
            converted_amount = CurrencyRepository.convert_amount(
                txn.amount,
                txn.account.currency,
                target_currency
            )
            total += converted_amount
    
    return total


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

