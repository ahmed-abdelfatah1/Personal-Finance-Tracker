"""Test Configuration - Pytest fixtures and test setup."""

import os
import sys
import pytest
from decimal import Decimal
from datetime import datetime, date

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import create_app
from app.extensions import db
from app.models import (
    User, Account, Category, Transaction,
    Budget, Goal, RecurringTransaction
)


class TestConfig:
    """Test configuration using in-memory SQLite database."""
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False


@pytest.fixture(scope='function')
def app():
    """Create application for testing."""
    application = create_app(TestConfig)

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db.session


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    with app.app_context():
        user = User(
            email='test@example.com',
            display_name='Test User'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(user)
        yield user


@pytest.fixture
def sample_account(app, sample_user):
    """Create a sample account for testing."""
    with app.app_context():
        # Re-query user to avoid detached instance
        user = User.query.get(sample_user.id)
        account = Account(
            user_id=user.id,
            name='Test Account',
            account_type='checking',
            initial_balance=Decimal('1000.00'),
            current_balance=Decimal('1000.00'),
            currency='EGP'
        )
        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        yield account


@pytest.fixture
def sample_category(app, sample_user):
    """Create a sample category for testing."""
    with app.app_context():
        user = User.query.get(sample_user.id)
        category = Category(
            user_id=user.id,
            name='Test Category',
            category_type='Expense',
            color='#3498db'
        )
        db.session.add(category)
        db.session.commit()
        db.session.refresh(category)
        yield category


@pytest.fixture
def sample_income_category(app, sample_user):
    """Create a sample income category for testing."""
    with app.app_context():
        user = User.query.get(sample_user.id)
        category = Category(
            user_id=user.id,
            name='Salary',
            category_type='Income',
            color='#27ae60'
        )
        db.session.add(category)
        db.session.commit()
        db.session.refresh(category)
        yield category


@pytest.fixture
def sample_transaction(app, sample_user, sample_account, sample_category):
    """Create a sample transaction for testing."""
    with app.app_context():
        user = User.query.get(sample_user.id)
        account = Account.query.get(sample_account.id)
        category = Category.query.get(sample_category.id)
        
        transaction = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date.today(),
            amount=Decimal('100.00'),
            transaction_type='Expense',
            description='Test transaction'
        )
        db.session.add(transaction)
        db.session.commit()
        db.session.refresh(transaction)
        yield transaction


@pytest.fixture
def sample_budget(app, sample_user, sample_category):
    """Create a sample budget for testing."""
    with app.app_context():
        user = User.query.get(sample_user.id)
        category = Category.query.get(sample_category.id)
        
        now = datetime.now()
        budget = Budget(
            user_id=user.id,
            category_id=category.id,
            month=now.month,
            year=now.year,
            limit_amount=Decimal('500.00'),
            current_spent=Decimal('0.00'),
            alert_threshold=80
        )
        db.session.add(budget)
        db.session.commit()
        db.session.refresh(budget)
        yield budget


@pytest.fixture
def sample_goal(app, sample_user):
    """Create a sample goal for testing."""
    with app.app_context():
        user = User.query.get(sample_user.id)
        goal = Goal(
            user_id=user.id,
            name='Test Goal',
            target_amount=Decimal('10000.00'),
            current_amount=Decimal('2500.00'),
            description='A test savings goal'
        )
        db.session.add(goal)
        db.session.commit()
        db.session.refresh(goal)
        yield goal


@pytest.fixture
def sample_recurring(app, sample_user, sample_account, sample_category):
    """Create a sample recurring transaction for testing."""
    with app.app_context():
        user = User.query.get(sample_user.id)
        account = Account.query.get(sample_account.id)
        category = Category.query.get(sample_category.id)
        
        today = date.today()
        recurring = RecurringTransaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            name='Monthly Rent',
            amount=Decimal('1500.00'),
            transaction_type='Expense',
            frequency='monthly',
            start_date=today,
            next_due=today,
            is_active=True
        )
        db.session.add(recurring)
        db.session.commit()
        db.session.refresh(recurring)
        yield recurring


@pytest.fixture
def authenticated_client(client, sample_user, app):
    """Create an authenticated test client."""
    with app.app_context():
        with client.session_transaction() as session:
            session['_user_id'] = str(sample_user.id)
            session['_fresh'] = True
    return client

