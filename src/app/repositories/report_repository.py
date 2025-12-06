"""Report Repository - Data access for reports."""

from datetime import date
from typing import List, Optional, Dict
from sqlalchemy import func, extract
from decimal import Decimal

from ..extensions import db
from ..models.finance_models import Transaction, Account, Category


class ReportRepository:
    """Repository for report data queries."""
    
    def get_transactions_by_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        transaction_type: Optional[str] = None,
        account_ids: Optional[List[int]] = None
    ) -> List[Transaction]:
        """Query transactions with filters."""
        query = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        
        if transaction_type and transaction_type in ['Income', 'Expense']:
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        if account_ids:
            query = query.filter(Transaction.account_id.in_(account_ids))
        
        return query.all()
    
    def get_monthly_aggregates(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """Get aggregated monthly data."""
        results = db.session.query(
            extract('year', Transaction.date).label('year'),
            extract('month', Transaction.date).label('month'),
            Transaction.transaction_type,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(
            extract('year', Transaction.date),
            extract('month', Transaction.date),
            Transaction.transaction_type
        ).order_by(
            extract('year', Transaction.date),
            extract('month', Transaction.date)
        ).all()
        
        return results
    
    def get_user_accounts(
        self,
        user_id: int,
        account_ids: Optional[List[int]] = None
    ) -> List[Account]:
        """Get user accounts with optional filtering."""
        query = Account.query.filter(Account.user_id == user_id)
        
        if account_ids:
            query = query.filter(Account.id.in_(account_ids))
        
        return query.all()
