"""Recurring Transaction Repository - Data access layer for RecurringTransaction model."""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from ..extensions import db
from ..models import RecurringTransaction


class RecurringTransactionRepository:
    """Repository for RecurringTransaction entity database operations."""

    @staticmethod
    def get_by_id(recurring_id: int) -> Optional[RecurringTransaction]:
        """Retrieve a recurring transaction by its ID."""
        return RecurringTransaction.query.get(recurring_id)

    @staticmethod
    def get_by_id_and_user(
        recurring_id: int,
        user_id: int
    ) -> Optional[RecurringTransaction]:
        """Retrieve a recurring transaction by ID ensuring it belongs to the user."""
        return RecurringTransaction.query.filter_by(
            id=recurring_id,
            user_id=user_id
        ).first()

    @staticmethod
    def get_by_id_and_user_or_404(recurring_id: int, user_id: int) -> RecurringTransaction:
        """Retrieve a recurring transaction by ID or raise 404."""
        return RecurringTransaction.query.filter_by(
            id=recurring_id,
            user_id=user_id
        ).first_or_404()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[RecurringTransaction]:
        """Retrieve all recurring transactions for a user ordered by next due date."""
        return RecurringTransaction.query.filter_by(user_id=user_id).order_by(
            RecurringTransaction.next_due
        ).all()

    @staticmethod
    def get_active(user_id: int) -> List[RecurringTransaction]:
        """Retrieve all active recurring transactions for a user."""
        return RecurringTransaction.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(RecurringTransaction.next_due).all()

    @staticmethod
    def get_inactive(user_id: int) -> List[RecurringTransaction]:
        """Retrieve all inactive recurring transactions for a user."""
        return RecurringTransaction.query.filter_by(
            user_id=user_id,
            is_active=False
        ).order_by(RecurringTransaction.next_due).all()

    @staticmethod
    def get_due(user_id: int, as_of_date: Optional[date] = None) -> List[RecurringTransaction]:
        """Retrieve all active recurring transactions that are due."""
        if as_of_date is None:
            as_of_date = date.today()

        return RecurringTransaction.query.filter(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_active == True,
            RecurringTransaction.next_due <= as_of_date
        ).all()

    @staticmethod
    def get_upcoming(user_id: int, days: int = 7) -> List[RecurringTransaction]:
        """Retrieve active recurring transactions due in the next N days."""
        today = date.today()
        end_date = today + timedelta(days=days)

        return RecurringTransaction.query.filter(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.is_active == True,
            RecurringTransaction.next_due >= today,
            RecurringTransaction.next_due <= end_date
        ).order_by(RecurringTransaction.next_due).all()

    @staticmethod
    def get_by_frequency(user_id: int, frequency: str) -> List[RecurringTransaction]:
        """Retrieve recurring transactions by frequency."""
        return RecurringTransaction.query.filter_by(
            user_id=user_id,
            frequency=frequency
        ).order_by(RecurringTransaction.next_due).all()

    @staticmethod
    def create(
        user_id: int,
        account_id: int,
        category_id: int,
        name: str,
        amount: Decimal,
        transaction_type: str,
        frequency: str,
        start_date: date,
        next_due: date,
        end_date: Optional[date] = None,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> RecurringTransaction:
        """Create a new recurring transaction."""
        recurring = RecurringTransaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            name=name,
            amount=amount,
            transaction_type=transaction_type,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            next_due=next_due,
            description=description,
            is_active=is_active
        )
        db.session.add(recurring)
        db.session.commit()
        return recurring

    @staticmethod
    def update(recurring: RecurringTransaction, **kwargs) -> RecurringTransaction:
        """Update recurring transaction attributes."""
        for key, value in kwargs.items():
            if hasattr(recurring, key):
                setattr(recurring, key, value)
        db.session.commit()
        return recurring

    @staticmethod
    def toggle_active(recurring: RecurringTransaction) -> RecurringTransaction:
        """Toggle the active status of a recurring transaction."""
        recurring.is_active = not recurring.is_active
        db.session.commit()
        return recurring

    @staticmethod
    def activate(recurring: RecurringTransaction) -> RecurringTransaction:
        """Activate a recurring transaction."""
        recurring.is_active = True
        db.session.commit()
        return recurring

    @staticmethod
    def deactivate(recurring: RecurringTransaction) -> RecurringTransaction:
        """Deactivate a recurring transaction."""
        recurring.is_active = False
        db.session.commit()
        return recurring

    @staticmethod
    def mark_generated(
        recurring: RecurringTransaction,
        generated_date: date,
        next_due: date
    ) -> RecurringTransaction:
        """Update recurring transaction after generating a transaction."""
        recurring.last_generated = generated_date
        recurring.next_due = next_due
        db.session.commit()
        return recurring

    @staticmethod
    def delete(recurring: RecurringTransaction) -> None:
        """Delete a recurring transaction."""
        db.session.delete(recurring)
        db.session.commit()

    @staticmethod
    def save(recurring: RecurringTransaction) -> RecurringTransaction:
        """Save changes to an existing recurring transaction."""
        db.session.commit()
        return recurring

    @staticmethod
    def rollback() -> None:
        """Rollback the current database session."""
        db.session.rollback()

    @staticmethod
    def commit() -> None:
        """Commit the current database session."""
        db.session.commit()

