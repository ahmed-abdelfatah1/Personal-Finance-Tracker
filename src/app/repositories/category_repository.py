"""Category Repository - Data access layer for Category model."""

from decimal import Decimal
from typing import List, Optional

from ..extensions import db
from ..models import Category, Transaction, Budget


class CategoryRepository:
    """Repository for Category entity database operations."""

    @staticmethod
    def get_by_id(category_id: int) -> Optional[Category]:
        """Retrieve a category by its ID."""
        return Category.query.get(category_id)

    @staticmethod
    def get_by_id_and_user(category_id: int, user_id: int) -> Optional[Category]:
        """Retrieve a category by ID ensuring it belongs to the user."""
        return Category.query.filter_by(id=category_id, user_id=user_id).first()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[Category]:
        """Retrieve all categories for a specific user."""
        return Category.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_by_type(user_id: int, category_type: str) -> List[Category]:
        """Retrieve categories of a specific type (Income/Expense) for a user."""
        return Category.query.filter_by(
            user_id=user_id,
            category_type=category_type
        ).all()

    @staticmethod
    def get_income_categories(user_id: int) -> List[Category]:
        """Retrieve all income categories for a user."""
        return CategoryRepository.get_by_type(user_id, 'Income')

    @staticmethod
    def get_expense_categories(user_id: int) -> List[Category]:
        """Retrieve all expense categories for a user."""
        return CategoryRepository.get_by_type(user_id, 'Expense')

    @staticmethod
    def exists_by_name_and_type(
        user_id: int,
        name: str,
        category_type: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """Check if a category with the same name and type exists."""
        query = Category.query.filter_by(
            user_id=user_id,
            name=name,
            category_type=category_type
        )
        if exclude_id:
            query = query.filter(Category.id != exclude_id)
        return query.first() is not None

    @staticmethod
    def create(
        user_id: int,
        name: str,
        category_type: str,
        color: Optional[str] = None,
        max_single_amount: Optional[Decimal] = None
    ) -> Category:
        """Create a new category."""
        category = Category(
            user_id=user_id,
            name=name,
            category_type=category_type,
            color=color,
            max_single_amount=max_single_amount
        )
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def update(category: Category, **kwargs) -> Category:
        """Update category attributes."""
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        db.session.commit()
        return category

    @staticmethod
    def get_transaction_count(category_id: int) -> int:
        """Get the number of transactions for a category."""
        return Transaction.query.filter_by(category_id=category_id).count()

    @staticmethod
    def get_budget_count(category_id: int) -> int:
        """Get the number of budgets for a category."""
        return Budget.query.filter_by(category_id=category_id).count()

    @staticmethod
    def has_transactions(category_id: int) -> bool:
        """Check if a category has any transactions."""
        return Transaction.query.filter_by(category_id=category_id).first() is not None

    @staticmethod
    def has_budgets(category_id: int) -> bool:
        """Check if a category has any budgets."""
        return Budget.query.filter_by(category_id=category_id).first() is not None

    @staticmethod
    def can_delete(category_id: int) -> tuple[bool, str]:
        """Check if a category can be deleted, returns (can_delete, reason)."""
        transaction_count = CategoryRepository.get_transaction_count(category_id)
        if transaction_count > 0:
            return False, f"Category has {transaction_count} transactions"

        budget_count = CategoryRepository.get_budget_count(category_id)
        if budget_count > 0:
            return False, f"Category has {budget_count} budgets"

        return True, ""

    @staticmethod
    def delete(category: Category) -> None:
        """Delete a category."""
        db.session.delete(category)
        db.session.commit()

    @staticmethod
    def save(category: Category) -> Category:
        """Save changes to an existing category."""
        db.session.commit()
        return category

