"""Report routes - financial reports and analytics."""

import csv
from io import StringIO
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from ..extensions import db
from ..models import Transaction, Category, Account

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
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start,
        Transaction.date <= end
    ).order_by(Transaction.date.desc()).all()
    
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
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    # Calculate totals
    total_income = sum(
        txn.amount for txn in transactions if txn.transaction_type == 'Income'
    )
    total_expense = sum(
        txn.amount for txn in transactions if txn.transaction_type == 'Expense'
    )
    net_savings = total_income - total_expense
    
    # Category breakdown
    category_breakdown = db.session.query(
        Category.name,
        Category.category_type,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).group_by(Category.id, Category.name, Category.category_type).all()
    
    # Account balances
    accounts = Account.query.filter_by(user_id=user_id).all()
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_savings': net_savings,
        'transaction_count': len(transactions),
        'category_breakdown': category_breakdown,
        'accounts': accounts,
        'transactions': transactions[:10]  # Latest 10 for preview
    }

