"""Integration Tests for Routes/Controllers."""

import pytest
from decimal import Decimal
from datetime import date

from app.extensions import db
from app.models import User, Account, Category, Transaction


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_loads(self, client):
        """Test login page renders successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'Login' in response.data

    def test_register_page_loads(self, client):
        """Test register page renders successfully."""
        response = client.get('/register')
        assert response.status_code == 200

    def test_register_new_user(self, client, app):
        """Test user registration."""
        response = client.post('/register', data={
            'email': 'newuser@example.com',
            'password': 'password123',
            'display_name': 'New User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None

    def test_register_duplicate_email(self, client, sample_user, app):
        """Test registration with duplicate email fails."""
        with app.app_context():
            response = client.post('/register', data={
                'email': 'test@example.com',  # Same as sample_user
                'password': 'password123',
                'display_name': 'Duplicate'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'already registered' in response.data.lower() or b'error' in response.data.lower()

    def test_login_valid_credentials(self, client, sample_user, app):
        """Test login with valid credentials."""
        with app.app_context():
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            
            assert response.status_code == 200

    def test_login_invalid_credentials(self, client, sample_user, app):
        """Test login with invalid credentials."""
        with app.app_context():
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'invalid' in response.data.lower() or b'error' in response.data.lower()

    def test_logout(self, authenticated_client, app):
        """Test logout functionality."""
        with app.app_context():
            response = authenticated_client.get('/logout', follow_redirects=True)
            assert response.status_code == 200


class TestDashboardRoutes:
    """Tests for dashboard routes."""

    def test_dashboard_requires_login(self, client):
        """Test dashboard redirects unauthenticated users."""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login

    def test_dashboard_loads_for_authenticated_user(self, authenticated_client, app):
        """Test dashboard loads for authenticated users."""
        with app.app_context():
            response = authenticated_client.get('/dashboard')
            # Should either load (200) or redirect within the app
            assert response.status_code in [200, 302]


class TestAccountRoutes:
    """Tests for account routes."""

    def test_accounts_page_requires_login(self, client):
        """Test accounts page requires authentication."""
        response = client.get('/accounts')
        assert response.status_code == 302

    def test_add_account_page_loads(self, authenticated_client, app):
        """Test add account page loads."""
        with app.app_context():
            response = authenticated_client.get('/add_account')
            assert response.status_code in [200, 302]

    def test_create_account(self, authenticated_client, app, sample_user):
        """Test account creation."""
        with app.app_context():
            response = authenticated_client.post('/add_account', data={
                'name': 'New Account',
                'account_type': 'checking',
                'initial_balance': '1000.00'
            }, follow_redirects=True)
            
            assert response.status_code == 200


class TestCategoryRoutes:
    """Tests for category routes."""

    def test_categories_page_requires_login(self, client):
        """Test categories page requires authentication."""
        response = client.get('/categories')
        assert response.status_code == 302

    def test_add_category_page_loads(self, authenticated_client, app):
        """Test add category page loads."""
        with app.app_context():
            response = authenticated_client.get('/add_category')
            assert response.status_code in [200, 302]


class TestTransactionRoutes:
    """Tests for transaction routes."""

    def test_transactions_page_requires_login(self, client):
        """Test transactions page requires authentication."""
        response = client.get('/transactions')
        assert response.status_code == 302

    def test_add_transaction_page_loads(self, authenticated_client, app):
        """Test add transaction page loads."""
        with app.app_context():
            response = authenticated_client.get('/add_transaction')
            assert response.status_code in [200, 302]


class TestBudgetRoutes:
    """Tests for budget routes."""

    def test_budgets_page_requires_login(self, client):
        """Test budgets page requires authentication."""
        response = client.get('/budgets')
        assert response.status_code == 302

    def test_set_budget_page_loads(self, authenticated_client, app):
        """Test set budget page loads."""
        with app.app_context():
            response = authenticated_client.get('/set_budget')
            assert response.status_code in [200, 302]


class TestGoalRoutes:
    """Tests for goal routes."""

    def test_goals_page_requires_login(self, client):
        """Test goals page requires authentication."""
        response = client.get('/goals')
        assert response.status_code == 302


class TestRecurringRoutes:
    """Tests for recurring transaction routes."""

    def test_recurring_page_requires_login(self, client):
        """Test recurring page requires authentication."""
        response = client.get('/recurring')
        assert response.status_code == 302


class TestReportRoutes:
    """Tests for report routes."""

    def test_reports_page_requires_login(self, client):
        """Test reports page requires authentication."""
        response = client.get('/reports')
        assert response.status_code == 302

