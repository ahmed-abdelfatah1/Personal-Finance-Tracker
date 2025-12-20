"""User Repository - Data access layer for User model."""

from typing import Optional

from ..extensions import db
from ..models import User


class UserRepository:
    """Repository for User entity database operations."""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """Retrieve a user by their ID."""
        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        return User.query.filter_by(email=email).first()

    @staticmethod
    def email_exists(email: str) -> bool:
        """Check if an email is already registered."""
        return User.query.filter_by(email=email).first() is not None

    @staticmethod
    def create(email: str, password: str, display_name: Optional[str] = None) -> User:
        """Create a new user with hashed password."""
        user = User(email=email, display_name=display_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update(user: User, **kwargs) -> User:
        """Update user attributes."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.session.commit()
        return user

    @staticmethod
    def delete(user: User) -> None:
        """Delete a user and all related data."""
        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def save(user: User) -> User:
        """Save changes to an existing user."""
        db.session.commit()
        return user

