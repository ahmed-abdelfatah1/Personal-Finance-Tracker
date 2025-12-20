"""Transaction Repository - Data access layer for Transaction model."""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import extract

from ..extensions import db
from ..models import Transaction


class TransactionRepository:
    """Repository for Transaction entity database operations."""

    @staticmethod
    def get_by_id(transaction_id: int) -> Optional[Transaction]:
        """Retrieve a transaction by its ID."""
        return Transaction.query.get(transaction_id)

    @staticmethod
    def get_by_id_and_user(transaction_id: int, user_id: int) -> Optional[Transaction]:
        """Retrieve a transaction by ID ensuring it belongs to the user."""
        return Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[Transaction]:
        """Retrieve all transactions for a user ordered by date descending."""
        return Transaction.query.filter_by(user_id=user_id).order_by(
            Transaction.date.desc()
        ).all()

    @staticmethod
    def get_recent(user_id: int, limit: int = 5) -> List[Transaction]:
        """Retrieve the most recent transactions for a user."""
        return Transaction.query.filter_by(user_id=user_id).order_by(
            Transaction.date.desc()
        ).limit(limit).all()

    @staticmethod
    def get_by_account(user_id: int, account_id: int) -> List[Transaction]:
        """Retrieve all transactions for a specific account."""
        return Transaction.query.filter_by(
            user_id=user_id,
            account_id=account_id
        ).order_by(Transaction.date.desc()).all()

    @staticmethod
    def get_by_category(user_id: int, category_id: int) -> List[Transaction]:
        """Retrieve all transactions for a specific category."""
        return Transaction.query.filter_by(
            user_id=user_id,
            category_id=category_id
        ).order_by(Transaction.date.desc()).all()

    @staticmethod
    def get_by_type(user_id: int, transaction_type: str) -> List[Transaction]:
        """Retrieve all transactions of a specific type (Income/Expense)."""
        return Transaction.query.filter_by(
            user_id=user_id,
            transaction_type=transaction_type
        ).order_by(Transaction.date.desc()).all()

    @staticmethod
    def get_by_date_range(
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """Retrieve transactions within a date range."""
        return Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(Transaction.date.desc()).all()

    @staticmethod
    def get_monthly_total(
        user_id: int,
        transaction_type: str,
        month: int,
        year: int
    ) -> Decimal:
        """Calculate total amount for a transaction type in a specific month."""
        result = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar()
        return Decimal(str(result))

    @staticmethod
    def get_category_monthly_total(
        user_id: int,
        category_id: int,
        month: int,
        year: int,
        transaction_type: str = 'Expense'
    ) -> Decimal:
        """Calculate total amount for a category in a specific month."""
        result = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.transaction_type == transaction_type,
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar()
        return Decimal(str(result))

    @staticmethod
    def filter_transactions(
        user_id: int,
        account_id: Optional[int] = None,
        category_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search_query: Optional[str] = None
    ) -> List[Transaction]:
        """
        Filter transactions with multiple optional criteria including text search.
        
        Args:
            user_id: User ID
            account_id: Optional account filter
            category_id: Optional category filter
            transaction_type: Optional type filter (Income/Expense)
            start_date: Optional start date filter
            end_date: Optional end date filter
            search_query: Optional text search in description and notes
        """
        from sqlalchemy import or_
        
        query = Transaction.query.filter_by(user_id=user_id)

        if account_id:
            query = query.filter_by(account_id=account_id)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if transaction_type in ['Income', 'Expense']:
            query = query.filter_by(transaction_type=transaction_type)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        # Text search in description and notes
        if search_query:
            search_term = f'%{search_query}%'
            query = query.filter(
                or_(
                    Transaction.description.ilike(search_term),
                    Transaction.notes.ilike(search_term)
                )
            )

        return query.order_by(Transaction.date.desc()).all()

    @staticmethod
    def create(
        user_id: int,
        account_id: int,
        category_id: int,
        transaction_date: date,
        amount: Decimal,
        transaction_type: str,
        description: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Transaction:
        """Create a new transaction."""
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            date=transaction_date,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            notes=notes
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    @staticmethod
    def update(transaction: Transaction, **kwargs) -> Transaction:
        """Update transaction attributes."""
        for key, value in kwargs.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)
        db.session.commit()
        return transaction

    @staticmethod
    def delete(transaction: Transaction) -> None:
        """Delete a transaction."""
        db.session.delete(transaction)
        db.session.commit()

    @staticmethod
    def save(transaction: Transaction) -> Transaction:
        """Save changes to an existing transaction."""
        db.session.commit()
        return transaction

    @staticmethod
    def add_without_commit(transaction: Transaction) -> Transaction:
        """Add a transaction without committing (for batch operations)."""
        db.session.add(transaction)
        return transaction

    @staticmethod
    def commit() -> None:
        """Commit the current database session."""
        db.session.commit()

