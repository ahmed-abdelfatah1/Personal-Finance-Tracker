"""Unit Tests for Repository Layer."""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta

from app.extensions import db
from app.models import User, Account, Category, Transaction, Budget, Goal, RecurringTransaction
from app.repositories import (
    UserRepository,
    AccountRepository,
    CategoryRepository,
    TransactionRepository,
    BudgetRepository,
    GoalRepository,
    RecurringTransactionRepository
)


class TestUserRepository:
    """Tests for UserRepository."""

    def test_get_by_id(self, app, sample_user):
        """Test retrieving user by ID."""
        with app.app_context():
            user = UserRepository.get_by_id(sample_user.id)
            assert user is not None
            assert user.email == 'test@example.com'

    def test_get_by_email(self, app, sample_user):
        """Test retrieving user by email."""
        with app.app_context():
            user = UserRepository.get_by_email('test@example.com')
            assert user is not None
            assert user.id == sample_user.id

    def test_email_exists(self, app, sample_user):
        """Test email existence check."""
        with app.app_context():
            assert UserRepository.email_exists('test@example.com') is True
            assert UserRepository.email_exists('nonexistent@example.com') is False

    def test_create_user(self, app):
        """Test user creation through repository."""
        with app.app_context():
            user = UserRepository.create(
                email='new@example.com',
                password='password123',
                display_name='New User'
            )
            assert user.id is not None
            assert user.email == 'new@example.com'
            assert user.check_password('password123')


class TestAccountRepository:
    """Tests for AccountRepository."""

    def test_get_by_id(self, app, sample_account):
        """Test retrieving account by ID."""
        with app.app_context():
            account = AccountRepository.get_by_id(sample_account.id)
            assert account is not None
            assert account.name == 'Test Account'

    def test_get_by_id_and_user(self, app, sample_account, sample_user):
        """Test retrieving account with user verification."""
        with app.app_context():
            account = AccountRepository.get_by_id_and_user(
                sample_account.id,
                sample_user.id
            )
            assert account is not None

            # Should return None for wrong user
            wrong_account = AccountRepository.get_by_id_and_user(
                sample_account.id,
                9999
            )
            assert wrong_account is None

    def test_get_all_by_user(self, app, sample_user):
        """Test retrieving all accounts for a user."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            
            # Create multiple accounts
            for i in range(3):
                account = Account(
                    user_id=user.id,
                    name=f'Account {i}',
                    current_balance=Decimal('100.00')
                )
                db.session.add(account)
            db.session.commit()

            accounts = AccountRepository.get_all_by_user(user.id)
            assert len(accounts) == 3

    def test_create_account(self, app, sample_user):
        """Test account creation through repository."""
        with app.app_context():
            account = AccountRepository.create(
                user_id=sample_user.id,
                name='New Account',
                account_type='savings',
                initial_balance=Decimal('5000.00')
            )
            assert account.id is not None
            assert account.current_balance == Decimal('5000.00')

    def test_update_balance_income(self, app, sample_account):
        """Test balance update for income."""
        with app.app_context():
            account = Account.query.get(sample_account.id)
            original_balance = account.current_balance
            
            AccountRepository.update_balance(
                account,
                Decimal('500.00'),
                is_income=True
            )
            
            assert account.current_balance == original_balance + Decimal('500.00')

    def test_update_balance_expense(self, app, sample_account):
        """Test balance update for expense."""
        with app.app_context():
            account = Account.query.get(sample_account.id)
            original_balance = account.current_balance
            
            AccountRepository.update_balance(
                account,
                Decimal('300.00'),
                is_income=False
            )
            
            assert account.current_balance == original_balance - Decimal('300.00')

    def test_has_transactions(self, app, sample_account, sample_transaction):
        """Test checking if account has transactions."""
        with app.app_context():
            assert AccountRepository.has_transactions(sample_account.id) is True

    def test_has_no_transactions(self, app, sample_account):
        """Test checking if account has no transactions."""
        with app.app_context():
            assert AccountRepository.has_transactions(sample_account.id) is False


class TestCategoryRepository:
    """Tests for CategoryRepository."""

    def test_get_by_type(self, app, sample_user, sample_category, sample_income_category):
        """Test retrieving categories by type."""
        with app.app_context():
            expense_cats = CategoryRepository.get_expense_categories(sample_user.id)
            income_cats = CategoryRepository.get_income_categories(sample_user.id)

            assert len(expense_cats) == 1
            assert len(income_cats) == 1
            assert expense_cats[0].category_type == 'Expense'
            assert income_cats[0].category_type == 'Income'

    def test_exists_by_name_and_type(self, app, sample_user, sample_category):
        """Test category existence check."""
        with app.app_context():
            exists = CategoryRepository.exists_by_name_and_type(
                sample_user.id,
                'Test Category',
                'Expense'
            )
            assert exists is True

            not_exists = CategoryRepository.exists_by_name_and_type(
                sample_user.id,
                'Nonexistent',
                'Expense'
            )
            assert not_exists is False

    def test_can_delete_empty_category(self, app, sample_category):
        """Test category can be deleted when empty."""
        with app.app_context():
            can_delete, reason = CategoryRepository.can_delete(sample_category.id)
            assert can_delete is True

    def test_cannot_delete_category_with_transactions(self, app, sample_category, sample_transaction):
        """Test category cannot be deleted with transactions."""
        with app.app_context():
            can_delete, reason = CategoryRepository.can_delete(sample_category.id)
            assert can_delete is False
            assert 'transactions' in reason.lower()


class TestTransactionRepository:
    """Tests for TransactionRepository."""

    def test_get_recent(self, app, sample_user, sample_account, sample_category):
        """Test retrieving recent transactions."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            account = Account.query.get(sample_account.id)
            category = Category.query.get(sample_category.id)
            
            # Create 10 transactions
            for i in range(10):
                txn = Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    category_id=category.id,
                    date=date.today() - timedelta(days=i),
                    amount=Decimal('50.00'),
                    transaction_type='Expense'
                )
                db.session.add(txn)
            db.session.commit()

            recent = TransactionRepository.get_recent(user.id, limit=5)
            assert len(recent) == 5

    def test_get_monthly_total(self, app, sample_user, sample_account, sample_category):
        """Test monthly total calculation."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            account = Account.query.get(sample_account.id)
            category = Category.query.get(sample_category.id)
            
            today = date.today()
            
            # Create expense transactions
            for _ in range(3):
                txn = Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    category_id=category.id,
                    date=today,
                    amount=Decimal('100.00'),
                    transaction_type='Expense'
                )
                db.session.add(txn)
            db.session.commit()

            total = TransactionRepository.get_monthly_total(
                user.id,
                'Expense',
                today.month,
                today.year
            )
            assert total == Decimal('300.00')

    def test_filter_transactions(self, app, sample_user, sample_account, sample_category):
        """Test transaction filtering."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            account = Account.query.get(sample_account.id)
            category = Category.query.get(sample_category.id)
            
            # Create mixed transactions
            for i in range(5):
                txn = Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    category_id=category.id,
                    date=date.today(),
                    amount=Decimal('100.00'),
                    transaction_type='Expense' if i % 2 == 0 else 'Income'
                )
                db.session.add(txn)
            db.session.commit()

            expenses = TransactionRepository.filter_transactions(
                user.id,
                transaction_type='Expense'
            )
            assert len(expenses) == 3


class TestBudgetRepository:
    """Tests for BudgetRepository."""

    def test_get_by_category_and_month(self, app, sample_budget, sample_user, sample_category):
        """Test retrieving budget by category and month."""
        with app.app_context():
            now = datetime.now()
            budget = BudgetRepository.get_by_category_and_month(
                sample_user.id,
                sample_category.id,
                now.month,
                now.year
            )
            assert budget is not None
            assert budget.limit_amount == Decimal('500.00')

    def test_create_or_update_creates_new(self, app, sample_user, sample_category):
        """Test create_or_update creates new budget."""
        with app.app_context():
            now = datetime.now()
            budget, action = BudgetRepository.create_or_update(
                sample_user.id,
                sample_category.id,
                now.month,
                now.year,
                Decimal('1000.00')
            )
            assert action == 'created'
            assert budget.limit_amount == Decimal('1000.00')

    def test_create_or_update_updates_existing(self, app, sample_budget, sample_user, sample_category):
        """Test create_or_update updates existing budget."""
        with app.app_context():
            now = datetime.now()
            budget, action = BudgetRepository.create_or_update(
                sample_user.id,
                sample_category.id,
                now.month,
                now.year,
                Decimal('750.00')
            )
            assert action == 'updated'
            assert budget.limit_amount == Decimal('750.00')


class TestGoalRepository:
    """Tests for GoalRepository."""

    def test_get_all_by_user(self, app, sample_user, sample_goal):
        """Test retrieving all goals for a user."""
        with app.app_context():
            goals = GoalRepository.get_all_by_user(sample_user.id)
            assert len(goals) == 1
            assert goals[0].name == 'Test Goal'

    def test_add_progress(self, app, sample_goal):
        """Test adding progress to a goal."""
        with app.app_context():
            goal = Goal.query.get(sample_goal.id)
            original_amount = goal.current_amount
            
            GoalRepository.add_progress(goal, Decimal('500.00'))
            
            assert goal.current_amount == original_amount + Decimal('500.00')

    def test_get_active_goals(self, app, sample_user):
        """Test retrieving active (incomplete) goals."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            
            # Create completed and incomplete goals
            incomplete = Goal(
                user_id=user.id,
                name='Incomplete',
                target_amount=Decimal('1000.00'),
                current_amount=Decimal('500.00')
            )
            completed = Goal(
                user_id=user.id,
                name='Completed',
                target_amount=Decimal('1000.00'),
                current_amount=Decimal('1000.00')
            )
            db.session.add_all([incomplete, completed])
            db.session.commit()

            active = GoalRepository.get_active_goals(user.id)
            assert len(active) == 1
            assert active[0].name == 'Incomplete'


class TestRecurringTransactionRepository:
    """Tests for RecurringTransactionRepository."""

    def test_get_active(self, app, sample_user, sample_recurring):
        """Test retrieving active recurring transactions."""
        with app.app_context():
            active = RecurringTransactionRepository.get_active(sample_user.id)
            assert len(active) == 1
            assert active[0].is_active is True

    def test_get_due(self, app, sample_recurring, sample_user):
        """Test retrieving due recurring transactions."""
        with app.app_context():
            due = RecurringTransactionRepository.get_due(sample_user.id)
            assert len(due) == 1

    def test_toggle_active(self, app, sample_recurring):
        """Test toggling active status."""
        with app.app_context():
            recurring = RecurringTransaction.query.get(sample_recurring.id)
            assert recurring.is_active is True
            
            RecurringTransactionRepository.toggle_active(recurring)
            assert recurring.is_active is False
            
            RecurringTransactionRepository.toggle_active(recurring)
            assert recurring.is_active is True

    def test_get_upcoming(self, app, sample_user, sample_account, sample_category):
        """Test retrieving upcoming recurring transactions."""
        with app.app_context():
            user = User.query.get(sample_user.id)
            account = Account.query.get(sample_account.id)
            category = Category.query.get(sample_category.id)
            
            # Create recurring with future due date
            future = RecurringTransaction(
                user_id=user.id,
                account_id=account.id,
                category_id=category.id,
                name='Future',
                amount=Decimal('100.00'),
                transaction_type='Expense',
                frequency='monthly',
                start_date=date.today(),
                next_due=date.today() + timedelta(days=3),
                is_active=True
            )
            db.session.add(future)
            db.session.commit()

            upcoming = RecurringTransactionRepository.get_upcoming(user.id, days=7)
            assert len(upcoming) == 1
            assert upcoming[0].name == 'Future'

