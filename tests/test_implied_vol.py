"""Tests for implied volatility solver."""

from src.analytics.options_pricing.black_scholes import BlackScholes
from src.analytics.options_pricing.implied_vol import ImpliedVolatilitySolver


class TestImpliedVolatility:
    """Test implied volatility calculations."""

    def test_iv_recovery(self):
        """Test that we can recover the volatility used to price an option."""
        bs = BlackScholes()
        iv_solver = ImpliedVolatilitySolver()

        # Known parameters
        S = 100
        K = 100
        r = 0.05
        T = 0.25
        true_sigma = 0.25

        # Calculate option price with known volatility
        call_price = bs.call_price(S, K, r, T, true_sigma)

        # Recover implied volatility
        calculated_iv = iv_solver.calculate_iv(
            option_price=call_price, S=S, K=K, r=r, T=T, option_type="CALL"
        )

        # Should recover the original volatility within tolerance
        assert calculated_iv is not None
        assert abs(calculated_iv - true_sigma) < 0.001

    def test_iv_put_option(self):
        """Test implied volatility for put options."""
        bs = BlackScholes()
        iv_solver = ImpliedVolatilitySolver()

        S = 90
        K = 100
        r = 0.05
        T = 0.5
        true_sigma = 0.3

        # Calculate put price
        put_price = bs.put_price(S, K, r, T, true_sigma)

        # Recover implied volatility
        calculated_iv = iv_solver.calculate_iv(
            option_price=put_price, S=S, K=K, r=r, T=T, option_type="PUT"
        )

        assert calculated_iv is not None
        assert abs(calculated_iv - true_sigma) < 0.001

    def test_iv_high_volatility(self):
        """Test IV solver with high volatility."""
        bs = BlackScholes()
        iv_solver = ImpliedVolatilitySolver()

        S = 100
        K = 100
        r = 0.05
        T = 1.0
        true_sigma = 0.8  # 80% volatility

        call_price = bs.call_price(S, K, r, T, true_sigma)

        calculated_iv = iv_solver.calculate_iv(
            option_price=call_price, S=S, K=K, r=r, T=T, option_type="CALL"
        )

        assert calculated_iv is not None
        assert abs(calculated_iv - true_sigma) < 0.001

    def test_iv_deep_itm_option(self):
        """Test IV for deep in-the-money option."""
        bs = BlackScholes()
        iv_solver = ImpliedVolatilitySolver()

        S = 150
        K = 100
        r = 0.05
        T = 0.25
        true_sigma = 0.2

        call_price = bs.call_price(S, K, r, T, true_sigma)

        calculated_iv = iv_solver.calculate_iv(
            option_price=call_price, S=S, K=K, r=r, T=T, option_type="CALL"
        )

        assert calculated_iv is not None
        # Deep ITM options may have less accurate IV
        assert abs(calculated_iv - true_sigma) < 0.01

    def test_iv_invalid_price(self):
        """Test IV solver with invalid option price."""
        iv_solver = ImpliedVolatilitySolver()

        S = 100
        K = 100
        r = 0.05
        T = 0.25

        # Price below intrinsic value
        invalid_price = 0.5  # Too low for ATM option

        calculated_iv = iv_solver.calculate_iv(
            option_price=invalid_price, S=S, K=K, r=r, T=T, option_type="CALL"
        )

        # Should return None for invalid price
        assert calculated_iv is None

    def test_iv_zero_time(self):
        """Test IV solver at expiration."""
        iv_solver = ImpliedVolatilitySolver()

        S = 105
        K = 100
        r = 0.05
        T = 0  # At expiration

        # At expiration, option price equals intrinsic value
        option_price = 5

        calculated_iv = iv_solver.calculate_iv(
            option_price=option_price, S=S, K=K, r=r, T=T, option_type="CALL"
        )

        # Cannot calculate IV at expiration
        assert calculated_iv is None

    def test_iv_bisection_fallback(self):
        """Test that bisection method works as fallback."""
        iv_solver = ImpliedVolatilitySolver(max_iterations=2)  # Force Newton-Raphson to fail
        bs = BlackScholes()

        S = 100
        K = 100
        r = 0.05
        T = 0.25
        true_sigma = 0.4

        call_price = bs.call_price(S, K, r, T, true_sigma)

        # Should fall back to bisection
        calculated_iv = iv_solver.calculate_iv(
            option_price=call_price, S=S, K=K, r=r, T=T, option_type="CALL"
        )

        assert calculated_iv is not None
        # Bisection might be less accurate but should be close
        assert abs(calculated_iv - true_sigma) < 0.01
