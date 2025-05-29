"""Options analytics API endpoints."""

from datetime import date
from decimal import Decimal
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from structlog import get_logger

from src.analytics.options_pricing.black_scholes import BlackScholes
from src.analytics.options_pricing.implied_vol import ImpliedVolatilitySolver


class OptionType(str, Enum):
    """Option type enum."""

    CALL = "CALL"
    PUT = "PUT"


from src.api.models import (
    GreeksRequest,
    GreeksResponse,
    ImpliedVolatilityRequest,
    ImpliedVolatilityResponse,
    OptionPricingRequest,
    OptionPricingResponse,
    VolatilitySurface,
    VolatilitySurfacePoint,
)
from src.storage.operations import DatabaseOperations

logger = get_logger()
router = APIRouter(prefix="/api/options", tags=["options"])


def get_db() -> DatabaseOperations:
    """Dependency to get database connection."""
    db = DatabaseOperations()
    try:
        yield db
    finally:
        db.close()


@router.post("/calculate", response_model=OptionPricingResponse)
async def calculate_option_price(request: OptionPricingRequest):
    """Calculate option price using Black-Scholes model."""
    try:
        calculator = BlackScholes()

        # Convert days to years
        time_to_expiry = request.days_to_expiry / 365.0

        # Calculate option price
        if request.option_type == "CALL":
            price = calculator.call_price(
                S=float(request.underlying_price),
                K=float(request.strike_price),
                r=float(request.risk_free_rate),
                T=time_to_expiry,
                sigma=float(request.volatility),
            )
            option_type = OptionType.CALL
        else:
            price = calculator.put_price(
                S=float(request.underlying_price),
                K=float(request.strike_price),
                r=float(request.risk_free_rate),
                T=time_to_expiry,
                sigma=float(request.volatility),
            )
            option_type = OptionType.PUT

        # Calculate intrinsic value
        if option_type == OptionType.CALL:
            intrinsic_value = max(0, float(request.underlying_price) - float(request.strike_price))
        else:
            intrinsic_value = max(0, float(request.strike_price) - float(request.underlying_price))

        # Time value
        time_value = price - intrinsic_value

        # Determine moneyness
        moneyness_ratio = float(request.underlying_price) / float(request.strike_price)
        if abs(moneyness_ratio - 1.0) < 0.02:
            moneyness = "ATM"
        elif (option_type == OptionType.CALL and moneyness_ratio > 1.02) or (
            option_type == OptionType.PUT and moneyness_ratio < 0.98
        ):
            moneyness = "ITM"
        else:
            moneyness = "OTM"

        return OptionPricingResponse(
            option_price=Decimal(str(round(price, 4))),
            intrinsic_value=Decimal(str(round(intrinsic_value, 4))),
            time_value=Decimal(str(round(time_value, 4))),
            moneyness=moneyness,
        )

    except Exception as e:
        logger.error("Failed to calculate option price", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to calculate option price")


@router.post("/greeks", response_model=GreeksResponse)
async def calculate_greeks(request: GreeksRequest):
    """Calculate all Greeks for an option."""
    try:
        calculator = BlackScholes()

        # Convert days to years
        time_to_expiry = request.days_to_expiry / 365.0

        # Calculate Greeks and option price
        S = float(request.underlying_price)
        K = float(request.strike_price)
        r = float(request.risk_free_rate)
        sigma = float(request.volatility)

        if request.option_type == "CALL":
            delta = calculator.delta_call(S, K, r, time_to_expiry, sigma)
            price = calculator.call_price(S, K, r, time_to_expiry, sigma)
        else:
            delta = calculator.delta_put(S, K, r, time_to_expiry, sigma)
            price = calculator.put_price(S, K, r, time_to_expiry, sigma)

        # Calculate other Greeks (same for calls and puts)
        gamma = calculator.gamma(S, K, r, time_to_expiry, sigma)
        theta = (
            calculator.theta_call(S, K, r, time_to_expiry, sigma)
            if request.option_type == "CALL"
            else calculator.theta_put(S, K, r, time_to_expiry, sigma)
        )
        vega = calculator.vega(S, K, r, time_to_expiry, sigma)
        rho = (
            calculator.rho_call(S, K, r, time_to_expiry, sigma)
            if request.option_type == "CALL"
            else calculator.rho_put(S, K, r, time_to_expiry, sigma)
        )

        return GreeksResponse(
            delta=Decimal(str(round(delta, 6))),
            gamma=Decimal(str(round(gamma, 6))),
            theta=Decimal(str(round(theta, 6))),
            vega=Decimal(str(round(vega, 6))),
            rho=Decimal(str(round(rho, 6))),
            option_price=Decimal(str(round(price, 4))),
        )

    except Exception as e:
        logger.error("Failed to calculate Greeks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to calculate Greeks")


@router.post("/implied-volatility", response_model=ImpliedVolatilityResponse)
async def calculate_implied_volatility(request: ImpliedVolatilityRequest):
    """Calculate implied volatility from option price."""
    try:
        solver = ImpliedVolatilitySolver()

        # Convert days to years
        time_to_expiry = request.days_to_expiry / 365.0

        # Calculate implied volatility
        option_type = request.option_type.lower()

        iv, iterations = solver.calculate_iv(
            option_price=float(request.option_price),
            S=float(request.underlying_price),
            K=float(request.strike_price),
            r=float(request.risk_free_rate),
            T=time_to_expiry,
            option_type=option_type,
        )

        if iv is None:
            raise HTTPException(
                status_code=400, detail="Failed to converge on implied volatility solution"
            )

        return ImpliedVolatilityResponse(
            implied_volatility=Decimal(str(round(iv, 6))),
            convergence_iterations=iterations,
            calculation_method="Newton-Raphson with bisection fallback",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to calculate implied volatility", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to calculate implied volatility")


@router.get("/volatility/surface/{commodity_id}", response_model=VolatilitySurface)
async def get_volatility_surface(
    commodity_id: str,
    calculation_date: date = None,
    db: DatabaseOperations = Depends(get_db),
):
    """Get implied volatility surface for a commodity."""
    try:
        if not calculation_date:
            calculation_date = date.today()

        # Get volatility surface data
        surface_df = db.get_implied_volatility_surface(commodity_id, calculation_date)

        if surface_df.empty:
            # Generate mock surface for demonstration
            # In production, this would come from actual options data
            logger.warning("No IV surface data found, generating mock data", commodity=commodity_id)

            # Get latest underlying price
            prices_df = db.get_futures_prices(commodity_id=commodity_id)
            if prices_df.empty:
                raise HTTPException(status_code=404, detail=f"No price data for {commodity_id}")

            underlying_price = float(prices_df.iloc[0]["close_price"])

            # Generate mock surface points
            surface_points = []
            strikes = [underlying_price * m for m in [0.8, 0.9, 1.0, 1.1, 1.2]]
            expiries = [30, 60, 90, 120]

            for strike in strikes:
                for expiry in expiries:
                    # Simple IV smile approximation
                    moneyness = strike / underlying_price
                    base_iv = 0.25  # 25% base volatility
                    smile_adjustment = 0.1 * (abs(moneyness - 1.0) ** 1.5)
                    iv = base_iv + smile_adjustment

                    for option_type in ["CALL", "PUT"]:
                        surface_points.append(
                            VolatilitySurfacePoint(
                                strike_price=Decimal(str(round(strike, 2))),
                                days_to_expiry=expiry,
                                implied_volatility=Decimal(str(round(iv, 4))),
                                option_type=option_type,
                            )
                        )

            return VolatilitySurface(
                commodity_id=commodity_id,
                underlying_price=Decimal(str(underlying_price)),
                calculation_date=calculation_date,
                surface_points=surface_points,
            )

        # Convert dataframe to response model
        surface_points = []
        underlying_price = surface_df.iloc[0]["underlying_price"]

        for _, row in surface_df.iterrows():
            days_to_expiry = (row["expiration_date"] - calculation_date).days
            surface_points.append(
                VolatilitySurfacePoint(
                    strike_price=Decimal(str(row["strike_price"])),
                    days_to_expiry=days_to_expiry,
                    implied_volatility=Decimal(str(row["implied_vol"])),
                    option_type=row["option_type"],
                )
            )

        return VolatilitySurface(
            commodity_id=commodity_id,
            underlying_price=Decimal(str(underlying_price)),
            calculation_date=calculation_date,
            surface_points=surface_points,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get volatility surface", commodity=commodity_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve volatility surface")
