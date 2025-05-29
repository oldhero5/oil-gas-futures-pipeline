"""System status and health check endpoints."""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from structlog import get_logger

from src.api.models import CommodityMetrics, SystemStatus
from src.storage.operations import DatabaseOperations

logger = get_logger()
router = APIRouter(prefix="/api/system", tags=["system"])


def get_db() -> DatabaseOperations:
    """Dependency to get database connection."""
    db = DatabaseOperations()
    try:
        yield db
    finally:
        db.close()


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: DatabaseOperations = Depends(get_db)):
    """Get overall system status and health."""
    try:
        # Check database health
        try:
            db.conn.execute("SELECT 1").fetchone()
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Get last data update
        query = """
            SELECT MAX(created_at) as last_update
            FROM market_data_log
            WHERE status = 'SUCCESS'
        """
        last_update_result = db.conn.execute(query).fetchone()
        last_update = (
            last_update_result[0]
            if last_update_result and last_update_result[0]
            else datetime.now(UTC)
        )

        # Get active commodities
        commodities_query = """
            SELECT DISTINCT commodity_id
            FROM futures_contracts
            WHERE is_active = TRUE
        """
        commodities = [row[0] for row in db.conn.execute(commodities_query).fetchall()]

        # Get total price records
        count_query = "SELECT COUNT(*) FROM futures_prices"
        total_records = db.conn.execute(count_query).fetchone()[0]

        return SystemStatus(
            api_status="healthy",
            database_status=db_status,
            last_data_update=last_update,
            active_commodities=commodities,
            total_price_records=total_records,
        )

    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        return SystemStatus(
            api_status="degraded",
            database_status="error",
            last_data_update=datetime.now(UTC),
            active_commodities=[],
            total_price_records=0,
        )


@router.get("/metrics", response_model=list[CommodityMetrics])
async def get_commodity_metrics(db: DatabaseOperations = Depends(get_db)):
    """Get key metrics for all commodities."""
    try:
        metrics = []

        # Get commodities
        commodities_query = "SELECT commodity_id, name FROM commodities"
        commodities = db.conn.execute(commodities_query).fetchall()

        for commodity_id, name in commodities:
            try:
                # Get latest price and volume
                latest_query = """
                    SELECT fp.close_price, fp.volume, fp.open_interest, fp.price_date
                    FROM futures_prices fp
                    JOIN futures_contracts fc ON fp.contract_id = fc.contract_id
                    WHERE fc.commodity_id = ?
                    ORDER BY fp.price_date DESC
                    LIMIT 2
                """
                latest_results = db.conn.execute(latest_query, [commodity_id]).fetchall()

                if len(latest_results) >= 1:
                    latest_price = float(latest_results[0][0])
                    volume = latest_results[0][1] or 0
                    open_interest = latest_results[0][2] or 0

                    # Calculate daily change
                    if len(latest_results) == 2:
                        previous_price = float(latest_results[1][0])
                        daily_change = latest_price - previous_price
                        daily_change_percent = (daily_change / previous_price) * 100
                    else:
                        daily_change = 0
                        daily_change_percent = 0

                    # Get weekly high/low
                    week_query = """
                        SELECT MAX(fp.high_price) as high, MIN(fp.low_price) as low
                        FROM futures_prices fp
                        JOIN futures_contracts fc ON fp.contract_id = fc.contract_id
                        WHERE fc.commodity_id = ?
                        AND fp.price_date >= CURRENT_DATE - INTERVAL 7 DAY
                    """
                    week_result = db.conn.execute(week_query, [commodity_id]).fetchone()
                    weekly_high = float(week_result[0]) if week_result[0] else latest_price
                    weekly_low = float(week_result[1]) if week_result[1] else latest_price

                    # Calculate monthly volatility (simplified)
                    vol_query = """
                        SELECT fp.close_price
                        FROM futures_prices fp
                        JOIN futures_contracts fc ON fp.contract_id = fc.contract_id
                        WHERE fc.commodity_id = ?
                        AND fp.price_date >= CURRENT_DATE - INTERVAL 30 DAY
                        ORDER BY fp.price_date
                    """
                    prices = [
                        float(row[0])
                        for row in db.conn.execute(vol_query, [commodity_id]).fetchall()
                    ]

                    if len(prices) > 1:
                        # Calculate simple historical volatility
                        returns = [(prices[i] / prices[i - 1] - 1) for i in range(1, len(prices))]
                        avg_return = sum(returns) / len(returns)
                        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                        monthly_volatility = (variance**0.5) * (252**0.5)  # Annualized
                    else:
                        monthly_volatility = 0.25  # Default 25%

                    metrics.append(
                        CommodityMetrics(
                            commodity_id=commodity_id,
                            name=name,
                            latest_price=Decimal(str(round(latest_price, 4))),
                            daily_change=Decimal(str(round(daily_change, 4))),
                            daily_change_percent=Decimal(str(round(daily_change_percent, 2))),
                            weekly_high=Decimal(str(round(weekly_high, 4))),
                            weekly_low=Decimal(str(round(weekly_low, 4))),
                            monthly_volatility=Decimal(str(round(monthly_volatility, 4))),
                            volume=volume,
                            open_interest=open_interest,
                        )
                    )

            except Exception as e:
                logger.warning(
                    "Failed to get metrics for commodity", commodity=commodity_id, error=str(e)
                )
                continue

        return metrics

    except Exception as e:
        logger.error("Failed to get commodity metrics", error=str(e))
        return []
