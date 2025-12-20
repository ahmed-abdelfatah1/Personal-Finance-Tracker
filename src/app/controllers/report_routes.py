"""Report routes - financial reports and analytics."""

import csv
import json
from io import StringIO
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user

from ..repositories import (
    TransactionRepository,
    AccountRepository,
    CategoryRepository,
    CurrencyRepository
)
from ..utils.currency_utils import convert_transaction_to_base

report_bp = Blueprint('report', __name__)


@report_bp.route('/reports')
@login_required
def reports():
    """Display financial reports page."""
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
    
    # Get date range from query params or default to current month
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_date = request.args.get('start_date', 
                                  (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('report.reports'))
    
    # Generate report data with selected currency
    report_data = generate_report(current_user.id, start, end, selected_currency_code)
    
    # Get all available currencies for the selector
    all_currencies = CurrencyRepository.get_all()
    
    return render_template('reports.html', 
                         report=report_data,
                         start_date=start_date,
                         end_date=end_date,
                         selected_currency=selected_currency_obj,
                         selected_currency_code=selected_currency_code if 'selected_currency_code' in locals() else selected_currency_obj.code,
                         currencies=all_currencies)


@report_bp.route('/reports/export')
@login_required
def export_report():
    """Export financial report as CSV."""
    # Get date range
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    start_date = request.args.get('start_date', 
                                  (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('report.reports'))
    
    # Get transactions
    transactions = TransactionRepository.get_by_date_range(
        current_user.id, start, end
    )
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Type', 'Category', 'Account', 'Amount', 'Description', 'Notes'])
    
    # Write data
    for txn in transactions:
        writer.writerow([
            txn.date.strftime('%Y-%m-%d'),
            txn.transaction_type,
            txn.category.name if txn.category else 'N/A',
            txn.account.name if txn.account else 'N/A',
            float(txn.amount),
            txn.description or '',
            txn.notes or ''
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=financial_report_{start_date}_to_{end_date}.csv'
    
    return response


def generate_report(user_id: int, start_date, end_date, target_currency: str = None) -> dict:
    """Generate financial report data for given date range with currency conversion."""
    from ..models import User
    user = User.query.get(user_id)
    if target_currency is None:
        target_currency = user.default_currency if user else 'EGP'
    
    # Get all transactions in range
    transactions = TransactionRepository.get_by_date_range(user_id, start_date, end_date)
    
    # Calculate totals with currency conversion to target currency
    total_income = Decimal('0.00')
    total_expense = Decimal('0.00')
    
    for txn in transactions:
        converted_amount = CurrencyRepository.convert_amount(
            txn.amount,
            txn.account.currency,
            target_currency
        )
        if txn.transaction_type == 'Income':
            total_income += converted_amount
        elif txn.transaction_type == 'Expense':
            total_expense += converted_amount
    
    net_savings = total_income - total_expense
    
    # Category breakdown with currency conversion
    category_totals = {}
    for txn in transactions:
        converted_amount = CurrencyRepository.convert_amount(
            txn.amount,
            txn.account.currency,
            target_currency
        )
        key = (txn.category.name if txn.category else 'Unknown', 
               txn.category.category_type if txn.category else 'Unknown')
        if key not in category_totals:
            category_totals[key] = Decimal('0.00')
        category_totals[key] += converted_amount
    
    category_breakdown = [
        (name, cat_type, float(total)) 
        for (name, cat_type), total in category_totals.items()
    ]
    
    # Account balances
    accounts = AccountRepository.get_all_by_user(user_id)
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_savings': net_savings,
        'transaction_count': len(transactions),
        'category_breakdown': category_breakdown,
        'accounts': accounts,
        'transactions': transactions[:10],  # Latest 10 for preview
        'currency': target_currency
    }


@report_bp.route('/reports/monthly-cash-flow')
@login_required
def monthly_cash_flow():
    """Display monthly net cash flow report with chart data."""
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
    
    # Get year from query params or default to current year
    year = request.args.get('year', datetime.now().year)
    
    try:
        year = int(year)
    except ValueError:
        year = datetime.now().year
    
    # Generate monthly cash flow data with selected currency
    monthly_data = generate_monthly_cash_flow(current_user.id, year, selected_currency_code)
    
    # Get all available currencies for the selector
    all_currencies = CurrencyRepository.get_all()
    
    return render_template(
        'monthly_cash_flow.html',
        monthly_data=monthly_data,
        year=year,
        selected_currency=selected_currency_obj,
        selected_currency_code=selected_currency_code,
        currencies=all_currencies
    )


@report_bp.route('/reports/monthly-cash-flow/chart-data')
@login_required
def monthly_cash_flow_chart_data():
    """API endpoint to get monthly cash flow chart data as JSON."""
    # Get selected currency from query parameter or use user's default
    selected_currency_code = request.args.get('currency', current_user.default_currency or 'EGP')
    
    # Validate currency exists
    currency = CurrencyRepository.get_by_code(selected_currency_code)
    if not currency:
        selected_currency_code = current_user.default_currency or 'EGP'
    
    year = request.args.get('year', datetime.now().year)

    try:
        year = int(year)
    except ValueError:
        year = datetime.now().year

    monthly_data = generate_monthly_cash_flow(current_user.id, year, selected_currency_code)
    
    # Format data for chart.js
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    income_data = [float(monthly_data[i]['income']) for i in range(12)]
    expense_data = [float(monthly_data[i]['expense']) for i in range(12)]
    net_data = [float(monthly_data[i]['net']) for i in range(12)]
    
    chart_data = {
        'labels': months,
        'datasets': [
            {
                'label': 'Income',
                'data': income_data,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            },
            {
                'label': 'Expenses',
                'data': expense_data,
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1
            },
            {
                'label': 'Net Cash Flow',
                'data': net_data,
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 2,
                'type': 'line',
                'fill': False
            }
        ]
    }
    
    return jsonify(chart_data)


def generate_monthly_cash_flow(user_id: int, year: int, target_currency: str = None) -> list:
    """Generate monthly cash flow data for a given year with currency conversion."""
    from ..models import User
    user = User.query.get(user_id)
    if target_currency is None:
        target_currency = user.default_currency if user else 'EGP'
    
    monthly_data = []
    
    for month in range(1, 13):
        # Calculate start and end dates for the month
        start_date = datetime(year, month, 1).date()
        
        # Get last day of month
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # Get transactions for the month
        transactions = TransactionRepository.get_by_date_range(
            user_id, start_date, end_date
        )
        
        # Calculate totals with currency conversion to target currency
        income = Decimal('0.00')
        expense = Decimal('0.00')
        
        for txn in transactions:
            converted_amount = CurrencyRepository.convert_amount(
                txn.amount,
                txn.account.currency,
                target_currency
            )
            if txn.transaction_type == 'Income':
                income += converted_amount
            elif txn.transaction_type == 'Expense':
                expense += converted_amount
        
        net = income - expense
        
        monthly_data.append({
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B'),
            'income': income,
            'expense': expense,
            'net': net,
            'transaction_count': len(transactions)
        })
    
    return monthly_data

