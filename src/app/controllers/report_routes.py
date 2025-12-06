"""Report routes - Financial reporting and CSV export."""

from flask import Blueprint, render_template, request, flash, make_response
from flask_login import login_required, current_user
from datetime import date, datetime

from ..services.report_service import ReportService
from ..services.csv_export_service import CSVExportService
from ..repositories.report_repository import ReportRepository

report_bp = Blueprint('report', __name__)


@report_bp.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    """Display report generation form and results."""
    report_service = ReportService()
    repository = ReportRepository()
    
    # Get user accounts for filter
    accounts = repository.get_user_accounts(current_user.id)
    
    report_data = None
    monthly_data = None
    
    if request.method == 'POST':
        try:
            # Get form data
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            transaction_type = request.form.get('transaction_type', 'All')
            selected_accounts = request.form.getlist('accounts')
            
            # Parse dates
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            else:
                # Default to current month
                today = date.today()
                start_date = today.replace(day=1)
                end_date = today
            
            # Convert account IDs to integers
            account_ids = [int(aid) for aid in selected_accounts] if selected_accounts else None
            
            # Filter transaction type
            type_filter = transaction_type if transaction_type != 'All' else None
            
            # Generate report
            report_data = report_service.generate_report(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date,
                transaction_type_filter=type_filter,
                account_ids=account_ids
            )
            
            # Generate monthly comparison
            monthly_data = report_service.get_monthly_comparison(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date
            )
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash(f'Error generating report: {str(e)}', 'error')
    else:
        # Default date range for GET request
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today
    
    return render_template(
        'reports.html',
        accounts=accounts,
        report_data=report_data,
        monthly_data=monthly_data,
        start_date=start_date if 'start_date' in locals() else None,
        end_date=end_date if 'end_date' in locals() else None
    )


@report_bp.route('/reports/export', methods=['POST'])
@login_required
def export_csv():
    """Generate and download CSV export of transactions."""
    try:
        # Get form data
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        transaction_type = request.form.get('transaction_type', 'All')
        selected_accounts = request.form.getlist('accounts')
        
        # Parse dates
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to current month
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
        
        # Convert account IDs
        account_ids = [int(aid) for aid in selected_accounts] if selected_accounts else None
        
        # Filter transaction type
        type_filter = transaction_type if transaction_type != 'All' else None
        
        # Get transactions
        repository = ReportRepository()
        transactions = repository.get_transactions_by_date_range(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            transaction_type=type_filter,
            account_ids=account_ids
        )
        
        # Generate CSV
        csv_service = CSVExportService()
        csv_content = csv_service.export_transactions(transactions, start_date, end_date)
        filename = csv_service.generate_filename(start_date, end_date)
        
        # Create response
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting CSV: {str(e)}', 'error')
        return render_template('reports.html')
