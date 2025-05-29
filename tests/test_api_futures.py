"""Tests for futures data API endpoints."""

from datetime import date, datetime
from unittest.mock import Mock, patch

import pandas as pd
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestFuturesEndpoints:
    """Test futures data endpoint functionality."""

    @patch("src.api.routes.futures.DatabaseOperations")
    def test_get_futures_contracts_success(self, mock_db_ops):
        """Test successful retrieval of futures contracts."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock DataFrame response
        mock_df = pd.DataFrame(
            {
                "contract_id": ["CL_2024_12", "NG_2024_12"],
                "commodity_id": ["WTI", "NG"],
                "symbol": ["CLZ24", "NGZ24"],
                "expiration_date": [date(2024, 12, 20), date(2024, 12, 27)],
                "is_active": [True, True],
                "created_at": [
                    datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
                    datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
                ],
            }
        )
        mock_db.get_active_contracts.return_value = mock_df

        response = client.get("/api/futures/contracts")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["contract_id"] == "CL_2024_12"
        assert data[0]["commodity_id"] == "WTI"
        assert data[1]["commodity_id"] == "NG"

    @patch("src.api.routes.futures.DatabaseOperations")
    def test_get_futures_contracts_with_filter(self, mock_db_ops):
        """Test futures contracts retrieval with commodity filter."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock DataFrame response for WTI only
        mock_df = pd.DataFrame(
            {
                "contract_id": ["CL_2024_12"],
                "commodity_id": ["WTI"],
                "symbol": ["CLZ24"],
                "expiration_date": [date(2024, 12, 20)],
                "is_active": [True],
                "created_at": [datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)],
            }
        )
        mock_db.get_active_contracts.return_value = mock_df

        response = client.get("/api/futures/contracts?commodity_id=WTI")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["commodity_id"] == "WTI"
        mock_db.get_active_contracts.assert_called_with("WTI")

    @patch("src.api.routes.futures.DatabaseOperations")
    def test_get_futures_prices_success(self, mock_db_ops):
        """Test successful retrieval of futures prices."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock DataFrame response
        mock_df = pd.DataFrame(
            {
                "price_id": [1, 2],
                "contract_id": ["CL_2024_12", "CL_2024_12"],
                "commodity_id": ["WTI", "WTI"],
                "symbol": ["CLZ24", "CLZ24"],
                "price_date": [date(2024, 1, 1), date(2024, 1, 2)],
                "open_price": [75.50, 76.00],
                "high_price": [76.00, 76.50],
                "low_price": [75.00, 75.50],
                "close_price": [75.75, 76.25],
                "volume": [100000, 95000],
                "open_interest": [500000, 495000],
            }
        )
        mock_db.get_futures_prices.return_value = mock_df

        response = client.get("/api/futures/prices")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert float(data[0]["close_price"]) == 75.75
        assert data[0]["volume"] == 100000

    @patch("src.api.routes.futures.DatabaseOperations")
    def test_get_latest_price_success(self, mock_db_ops):
        """Test successful retrieval of latest price."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock DataFrame with two rows for change calculation
        mock_df = pd.DataFrame(
            {
                "close_price": [76.25, 75.75],
                "symbol": ["CLZ24", "CLZ24"],
                "volume": [95000, 100000],
                "price_date": [date(2024, 1, 2), date(2024, 1, 1)],
            }
        )
        mock_db.get_futures_prices.return_value = mock_df

        response = client.get("/api/futures/prices/WTI/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["commodity_id"] == "WTI"
        assert data["symbol"] == "CLZ24"
        assert float(data["price"]) == 76.25
        assert float(data["change"]) == 0.50  # 76.25 - 75.75
        assert data["volume"] == 95000

    @patch("src.api.routes.futures.DatabaseOperations")
    def test_get_latest_price_not_found(self, mock_db_ops):
        """Test latest price when no data found."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock empty DataFrame
        mock_df = pd.DataFrame()
        mock_db.get_futures_prices.return_value = mock_df

        response = client.get("/api/futures/prices/INVALID/latest")

        assert response.status_code == 404
        assert "No prices found" in response.json()["detail"]

    @patch("src.api.routes.futures.DatabaseOperations")
    def test_get_historical_prices_success(self, mock_db_ops):
        """Test successful retrieval of historical prices."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock DataFrame response
        mock_df = pd.DataFrame(
            {
                "price_id": [1, 2, 3],
                "contract_id": ["CL_2024_12", "CL_2024_12", "CL_2024_12"],
                "commodity_id": ["WTI", "WTI", "WTI"],
                "symbol": ["CLZ24", "CLZ24", "CLZ24"],
                "price_date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)],
                "open_price": [75.50, 76.00, 75.80],
                "high_price": [76.00, 76.50, 76.20],
                "low_price": [75.00, 75.50, 75.30],
                "close_price": [75.75, 76.25, 75.90],
                "volume": [100000, 95000, 98000],
                "open_interest": [500000, 495000, 492000],
            }
        )
        mock_db.get_futures_prices.return_value = mock_df

        request_data = {"start_date": "2024-01-01", "end_date": "2024-01-31", "limit": 100}

        response = client.post("/api/futures/prices/WTI/historical", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert float(data[0]["close_price"]) == 75.75

    @patch("src.api.routes.futures.DatabaseOperations")
    def test_get_historical_prices_with_defaults(self, mock_db_ops):
        """Test historical prices with default date range."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db

        # Mock DataFrame response
        mock_df = pd.DataFrame(
            {
                "price_id": [1],
                "contract_id": ["CL_2024_12"],
                "commodity_id": ["WTI"],
                "symbol": ["CLZ24"],
                "price_date": [date(2024, 1, 1)],
                "open_price": [75.50],
                "high_price": [76.00],
                "low_price": [75.00],
                "close_price": [75.75],
                "volume": [100000],
                "open_interest": [500000],
            }
        )
        mock_db.get_futures_prices.return_value = mock_df

        # Empty request - should use defaults
        request_data = {}

        response = client.post("/api/futures/prices/WTI/historical", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_futures_price_validation(self):
        """Test request validation for futures endpoints."""
        # Test invalid query parameters
        response = client.get("/api/futures/prices?limit=2000")  # Exceeds maximum
        # Should still work but limit will be capped by Query validation
        assert response.status_code in [200, 422]

    @patch("src.api.routes.futures.DatabaseOperations")
    def test_database_error_handling(self, mock_db_ops):
        """Test handling of database errors."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        mock_db.get_active_contracts.side_effect = Exception("Database connection failed")

        response = client.get("/api/futures/contracts")

        assert response.status_code == 500
        assert "Failed to retrieve contracts" in response.json()["detail"]

    def test_invalid_commodity_id_format(self):
        """Test handling of invalid commodity ID formats."""
        response = client.get("/api/futures/prices/INVALID_VERY_LONG_COMMODITY_ID/latest")
        # This should still reach the endpoint but return 404 if no data found
        # The validation is done at the database level
        assert response.status_code in [404, 500]
