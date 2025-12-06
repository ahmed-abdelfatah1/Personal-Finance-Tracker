# Financial Reporting Feature Design

## Overview

The Financial Reporting feature extends the Personal Finance Tracker application with comprehensive reporting and data export capabilities. Users can generate customizable financial reports covering income, expenses, and account balances over specified time periods, with visual charts and CSV export functionality. The feature integrates seamlessly with existing Transaction, Account, and Category models.

## Architecture

The feature follows the existing application's layered architecture:

- **Presentation Layer**: Flask routes and Jinja2 templates for report UI
- **Business Logic Layer**: Report service classes for data aggregation and calculations
- **Data Access Layer**: Repository pattern for querying financial data
- **Export Layer**: CSV generation utilities

The implementation leverages existing models (Transaction, Account, Category, User) and extends the application with new report generation and export capabilities.

## Components and Interfaces

### 1. Report Routes (`report_routes.py`)

Flask Blueprint handling HTTP requests for report generation and CSV export:

```python
@report_bp.route('/reports', methods=['GET', 'POST'])
@login_required
def reports() -> str:
    """Display report generation form and results"""

@report_bp.route('/reports/export', methods=['POST'])
@login_required
def export_csv() -> Response:
    """Generate and download CSV export of transactions"""
```

### 2. Report Service (`report_service.py`)

Business logic for report generation and data aggregation:

```python
class ReportService:
    def generate_report(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        transaction_type_filter: Optional[str] = None,
        account_ids: Optional[List[int]] = None
    ) -> ReportData:
        """Generate comprehensive financial report"""
    
    def get_category_breakdown(
        self,
        transactions: List[Transaction],
        transaction_type: str
    ) -> List[CategoryBreakdown]:
        """Calculate category-wise breakdown with percentages"""
    
    def get_monthly_comparison(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[MonthlyData]:
        """Generate month-by-month comparison data"""
    
    def get_account_summary(
        self,
        user_id: int,
        account_ids: Optional[List[int]] = None
    ) -> List[AccountSummary]:
        """Get current balance summary for accounts"""
```

### 3. CSV Export Service (`csv_export_service.py`)

Handles CSV file generation:

```python
class CSVExportService:
    def export_transactions(
        self,
        transactions: List[Transaction],
        start_date: date,
        end_date: date
    ) -> str:
        """Generate CSV content from transactions"""
    
    def generate_filename(
        self,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate standardized filename"""
```

### 4. Report Repository (`report_repository.py`)

Data access layer for report queries:

```python
class ReportRepository:
    def get_transactions_by_date_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        transaction_type: Optional[str] = None,
        account_ids: Optional[List[int]] = None
    ) -> List[Transaction]:
        """Query transactions with filters"""
    
    def get_monthly_aggregates(
        self,
        user_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """Get aggregated monthly data"""
```

## Data Models

### ReportData (Data Transfer Object)

```python
@dataclass
class ReportData:
    start_date: date
    end_date: date
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    income_by_category: List[CategoryBreakdown]
    expenses_by_category: List[CategoryBreakdown]
    account_summaries: List[AccountSummary]
    transaction_count: int
```

### CategoryBreakdown (Data Transfer Object)

```python
@dataclass
class CategoryBreakdown:
    category_id: int
    category_name: str
    amount: Decimal
    percentage: float
    transaction_count: int
```

### AccountSummary (Data Transfer Object)

```python
@dataclass
class AccountSummary:
    account_id: int
    account_name: str
    current_balance: Decimal
    currency: str
```

### MonthlyData (Data Transfer Object)

```python
@dataclass
class MonthlyData:
    month: int
    year: int
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    month_over_month_change: Optional[float]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Date range validation
*For any* report request, if the start date is after the end date, the system should reject the request
**Validates: Requirements 1.3**

### Property 2: Financial calculations correctness
*For any* set of transactions in a date range, the report should correctly calculate: (1) total income as sum of all income transactions, (2) total expenses as sum of all expense transactions, and (3) net savings as income minus expenses
**Validates: Requirements 1.5**

### Property 3: Category breakdown completeness
*For any* report, transactions should be grouped by category with correct amounts and percentages, where the sum of category amounts equals the total and percentages sum to 100% (within rounding tolerance)
**Validates: Requirements 2.1, 2.2, 2.5**

### Property 4: Category sorting
*For any* category breakdown, categories should be sorted by amount in descending order
**Validates: Requirements 2.4**

### Property 5: Empty category exclusion
*For any* report, categories with zero transactions in the date range should not appear in the category breakdown
**Validates: Requirements 2.3**

### Property 6: Account balance display
*For any* report, all user accounts should be displayed with their current balance in the correct currency, regardless of whether they have transactions in the date range
**Validates: Requirements 3.1, 3.3, 3.4**

### Property 7: Total balance calculation
*For any* report, the total balance should equal the sum of all account balances
**Validates: Requirements 3.2**

### Property 8: CSV structure correctness
*For any* CSV export, the file should have a header row with correct column names, and the number of data rows should equal the number of transactions
**Validates: Requirements 4.1, 4.2, 4.4**

### Property 9: CSV field escaping
*For any* transaction with special characters (commas, quotes, newlines) in text fields, the CSV export should properly escape and quote those fields
**Validates: Requirements 4.3**

### Property 10: CSV filename format
*For any* CSV export, the filename should follow the format "transactions_YYYY-MM-DD_to_YYYY-MM-DD.csv" with the correct date range
**Validates: Requirements 4.5**

### Property 11: Transaction type filter correctness
*For any* report with a transaction type filter applied, all returned transactions should match the selected type (Income, Expense, or All)
**Validates: Requirements 5.1, 5.2, 5.3**

### Property 12: Account filter correctness
*For any* report with account filter applied, all transactions should belong to the selected accounts, or all accounts if none selected
**Validates: Requirements 6.1, 6.2**

### Property 13: Monthly aggregation correctness
*For any* monthly comparison report, each month should show correct totals for income, expenses, and net savings calculated from transactions in that month
**Validates: Requirements 7.1, 7.3**

### Property 14: Month-over-month calculation
*For any* monthly comparison report with multiple months, the month-over-month percentage change should be correctly calculated as ((current - previous) / previous) * 100
**Validates: Requirements 7.2**

### Property 15: Monthly chronological order
*For any* monthly comparison report, the monthly data should be ordered chronologically from earliest to latest
**Validates: Requirements 7.4**

## Error Handling

### Input Validation Errors
- Invalid date formats: Return 400 with clear error message
- Start date after end date: Return 400 with validation error
- Invalid transaction type filter: Return 400 with allowed values
- Invalid account IDs: Return 400 with error message

### Data Access Errors
- Database connection failures: Return 500 with generic error, log details
- Query timeouts: Return 504 with timeout message
- No data found: Return successful response with empty report (not an error)

### Export Errors
- CSV generation failures: Return 500 with error message
- File encoding issues: Use UTF-8 with BOM, fallback to ASCII
- Memory issues with large exports: Implement streaming for large datasets

### User Authorization
- Unauthorized access: Redirect to login
- Access to other users' data: Return 403 Forbidden

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples and edge cases:

- Date range validation with various invalid inputs
- Empty transaction list handling
- Single transaction report generation
- CSV escaping with special characters (commas, quotes, newlines)
- Percentage calculation with zero totals
- Month-over-month calculation edge cases

### Property-Based Testing

Property-based tests will verify universal properties across all inputs using the **Hypothesis** library for Python. Each property-based test will run a minimum of 100 iterations.

Each property-based test will be tagged with a comment explicitly referencing the correctness property from this design document using the format: `**Feature: financial-reporting, Property {number}: {property_text}**`

Property tests will include:

1. **Date range validation property** - Generate random date pairs and verify rejection when start > end
2. **Calculation correctness properties** - Generate random transaction sets and verify income/expense/net savings calculations
3. **Category breakdown properties** - Generate random transactions and verify percentage sums and amount sums
4. **CSV format properties** - Generate random transactions and verify CSV structure, row counts, and field escaping
5. **Filter correctness properties** - Generate random transactions and filters, verify filtered results contain only matching transactions
6. **Sorting properties** - Generate random data and verify chronological ordering

### Integration Testing

Integration tests will verify end-to-end workflows:

- Complete report generation flow from HTTP request to rendered template
- CSV export download flow
- Filter application across multiple parameters
- Chart data generation for visualization

### Test Data Strategy

- Use factories to generate test transactions with varied attributes
- Create fixtures for common scenarios (empty data, single month, multi-month)
- Use Hypothesis strategies for property-based test data generation
- Ensure test data covers edge cases: leap years, month boundaries, year transitions
