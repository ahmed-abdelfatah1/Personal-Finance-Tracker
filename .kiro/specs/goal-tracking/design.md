# Goal Setting & Tracking Feature Design

## Overview

The Goal Setting & Tracking feature adds financial goal management capabilities to the Personal Finance Tracker. Users can create savings goals with target amounts and deadlines, track contributions over time, and visualize progress. The feature integrates with existing User and Account models while introducing new Goal and GoalContribution models.

## Architecture

The feature follows the existing application's layered architecture:

- **Presentation Layer**: Flask routes and Jinja2 templates for goal management UI
- **Business Logic Layer**: Goal service classes for progress calculations and validations
- **Data Access Layer**: Repository pattern for goal and contribution data access
- **Data Model Layer**: SQLAlchemy models for Goal and GoalContribution entities

## Components and Interfaces

### 1. Goal Routes (`goal_routes.py`)

Flask Blueprint handling HTTP requests for goal management:

```python
@goal_bp.route('/goals', methods=['GET'])
@login_required
def goals() -> str:
    """Display all user goals"""

@goal_bp.route('/goals/add', methods=['GET', 'POST'])
@login_required
def add_goal():
    """Create a new goal"""

@goal_bp.route('/goals/<int:goal_id>', methods=['GET'])
@login_required
def goal_detail(goal_id: int) -> str:
    """Display goal details and contribution history"""

@goal_bp.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_goal(goal_id: int):
    """Edit an existing goal"""

@goal_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id: int):
    """Delete a goal"""

@goal_bp.route('/goals/<int:goal_id>/contribute', methods=['POST'])
@login_required
def add_contribution(goal_id: int):
    """Add a contribution to a goal"""
```

### 2. Goal Service (`goal_service.py`)

Business logic for goal calculations and validations:

```python
class GoalService:
    def calculate_progress_percentage(
        self,
        current_amount: Decimal,
        target_amount: Decimal
    ) -> float:
        """Calculate progress percentage"""
    
    def is_achieved(
        self,
        current_amount: Decimal,
        target_amount: Decimal
    ) -> bool:
        """Check if goal is achieved"""
    
    def is_overdue(
        self,
        deadline: Optional[date],
        current_amount: Decimal,
        target_amount: Decimal
    ) -> bool:
        """Check if goal is overdue"""
    
    def days_remaining(
        self,
        deadline: Optional[date]
    ) -> Optional[int]:
        """Calculate days until deadline"""
    
    def validate_goal_data(
        self,
        target_amount: Decimal,
        deadline: Optional[date]
    ) -> tuple[bool, Optional[str]]:
        """Validate goal creation/update data"""
```

### 3. Goal Repository (`goal_repository.py`)

Data access layer for goal queries:

```python
class GoalRepository:
    def get_user_goals(
        self,
        user_id: int,
        include_achieved: bool = True
    ) -> List[Goal]:
        """Get all goals for a user"""
    
    def get_goal_by_id(
        self,
        goal_id: int,
        user_id: int
    ) -> Optional[Goal]:
        """Get a specific goal"""
    
    def get_goal_statistics(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get aggregated goal statistics for dashboard"""
```

## Data Models

### Goal Model

```python
class Goal(db.Model):
    __tablename__ = 'goal'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    target_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal('0.00')
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="goals")
    contributions: Mapped[List["GoalContribution"]] = relationship(
        "GoalContribution", back_populates="goal", cascade="all, delete-orphan"
    )
    linked_accounts: Mapped[List["Account"]] = relationship(
        "Account", secondary="goal_account_link", back_populates="linked_goals"
    )
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.target_amount == 0:
            return 0.0
        return float((self.current_amount / self.target_amount) * 100)
    
    @property
    def is_achieved(self) -> bool:
        """Check if goal is achieved"""
        return self.current_amount >= self.target_amount
    
    @property
    def is_overdue(self) -> bool:
        """Check if goal is overdue"""
        if not self.deadline:
            return False
        return date.today() > self.deadline and not self.is_achieved
    
    @property
    def days_remaining(self) -> Optional[int]:
        """Calculate days until deadline"""
        if not self.deadline:
            return None
        delta = self.deadline - date.today()
        return delta.days
```

### GoalContribution Model

```python
class GoalContribution(db.Model):
    __tablename__ = 'goal_contribution'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('goal.id', ondelete='CASCADE'), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    contribution_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    goal: Mapped["Goal"] = relationship("Goal", back_populates="contributions")
```

### GoalAccountLink Model (Association Table)

```python
class GoalAccountLink(db.Model):
    __tablename__ = 'goal_account_link'
    
    goal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('goal.id', ondelete='CASCADE'), primary_key=True
    )
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('account.id', ondelete='CASCADE'), primary_key=True
    )
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Goal validation
*For any* goal creation or update, if the target amount is less than or equal to zero or the deadline is in the past, the system should reject the operation
**Validates: Requirements 1.4, 1.5**

### Property 2: Initial amount invariant
*For any* newly created goal, the current amount should be initialized to zero
**Validates: Requirements 1.6**

### Property 3: Contribution accumulation
*For any* goal and contribution, adding the contribution should increase the goal's current amount by exactly the contribution amount
**Validates: Requirements 2.1**

### Property 4: Progress calculation correctness
*For any* goal, the progress percentage should equal (current_amount / target_amount) * 100
**Validates: Requirements 3.2, 2.5**

### Property 5: Achievement status
*For any* goal, if the current amount is greater than or equal to the target amount, the goal should be marked as achieved
**Validates: Requirements 3.5**

### Property 6: Overdue status
*For any* goal with a deadline, if today's date is past the deadline and the goal is not achieved, the goal should be marked as overdue
**Validates: Requirements 3.4**

### Property 7: Days remaining calculation
*For any* goal with a deadline, the days remaining should equal the deadline date minus today's date
**Validates: Requirements 3.3**

### Property 8: Contribution ordering
*For any* goal's contribution list, contributions should be ordered in reverse chronological order (newest first)
**Validates: Requirements 6.1**

### Property 9: Cascade deletion
*For any* goal deletion, all associated contributions should also be deleted
**Validates: Requirements 5.1**

### Property 10: Data isolation
*For any* goal deletion, no transactions or accounts should be affected
**Validates: Requirements 5.3**

### Property 11: Current amount immutability
*For any* goal edit operation, the current amount should not be directly modifiable (only through contributions)
**Validates: Requirements 4.2**

### Property 12: Dashboard statistics accuracy
*For any* user, the dashboard should correctly count active goals, achieved goals, and sum target and current amounts across all goals
**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

## Error Handling

### Input Validation Errors
- Missing required fields (name, target amount): Return 400 with clear error message
- Invalid target amount (≤ 0): Return 400 with validation error
- Past deadline date: Return 400 with validation error
- Invalid contribution amount (≤ 0): Return 400 with validation error

### Data Access Errors
- Goal not found: Return 404 with error message
- Unauthorized access to other user's goals: Return 403 Forbidden
- Database connection failures: Return 500 with generic error, log details

### Business Logic Errors
- Attempting to modify current amount directly: Return 400 with error message
- Invalid goal state transitions: Return 400 with explanation

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples and edge cases:

- Goal creation with valid and invalid data
- Contribution addition with various amounts
- Progress calculation with edge cases (zero target, over 100%)
- Status determination (achieved, overdue) with various dates
- Cascade deletion behavior

### Property-Based Testing

Property-based tests will verify universal properties across all inputs using the **Hypothesis** library for Python. Each property-based test will run a minimum of 100 iterations.

Each property-based test will be tagged with a comment explicitly referencing the correctness property from this design document using the format: `**Feature: goal-tracking, Property {number}: {property_text}**`

Property tests will include:

1. **Validation properties** - Generate random invalid inputs and verify rejection
2. **Calculation properties** - Generate random goals and contributions, verify progress calculations
3. **Status properties** - Generate random dates and amounts, verify achievement and overdue status
4. **Ordering properties** - Generate random contributions, verify chronological ordering
5. **Deletion properties** - Generate random goals with contributions, verify cascade behavior

### Integration Testing

Integration tests will verify end-to-end workflows:

- Complete goal creation flow from HTTP request to database
- Contribution addition and progress update flow
- Goal editing and validation flow
- Dashboard statistics calculation