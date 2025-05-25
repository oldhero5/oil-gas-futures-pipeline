"""Pydantic models for data validation."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class FuturesContract(BaseModel):
    """Model for futures contract data."""

    contract_id: str
    commodity_id: str
    symbol: str
    expiration_date: date
    first_trade_date: date | None = None
    last_trade_date: date | None = None
    is_active: bool = True

    @field_validator("commodity_id")
    def validate_commodity(cls, v: str) -> str:
        """Validate commodity ID."""
        valid_commodities = ["WTI", "NG"]
        if v not in valid_commodities:
            raise ValueError(f"Invalid commodity: {v}")
        return v


class FuturesPrice(BaseModel):
    """Model for futures price data."""

    contract_id: str
    price_date: date
    price_time: datetime | None = None
    open_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    close_price: Decimal
    settlement_price: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None

    @field_validator("close_price", "open_price", "high_price", "low_price", "settlement_price")
    def validate_price(cls, v: Decimal | None) -> Decimal | None:
        """Validate price is positive."""
        if v is not None and v <= 0:
            raise ValueError("Price must be positive")
        return v

    @field_validator("volume", "open_interest")
    def validate_volume(cls, v: int | None) -> int | None:
        """Validate volume is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Volume must be non-negative")
        return v


class OptionContract(BaseModel):
    """Model for option contract data."""

    option_id: str
    underlying_contract_id: str
    option_type: str = Field(..., pattern="^(CALL|PUT)$")
    strike_price: Decimal
    expiration_date: date
    exercise_style: str = "AMERICAN"
    is_active: bool = True

    @field_validator("strike_price")
    def validate_strike(cls, v: Decimal) -> Decimal:
        """Validate strike price is positive."""
        if v <= 0:
            raise ValueError("Strike price must be positive")
        return v


class OptionPrice(BaseModel):
    """Model for option price data."""

    option_id: str
    price_date: date
    price_time: datetime | None = None
    bid_price: Decimal | None = None
    ask_price: Decimal | None = None
    last_price: Decimal | None = None
    settlement_price: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None

    @field_validator("bid_price", "ask_price", "last_price", "settlement_price")
    def validate_price(cls, v: Decimal | None) -> Decimal | None:
        """Validate price is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Option price cannot be negative")
        return v


class ImpliedVolatility(BaseModel):
    """Model for implied volatility data."""

    option_id: str
    price_date: date
    implied_vol: Decimal
    underlying_price: Decimal
    risk_free_rate: Decimal | None = None
    calculation_method: str = "BLACK_SCHOLES"

    @field_validator("implied_vol")
    def validate_vol(cls, v: Decimal) -> Decimal:
        """Validate implied volatility is reasonable."""
        if v <= 0 or v > 5:  # 500% annualized vol is a reasonable upper limit
            raise ValueError("Implied volatility must be between 0 and 500%")
        return v

    @field_validator("underlying_price")
    def validate_underlying(cls, v: Decimal) -> Decimal:
        """Validate underlying price is positive."""
        if v <= 0:
            raise ValueError("Underlying price must be positive")
        return v


class Greeks(BaseModel):
    """Model for option Greeks."""

    option_id: str
    price_date: date
    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None
    rho: Decimal | None = None
    underlying_price: Decimal
    implied_vol: Decimal

    @field_validator("delta")
    def validate_delta(cls, v: Decimal | None) -> Decimal | None:
        """Validate delta is between -1 and 1."""
        if v is not None and (v < -1 or v > 1):
            raise ValueError("Delta must be between -1 and 1")
        return v

    @field_validator("gamma", "vega")
    def validate_positive_greeks(cls, v: Decimal | None) -> Decimal | None:
        """Validate gamma and vega are non-negative."""
        if v is not None and v < 0:
            raise ValueError("Gamma and Vega must be non-negative")
        return v
