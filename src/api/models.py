"""Pydantic models for API requests and responses."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# Authentication Models
class UserCreate(BaseModel):
    """User registration request."""

    email: str
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    """User login request."""

    email: str
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class User(BaseModel):
    """User response model."""

    user_id: str
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None


# Futures Models
class FuturesContract(BaseModel):
    """Futures contract details."""

    contract_id: str
    commodity_id: str
    symbol: str
    expiration_date: date
    is_active: bool
    created_at: datetime


class FuturesPrice(BaseModel):
    """Futures price data."""

    price_id: int
    contract_id: str
    commodity_id: str
    symbol: str
    price_date: date
    open_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    close_price: Decimal
    volume: int | None = None
    open_interest: int | None = None


class LatestPrice(BaseModel):
    """Latest futures price."""

    commodity_id: str
    symbol: str
    price: Decimal
    change: Decimal
    change_percent: Decimal
    volume: int | None = None
    timestamp: datetime


class PriceHistoryRequest(BaseModel):
    """Request for historical prices."""

    start_date: date | None = None
    end_date: date | None = None
    limit: int | None = Field(default=100, le=1000)


# Options Models
class OptionPricingRequest(BaseModel):
    """Request to calculate option price."""

    commodity_id: str
    underlying_price: Decimal = Field(gt=0)
    strike_price: Decimal = Field(gt=0)
    days_to_expiry: int = Field(gt=0)
    risk_free_rate: Decimal = Field(default=0.05, ge=0, le=1)
    volatility: Decimal = Field(gt=0, le=5)
    option_type: str = Field(pattern="^(CALL|PUT)$")


class OptionPricingResponse(BaseModel):
    """Option pricing calculation result."""

    option_price: Decimal
    intrinsic_value: Decimal
    time_value: Decimal
    moneyness: str  # ITM, ATM, OTM


class GreeksRequest(BaseModel):
    """Request to calculate Greeks."""

    commodity_id: str
    underlying_price: Decimal = Field(gt=0)
    strike_price: Decimal = Field(gt=0)
    days_to_expiry: int = Field(gt=0)
    risk_free_rate: Decimal = Field(default=0.05, ge=0, le=1)
    volatility: Decimal = Field(gt=0, le=5)
    option_type: str = Field(pattern="^(CALL|PUT)$")


class GreeksResponse(BaseModel):
    """Greeks calculation result."""

    delta: Decimal
    gamma: Decimal
    theta: Decimal
    vega: Decimal
    rho: Decimal
    option_price: Decimal


class ImpliedVolatilityRequest(BaseModel):
    """Request to calculate implied volatility."""

    commodity_id: str
    option_price: Decimal = Field(gt=0)
    underlying_price: Decimal = Field(gt=0)
    strike_price: Decimal = Field(gt=0)
    days_to_expiry: int = Field(gt=0)
    risk_free_rate: Decimal = Field(default=0.05, ge=0, le=1)
    option_type: str = Field(pattern="^(CALL|PUT)$")


class ImpliedVolatilityResponse(BaseModel):
    """Implied volatility calculation result."""

    implied_volatility: Decimal
    convergence_iterations: int
    calculation_method: str


class VolatilitySurfacePoint(BaseModel):
    """Single point on volatility surface."""

    strike_price: Decimal
    days_to_expiry: int
    implied_volatility: Decimal
    option_type: str


class VolatilitySurface(BaseModel):
    """Volatility surface data."""

    commodity_id: str
    underlying_price: Decimal
    calculation_date: date
    surface_points: list[VolatilitySurfacePoint]


# Analytics Models
class CommodityMetrics(BaseModel):
    """Key metrics for a commodity."""

    commodity_id: str
    name: str
    latest_price: Decimal
    daily_change: Decimal
    daily_change_percent: Decimal
    weekly_high: Decimal
    weekly_low: Decimal
    monthly_volatility: Decimal
    volume: int
    open_interest: int


class SystemStatus(BaseModel):
    """System health and status."""

    api_status: str
    database_status: str
    last_data_update: datetime
    active_commodities: list[str]
    total_price_records: int
