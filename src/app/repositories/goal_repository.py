"""Goal Repository - Data access layer for Goal model."""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from ..extensions import db
from ..models import Goal


class GoalRepository:
    """Repository for Goal entity database operations."""

    @staticmethod
    def get_by_id(goal_id: int) -> Optional[Goal]:
        """Retrieve a goal by its ID."""
        return Goal.query.get(goal_id)

    @staticmethod
    def get_by_id_and_user(goal_id: int, user_id: int) -> Optional[Goal]:
        """Retrieve a goal by ID ensuring it belongs to the user."""
        return Goal.query.filter_by(id=goal_id, user_id=user_id).first()

    @staticmethod
    def get_by_id_and_user_or_404(goal_id: int, user_id: int) -> Goal:
        """Retrieve a goal by ID or raise 404."""
        return Goal.query.filter_by(id=goal_id, user_id=user_id).first_or_404()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[Goal]:
        """Retrieve all goals for a user ordered by creation date descending."""
        return Goal.query.filter_by(user_id=user_id).order_by(
            Goal.created_at.desc()
        ).all()

    @staticmethod
    def get_active_goals(user_id: int) -> List[Goal]:
        """Retrieve all incomplete goals for a user."""
        goals = Goal.query.filter_by(user_id=user_id).order_by(
            Goal.created_at.desc()
        ).all()
        return [g for g in goals if not g.is_completed]

    @staticmethod
    def get_completed_goals(user_id: int) -> List[Goal]:
        """Retrieve all completed goals for a user."""
        goals = Goal.query.filter_by(user_id=user_id).order_by(
            Goal.created_at.desc()
        ).all()
        return [g for g in goals if g.is_completed]

    @staticmethod
    def get_upcoming_deadlines(user_id: int, days: int = 30) -> List[Goal]:
        """Retrieve goals with deadlines within the specified days."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now().date() + timedelta(days=days)
        
        goals = Goal.query.filter(
            Goal.user_id == user_id,
            Goal.target_date.isnot(None),
            Goal.target_date <= cutoff_date
        ).order_by(Goal.target_date).all()
        
        return [g for g in goals if not g.is_completed]

    @staticmethod
    def create(
        user_id: int,
        name: str,
        target_amount: Decimal,
        current_amount: Decimal = Decimal('0.00'),
        target_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> Goal:
        """Create a new goal."""
        goal = Goal(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target_date,
            description=description
        )
        db.session.add(goal)
        db.session.commit()
        return goal

    @staticmethod
    def update(goal: Goal, **kwargs) -> Goal:
        """Update goal attributes."""
        for key, value in kwargs.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        db.session.commit()
        return goal

    @staticmethod
    def add_progress(goal: Goal, amount: Decimal) -> Goal:
        """Add to the current amount of a goal."""
        if amount > 0:
            goal.current_amount += amount
            db.session.commit()
        return goal

    @staticmethod
    def set_progress(goal: Goal, amount: Decimal) -> Goal:
        """Set the current amount of a goal."""
        goal.current_amount = amount
        db.session.commit()
        return goal

    @staticmethod
    def delete(goal: Goal) -> None:
        """Delete a goal."""
        db.session.delete(goal)
        db.session.commit()

    @staticmethod
    def save(goal: Goal) -> Goal:
        """Save changes to an existing goal."""
        db.session.commit()
        return goal

    @staticmethod
    def rollback() -> None:
        """Rollback the current database session."""
        db.session.rollback()

