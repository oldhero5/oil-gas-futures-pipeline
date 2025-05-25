"""Tests for Black-Scholes option pricing model."""

from src.analytics.options_pricing.black_scholes import BlackScholes


class TestBlackScholes:
    """Test Black-Scholes pricing model."""

    def test_call_price_at_the_money(self):
        """Test call option pricing at the money."""
        bs = BlackScholes()

        # At-the-money call option
        S = 100  # Current price
        K = 100  # Strike price
        r = 0.05  # Risk-free rate
        T = 0.25  # 3 months
        sigma = 0.2  # 20% volatility

        call_price = bs.call_price(S, K, r, T, sigma)

        # Should be approximately 4.06 based on standard BS formula
        assert 3.5 < call_price < 4.5

    def test_put_price_at_the_money(self):
        """Test put option pricing at the money."""
        bs = BlackScholes()

        S = 100
        K = 100
        r = 0.05
        T = 0.25
        sigma = 0.2

        put_price = bs.put_price(S, K, r, T, sigma)

        # Should be approximately 2.82 based on standard BS formula
        assert 2.5 < put_price < 3.5

    def test_put_call_parity(self):
        """Test put-call parity relationship."""
        bs = BlackScholes()

        S = 100
        K = 110
        r = 0.05
        T = 1.0
        sigma = 0.3

        call_price = bs.call_price(S, K, r, T, sigma)
        put_price = bs.put_price(S, K, r, T, sigma)

        # Put-Call Parity: C - P = S - K * exp(-r*T)
        import numpy as np

        left_side = call_price - put_price
        right_side = S - K * np.exp(-r * T)

        assert abs(left_side - right_side) < 0.01

    def test_deep_in_the_money_call(self):
        """Test deep in-the-money call option."""
        bs = BlackScholes()

        S = 100
        K = 50  # Deep ITM
        r = 0.05
        T = 0.25
        sigma = 0.2

        call_price = bs.call_price(S, K, r, T, sigma)

        # Should be close to intrinsic value (S - K)
        intrinsic = S - K
        assert call_price > intrinsic
        assert call_price < intrinsic + 2  # Small time value

    def test_deep_out_of_money_put(self):
        """Test deep out-of-the-money put option."""
        bs = BlackScholes()

        S = 100
        K = 50  # Deep OTM for put
        r = 0.05
        T = 0.25
        sigma = 0.2

        put_price = bs.put_price(S, K, r, T, sigma)

        # Should be very close to zero
        assert put_price < 0.01

    def test_greeks_delta(self):
        """Test delta calculation."""
        bs = BlackScholes()

        S = 100
        K = 100
        r = 0.05
        T = 0.25
        sigma = 0.2

        call_delta = bs.delta_call(S, K, r, T, sigma)
        put_delta = bs.delta_put(S, K, r, T, sigma)

        # ATM call delta should be around 0.5
        assert 0.4 < call_delta < 0.6

        # Put delta should be negative
        assert -0.6 < put_delta < -0.4

        # Put-call delta relationship
        assert abs((call_delta - put_delta) - 1.0) < 0.01

    def test_greeks_gamma(self):
        """Test gamma calculation."""
        bs = BlackScholes()

        S = 100
        K = 100
        r = 0.05
        T = 0.25
        sigma = 0.2

        gamma = bs.gamma(S, K, r, T, sigma)

        # Gamma should be positive
        assert gamma > 0

        # ATM gamma is highest
        gamma_otm = bs.gamma(S, K * 1.2, r, T, sigma)
        assert gamma > gamma_otm

    def test_greeks_vega(self):
        """Test vega calculation."""
        bs = BlackScholes()

        S = 100
        K = 100
        r = 0.05
        T = 0.25
        sigma = 0.2

        vega = bs.vega(S, K, r, T, sigma)

        # Vega should be positive
        assert vega > 0

        # Vega decreases as time to expiration decreases
        vega_short = bs.vega(S, K, r, 0.08, sigma)  # 1 month
        assert vega > vega_short

    def test_expired_option(self):
        """Test option at expiration."""
        bs = BlackScholes()

        S = 100
        K = 95
        r = 0.05
        T = 0  # Expired
        sigma = 0.2

        call_price = bs.call_price(S, K, r, T, sigma)
        put_price = bs.put_price(S, K, r, T, sigma)

        # At expiration, only intrinsic value
        assert call_price == 5  # max(S - K, 0)
        assert put_price == 0  # max(K - S, 0)
