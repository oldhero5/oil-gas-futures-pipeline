"""Tests for options analytics API endpoints."""

from datetime import date
from unittest.mock import Mock, patch

import pandas as pd
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestOptionsEndpoints:
    """Test options analytics endpoint functionality."""

    @patch("src.analytics.options_pricing.black_scholes.BlackScholes")
    def test_calculate_option_price_call_success(self, mock_bs_class):
        """Test successful call option price calculation."""
        mock_bs = Mock()
        mock_bs_class.return_value = mock_bs
        mock_bs.call_price.return_value = 5.25

        request_data = {
            "commodity_id": "WTI",
            "underlying_price": "75.50",
            "strike_price": "75.00",
            "days_to_expiry": 30,
            "risk_free_rate": "0.05",
            "volatility": "0.25",
            "option_type": "CALL",
        }

        response = client.post("/api/options/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert float(data["option_price"]) == 5.25
        assert float(data["intrinsic_value"]) == 0.50  # max(75.50 - 75.00, 0)
        assert float(data["time_value"]) == 4.75  # 5.25 - 0.50
        assert data["moneyness"] == "ITM"

    @patch("src.analytics.options_pricing.black_scholes.BlackScholes")
    def test_calculate_option_price_put_success(self, mock_bs_class):
        """Test successful put option price calculation."""
        mock_bs = Mock()
        mock_bs_class.return_value = mock_bs
        mock_bs.put_price.return_value = 3.75

        request_data = {
            "commodity_id": "WTI",
            "underlying_price": "74.50",
            "strike_price": "75.00",
            "days_to_expiry": 30,
            "risk_free_rate": "0.05",
            "volatility": "0.25",
            "option_type": "PUT",
        }

        response = client.post("/api/options/calculate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert float(data["option_price"]) == 3.75
        assert float(data["intrinsic_value"]) == 0.50  # max(75.00 - 74.50, 0)
        assert float(data["time_value"]) == 3.25  # 3.75 - 0.50
        assert data["moneyness"] == "ITM"

    @patch("src.analytics.options_pricing.black_scholes.BlackScholes")
    def test_calculate_greeks_call_success(self, mock_bs_class):
        """Test successful Greeks calculation for call option."""
        mock_bs = Mock()
        mock_bs_class.return_value = mock_bs
        mock_bs.call_price.return_value = 5.25
        mock_bs.delta_call.return_value = 0.6234
        mock_bs.gamma.return_value = 0.0234
        mock_bs.theta_call.return_value = -0.0156
        mock_bs.vega.return_value = 0.1234
        mock_bs.rho_call.return_value = 0.0567

        request_data = {
            "commodity_id": "WTI",
            "underlying_price": "75.50",
            "strike_price": "75.00",
            "days_to_expiry": 30,
            "risk_free_rate": "0.05",
            "volatility": "0.25",
            "option_type": "CALL",
        }

        response = client.post("/api/options/greeks", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert float(data["delta"]) == 0.623400
        assert float(data["gamma"]) == 0.023400
        assert float(data["theta"]) == -0.015600
        assert float(data["vega"]) == 0.123400
        assert float(data["rho"]) == 0.056700
        assert float(data["option_price"]) == 5.25

    @patch("src.analytics.options_pricing.black_scholes.BlackScholes")
    def test_calculate_greeks_put_success(self, mock_bs_class):
        """Test successful Greeks calculation for put option."""
        mock_bs = Mock()
        mock_bs_class.return_value = mock_bs
        mock_bs.put_price.return_value = 3.75
        mock_bs.delta_put.return_value = -0.3766
        mock_bs.gamma.return_value = 0.0234
        mock_bs.theta_put.return_value = -0.0134
        mock_bs.vega.return_value = 0.1234
        mock_bs.rho_put.return_value = -0.0433

        request_data = {
            "commodity_id": "WTI",
            "underlying_price": "74.50",
            "strike_price": "75.00",
            "days_to_expiry": 30,
            "risk_free_rate": "0.05",
            "volatility": "0.25",
            "option_type": "PUT",
        }

        response = client.post("/api/options/greeks", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert float(data["delta"]) == -0.376600
        assert float(data["gamma"]) == 0.023400
        assert float(data["theta"]) == -0.013400
        assert float(data["vega"]) == 0.123400
        assert float(data["rho"]) == -0.043300
        assert float(data["option_price"]) == 3.75

    @patch("src.analytics.options_pricing.implied_vol.ImpliedVolatilitySolver")
    def test_calculate_implied_volatility_success(self, mock_iv_class):
        """Test successful implied volatility calculation."""
        mock_iv_solver = Mock()
        mock_iv_class.return_value = mock_iv_solver
        mock_iv_solver.calculate_iv.return_value = (0.2567, 5)  # IV and iterations

        request_data = {
            "commodity_id": "WTI",
            "option_price": "5.25",
            "underlying_price": "75.50",
            "strike_price": "75.00",
            "days_to_expiry": 30,
            "risk_free_rate": "0.05",
            "option_type": "CALL",
        }

        response = client.post("/api/options/implied-volatility", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert float(data["implied_volatility"]) == 0.256700
        assert data["convergence_iterations"] == 5
        assert data["calculation_method"] == "Newton-Raphson with bisection fallback"

    @patch("src.analytics.options_pricing.implied_vol.ImpliedVolatilitySolver")
    def test_calculate_implied_volatility_no_convergence(self, mock_iv_class):
        """Test implied volatility calculation that fails to converge."""
        mock_iv_solver = Mock()
        mock_iv_class.return_value = mock_iv_solver
        mock_iv_solver.calculate_iv.return_value = (None, 100)  # No convergence

        request_data = {
            "commodity_id": "WTI",
            "option_price": "50.00",  # Unrealistic price
            "underlying_price": "75.50",
            "strike_price": "75.00",
            "days_to_expiry": 1,
            "risk_free_rate": "0.05",
            "option_type": "CALL",
        }

        response = client.post("/api/options/implied-volatility", json=request_data)

        assert response.status_code == 400
        assert "Failed to converge" in response.json()["detail"]

    @patch("src.api.routes.options.DatabaseOperations")
    def test_get_volatility_surface_success(self, mock_db_ops):
        """Test successful volatility surface retrieval."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock DataFrame with volatility surface data
        mock_df = pd.DataFrame(
            {
                "strike_price": [70.0, 75.0, 80.0],
                "expiration_date": [date(2024, 2, 15), date(2024, 2, 15), date(2024, 2, 15)],
                "option_type": ["CALL", "CALL", "CALL"],
                "implied_vol": [0.28, 0.25, 0.27],
                "underlying_price": [75.0, 75.0, 75.0],
            }
        )
        mock_db.get_implied_volatility_surface.return_value = mock_df

        response = client.get("/api/options/volatility/surface/WTI")

        assert response.status_code == 200
        data = response.json()
        assert data["commodity_id"] == "WTI"
        assert float(data["underlying_price"]) == 75.0
        assert len(data["surface_points"]) == 3
        assert float(data["surface_points"][0]["strike_price"]) == 70.0
        assert float(data["surface_points"][0]["implied_volatility"]) == 0.28

    @patch("src.api.routes.options.DatabaseOperations")
    def test_get_volatility_surface_mock_data(self, mock_db_ops):
        """Test volatility surface with mock data generation."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock empty DataFrame to trigger mock data generation
        mock_surface_df = pd.DataFrame()
        mock_db.get_implied_volatility_surface.return_value = mock_surface_df

        # Mock prices DataFrame for underlying price
        mock_prices_df = pd.DataFrame({"close_price": [75.50]})
        mock_db.get_futures_prices.return_value = mock_prices_df

        response = client.get("/api/options/volatility/surface/WTI")

        assert response.status_code == 200
        data = response.json()
        assert data["commodity_id"] == "WTI"
        assert float(data["underlying_price"]) == 75.50
        # Should have mock surface points (5 strikes × 4 expiries × 2 option types = 40 points)
        assert len(data["surface_points"]) == 40

    @patch("src.api.routes.options.DatabaseOperations")
    def test_get_volatility_surface_no_data(self, mock_db_ops):
        """Test volatility surface when no price data available."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock empty DataFrames for both surface and prices
        mock_empty_df = pd.DataFrame()
        mock_db.get_implied_volatility_surface.return_value = mock_empty_df
        mock_db.get_futures_prices.return_value = mock_empty_df

        response = client.get("/api/options/volatility/surface/INVALID")

        assert response.status_code == 404
        assert "No price data" in response.json()["detail"]

    def test_option_pricing_validation(self):
        """Test request validation for option pricing endpoints."""
        # Test invalid option type
        request_data = {
            "commodity_id": "WTI",
            "underlying_price": "75.50",
            "strike_price": "75.00",
            "days_to_expiry": 30,
            "risk_free_rate": "0.05",
            "volatility": "0.25",
            "option_type": "INVALID",
        }

        response = client.post("/api/options/calculate", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_option_pricing_invalid_values(self):
        """Test option pricing with invalid parameter values."""
        # Test negative underlying price
        request_data = {
            "commodity_id": "WTI",
            "underlying_price": "-75.50",
            "strike_price": "75.00",
            "days_to_expiry": 30,
            "risk_free_rate": "0.05",
            "volatility": "0.25",
            "option_type": "CALL",
        }

        response = client.post("/api/options/calculate", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_greeks_calculation_error_handling(self):
        """Test error handling in Greeks calculation."""
        with patch("src.analytics.options_pricing.black_scholes.BlackScholes") as mock_bs_class:
            mock_bs = Mock()
            mock_bs_class.return_value = mock_bs
            mock_bs.call_price.side_effect = Exception("Calculation error")

            request_data = {
                "commodity_id": "WTI",
                "underlying_price": "75.50",
                "strike_price": "75.00",
                "days_to_expiry": 30,
                "risk_free_rate": "0.05",
                "volatility": "0.25",
                "option_type": "CALL",
            }

            response = client.post("/api/options/greeks", json=request_data)

            assert response.status_code == 500
            assert "Failed to calculate Greeks" in response.json()["detail"]

    def test_moneyness_classification(self):
        """Test moneyness classification logic."""
        with patch("src.analytics.options_pricing.black_scholes.BlackScholes") as mock_bs_class:
            mock_bs = Mock()
            mock_bs_class.return_value = mock_bs
            mock_bs.call_price.return_value = 2.50

            # Test ATM option (within 2% of spot)
            request_data = {
                "commodity_id": "WTI",
                "underlying_price": "75.00",
                "strike_price": "75.00",
                "days_to_expiry": 30,
                "risk_free_rate": "0.05",
                "volatility": "0.25",
                "option_type": "CALL",
            }

            response = client.post("/api/options/calculate", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["moneyness"] == "ATM"
