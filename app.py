from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from src.app.models import User
from src.app.extensions import db
from src.app.models.finance_models import Transaction, Account, Category, Budget


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-this-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'

# Initialize database and login manager
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Where to redirect if not logged in

# This function loads a user from the database
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def index():
    return redirect(url_for('login'))

# Login route (we'll implement this next)
@app.route('/login', methods=['GET', 'POST'])

def login():
    if request.method == 'GET':
        # Show login form
        return render_template('login.html')
    
    # POST request - process login
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Validate inputs
    if not email or not password:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('login'))
    
    # Find user in database
    user = User.query.filter_by(email=email).first()
    
    # Check if user exists and password is correct
    if user and user.check_password(password):
        login_user(user)  # Create session
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email or password', 'error')
        return redirect(url_for('login'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    # Get form data
    email = request.form.get('email')
    password = request.form.get('password')
    display_name = request.form.get('display_name')
    
    # Validate inputs
    if not email or not password:
        flash('Email and password are required', 'error')
        return redirect(url_for('register'))
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email already registered', 'error')
        return redirect(url_for('register'))
    
    # Create new user
    new_user = User(email=email, display_name=display_name)
    new_user.set_password(password)  # This should hash the password
    
    # Save to database
    db.session.add(new_user)
    db.session.commit()
    
    flash('Registration successful! Please login.', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()  # This destroys the session
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Dashboard route (protected)
@app.route('/dashboard')
@login_required
def dashboard():
    # Get current user's data
    user = current_user
    
    # Calculate total balance (sum of all accounts)
    total_balance = user.get_total_balance()
    
    # Get recent transactions (last 5)
    recent_transactions = Transaction.query.filter_by(
        user_id=user.id
    ).order_by(Transaction.date.desc()).limit(5).all()
    
    # Get monthly summary (you'll need to implement this in the Model)
    # For now, we'll use placeholder
    monthly_summary = {
        'income': 0,
        'expenses': 0,
        'net': 0
    }
    
    # Pass data to template
    return render_template(
        'dashboard.html',
        user=user,
        total_balance=total_balance,
        recent_transactions=recent_transactions,
        monthly_summary=monthly_summary
    )

@app.route('/transactions')
@login_required
def transactions():
    # Get filter parameters from URL
    category_id = request.args.get('category', type=int)
    transaction_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Start with all user's transactions
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    # Apply filters if provided
    if category_id:
        query = query.filter_by(category_id=category_id)
    if transaction_type and transaction_type in ['Income', 'Expense']:
        query = query.filter_by(transaction_type=transaction_type)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    # Order by date (newest first) and get all
    all_transactions = query.order_by(Transaction.date.desc()).all()
    
    # Get user's accounts and categories for the form
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'transactions.html',
        transactions=all_transactions,
        accounts=accounts,
        categories=categories
    )

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'GET':
        # Show the form with accounts and categories
        accounts = Account.query.filter_by(user_id=current_user.id).all()
        categories = Category.query.filter_by(user_id=current_user.id).all()
        
        return render_template(
            'add_transaction.html',
            accounts=accounts,
            categories=categories
        )
    
    # POST request - process the form
    try:
        # Get form data
        account_id = request.form.get('account_id')
        category_id = request.form.get('category_id')
        date = request.form.get('date')
        amount = float(request.form.get('amount'))
        transaction_type = request.form.get('transaction_type')
        description = request.form.get('description', '')
        
        # Validate required fields
        if not all([account_id, category_id, date, amount, transaction_type]):
            flash('All fields except description are required', 'error')
            return redirect(url_for('add_transaction'))
        
        # Validate transaction type
        if transaction_type not in ['Income', 'Expense']:
            flash('Invalid transaction type', 'error')
            return redirect(url_for('add_transaction'))
        
        # Create new transaction
        new_transaction = Transaction(
            user_id=current_user.id,
            account_id=account_id,
            category_id=category_id,
            date=date,
            amount=amount,
            transaction_type=transaction_type,
            description=description
        )
        
        # Save to database
        db.session.add(new_transaction)
        db.session.commit()
        
        # Update account balance (this should be in the Model)
        # For now, we'll call a method
        account = Account.query.get(account_id)
        if transaction_type == 'Income':
            account.current_balance += amount
        else:
            account.current_balance -= amount
        db.session.commit()
        
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transactions'))
        
    except ValueError:
        flash('Invalid amount format', 'error')
        return redirect(url_for('add_transaction'))
    except Exception as e:
        flash(f'Error adding transaction: {str(e)}', 'error')
        return redirect(url_for('add_transaction'))

@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    # Get the transaction, ensuring it belongs to current user
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        user_id=current_user.id
    ).first()
    
    if not transaction:
        flash('Transaction not found', 'error')
        return redirect(url_for('transactions'))
    
    if request.method == 'GET':
        # Show edit form with current values
        accounts = Account.query.filter_by(user_id=current_user.id).all()
        categories = Category.query.filter_by(user_id=current_user.id).all()
        
        return render_template(
            'edit_transaction.html',
            transaction=transaction,
            accounts=accounts,
            categories=categories
        )
    
    # POST request - update transaction
    try:
        # Store old values for balance adjustment
        old_amount = transaction.amount
        old_type = transaction.transaction_type
        old_account_id = transaction.account_id
        
        # Get new values
        transaction.account_id = request.form.get('account_id')
        transaction.category_id = request.form.get('category_id')
        transaction.date = request.form.get('date')
        transaction.amount = float(request.form.get('amount'))
        transaction.transaction_type = request.form.get('transaction_type')
        transaction.description = request.form.get('description', '')
        
        # Validate
        if transaction.transaction_type not in ['Income', 'Expense']:
            flash('Invalid transaction type', 'error')
            return redirect(url_for('edit_transaction', transaction_id=transaction_id))
        
        # Update old account balance (reverse old transaction)
        old_account = Account.query.get(old_account_id)
        if old_type == 'Income':
            old_account.current_balance -= old_amount
        else:
            old_account.current_balance += old_amount
        
        # Update new account balance (apply new transaction)
        new_account = Account.query.get(transaction.account_id)
        if transaction.transaction_type == 'Income':
            new_account.current_balance += transaction.amount
        else:
            new_account.current_balance -= transaction.amount
        
        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transactions'))
        
    except Exception as e:
        flash(f'Error updating transaction: {str(e)}', 'error')
        return redirect(url_for('edit_transaction', transaction_id=transaction_id))

@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    # Get the transaction
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        user_id=current_user.id
    ).first()
    
    if not transaction:
        flash('Transaction not found', 'error')
        return redirect(url_for('transactions'))
    
    try:
        # Get account for balance adjustment
        account = Account.query.get(transaction.account_id)
        
        # Reverse the transaction effect on account balance
        if transaction.transaction_type == 'Income':
            account.current_balance -= transaction.amount
        else:
            account.current_balance += transaction.amount
        
        # Delete the transaction
        db.session.delete(transaction)
        db.session.commit()
        
        flash('Transaction deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting transaction: {str(e)}', 'error')
    
    return redirect(url_for('transactions'))

@app.route('/accounts')
@login_required
def accounts():
    # Get all accounts for current user
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    
    # Calculate total balance
    total_balance = sum(account.current_balance for account in user_accounts)
    
    return render_template(
        'accounts.html',
        accounts=user_accounts,
        total_balance=total_balance
    )

@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'GET':
        return render_template('add_account.html')
    
    # POST request - create new account
    try:
        name = request.form.get('name')
        account_type = request.form.get('account_type')
        initial_balance = float(request.form.get('initial_balance', 0))
        
        # Validate
        if not name:
            flash('Account name is required', 'error')
            return redirect(url_for('add_account'))
        
        # Create new account
        new_account = Account(
            user_id=current_user.id,
            name=name,
            account_type=account_type,
            initial_balance=initial_balance,
            current_balance=initial_balance
        )
        
        db.session.add(new_account)
        db.session.commit()
        
        flash(f'Account "{name}" created successfully!', 'success')
        return redirect(url_for('accounts'))
        
    except ValueError:
        flash('Invalid balance amount', 'error')
        return redirect(url_for('add_account'))
    except Exception as e:
        flash(f'Error creating account: {str(e)}', 'error')
        return redirect(url_for('add_account'))


@app.route('/edit_account/<int:account_id>', methods=['GET', 'POST'])
@login_required
def edit_account(account_id):
    # Get account, ensuring it belongs to current user
    account = Account.query.filter_by(
        id=account_id,
        user_id=current_user.id
    ).first()
    
    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('accounts'))
    
    if request.method == 'GET':
        return render_template('edit_account.html', account=account)
    
    # POST request - update account
    try:
        account.name = request.form.get('name')
        account.account_type = request.form.get('account_type')
        
        # Only update initial balance if no transactions exist
        transaction_count = Transaction.query.filter_by(account_id=account.id).count()
        if transaction_count == 0:
            new_initial = float(request.form.get('initial_balance', 0))
            difference = new_initial - account.initial_balance
            account.initial_balance = new_initial
            account.current_balance += difference
        
        db.session.commit()
        
        flash('Account updated successfully!', 'success')
        return redirect(url_for('accounts'))
        
    except ValueError:
        flash('Invalid balance amount', 'error')
        return redirect(url_for('edit_account', account_id=account_id))
    except Exception as e:
        flash(f'Error updating account: {str(e)}', 'error')
        return redirect(url_for('edit_account', account_id=account_id))

@app.route('/delete_account/<int:account_id>', methods=['POST'])
@login_required
def delete_account(account_id):
    # Get account
    account = Account.query.filter_by(
        id=account_id,
        user_id=current_user.id
    ).first()
    
    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('accounts'))
    
    # Check if account has transactions
    transaction_count = Transaction.query.filter_by(account_id=account.id).count()
    
    if transaction_count > 0:
        flash(f'Cannot delete account "{account.name}" because it has {transaction_count} transactions. Delete transactions first.', 'error')
        return redirect(url_for('accounts'))
    
    try:
        db.session.delete(account)
        db.session.commit()
        flash(f'Account "{account.name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting account: {str(e)}', 'error')
    
    return redirect(url_for('accounts'))

@app.route('/budgets')
@login_required
def budgets():
    # Get current month and year
    from datetime import datetime
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Get all budgets for current user
    user_budgets = Budget.query.filter_by(
        user_id=current_user.id
    ).order_by(Budget.year.desc(), Budget.month.desc()).all()
    
    # Get categories for the form
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Filter categories to only expense categories (since we budget expenses)
    expense_categories = [c for c in categories if c.category_type == 'Expense']
    
    return render_template(
        'budgets.html',
        budgets=user_budgets,
        categories=expense_categories,
        current_month=current_month,
        current_year=current_year
    )

@app.route('/set_budget', methods=['GET', 'POST'])
@login_required
def set_budget():
    if request.method == 'GET':
        # Get expense categories for dropdown
        categories = Category.query.filter_by(
            user_id=current_user.id,
            category_type='Expense'
        ).all()
        
        return render_template('set_budget.html', categories=categories)
    
    # POST request - create/update budget
    try:
        category_id = request.form.get('category_id')
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))
        limit_amount = float(request.form.get('limit_amount'))
        
        # Validate
        if not all([category_id, month, year, limit_amount]):
            flash('All fields are required', 'error')
            return redirect(url_for('set_budget'))
        
        if not (1 <= month <= 12):
            flash('Month must be between 1 and 12', 'error')
            return redirect(url_for('set_budget'))
        
        if limit_amount <= 0:
            flash('Budget amount must be positive', 'error')
            return redirect(url_for('set_budget'))
        
        # Check if budget already exists for this category/month/year
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=category_id,
            month=month,
            year=year
        ).first()
        
        if existing_budget:
            # Update existing budget
            existing_budget.limit_amount = limit_amount
            existing_budget.update_current_spent()  # Recalculate spent amount
            action = 'updated'
        else:
            # Create new budget
            new_budget = Budget(
                user_id=current_user.id,
                category_id=category_id,
                month=month,
                year=year,
                limit_amount=limit_amount
            )
            new_budget.update_current_spent()  # Calculate initial spent
            db.session.add(new_budget)
            action = 'created'
        
        db.session.commit()
        
        # Check if budget is over threshold
        budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=category_id,
            month=month,
            year=year
        ).first()
        
        if budget and budget.check_alert_threshold():
            category = Category.query.get(category_id)
            flash(f'Budget {action} successfully! ⚠ Warning: {category.name} budget is {budget.get_percentage_used():.1f}% used.', 'warning')
        else:
            flash(f'Budget {action} successfully!', 'success')
        
        return redirect(url_for('budgets'))
        
    except ValueError:
        flash('Invalid number format', 'error')
        return redirect(url_for('set_budget'))
    except Exception as e:
        flash(f'Error setting budget: {str(e)}', 'error')
        return redirect(url_for('set_budget'))

@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    # Get budget
    budget = Budget.query.filter_by(
        id=budget_id,
        user_id=current_user.id
    ).first()
    
    if not budget:
        flash('Budget not found', 'error')
        return redirect(url_for('budgets'))
    
    try:
        category_name = budget.category.name if budget.category else 'Unknown'
        db.session.delete(budget)
        db.session.commit()
        flash(f'Budget for {category_name} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting budget: {str(e)}', 'error')
    
    return redirect(url_for('budgets'))

@app.route('/categories')
@login_required
def categories():
    # Get all categories for current user
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Separate income and expense categories
    income_categories = [c for c in user_categories if c.category_type == 'Income']
    expense_categories = [c for c in user_categories if c.category_type == 'Expense']
    
    return render_template(
        'categories.html',
        income_categories=income_categories,
        expense_categories=expense_categories
    )

@app.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'GET':
        return render_template('add_category.html')
    
    # POST request - create new category
    try:
        name = request.form.get('name')
        category_type = request.form.get('category_type')
        color = request.form.get('color', '#3498db')  # Default blue
        
        # Validate
        if not name or not category_type:
            flash('Name and type are required', 'error')
            return redirect(url_for('add_category'))
        
        if category_type not in ['Income', 'Expense']:
            flash('Invalid category type', 'error')
            return redirect(url_for('add_category'))
        
        # Check if category already exists for this user
        existing = Category.query.filter_by(
            user_id=current_user.id,
            name=name,
            category_type=category_type
        ).first()
        
        if existing:
            flash(f'Category "{name}" ({category_type}) already exists', 'error')
            return redirect(url_for('add_category'))
        
        # Create new category
        new_category = Category(
            user_id=current_user.id,
            name=name,
            category_type=category_type,
            color=color
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        flash(f'Category "{name}" created successfully!', 'success')
        return redirect(url_for('categories'))
        
    except Exception as e:
        flash(f'Error creating category: {str(e)}', 'error')
        return redirect(url_for('add_category'))

@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    # Get category
    category = Category.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first()
    
    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('categories'))
    
    # Check if category has transactions
    transaction_count = Transaction.query.filter_by(category_id=category.id).count()
    
    if transaction_count > 0:
        flash(f'Cannot delete category "{category.name}" because it has {transaction_count} transactions. Delete or reassign transactions first.', 'error')
        return redirect(url_for('categories'))
    
    # Check if category has budgets
    budget_count = Budget.query.filter_by(category_id=category.id).count()
    if budget_count > 0:
        flash(f'Cannot delete category "{category.name}" because it has {budget_count} budgets. Delete budgets first.', 'error')
        return redirect(url_for('categories'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('categories'))

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True)