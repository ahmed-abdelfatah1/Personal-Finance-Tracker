"""Currency Repository - Data access layer for Currency model."""

from decimal import Decimal
from typing import Optional, List

from ..extensions import db
from ..models import Currency


class CurrencyRepository:
    """Repository for Currency entity database operations."""

    @staticmethod
    def get_by_code(code: str) -> Optional[Currency]:
        """Retrieve a currency by its code."""
        return Currency.query.get(code)

    @staticmethod
    def get_base_currency() -> Optional[Currency]:
        """Get the base currency (EGP)."""
        return CurrencyRepository.get_by_code('EGP')

    @staticmethod
    def get_all() -> List[Currency]:
        """Retrieve all currencies."""
        return Currency.query.all()

    @staticmethod
    def convert_amount(
        amount: Decimal,
        from_currency_code: str,
        to_currency_code: str = 'EGP'
    ) -> Decimal:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency_code: Source currency code
            to_currency_code: Target currency code (default: EGP)
        
        Returns:
            Converted amount in target currency
        """
        if from_currency_code == to_currency_code:
            return amount

        from_currency = CurrencyRepository.get_by_code(from_currency_code)
        to_currency = CurrencyRepository.get_by_code(to_currency_code)

        if not from_currency or not to_currency:
            # If currency not found, return original amount
            return amount

        # rate_to_base means: 1 unit of this currency = rate_to_base units of base currency
        # So: 1 USD = 47.5329 EGP means USD.rate_to_base = 47.5329
        
        # Convert from source currency to base currency (EGP)
        # amount_in_base = amount * from_currency.rate_to_base
        if from_currency_code == 'EGP':
            amount_in_base = amount
        else:
            amount_in_base = amount * from_currency.rate_to_base
        
        # Convert from base currency to target currency
        # amount_in_target = amount_in_base / to_currency.rate_to_base
        if to_currency_code == 'EGP':
            converted = amount_in_base
        else:
            converted = amount_in_base / to_currency.rate_to_base

        return Decimal(str(round(converted, 2)))

