"""Implied volatility calculation using Newton-Raphson method."""

import numpy as np
from structlog import get_logger

from .black_scholes import BlackScholes

logger = get_logger()


class ImpliedVolatilitySolver:
    """Calculate implied volatility from option prices."""

    def __init__(
        self, max_iterations: int = 100, tolerance: float = 1e-6, initial_guess: float = 0.2
    ) -> None:
        """Initialize the implied volatility solver.

        Args:
            max_iterations: Maximum number of iterations for convergence
            tolerance: Convergence tolerance
            initial_guess: Initial volatility guess
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.initial_guess = initial_guess
        self.bs = BlackScholes()

    def calculate_iv_newton_raphson(
        self, option_price: float, S: float, K: float, r: float, T: float, option_type: str = "CALL"
    ) -> float | None:
        """Calculate implied volatility using Newton-Raphson method.

        Args:
            option_price: Market price of the option
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            option_type: "CALL" or "PUT"

        Returns:
            Implied volatility, or None if no solution found
        """
        if T <= 0:
            logger.warning("Cannot calculate IV for expired option")
            return None

        # Check for valid inputs
        if option_price <= 0:
            logger.warning("Option price must be positive", price=option_price)
            return None

        # Check intrinsic value bounds
        if option_type == "CALL":
            intrinsic = max(0, S - K * np.exp(-r * T))
            if option_price < intrinsic:
                logger.warning(
                    "Call price below intrinsic value", price=option_price, intrinsic=intrinsic
                )
                return None
        else:
            intrinsic = max(0, K * np.exp(-r * T) - S)
            if option_price < intrinsic:
                logger.warning(
                    "Put price below intrinsic value", price=option_price, intrinsic=intrinsic
                )
                return None

        # Newton-Raphson iteration
        sigma = self.initial_guess

        for i in range(self.max_iterations):
            # Calculate option price and vega
            if option_type == "CALL":
                price = self.bs.call_price(S, K, r, T, sigma)
            else:
                price = self.bs.put_price(S, K, r, T, sigma)

            vega = self.bs.vega(S, K, r, T, sigma)

            # Check convergence
            price_diff = price - option_price
            if abs(price_diff) < self.tolerance:
                logger.debug("IV converged", iterations=i + 1, iv=sigma, error=price_diff)
                return sigma

            # Avoid division by zero
            if vega < 1e-10:
                logger.warning("Vega too small, trying bisection method")
                return self.calculate_iv_bisection(option_price, S, K, r, T, option_type)

            # Newton-Raphson update
            sigma = sigma - price_diff / vega

            # Ensure sigma stays positive
            if sigma <= 0:
                sigma = 0.001
            elif sigma > 5:  # Cap at 500% volatility
                sigma = 5

        logger.warning("Newton-Raphson did not converge", iterations=self.max_iterations)

        # Fall back to bisection method
        return self.calculate_iv_bisection(option_price, S, K, r, T, option_type)

    def calculate_iv_bisection(
        self, option_price: float, S: float, K: float, r: float, T: float, option_type: str = "CALL"
    ) -> float | None:
        """Calculate implied volatility using bisection method.

        Args:
            option_price: Market price of the option
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            option_type: "CALL" or "PUT"

        Returns:
            Implied volatility, or None if no solution found
        """
        # Set bounds for bisection
        sigma_low = 0.001
        sigma_high = 5.0

        # Calculate prices at bounds
        if option_type == "CALL":
            price_low = self.bs.call_price(S, K, r, T, sigma_low)
            price_high = self.bs.call_price(S, K, r, T, sigma_high)
        else:
            price_low = self.bs.put_price(S, K, r, T, sigma_low)
            price_high = self.bs.put_price(S, K, r, T, sigma_high)

        # Check if solution exists within bounds
        if option_price < price_low or option_price > price_high:
            logger.warning(
                "Option price outside valid bounds",
                price=option_price,
                bounds=(price_low, price_high),
            )
            return None

        # Bisection iteration
        for i in range(self.max_iterations):
            sigma_mid = (sigma_low + sigma_high) / 2

            if option_type == "CALL":
                price_mid = self.bs.call_price(S, K, r, T, sigma_mid)
            else:
                price_mid = self.bs.put_price(S, K, r, T, sigma_mid)

            # Check convergence
            if abs(price_mid - option_price) < self.tolerance:
                logger.debug("IV converged (bisection)", iterations=i + 1, iv=sigma_mid)
                return sigma_mid

            # Update bounds
            if price_mid < option_price:
                sigma_low = sigma_mid
            else:
                sigma_high = sigma_mid

        logger.error("Bisection method did not converge")
        return None

    def calculate_iv(
        self, option_price: float, S: float, K: float, r: float, T: float, option_type: str = "CALL"
    ) -> float | None:
        """Calculate implied volatility (main interface).

        Args:
            option_price: Market price of the option
            S: Current price of underlying
            K: Strike price
            r: Risk-free rate
            T: Time to maturity (in years)
            option_type: "CALL" or "PUT"

        Returns:
            Implied volatility, or None if no solution found
        """
        try:
            # Try Newton-Raphson first (faster)
            iv = self.calculate_iv_newton_raphson(option_price, S, K, r, T, option_type)

            if iv is not None:
                return iv

            # Fall back to bisection if Newton-Raphson fails
            logger.info("Falling back to bisection method")
            return self.calculate_iv_bisection(option_price, S, K, r, T, option_type)

        except Exception as e:
            logger.error(
                "Failed to calculate implied volatility",
                error=str(e),
                option_price=option_price,
                S=S,
                K=K,
                T=T,
            )
            return None
