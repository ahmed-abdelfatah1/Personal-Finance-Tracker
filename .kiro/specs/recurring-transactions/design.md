# Recurring Transactions Feature Design

## Overview

The Recurring Transactions feature automates the creation of regular transactions based on user-defined schedules. The system supports multiple recurrence patterns (daily, weekly, monthly, yearly) and automatically generates transactions when due, reducing manual data entry for predictable financial activities.

## Architecture

- **Presentation Layer**: Flask routes and templates for recurring transaction management
- **Business Logic Layer**: Recurrence calculation and transaction generation services
- **Data Access Layer**: Repository for recurring transaction queries
- **Scheduler Layer**: Batch process for automatic transaction generation

## Components and Interfaces

### 1. RecurringTransaction Model

```python
class RecurringTransaction(db.Model):
    __tablename__ = 'recurring_transaction'
    
    id: Mapped[int]
    user_id: Mapped[int]
    account_id: Mapped[int]
    category_id: Mapped[int]
    amount: Mapped[Decimal]
    transaction_type: Mapped[str]  # 'Income' or 'Expense'
    description: Mapped[Optional[str]]
    notes: Mapped[Optional[str]]
    recurrence_pattern: Mapped[str]  # 'daily', 'weekly', 'monthly', 'yearly'
    recurrence_interval: Mapped[int]  # e.g., every 2 weeks
    start_date: Mapped[date]
    end_date: Mapped[Optional[date]]
    next_occurrence: Mapped[date]
    is_active: Mapped[bool]
    is_paused: Mapped[bool]
    created_at: Mapped[datetime]
```

### 2. RecurrenceService

```python
class RecurrenceService:
    def calculate_next_occurrence(
        self,
        current_date: date,
        pattern: str,
        interval: int
    ) -> date:
        """Calculate next occurrence date based on pattern"""
    
    def should_generate(
        self,
        recurring_transaction: RecurringTransaction
    ) -> bool:
        """Check if transaction should be generated"""
    
    def generate_transaction(
        self,
        recurring_transaction: RecurringTransaction
    ) -> Transaction:
        """Generate a transaction from recurring template"""
```

### 3. Batch Generation Service

```python
class BatchGenerationService:
    def process_due_recurring_transactions(self) -> int:
        """Process all due recurring transactions and return count generated"""
```

## Data Models

The RecurringTransaction model extends the existing transaction structure with recurrence scheduling fields. Generated transactions link back to their source recurring template.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Date validation
*For any* recurring transaction, if the end date is before the start date, the system should reject creation
**Validates: Requirements 1.5**

### Property 2: Next occurrence calculation
*For any* recurring transaction and recurrence pattern, the next occurrence date should be correctly calculated based on the pattern and interval
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.4**

### Property 3: Transaction generation
*For any* recurring transaction where current date >= next occurrence date and is_active and not is_paused, a transaction should be generated
**Validates: Requirements 3.1, 6.4**

### Property 4: Generated transaction properties
*For any* generated transaction, it should have the same account, category, amount, type, description, and notes as the recurring template
**Validates: Requirements 3.2**

### Property 5: Balance update
*For any* generated transaction, the account balance should be updated according to the transaction type
**Validates: Requirements 3.3**

### Property 6: End date enforcement
*For any* recurring transaction with an end date, if the next occurrence would exceed the end date, no transaction should be generated
**Validates: Requirements 3.5**

### Property 7: Pause behavior
*For any* paused recurring transaction, no transactions should be generated regardless of the next occurrence date
**Validates: Requirements 6.1, 6.4**

### Property 8: Historical preservation
*For any* recurring transaction deletion or modification, previously generated transactions should remain unchanged
**Validates: Requirements 7.2, 5.3**

## Error Handling

- Invalid recurrence patterns: Return 400 with error
- Invalid date ranges: Return 400 with validation error
- Missing required fields: Return 400 with clear message
- Unauthorized access: Return 403 Forbidden
- Database errors: Return 500, log details

## Testing Strategy

### Unit Testing
- Recurrence calculation for each pattern type
- Date validation edge cases
- Transaction generation logic
- Pause/resume functionality

### Property-Based Testing
Using **Hypothesis** library with minimum 100 iterations per test:
- Date validation properties
- Next occurrence calculation for all patterns
- Transaction generation conditions
- Balance update correctness

### Integration Testing
- End-to-end recurring transaction creation and generation
- Batch process execution
- Account balance updates through generated transactions
