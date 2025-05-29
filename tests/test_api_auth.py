"""Tests for authentication API endpoints."""

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoint functionality."""

    def test_health_check(self):
        """Test API health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "oil-gas-futures-api"}

    @patch("src.api.routes.auth.DatabaseOperations")
    def test_user_registration_success(self, mock_db_ops):
        """Test successful user registration."""
        # Mock database operations
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        mock_db.conn.execute.return_value.fetchone.return_value = None  # No existing user

        # Mock successful user creation
        mock_user_row = (
            "123e4567-e89b-12d3-a456-426614174000",
            "test@example.com",
            "hashed_password",
            "Test User",
            "viewer",
            True,
            "2024-01-01T00:00:00",
            "2024-01-01T00:00:00",
            None,
        )
        mock_db.conn.execute.return_value.fetchone.side_effect = [None, mock_user_row]

        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",  # pragma: allowlist secret
            "full_name": "Test User",
        }

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["role"] == "viewer"
        assert data["is_active"] is True
        assert "user_id" in data

    @patch("src.api.routes.auth.DatabaseOperations")
    def test_user_registration_duplicate_email(self, mock_db_ops):
        """Test user registration with existing email."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        # Mock existing user found
        mock_db.conn.execute.return_value.fetchone.return_value = ("existing_user",)

        user_data = {
            "email": "existing@example.com",
            "password": "testpassword123",  # pragma: allowlist secret
            "full_name": "Test User",  # pragma: allowlist secret
        }

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @patch("src.api.routes.auth.DatabaseOperations")
    @patch("src.api.routes.auth.verify_password")
    def test_user_login_success(self, mock_verify_password, mock_db_ops):
        """Test successful user login."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        mock_verify_password.return_value = True

        # Mock user found in database
        mock_user_row = (
            "123e4567-e89b-12d3-a456-426614174000",
            "test@example.com",
            "hashed_password",
            "Test User",
            "viewer",
            True,
            "2024-01-01T00:00:00",
            "2024-01-01T00:00:00",
            None,
        )
        mock_db.conn.execute.return_value.fetchone.return_value = mock_user_row

        login_data = {
            "email": "test@example.com",
            "password": "testpassword123",  # pragma: allowlist secret
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800  # 30 minutes in seconds

    @patch("src.api.routes.auth.DatabaseOperations")
    def test_user_login_invalid_credentials(self, mock_db_ops):
        """Test login with invalid credentials."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        # Mock no user found
        mock_db.conn.execute.return_value.fetchone.return_value = None
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword",  # pragma: allowlist secret
        }
        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @patch("src.api.routes.auth.DatabaseOperations")
    @patch("src.api.routes.auth.verify_password")
    def test_user_login_inactive_account(self, mock_verify_password, mock_db_ops):
        """Test login with inactive user account."""
        mock_db = Mock()
        mock_db_ops.return_value = mock_db
        mock_verify_password.return_value = True

        # Mock inactive user
        mock_user_row = (
            "123e4567-e89b-12d3-a456-426614174000",
            "test@example.com",
            "hashed_password",
            "Test User",
            "viewer",
            False,  # is_active = False
            "2024-01-01T00:00:00",
            "2024-01-01T00:00:00",
            None,
        )
        mock_db.conn.execute.return_value.fetchone.return_value = mock_user_row

        login_data = {
            "email": "test@example.com",
            "password": "testpassword123",  # pragma: allowlist secret
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        assert "User account is disabled" in response.json()["detail"]

    def test_get_current_user_success(self):
        """Test getting current user information."""
        from src.api.main import app
        from src.api.routes.auth import get_db, verify_token

        # Create a mock function that returns user data
        def mock_verify_token():
            return {"user_id": "123", "email": "test@example.com"}

        def mock_get_db():
            mock_db = Mock()
            mock_user_row = (
                "123e4567-e89b-12d3-a456-426614174000",
                "test@example.com",
                "hashed_password",
                "Test User",
                "viewer",
                True,
                "2024-01-01T00:00:00",
                "2024-01-01T00:00:00",
                None,
            )
            mock_db.conn.execute.return_value.fetchone.return_value = mock_user_row
            return mock_db

        # Override dependencies
        app.dependency_overrides[verify_token] = mock_verify_token
        app.dependency_overrides[get_db] = mock_get_db

        try:
            response = client.get("/api/auth/me")

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["full_name"] == "Test User"
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_logout_endpoint(self):
        """Test logout endpoint."""
        from src.api.main import app
        from src.api.routes.auth import verify_token

        def mock_verify_token():
            return {"user_id": "123", "email": "test@example.com"}

        app.dependency_overrides[verify_token] = mock_verify_token

        try:
            response = client.post("/api/auth/logout")

            assert response.status_code == 200
            assert response.json()["message"] == "Successfully logged out"
        finally:
            app.dependency_overrides.clear()

    def test_missing_authorization_header(self):
        """Test API endpoints without authorization header."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403  # HTTPBearer requires header

    def test_invalid_token_format(self):
        """Test API endpoints with invalid token format."""
        response = client.get("/api/auth/me", headers={"Authorization": "Invalid token_format"})
        assert response.status_code == 403  # HTTPBearer validation
