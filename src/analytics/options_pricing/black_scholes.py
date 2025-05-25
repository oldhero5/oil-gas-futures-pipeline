"""Black-Scholes option pricing model implementation."""

import numpy as np
from scipy import stats
from structlog import get_logger

logger = get_logger()


class BlackScholes:
    """Black-Scholes option pricing model for European options."""

    @staticmethod
    def calculate_d1_d2(
        S: float, K: float, r: float, T: float, sigma: float
    ) -> tuple[float, float]:
        """Calculate d1 and d2 parameters for Black-Scholes.

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Tuple of (d1, d2)
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2

    @staticmethod
    def call_price(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate European call option price.

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Call option price
        """
        if T <= 0:
            return max(0, S - K)

        d1, d2 = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)

        return S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)

    @staticmethod
    def put_price(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate European put option price.

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Put option price
        """
        if T <= 0:
            return max(0, K - S)

        d1, d2 = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)

        return K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)

    @staticmethod
    def vega(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate vega (derivative with respect to volatility).

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Vega
        """
        if T <= 0:
            return 0.0

        d1, _ = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)
        return S * stats.norm.pdf(d1) * np.sqrt(T)

    @staticmethod
    def delta_call(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate delta for a call option.

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Call delta
        """
        if T <= 0:
            return 1.0 if S > K else 0.0

        d1, _ = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)
        return stats.norm.cdf(d1)

    @staticmethod
    def delta_put(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate delta for a put option.

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Put delta
        """
        if T <= 0:
            return -1.0 if S < K else 0.0

        d1, _ = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)
        return stats.norm.cdf(d1) - 1

    @staticmethod
    def gamma(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate gamma (second derivative with respect to underlying price).

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Gamma
        """
        if T <= 0:
            return 0.0

        d1, _ = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)
        return stats.norm.pdf(d1) / (S * sigma * np.sqrt(T))

    @staticmethod
    def theta_call(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate theta for a call option (time decay).

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Call theta (per day)
        """
        if T <= 0:
            return 0.0

        d1, d2 = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)

        theta = -S * stats.norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(
            -r * T
        ) * stats.norm.cdf(d2)

        # Convert to per-day theta
        return theta / 365

    @staticmethod
    def theta_put(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate theta for a put option (time decay).

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Put theta (per day)
        """
        if T <= 0:
            return 0.0

        d1, d2 = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)

        theta = -S * stats.norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + r * K * np.exp(
            -r * T
        ) * stats.norm.cdf(-d2)

        # Convert to per-day theta
        return theta / 365

    @staticmethod
    def rho_call(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate rho for a call option (sensitivity to interest rate).

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Call rho
        """
        if T <= 0:
            return 0.0

        _, d2 = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)
        return K * T * np.exp(-r * T) * stats.norm.cdf(d2)

    @staticmethod
    def rho_put(S: float, K: float, r: float, T: float, sigma: float) -> float:
        """Calculate rho for a put option (sensitivity to interest rate).

        Args:
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            sigma: Volatility

        Returns:
            Put rho
        """
        if T <= 0:
            return 0.0

        _, d2 = BlackScholes.calculate_d1_d2(S, K, r, T, sigma)
        return -K * T * np.exp(-r * T) * stats.norm.cdf(-d2)
