from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CommodityValidator(BaseModel):
    commodity_id: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    symbol: str = Field(..., max_length=255)
    exchange: str = Field(..., max_length=255)
    tick_size: Decimal | None = Field(default=None)
    contract_size: Decimal | None = Field(default=None)
    units: str | None = Field(default=None, max_length=255)
    created_at: datetime | None = Field(default=None)

    class Config:
        from_attributes = True


class FuturesContractValidator(BaseModel):
    contract_id: str = Field(..., max_length=255)
    commodity_id: str = Field(..., max_length=255)
    symbol: str = Field(..., max_length=255)
    expiration_date: date
    first_trade_date: date | None = Field(default=None)
    last_trade_date: date | None = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)

    class Config:
        from_attributes = True


class FuturesPriceValidator(BaseModel):
    price_id: int | None = Field(default=None)  # Auto-incrementing, usually not provided
    contract_id: str = Field(..., max_length=255)
    price_date: date
    price_time: datetime | None = Field(default=None)
    open_price: Decimal | None = Field(default=None)
    high_price: Decimal | None = Field(default=None)
    low_price: Decimal | None = Field(default=None)
    close_price: Decimal
    settlement_price: Decimal | None = Field(default=None)
    volume: int | None = Field(default=None)
    open_interest: int | None = Field(default=None)
    created_at: datetime | None = Field(default=None)

    class Config:
        from_attributes = True


# Example of how to use these validators:
# try:
#     contract_data = { ... }
#     validated_contract = FuturesContractValidator(**contract_data)
#     # Proceed with validated_contract.model_dump()
# except ValidationError as e:
#     print(f"Validation Error: {e.json()}")
