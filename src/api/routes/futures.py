"""Futures data API endpoints."""

from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from structlog import get_logger

from src.api.models import (
    FuturesContract,
    FuturesPrice,
    LatestPrice,
    PriceHistoryRequest,
)
from src.storage.operations import DatabaseOperations

logger = get_logger()
router = APIRouter(prefix="/api/futures", tags=["futures"])


def get_db() -> DatabaseOperations:
    """Dependency to get database connection."""
    db = DatabaseOperations()
    try:
        yield db
    finally:
        db.close()


@router.get("/contracts", response_model=list[FuturesContract])
async def get_futures_contracts(
    commodity_id: str | None = Query(None, description="Filter by commodity"),
    active_only: bool = Query(True, description="Only return active contracts"),
    db: DatabaseOperations = Depends(get_db),
):
    """Get list of futures contracts."""
    try:
        contracts_df = db.get_active_contracts(commodity_id)

        if active_only:
            contracts_df = contracts_df[contracts_df["is_active"]]

        contracts = []
        for _, row in contracts_df.iterrows():
            contracts.append(
                FuturesContract(
                    contract_id=row["contract_id"],
                    commodity_id=row["commodity_id"],
                    symbol=row["symbol"],
                    expiration_date=row["expiration_date"],
                    is_active=row["is_active"],
                    created_at=row["created_at"],
                )
            )

        return contracts

    except Exception as e:
        logger.error("Failed to get futures contracts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve contracts")


@router.get("/prices", response_model=list[FuturesPrice])
async def get_futures_prices(
    commodity_id: str | None = Query(None, description="Filter by commodity"),
    start_date: date | None = Query(None, description="Start date"),
    end_date: date | None = Query(None, description="End date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: DatabaseOperations = Depends(get_db),
):
    """Get futures price data with optional filters."""
    try:
        prices_df = db.get_futures_prices(
            commodity_id=commodity_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Apply limit
        prices_df = prices_df.head(limit)

        prices = []
        for _, row in prices_df.iterrows():
            prices.append(
                FuturesPrice(
                    price_id=row["price_id"],
                    contract_id=row["contract_id"],
                    commodity_id=row["commodity_id"],
                    symbol=row["symbol"],
                    price_date=row["price_date"],
                    open_price=Decimal(str(row["open_price"])) if row["open_price"] else None,
                    high_price=Decimal(str(row["high_price"])) if row["high_price"] else None,
                    low_price=Decimal(str(row["low_price"])) if row["low_price"] else None,
                    close_price=Decimal(str(row["close_price"])),
                    volume=row["volume"],
                    open_interest=row["open_interest"],
                )
            )

        return prices

    except Exception as e:
        logger.error("Failed to get futures prices", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve prices")


@router.get("/prices/{commodity_id}/latest", response_model=LatestPrice)
async def get_latest_price(
    commodity_id: str,
    db: DatabaseOperations = Depends(get_db),
):
    """Get the latest price for a specific commodity."""
    try:
        # Get latest price
        prices_df = db.get_futures_prices(
            commodity_id=commodity_id,
            start_date=date.today() - timedelta(days=7),  # Last week
        )

        if prices_df.empty:
            raise HTTPException(status_code=404, detail=f"No prices found for {commodity_id}")

        latest = prices_df.iloc[0]

        # Calculate daily change
        if len(prices_df) > 1:
            previous = prices_df.iloc[1]
            change = Decimal(str(latest["close_price"])) - Decimal(str(previous["close_price"]))
            change_percent = (change / Decimal(str(previous["close_price"]))) * 100
        else:
            change = Decimal("0")
            change_percent = Decimal("0")

        return LatestPrice(
            commodity_id=commodity_id,
            symbol=latest["symbol"],
            price=Decimal(str(latest["close_price"])),
            change=change,
            change_percent=change_percent,
            volume=latest["volume"],
            timestamp=datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get latest price", commodity=commodity_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve latest price")


@router.post("/prices/{commodity_id}/historical", response_model=list[FuturesPrice])
async def get_historical_prices(
    commodity_id: str,
    request: PriceHistoryRequest,
    db: DatabaseOperations = Depends(get_db),
):
    """Get historical price data for a specific commodity."""
    try:
        # Default date range if not provided
        if not request.end_date:
            request.end_date = date.today()
        if not request.start_date:
            request.start_date = request.end_date - timedelta(days=30)

        prices_df = db.get_futures_prices(
            commodity_id=commodity_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        if request.limit:
            prices_df = prices_df.head(request.limit)

        prices = []
        for _, row in prices_df.iterrows():
            prices.append(
                FuturesPrice(
                    price_id=row["price_id"],
                    contract_id=row["contract_id"],
                    commodity_id=row["commodity_id"],
                    symbol=row["symbol"],
                    price_date=row["price_date"],
                    open_price=Decimal(str(row["open_price"])) if row["open_price"] else None,
                    high_price=Decimal(str(row["high_price"])) if row["high_price"] else None,
                    low_price=Decimal(str(row["low_price"])) if row["low_price"] else None,
                    close_price=Decimal(str(row["close_price"])),
                    volume=row["volume"],
                    open_interest=row["open_interest"],
                )
            )

        return prices

    except Exception as e:
        logger.error("Failed to get historical prices", commodity=commodity_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve historical prices")
