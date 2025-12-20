"""Budget Repository - Data access layer for Budget model."""

from decimal import Decimal
from typing import List, Optional

from ..extensions import db
from ..models import Budget


class BudgetRepository:
    """Repository for Budget entity database operations."""

    @staticmethod
    def get_by_id(budget_id: int) -> Optional[Budget]:
        """Retrieve a budget by its ID."""
        return Budget.query.get(budget_id)

    @staticmethod
    def get_by_id_and_user(budget_id: int, user_id: int) -> Optional[Budget]:
        """Retrieve a budget by ID ensuring it belongs to the user."""
        return Budget.query.filter_by(id=budget_id, user_id=user_id).first()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[Budget]:
        """Retrieve all budgets for a user ordered by date descending."""
        return Budget.query.filter_by(user_id=user_id).order_by(
            Budget.year.desc(),
            Budget.month.desc()
        ).all()

    @staticmethod
    def get_by_month(user_id: int, month: int, year: int) -> List[Budget]:
        """Retrieve all budgets for a specific month."""
        return Budget.query.filter_by(
            user_id=user_id,
            month=month,
            year=year
        ).all()

    @staticmethod
    def get_by_category(user_id: int, category_id: int) -> List[Budget]:
        """Retrieve all budgets for a specific category."""
        return Budget.query.filter_by(
            user_id=user_id,
            category_id=category_id
        ).order_by(Budget.year.desc(), Budget.month.desc()).all()

    @staticmethod
    def get_by_category_and_month(
        user_id: int,
        category_id: int,
        month: int,
        year: int
    ) -> Optional[Budget]:
        """Retrieve a specific budget for a category in a month."""
        return Budget.query.filter_by(
            user_id=user_id,
            category_id=category_id,
            month=month,
            year=year
        ).first()

    @staticmethod
    def get_current_month_budgets(user_id: int, month: int, year: int) -> List[Budget]:
        """Retrieve all budgets for the current month."""
        return Budget.query.filter_by(
            user_id=user_id,
            month=month,
            year=year
        ).all()

    @staticmethod
    def get_over_threshold(user_id: int, month: int, year: int) -> List[Budget]:
        """Retrieve budgets that are over their alert threshold."""
        budgets = BudgetRepository.get_by_month(user_id, month, year)
        return [b for b in budgets if b.is_over_threshold]

    @staticmethod
    def get_over_budget(user_id: int, month: int, year: int) -> List[Budget]:
        """Retrieve budgets that have exceeded their limit."""
        budgets = BudgetRepository.get_by_month(user_id, month, year)
        return [b for b in budgets if b.is_over_budget]

    @staticmethod
    def exists(
        user_id: int,
        category_id: int,
        month: int,
        year: int
    ) -> bool:
        """Check if a budget already exists for this category and month."""
        return Budget.query.filter_by(
            user_id=user_id,
            category_id=category_id,
            month=month,
            year=year
        ).first() is not None

    @staticmethod
    def create(
        user_id: int,
        category_id: int,
        month: int,
        year: int,
        limit_amount: Decimal,
        alert_threshold: int = 80
    ) -> Budget:
        """Create a new budget."""
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            month=month,
            year=year,
            limit_amount=limit_amount,
            alert_threshold=alert_threshold
        )
        budget.update_current_spent()
        db.session.add(budget)
        db.session.commit()
        return budget

    @staticmethod
    def create_or_update(
        user_id: int,
        category_id: int,
        month: int,
        year: int,
        limit_amount: Decimal,
        alert_threshold: int = 80
    ) -> tuple[Budget, str]:
        """Create a new budget or update existing one. Returns (budget, action)."""
        existing = BudgetRepository.get_by_category_and_month(
            user_id, category_id, month, year
        )

        if existing:
            existing.limit_amount = limit_amount
            existing.alert_threshold = alert_threshold
            existing.update_current_spent()
            db.session.commit()
            return existing, 'updated'

        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            month=month,
            year=year,
            limit_amount=limit_amount,
            alert_threshold=alert_threshold
        )
        budget.update_current_spent()
        db.session.add(budget)
        db.session.commit()
        return budget, 'created'

    @staticmethod
    def update(budget: Budget, **kwargs) -> Budget:
        """Update budget attributes."""
        for key, value in kwargs.items():
            if hasattr(budget, key):
                setattr(budget, key, value)
        db.session.commit()
        return budget

    @staticmethod
    def update_spent(budget: Budget) -> Budget:
        """Recalculate and update the current spent amount."""
        budget.update_current_spent()
        db.session.commit()
        return budget

    @staticmethod
    def update_affected_budgets(
        user_id: int,
        category_id: int,
        month: int,
        year: int
    ) -> None:
        """Update all budgets affected by a transaction change."""
        budgets = Budget.query.filter_by(
            user_id=user_id,
            category_id=category_id,
            month=month,
            year=year
        ).all()
        for budget in budgets:
            budget.update_current_spent()
        db.session.commit()

    @staticmethod
    def delete(budget: Budget) -> None:
        """Delete a budget."""
        db.session.delete(budget)
        db.session.commit()

    @staticmethod
    def save(budget: Budget) -> Budget:
        """Save changes to an existing budget."""
        db.session.commit()
        return budget

