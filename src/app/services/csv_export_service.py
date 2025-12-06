"""CSV Export Service - Handles CSV file generation."""

import csv
import io
from datetime import date
from typing import List

from ..models.finance_models import Transaction


class CSVExportService:
    """Service for CSV export functionality."""
    
    def export_transactions(
        self,
        transactions: List[Transaction],
        start_date: date,
        end_date: date
    ) -> str:
        """Generate CSV content from transactions."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        writer.writerow([
            'Date',
            'Description',
            'Category',
            'Account',
            'Type',
            'Amount',
            'Notes'
        ])
        
        # Write data rows
        for transaction in transactions:
            writer.writerow([
                transaction.date.strftime('%Y-%m-%d'),
                transaction.description or '',
                transaction.category.name if transaction.category else '',
                transaction.account.name if transaction.account else '',
                transaction.transaction_type,
                str(transaction.amount),
                transaction.notes or ''
            ])
        
        return output.getvalue()
    
    def generate_filename(
        self,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate standardized filename."""
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        return f'transactions_{start_str}_to_{end_str}.csv'
