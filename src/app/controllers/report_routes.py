"""Report routes - financial reports and analytics."""

import csv
from io import StringIO
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for
from flask_login import login_required, current_user

from ..repositories import TransactionRepository, AccountRepository, CategoryRepository

report_bp = Blueprint('report', __name__)


@report_bp.route('/reports')
@login_required
def reports():
    """Display financial reports page."""
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
    
    # Generate report data
    report_data = generate_report(current_user.id, start, end)
    
    return render_template('reports.html', 
                         report=report_data,
                         start_date=start_date,
                         end_date=end_date)


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


def generate_report(user_id: int, start_date, end_date) -> dict:
    """Generate financial report data for given date range."""
    
    # Get all transactions in range
    transactions = TransactionRepository.get_by_date_range(user_id, start_date, end_date)
    
    # Calculate totals
    total_income = sum(
        txn.amount for txn in transactions if txn.transaction_type == 'Income'
    )
    total_expense = sum(
        txn.amount for txn in transactions if txn.transaction_type == 'Expense'
    )
    net_savings = total_income - total_expense
    
    # Category breakdown - simplified version
    # Note: For full category breakdown with SQL aggregation, 
    # we'd need to add a method to TransactionRepository
    category_totals = {}
    for txn in transactions:
        key = (txn.category.name if txn.category else 'Unknown', 
               txn.category.category_type if txn.category else 'Unknown')
        if key not in category_totals:
            category_totals[key] = 0
        category_totals[key] += float(txn.amount)
    
    category_breakdown = [
        (name, cat_type, total) 
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
        'transactions': transactions[:10]  # Latest 10 for preview
    }

