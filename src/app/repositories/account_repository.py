"""Account Repository - Data access layer for Account model."""

from decimal import Decimal
from typing import List, Optional

from ..extensions import db
from ..models import Account, Transaction


class AccountRepository:
    """Repository for Account entity database operations."""

    @staticmethod
    def get_by_id(account_id: int) -> Optional[Account]:
        """Retrieve an account by its ID."""
        return Account.query.get(account_id)

    @staticmethod
    def get_by_id_and_user(account_id: int, user_id: int) -> Optional[Account]:
        """Retrieve an account by ID ensuring it belongs to the user."""
        return Account.query.filter_by(id=account_id, user_id=user_id).first()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[Account]:
        """Retrieve all accounts for a specific user."""
        return Account.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_total_balance(user_id: int) -> Decimal:
        """Calculate total balance across all user accounts."""
        accounts = Account.query.filter_by(user_id=user_id).all()
        return sum((acc.current_balance for acc in accounts), Decimal('0.00'))

    @staticmethod
    def create(
        user_id: int,
        name: str,
        account_type: Optional[str] = None,
        initial_balance: Decimal = Decimal('0.00'),
        currency: str = 'EGP'
    ) -> Account:
        """Create a new account."""
        account = Account(
            user_id=user_id,
            name=name,
            account_type=account_type,
            initial_balance=initial_balance,
            current_balance=initial_balance,
            currency=currency
        )
        db.session.add(account)
        db.session.commit()
        return account

    @staticmethod
    def update(account: Account, **kwargs) -> Account:
        """Update account attributes."""
        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)
        db.session.commit()
        return account

    @staticmethod
    def update_balance(account: Account, amount: Decimal, is_income: bool) -> Account:
        """Update account balance based on transaction type."""
        if is_income:
            account.current_balance += amount
        else:
            account.current_balance -= amount
        db.session.commit()
        return account

    @staticmethod
    def reverse_balance(account: Account, amount: Decimal, was_income: bool) -> Account:
        """Reverse a previous balance change."""
        if was_income:
            account.current_balance -= amount
        else:
            account.current_balance += amount
        db.session.commit()
        return account

    @staticmethod
    def get_transaction_count(account_id: int) -> int:
        """Get the number of transactions for an account."""
        return Transaction.query.filter_by(account_id=account_id).count()

    @staticmethod
    def has_transactions(account_id: int) -> bool:
        """Check if an account has any transactions."""
        return Transaction.query.filter_by(account_id=account_id).first() is not None

    @staticmethod
    def delete(account: Account) -> None:
        """Delete an account."""
        db.session.delete(account)
        db.session.commit()

    @staticmethod
    def save(account: Account) -> Account:
        """Save changes to an existing account."""
        db.session.commit()
        return account

