"""Tests for system status and health check endpoints."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime, UTC

from src.api.main import app


client = TestClient(app)


class TestSystemEndpoints:
    """Test system status and health check functionality."""

    @patch("src.api.routes.system.DatabaseOperations")
    def test_get_system_status_healthy(self, mock_db_ops):
        """Test system status when everything is healthy."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        
        # Mock successful database health check
        mock_db.conn.execute.return_value.fetchone.side_effect = [
            (1,),  # Health check query
            (datetime.now(UTC),),  # Last update query
            [("WTI",), ("NG",)],  # Active commodities query
            (150,)  # Total records query
        ]
        
        # Mock fetchall for commodities query
        mock_db.conn.execute.return_value.fetchall.return_value = [("WTI",), ("NG",)]
        
        response = client.get("/api/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["api_status"] == "healthy"
        assert data["database_status"] == "healthy"
        assert "last_data_update" in data
        assert "WTI" in data["active_commodities"]
        assert "NG" in data["active_commodities"]
        assert data["total_price_records"] == 150

    @patch("src.api.routes.system.DatabaseOperations")
    def test_get_system_status_database_error(self, mock_db_ops):
        """Test system status when database has issues."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        
        # Mock database error for health check
        mock_db.conn.execute.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["api_status"] == "degraded"
        assert data["database_status"] == "error"
        assert data["active_commodities"] == []
        assert data["total_price_records"] == 0

    @patch("src.api.routes.system.DatabaseOperations")
    def test_get_commodity_metrics_success(self, mock_db_ops):
        """Test successful commodity metrics retrieval."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        
        # Mock commodities query
        commodities_data = [("WTI", "West Texas Intermediate"), ("NG", "Natural Gas")]
        
        # Mock price data for each commodity
        price_data_wti = [
            (76.25, 95000, 500000, "2024-01-02"),  # Latest
            (75.75, 100000, 505000, "2024-01-01")  # Previous
        ]
        
        price_data_ng = [
            (3.45, 85000, 300000, "2024-01-02"),  # Latest
            (3.40, 90000, 305000, "2024-01-01")  # Previous
        ]
        
        # Mock weekly high/low data
        week_data_wti = (77.00, 75.00)  # High, Low
        week_data_ng = (3.50, 3.35)
        
        # Mock volatility calculation data
        vol_data_wti = [(76.25,), (75.75,), (76.00,), (75.50,)]
        vol_data_ng = [(3.45,), (3.40,), (3.42,), (3.38,)]
        
        def mock_execute_side_effect(*args, **kwargs):
            query = args[0]
            params = args[1] if len(args) > 1 else []
            
            if "SELECT commodity_id, name FROM commodities" in query:
                return Mock(fetchall=Mock(return_value=commodities_data))
            elif "SELECT fp.close_price, fp.volume, fp.open_interest" in query:
                if params[0] == "WTI":
                    return Mock(fetchall=Mock(return_value=price_data_wti))
                else:
                    return Mock(fetchall=Mock(return_value=price_data_ng))
            elif "SELECT MAX(fp.high_price)" in query:
                if params[0] == "WTI":
                    return Mock(fetchone=Mock(return_value=week_data_wti))
                else:
                    return Mock(fetchone=Mock(return_value=week_data_ng))
            elif "SELECT fp.close_price" in query and "INTERVAL 30 DAY" in query:
                if params[0] == "WTI":
                    return Mock(fetchall=Mock(return_value=vol_data_wti))
                else:
                    return Mock(fetchall=Mock(return_value=vol_data_ng))
            else:
                return Mock(fetchall=Mock(return_value=[]), fetchone=Mock(return_value=None))
        
        mock_db.conn.execute.side_effect = mock_execute_side_effect
        
        response = client.get("/api/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check WTI metrics
        wti_metrics = next(m for m in data if m["commodity_id"] == "WTI")
        assert wti_metrics["name"] == "West Texas Intermediate"
        assert float(wti_metrics["latest_price"]) == 76.25
        assert float(wti_metrics["daily_change"]) == 0.50  # 76.25 - 75.75
        assert wti_metrics["volume"] == 95000
        assert wti_metrics["open_interest"] == 500000
        
        # Check NG metrics
        ng_metrics = next(m for m in data if m["commodity_id"] == "NG")
        assert ng_metrics["name"] == "Natural Gas"
        assert float(ng_metrics["latest_price"]) == 3.45
        assert float(ng_metrics["daily_change"]) == 0.05  # 3.45 - 3.40
        assert ng_metrics["volume"] == 85000
        assert ng_metrics["open_interest"] == 300000

    @patch("src.api.routes.system.DatabaseOperations")
    def test_get_commodity_metrics_partial_failure(self, mock_db_ops):
        """Test commodity metrics when some commodities fail to load."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        
        # Mock commodities query
        commodities_data = [("WTI", "West Texas Intermediate"), ("INVALID", "Invalid Commodity")]
        
        def mock_execute_side_effect(*args, **kwargs):
            query = args[0]
            params = args[1] if len(args) > 1 else []
            
            if "SELECT commodity_id, name FROM commodities" in query:
                return Mock(fetchall=Mock(return_value=commodities_data))
            elif params and params[0] == "WTI":
                # Return valid data for WTI
                if "SELECT fp.close_price, fp.volume" in query:
                    return Mock(fetchall=Mock(return_value=[(76.25, 95000, 500000, "2024-01-02")]))
                elif "SELECT MAX(fp.high_price)" in query:
                    return Mock(fetchone=Mock(return_value=(77.00, 75.00)))
                elif "SELECT fp.close_price" in query and "INTERVAL 30 DAY" in query:
                    return Mock(fetchall=Mock(return_value=[(76.25,), (75.75,)]))
            elif params and params[0] == "INVALID":
                # Simulate error for invalid commodity
                raise Exception("No data for invalid commodity")
            
            return Mock(fetchall=Mock(return_value=[]), fetchone=Mock(return_value=None))
        
        mock_db.conn.execute.side_effect = mock_execute_side_effect
        
        response = client.get("/api/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        # Should only return metrics for WTI, INVALID should be skipped
        assert len(data) == 1
        assert data[0]["commodity_id"] == "WTI"

    @patch("src.api.routes.system.DatabaseOperations")
    def test_get_commodity_metrics_empty_database(self, mock_db_ops):
        """Test commodity metrics with empty database."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        
        # Mock empty commodities query
        mock_db.conn.execute.return_value.fetchall.return_value = []
        
        response = client.get("/api/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @patch("src.api.routes.system.DatabaseOperations")
    def test_get_commodity_metrics_database_error(self, mock_db_ops):
        """Test commodity metrics with database error."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        
        # Mock database error
        mock_db.conn.execute.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0  # Should return empty list on error

    @patch("src.api.routes.system.DatabaseOperations")
    def test_volatility_calculation_edge_cases(self, mock_db_ops):
        """Test volatility calculation with edge cases."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        
        # Mock commodities query
        commodities_data = [("TEST", "Test Commodity")]
        
        def mock_execute_side_effect(*args, **kwargs):
            query = args[0]
            params = args[1] if len(args) > 1 else []
            
            if "SELECT commodity_id, name FROM commodities" in query:
                return Mock(fetchall=Mock(return_value=commodities_data))
            elif "SELECT fp.close_price, fp.volume" in query:
                # Return single price point
                return Mock(fetchall=Mock(return_value=[(75.00, 100000, 500000, "2024-01-01")]))
            elif "SELECT MAX(fp.high_price)" in query:
                return Mock(fetchone=Mock(return_value=(75.00, 75.00)))
            elif "SELECT fp.close_price" in query and "INTERVAL 30 DAY" in query:
                # Return only one price point (insufficient for volatility calculation)
                return Mock(fetchall=Mock(return_value=[(75.00,)]))
            
            return Mock(fetchall=Mock(return_value=[]), fetchone=Mock(return_value=None))
        
        mock_db.conn.execute.side_effect = mock_execute_side_effect
        
        response = client.get("/api/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        # Should use default volatility when insufficient data
        assert float(data[0]["monthly_volatility"]) == 0.25

    def test_system_endpoints_no_auth_required(self):
        """Test that system endpoints don't require authentication."""
        # These endpoints should be accessible without authentication
        response1 = client.get("/api/system/status")
        response2 = client.get("/api/system/metrics")
        
        # Should not get 401/403 auth errors
        assert response1.status_code != 401
        assert response1.status_code != 403
        assert response2.status_code != 401
        assert response2.status_code != 403