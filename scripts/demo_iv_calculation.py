#!/usr/bin/env python3
"""Demonstrate implied volatility calculation for oil futures options."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.analytics import BlackScholes, ImpliedVolatilitySolver
from src.storage import DatabaseOperations


def main():
    """Calculate implied volatility for hypothetical WTI options."""

    # Get latest WTI price from database
    with DatabaseOperations() as db_ops:
        prices_df = db_ops.get_futures_prices(commodity_id="WTI", start_date=None, end_date=None)

        if prices_df.empty:
            print("No WTI prices found in database")
            return

        # Get the latest price
        latest_price = float(prices_df.iloc[0]["close_price"])
        latest_date = prices_df.iloc[0]["price_date"]

        print("\n📊 WTI Crude Oil Analysis")
        print(f"Latest Price: ${latest_price:.2f}")
        print(f"Date: {latest_date}")
        print("\n" + "=" * 60 + "\n")

    # Create hypothetical options
    bs = BlackScholes()
    iv_solver = ImpliedVolatilitySolver()

    # Risk-free rate (approximate US Treasury 3-month rate)
    r = 0.05

    # Time to expiration (30 days)
    T = 30 / 365

    # Calculate option prices for different strikes
    strikes = [
        latest_price * 0.9,  # 10% OTM put
        latest_price * 0.95,  # 5% OTM put
        latest_price,  # ATM
        latest_price * 1.05,  # 5% OTM call
        latest_price * 1.1,  # 10% OTM call
    ]

    print("Option Pricing Analysis (Assuming 30% Volatility):")
    print("-" * 60)
    print(f"{'Strike':>8} {'Type':>6} {'Price':>8} {'Delta':>7} {'Gamma':>7} {'Vega':>7}")
    print("-" * 60)

    true_vol = 0.30  # 30% assumed volatility

    for strike in strikes:
        # Call option
        call_price = bs.call_price(latest_price, strike, r, T, true_vol)
        call_delta = bs.delta_call(latest_price, strike, r, T, true_vol)
        gamma = bs.gamma(latest_price, strike, r, T, true_vol)
        vega = bs.vega(latest_price, strike, r, T, true_vol)

        print(
            f"{strike:8.2f} {'CALL':>6} {call_price:8.3f} {call_delta:7.3f} "
            f"{gamma:7.4f} {vega:7.3f}"
        )

        # Put option
        put_price = bs.put_price(latest_price, strike, r, T, true_vol)
        put_delta = bs.delta_put(latest_price, strike, r, T, true_vol)

        print(
            f"{strike:8.2f} {'PUT':>6} {put_price:8.3f} {put_delta:7.3f} {gamma:7.4f} {vega:7.3f}"
        )

    print("\n" + "=" * 60 + "\n")

    # Demonstrate implied volatility calculation
    print("Implied Volatility Calculation Examples:")
    print("-" * 60)

    # ATM call with market price
    market_call_price = 2.5  # Hypothetical market price

    print("\nATM Call Option:")
    print(f"Strike: ${latest_price:.2f}")
    print(f"Market Price: ${market_call_price:.2f}")

    calculated_iv = iv_solver.calculate_iv(
        option_price=market_call_price, S=latest_price, K=latest_price, r=r, T=T, option_type="CALL"
    )

    if calculated_iv:
        print(f"Implied Volatility: {calculated_iv:.1%}")

        # Verify by calculating price with found IV
        verify_price = bs.call_price(latest_price, latest_price, r, T, calculated_iv)
        print(f"Verification Price: ${verify_price:.2f}")
    else:
        print("Could not calculate implied volatility")

    # OTM put with market price
    otm_strike = latest_price * 0.95
    market_put_price = 1.2  # Hypothetical market price

    print("\n5% OTM Put Option:")
    print(f"Strike: ${otm_strike:.2f}")
    print(f"Market Price: ${market_put_price:.2f}")

    calculated_iv = iv_solver.calculate_iv(
        option_price=market_put_price, S=latest_price, K=otm_strike, r=r, T=T, option_type="PUT"
    )

    if calculated_iv:
        print(f"Implied Volatility: {calculated_iv:.1%}")

        # Verify
        verify_price = bs.put_price(latest_price, otm_strike, r, T, calculated_iv)
        print(f"Verification Price: ${verify_price:.2f}")


if __name__ == "__main__":
    main()
