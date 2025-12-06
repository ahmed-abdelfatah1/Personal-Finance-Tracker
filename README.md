# Personal Finance Tracker

A comprehensive web-based personal finance management application built with Flask and SQLAlchemy.

## Features

### Core Features
- **User Authentication**: Secure login and registration with password hashing
- **Dashboard**: Overview of financial status with key metrics
- **Transaction Management**: Add, edit, delete, and filter income/expense transactions
- **Account Management**: Manage multiple financial accounts (bank accounts, wallets, etc.)
- **Category Management**: Organize transactions with custom categories
- **Budget Tracking**: Set monthly budgets per category with alerts

### New Features (Recently Added)

#### FR-10: Financial Reporting ✅
- Generate comprehensive financial reports for custom date ranges
- View income and expense breakdowns by category with percentages
- Account balance summaries
- Monthly comparison reports with month-over-month changes
- CSV export functionality for transaction data
- Filter reports by transaction type and accounts

## Technology Stack

- **Backend**: Flask 3.0.3
- **Database**: SQLAlchemy 2.0.44 with SQLite
- **Authentication**: Flask-Login 0.6.3
- **Password Hashing**: Flask-Bcrypt 1.0.1
- **Testing**: Pytest 8.3.3

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Personal-Finance-Tracker
```

2. Create and activate virtual environment:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python run.py
```

5. Access the application at `http://127.0.0.1:5000`

## Project Structure

```
Personal-Finance-Tracker/
├── src/
│   └── app/
│       ├── controllers/          # Route handlers (blueprints)
│       │   ├── auth_routes.py
│       │   ├── dashboard_routes.py
│       │   ├── transaction_routes.py
│       │   ├── account_routes.py
│       │   ├── budget_routes.py
│       │   ├── category_routes.py
│       │   └── report_routes.py  # NEW: Financial reporting
│       ├── models/               # Database models
│       │   ├── finance_models.py
│       │   └── report_models.py  # NEW: Report DTOs
│       ├── repositories/         # Data access layer
│       │   └── report_repository.py  # NEW: Report queries
│       ├── services/             # Business logic
│       │   ├── report_service.py      # NEW: Report generation
│       │   └── csv_export_service.py  # NEW: CSV export
│       ├── templates/            # HTML templates
│       ├── static/               # CSS, JS, images
│       ├── config.py             # Configuration
│       ├── extensions.py         # Flask extensions
│       └── __init__.py           # App factory
├── tests/                        # Test files
├── .kiro/                        # Spec files for features
│   └── specs/
│       ├── financial-reporting/  # NEW: FR-10 spec
│       ├── goal-tracking/        # NEW: FR-11 spec (planned)
│       └── recurring-transactions/  # NEW: FR-12 spec (planned)
├── finance.db                    # SQLite database
├── requirements.txt              # Python dependencies
├── run.py                        # Application entry point
└── README.md                     # This file
```

## Database Schema

### Core Tables
- **user**: User accounts with authentication
- **account**: Financial accounts (bank, wallet, etc.)
- **category**: Transaction categories
- **transaction**: Income and expense records
- **budget**: Monthly budget limits per category
- **transaction_template**: Templates for recurring transactions
- **currency**: Multi-currency support

## Usage

### Financial Reports

1. Navigate to **Reports** from the main menu
2. Select date range (start and end dates)
3. Optionally filter by:
   - Transaction type (All, Income, Expense)
   - Specific accounts
4. Click **Generate Report** to view:
   - Summary metrics (total income, expenses, net savings)
   - Category breakdowns with percentages
   - Account balances
   - Monthly comparison data
5. Click **Export to CSV** to download transaction data

## Planned Features

### FR-11: Goal Setting & Tracking (Spec Ready)
- Create savings goals with target amounts and deadlines
- Track contributions toward goals
- View progress with visual indicators
- Link goals to specific accounts

### FR-12: Recurring Transactions (Spec Ready)
- Set up automatic transaction generation
- Support for daily, weekly, monthly, yearly patterns
- Pause/resume recurring transactions
- Batch processing for due transactions

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
The application uses SQLAlchemy for database management. The database is automatically created on first run.

## Spec-Driven Development

This project follows a spec-driven development approach with comprehensive documentation in `.kiro/specs/`:

- **requirements.md**: User stories and acceptance criteria (EARS format)
- **design.md**: Architecture, components, data models, and correctness properties
- **tasks.md**: Implementation task breakdown

## Contributing

1. Create feature specs in `.kiro/specs/<feature-name>/`
2. Follow the existing architecture patterns
3. Write tests for new functionality
4. Update documentation

## License

This project is for educational purposes.

## Notes

- Default currency is EGP (Egyptian Pound)
- The application runs in debug mode by default (change in production)
- SQLite database is used for simplicity (consider PostgreSQL for production)
- Python 3.14+ compatible (requires SQLAlchemy 2.0.44+)
