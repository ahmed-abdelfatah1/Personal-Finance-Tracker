"""Report Data Transfer Objects."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional


@dataclass
class CategoryBreakdown:
    """Category breakdown with amount and percentage."""
    category_id: int
    category_name: str
    amount: Decimal
    percentage: float
    transaction_count: int


@dataclass
class AccountSummary:
    """Account summary with current balance."""
    account_id: int
    account_name: str
    current_balance: Decimal
    currency: str


@dataclass
class MonthlyData:
    """Monthly aggregated data."""
    month: int
    year: int
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    month_over_month_change: Optional[float] = None


@dataclass
class ReportData:
    """Complete report data."""
    start_date: date
    end_date: date
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    income_by_category: List[CategoryBreakdown]
    expenses_by_category: List[CategoryBreakdown]
    account_summaries: List[AccountSummary]
    transaction_count: int
