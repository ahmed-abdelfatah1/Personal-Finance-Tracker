"""Transaction Template Repository - Data access layer for TransactionTemplate model."""

from decimal import Decimal
from typing import List, Optional

from ..extensions import db
from ..models import TransactionTemplate


class TransactionTemplateRepository:
    """Repository for TransactionTemplate entity database operations."""

    @staticmethod
    def get_by_id(template_id: int) -> Optional[TransactionTemplate]:
        """Retrieve a template by its ID."""
        return TransactionTemplate.query.get(template_id)

    @staticmethod
    def get_by_id_and_user(template_id: int, user_id: int) -> Optional[TransactionTemplate]:
        """Retrieve a template by ID ensuring it belongs to the user."""
        return TransactionTemplate.query.filter_by(
            id=template_id,
            user_id=user_id
        ).first()

    @staticmethod
    def get_by_id_and_user_or_404(template_id: int, user_id: int) -> TransactionTemplate:
        """Retrieve a template by ID or raise 404."""
        return TransactionTemplate.query.filter_by(
            id=template_id,
            user_id=user_id
        ).first_or_404()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[TransactionTemplate]:
        """Retrieve all templates for a user."""
        return TransactionTemplate.query.filter_by(
            user_id=user_id
        ).order_by(TransactionTemplate.name).all()

    @staticmethod
    def get_by_type(user_id: int, transaction_type: str) -> List[TransactionTemplate]:
        """Retrieve templates by transaction type."""
        return TransactionTemplate.query.filter_by(
            user_id=user_id,
            transaction_type=transaction_type
        ).order_by(TransactionTemplate.name).all()

    @staticmethod
    def create(
        user_id: int,
        name: str,
        transaction_type: str,
        default_amount: Optional[Decimal] = None,
        account_id: Optional[int] = None,
        category_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> TransactionTemplate:
        """Create a new transaction template."""
        template = TransactionTemplate(
            user_id=user_id,
            name=name,
            transaction_type=transaction_type,
            default_amount=default_amount,
            account_id=account_id,
            category_id=category_id,
            description=description
        )
        db.session.add(template)
        db.session.commit()
        return template

    @staticmethod
    def update(template: TransactionTemplate, **kwargs) -> TransactionTemplate:
        """Update template attributes."""
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        db.session.commit()
        return template

    @staticmethod
    def delete(template: TransactionTemplate) -> None:
        """Delete a template."""
        db.session.delete(template)
        db.session.commit()

    @staticmethod
    def save(template: TransactionTemplate) -> TransactionTemplate:
        """Save changes to an existing template."""
        db.session.commit()
        return template

