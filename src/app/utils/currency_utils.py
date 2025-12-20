"""Currency conversion utilities."""

from decimal import Decimal
from typing import Optional

from ..repositories import CurrencyRepository, AccountRepository


def convert_transaction_to_base(
    amount: Decimal,
    account_id: int
) -> Decimal:
    """
    Convert transaction amount to base currency (EGP) based on account currency.
    
    Args:
        amount: Transaction amount in account's currency
        account_id: ID of the account
    
    Returns:
        Amount converted to base currency (EGP)
    """
    account = AccountRepository.get_by_id(account_id)
    if not account:
        return amount

    return CurrencyRepository.convert_amount(
        amount,
        account.currency,
        'EGP'
    )


def convert_to_user_currency(
    amount: Decimal,
    from_currency_code: str,
    user_currency_code: str = 'EGP'
) -> Decimal:
    """
    Convert amount to user's default currency.
    
    Args:
        amount: Amount to convert
        from_currency_code: Source currency code
        user_currency_code: User's default currency code
    
    Returns:
        Amount converted to user's currency
    """
    return CurrencyRepository.convert_amount(
        amount,
        from_currency_code,
        user_currency_code
    )

