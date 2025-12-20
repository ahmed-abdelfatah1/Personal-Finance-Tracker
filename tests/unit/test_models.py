"""Unit Tests for Database Models."""

import pytest
from decimal import Decimal
from datetime import datetime, date

from app.extensions import db
from app.models import (
    User, Account, Category, Transaction,
    Budget, Goal, RecurringTransaction
)


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app):
        """Test user creation with valid data."""
        with app.app_context():
            user = User(email='new@example.com', display_name='New User')
            user.set_password('securepassword')
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.email == 'new@example.com'
            assert user.display_name == 'New User'
            assert user.default_currency == 'EGP'

    def test_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(email='hash@example.com')
            user.set_password('mypassword')
            db.session.add(user)
            db.session.commit()

            assert user.password_hash != 'mypassword'
            assert user.check_password('mypassword') is True
            assert user.check_password('wrongpassword') is False

    def test_user_repr(self, sample_user, app):
        """Test user string representation."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            assert 'test@example.com' in repr(user)

    def test_get_total_balance(self, app, sample_user):
        """Test total balance calculation across accounts."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            
            # Create two accounts
            acc1 = Account(
                user_id=user.id,
                name='Account 1',
                current_balance=Decimal('1000.00')
            )
            acc2 = Account(
                user_id=user.id,
                name='Account 2',
                current_balance=Decimal('500.00')
            )
            db.session.add_all([acc1, acc2])
            db.session.commit()

            # Refresh user to get updated relationships
            db.session.refresh(user)
            total = user.get_total_balance()
            assert total == Decimal('1500.00')


class TestAccountModel:
    """Tests for the Account model."""

    def test_create_account(self, app, sample_user):
        """Test account creation."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            account = Account(
                user_id=user.id,
                name='Savings Account',
                account_type='savings',
                initial_balance=Decimal('5000.00'),
                current_balance=Decimal('5000.00')
            )
            db.session.add(account)
            db.session.commit()

            assert account.id is not None
            assert account.name == 'Savings Account'
            assert account.currency == 'EGP'

    def test_account_repr(self, sample_account, app):
        """Test account string representation."""
        with app.app_context():
            account = Account.query.get(sample_account.id)
            assert 'Test Account' in repr(account)


class TestCategoryModel:
    """Tests for the Category model."""

    def test_create_expense_category(self, app, sample_user):
        """Test expense category creation."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            category = Category(
                user_id=user.id,
                name='Food',
                category_type='Expense',
                color='#e74c3c'
            )
            db.session.add(category)
            db.session.commit()

            assert category.id is not None
            assert category.category_type == 'Expense'

    def test_create_income_category(self, app, sample_user):
        """Test income category creation."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            category = Category(
                user_id=user.id,
                name='Freelance',
                category_type='Income',
                color='#27ae60'
            )
            db.session.add(category)
            db.session.commit()

            assert category.category_type == 'Income'

    def test_category_with_max_amount(self, app, sample_user):
        """Test category with max single amount limit."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            category = Category(
                user_id=user.id,
                name='Entertainment',
                category_type='Expense',
                max_single_amount=Decimal('100.00')
            )
            db.session.add(category)
            db.session.commit()

            assert category.max_single_amount == Decimal('100.00')


class TestTransactionModel:
    """Tests for the Transaction model."""

    def test_create_expense_transaction(self, sample_transaction, app):
        """Test expense transaction creation."""
        with app.app_context():
            transaction = Transaction.query.get(sample_transaction.id)
            assert transaction.transaction_type == 'Expense'
            assert transaction.amount == Decimal('100.00')

    def test_create_income_transaction(self, app, sample_user, sample_account, sample_income_category):
        """Test income transaction creation."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            account = Account.query.get(sample_account.id)
            category = Category.query.get(sample_income_category.id)
            
            transaction = Transaction(
                user_id=user.id,
                account_id=account.id,
                category_id=category.id,
                date=date.today(),
                amount=Decimal('5000.00'),
                transaction_type='Income',
                description='Monthly salary'
            )
            db.session.add(transaction)
            db.session.commit()

            assert transaction.transaction_type == 'Income'


class TestBudgetModel:
    """Tests for the Budget model."""

    def test_create_budget(self, sample_budget, app):
        """Test budget creation."""
        with app.app_context():
            budget = Budget.query.get(sample_budget.id)
            assert budget.limit_amount == Decimal('500.00')
            assert budget.alert_threshold == 80

    def test_spent_percentage(self, app, sample_user, sample_category):
        """Test budget spent percentage calculation."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            category = Category.query.get(sample_category.id)
            
            now = datetime.now()
            budget = Budget(
                user_id=user.id,
                category_id=category.id,
                month=now.month,
                year=now.year,
                limit_amount=Decimal('200.00'),
                current_spent=Decimal('100.00')
            )
            db.session.add(budget)
            db.session.commit()

            assert budget.spent_percentage == 50.0

    def test_is_over_threshold(self, app, sample_user, sample_category):
        """Test budget over threshold detection."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            category = Category.query.get(sample_category.id)
            
            now = datetime.now()
            budget = Budget(
                user_id=user.id,
                category_id=category.id,
                month=now.month,
                year=now.year,
                limit_amount=Decimal('100.00'),
                current_spent=Decimal('85.00'),
                alert_threshold=80
            )
            db.session.add(budget)
            db.session.commit()

            assert budget.is_over_threshold is True

    def test_is_over_budget(self, app, sample_user, sample_category):
        """Test budget exceeded detection."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            category = Category.query.get(sample_category.id)
            
            now = datetime.now()
            budget = Budget(
                user_id=user.id,
                category_id=category.id,
                month=now.month,
                year=now.year,
                limit_amount=Decimal('100.00'),
                current_spent=Decimal('150.00')
            )
            db.session.add(budget)
            db.session.commit()

            assert budget.is_over_budget is True


class TestGoalModel:
    """Tests for the Goal model."""

    def test_create_goal(self, sample_goal, app):
        """Test goal creation."""
        with app.app_context():
            goal = Goal.query.get(sample_goal.id)
            assert goal.name == 'Test Goal'
            assert goal.target_amount == Decimal('10000.00')

    def test_progress_percentage(self, sample_goal, app):
        """Test goal progress percentage calculation."""
        with app.app_context():
            goal = Goal.query.get(sample_goal.id)
            # current_amount is 2500, target is 10000
            assert goal.progress_percentage == 25.0

    def test_remaining_amount(self, sample_goal, app):
        """Test goal remaining amount calculation."""
        with app.app_context():
            goal = Goal.query.get(sample_goal.id)
            assert goal.remaining_amount == Decimal('7500.00')

    def test_is_completed(self, app, sample_user):
        """Test goal completion detection."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            
            goal = Goal(
                user_id=user.id,
                name='Completed Goal',
                target_amount=Decimal('1000.00'),
                current_amount=Decimal('1000.00')
            )
            db.session.add(goal)
            db.session.commit()

            assert goal.is_completed is True


class TestRecurringTransactionModel:
    """Tests for the RecurringTransaction model."""

    def test_create_recurring(self, sample_recurring, app):
        """Test recurring transaction creation."""
        with app.app_context():
            recurring = RecurringTransaction.query.get(sample_recurring.id)
            assert recurring.name == 'Monthly Rent'
            assert recurring.frequency == 'monthly'
            assert recurring.is_active is True

    def test_recurring_repr(self, sample_recurring, app):
        """Test recurring transaction string representation."""
        with app.app_context():
            recurring = RecurringTransaction.query.get(sample_recurring.id)
            assert 'Monthly Rent' in repr(recurring)
            assert 'monthly' in repr(recurring)

