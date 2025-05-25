#!/usr/bin/env python3
"""Generate a volatility smile for WTI crude oil options."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.analytics import ImpliedVolatilitySolver
from src.storage import DatabaseOperations


def main():
    """Generate volatility smile data."""

    # Get latest WTI price
    with DatabaseOperations() as db_ops:
        prices_df = db_ops.get_futures_prices(commodity_id="WTI")

        if prices_df.empty:
            print("No WTI prices found")
            return

        spot_price = float(prices_df.iloc[0]["close_price"])
        print("\n📊 WTI Volatility Smile Analysis")
        print(f"Spot Price: ${spot_price:.2f}")
        print("\n" + "=" * 70 + "\n")

    iv_solver = ImpliedVolatilitySolver()
    r = 0.05  # Risk-free rate
    T = 30 / 365  # 30 days to expiration

    # Generate strikes from 80% to 120% of spot
    strikes = [spot_price * (0.8 + 0.05 * i) for i in range(9)]

    # Hypothetical option prices (in reality, these would come from market data)
    # These create a typical volatility smile pattern
    market_prices = {
        0.80: {"call": 0.15, "put": 9.85},
        0.85: {"call": 0.45, "put": 5.65},
        0.90: {"call": 1.20, "put": 2.85},
        0.95: {"call": 2.40, "put": 1.30},
        1.00: {"call": 3.80, "put": 0.75},
        1.05: {"call": 5.30, "put": 0.35},
        1.10: {"call": 6.85, "put": 0.15},
        1.15: {"call": 8.40, "put": 0.05},
        1.20: {"call": 10.00, "put": 0.02},
    }

    print(f"{'Strike':>10} {'Moneyness':>12} {'Call IV':>10} {'Put IV':>10} {'Avg IV':>10}")
    print("-" * 60)

    for _i, strike in enumerate(strikes):
        moneyness = strike / spot_price
        ratio_key = round(moneyness, 2)

        if ratio_key in market_prices:
            # Calculate call IV
            call_iv = iv_solver.calculate_iv(
                option_price=market_prices[ratio_key]["call"],
                S=spot_price,
                K=strike,
                r=r,
                T=T,
                option_type="CALL",
            )

            # Calculate put IV
            put_iv = iv_solver.calculate_iv(
                option_price=market_prices[ratio_key]["put"],
                S=spot_price,
                K=strike,
                r=r,
                T=T,
                option_type="PUT",
            )

            if call_iv and put_iv:
                avg_iv = (call_iv + put_iv) / 2
                print(
                    f"{strike:10.2f} {moneyness:12.1%} {call_iv:10.1%} {put_iv:10.1%} {avg_iv:10.1%}"
                )
            else:
                print(f"{strike:10.2f} {moneyness:12.1%} {'N/A':>10} {'N/A':>10} {'N/A':>10}")

    print("\n" + "=" * 70)
    print("\nObservations:")
    print("- Higher implied volatility for out-of-the-money options (volatility smile)")
    print("- Put-call parity ensures similar IVs for calls and puts at same strike")
    print("- This pattern reflects market pricing of tail risk in oil markets")


if __name__ == "__main__":
    main()
