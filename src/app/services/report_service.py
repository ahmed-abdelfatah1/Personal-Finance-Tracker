"""Report Service - Business logic for report generation."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict
from collections import defaultdict

from ..models.report_models import (
    ReportData, CategoryBreakdown, AccountSummary, MonthlyData
)
from ..models.finance_models import Transaction
from ..repositories.report_repository import ReportRepository


class ReportService:
    """Service for report generation and calculations."""
    
    def __init__(self):
        self.repository = ReportRepository()
    
    def generate_report(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        transaction_type_filter: Optional[str] = None,
        account_ids: Optional[List[int]] = None
    ) -> ReportData:
        """Generate comprehensive financial report."""
        # Validate date range
        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")
        
        # Get transactions
        transactions = self.repository.get_transactions_by_date_range(
            user_id, start_date, end_date, transaction_type_filter, account_ids
        )
        
        # Calculate totals
        total_income = sum(
            (t.amount for t in transactions if t.transaction_type == 'Income'),
            Decimal('0.00')
        )
        total_expenses = sum(
            (t.amount for t in transactions if t.transaction_type == 'Expense'),
            Decimal('0.00')
        )
        net_savings = total_income - total_expenses
        
        # Get category breakdowns
        income_transactions = [t for t in transactions if t.transaction_type == 'Income']
        expense_transactions = [t for t in transactions if t.transaction_type == 'Expense']
        
        income_by_category = self.get_category_breakdown(income_transactions, total_income)
        expenses_by_category = self.get_category_breakdown(expense_transactions, total_expenses)
        
        # Get account summaries
        accounts = self.repository.get_user_accounts(user_id, account_ids)
        account_summaries = [
            AccountSummary(
                account_id=acc.id,
                account_name=acc.name,
                current_balance=acc.current_balance,
                currency=acc.currency
            )
            for acc in accounts
        ]
        
        return ReportData(
            start_date=start_date,
            end_date=end_date,
            total_income=total_income,
            total_expenses=total_expenses,
            net_savings=net_savings,
            income_by_category=income_by_category,
            expenses_by_category=expenses_by_category,
            account_summaries=account_summaries,
            transaction_count=len(transactions)
        )
    
    def get_category_breakdown(
        self,
        transactions: List[Transaction],
        total: Decimal
    ) -> List[CategoryBreakdown]:
        """Calculate category-wise breakdown with percentages."""
        if not transactions:
            return []
        
        # Group by category
        category_data = defaultdict(lambda: {'amount': Decimal('0.00'), 'count': 0, 'name': ''})
        
        for t in transactions:
            category_data[t.category_id]['amount'] += t.amount
            category_data[t.category_id]['count'] += 1
            category_data[t.category_id]['name'] = t.category.name
        
        # Calculate percentages and create breakdown list
        breakdowns = []
        for cat_id, data in category_data.items():
            percentage = float((data['amount'] / total) * 100) if total > 0 else 0.0
            breakdowns.append(CategoryBreakdown(
                category_id=cat_id,
                category_name=data['name'],
                amount=data['amount'],
                percentage=percentage,
                transaction_count=data['count']
            ))
        
        # Sort by amount descending
        breakdowns.sort(key=lambda x: x.amount, reverse=True)
        
        return breakdowns
    
    def get_monthly_comparison(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[MonthlyData]:
        """Generate month-by-month comparison data."""
        aggregates = self.repository.get_monthly_aggregates(user_id, start_date, end_date)
        
        # Group by month/year
        monthly_dict = defaultdict(lambda: {'income': Decimal('0.00'), 'expenses': Decimal('0.00')})
        
        for row in aggregates:
            key = (int(row.year), int(row.month))
            if row.transaction_type == 'Income':
                monthly_dict[key]['income'] = Decimal(str(row.total))
            elif row.transaction_type == 'Expense':
                monthly_dict[key]['expenses'] = Decimal(str(row.total))
        
        # Create monthly data list
        monthly_data = []
        prev_net_savings = None
        
        for (year, month), data in sorted(monthly_dict.items()):
            net_savings = data['income'] - data['expenses']
            
            # Calculate month-over-month change
            mom_change = None
            if prev_net_savings is not None and prev_net_savings != 0:
                mom_change = float(((net_savings - prev_net_savings) / prev_net_savings) * 100)
            
            monthly_data.append(MonthlyData(
                month=month,
                year=year,
                total_income=data['income'],
                total_expenses=data['expenses'],
                net_savings=net_savings,
                month_over_month_change=mom_change
            ))
            
            prev_net_savings = net_savings
        
        return monthly_data
    
    def get_account_summary(
        self,
        user_id: int,
        account_ids: Optional[List[int]] = None
    ) -> List[AccountSummary]:
        """Get current balance summary for accounts."""
        accounts = self.repository.get_user_accounts(user_id, account_ids)
        
        return [
            AccountSummary(
                account_id=acc.id,
                account_name=acc.name,
                current_balance=acc.current_balance,
                currency=acc.currency
            )
            for acc in accounts
        ]
