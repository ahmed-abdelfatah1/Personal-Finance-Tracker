"""Debt Repository - Data access layer for Debt model."""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from ..extensions import db
from ..models import Debt


class DebtRepository:
    """Repository for Debt entity database operations."""

    @staticmethod
    def get_by_id(debt_id: int) -> Optional[Debt]:
        """Retrieve a debt by its ID."""
        return Debt.query.get(debt_id)

    @staticmethod
    def get_by_id_and_user(debt_id: int, user_id: int) -> Optional[Debt]:
        """Retrieve a debt by ID ensuring it belongs to the user."""
        return Debt.query.filter_by(id=debt_id, user_id=user_id).first()

    @staticmethod
    def get_by_id_and_user_or_404(debt_id: int, user_id: int) -> Debt:
        """Retrieve a debt by ID or raise 404."""
        return Debt.query.filter_by(id=debt_id, user_id=user_id).first_or_404()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[Debt]:
        """Retrieve all debts for a user."""
        return Debt.query.filter_by(user_id=user_id).order_by(Debt.created_at.desc()).all()

    @staticmethod
    def get_by_type(user_id: int, debt_type: str) -> List[Debt]:
        """Retrieve debts by type (Debt or Loan)."""
        return Debt.query.filter_by(
            user_id=user_id,
            debt_type=debt_type
        ).order_by(Debt.created_at.desc()).all()

    @staticmethod
    def get_debts(user_id: int) -> List[Debt]:
        """Retrieve all debts (money owed)."""
        return DebtRepository.get_by_type(user_id, 'Debt')

    @staticmethod
    def get_loans(user_id: int) -> List[Debt]:
        """Retrieve all loans (money lent)."""
        return DebtRepository.get_by_type(user_id, 'Loan')

    @staticmethod
    def get_active(user_id: int) -> List[Debt]:
        """Retrieve all active (not paid off) debts."""
        debts = Debt.query.filter_by(user_id=user_id).all()
        return [d for d in debts if not d.is_paid_off]

    @staticmethod
    def get_paid_off(user_id: int) -> List[Debt]:
        """Retrieve all paid off debts."""
        debts = Debt.query.filter_by(user_id=user_id).all()
        return [d for d in debts if d.is_paid_off]

    @staticmethod
    def get_total_debt(user_id: int) -> Decimal:
        """Calculate total remaining debt amount."""
        debts = DebtRepository.get_debts(user_id)
        return sum((d.remaining_amount for d in debts if not d.is_paid_off), Decimal('0.00'))

    @staticmethod
    def get_total_loan(user_id: int) -> Decimal:
        """Calculate total remaining loan amount."""
        loans = DebtRepository.get_loans(user_id)
        return sum((l.remaining_amount for l in loans if not l.is_paid_off), Decimal('0.00'))

    @staticmethod
    def create(
        user_id: int,
        name: str,
        debt_type: str,
        principal_amount: Decimal,
        remaining_amount: Optional[Decimal] = None,
        interest_rate: Optional[Decimal] = None,
        minimum_payment: Optional[Decimal] = None,
        due_date: Optional[date] = None,
        lender_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Debt:
        """Create a new debt."""
        if remaining_amount is None:
            remaining_amount = principal_amount

        debt = Debt(
            user_id=user_id,
            name=name,
            debt_type=debt_type,
            principal_amount=principal_amount,
            remaining_amount=remaining_amount,
            interest_rate=interest_rate,
            minimum_payment=minimum_payment,
            due_date=due_date,
            lender_name=lender_name,
            description=description
        )
        db.session.add(debt)
        db.session.commit()
        return debt

    @staticmethod
    def update(debt: Debt, **kwargs) -> Debt:
        """Update debt attributes."""
        for key, value in kwargs.items():
            if hasattr(debt, key):
                setattr(debt, key, value)
        db.session.commit()
        return debt

    @staticmethod
    def make_payment(debt: Debt, payment_amount: Decimal) -> Debt:
        """Record a payment on a debt."""
        if payment_amount > 0:
            debt.remaining_amount = max(Decimal('0.00'), debt.remaining_amount - payment_amount)
            db.session.commit()
        return debt

    @staticmethod
    def delete(debt: Debt) -> None:
        """Delete a debt."""
        db.session.delete(debt)
        db.session.commit()

    @staticmethod
    def save(debt: Debt) -> Debt:
        """Save changes to an existing debt."""
        db.session.commit()
        return debt

