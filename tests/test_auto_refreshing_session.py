"""Tests for pylotoncycle.AutoRefreshingSession module."""

import unittest
from unittest.mock import Mock, patch
from pylotoncycle.AutoRefreshingSession import AutoRefreshingSession


class TestAutoRefreshingSessionInit(unittest.TestCase):
    """Tests for AutoRefreshingSession initialization."""

    def test_init_stores_credentials(self):
        """Test that initialization stores all credentials."""
        session = AutoRefreshingSession(
            username="user@example.com",
            password="secret123",
            access_token="access_abc",
            refresh_token="refresh_xyz",
            client_id="client_123",
            redirect_uri="https://example.com/callback",
            token_url="https://auth.example.com/token",
        )

        self.assertEqual(session.username, "user@example.com")
        self.assertEqual(session.password, "secret123")
        self.assertEqual(session.access_token, "access_abc")
        self.assertEqual(session.refresh_token, "refresh_xyz")
        self.assertEqual(session.client_id, "client_123")

    def test_init_creates_last_auth(self):
        """Test that initialization creates last_auth dict."""
        session = AutoRefreshingSession(
            username="user",
            password="pass",
            access_token="token",
            refresh_token="refresh",
            client_id="client",
            redirect_uri="https://example.com",
            token_url="https://auth.example.com",
        )

        self.assertIn("access_token", session.last_auth)
        self.assertIn("refresh_token", session.last_auth)
        self.assertIn("username", session.last_auth)


class TestAutoRefreshingSessionRequest(unittest.TestCase):
    """Tests for the request method with automatic token handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.session = AutoRefreshingSession(
            username="user",
            password="pass",
            access_token="valid_token",
            refresh_token="refresh_token",
            client_id="client_id",
            redirect_uri="https://example.com",
            token_url="https://auth.example.com/token",
        )

    @patch("requests.Session.request")
    def test_request_adds_auth_header(self, mock_request):
        """Test that requests include Authorization header."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.session.request("GET", "https://api.example.com/data")

        call_kwargs = mock_request.call_args[1]
        self.assertIn("Authorization", call_kwargs["headers"])
        self.assertEqual(
            call_kwargs["headers"]["Authorization"], "Bearer valid_token"
        )

    @patch("requests.Session.request")
    def test_request_no_auth_header_without_token(self, mock_request):
        """Test that no auth header is added when no token exists."""
        self.session.access_token = None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.session.request("GET", "https://api.example.com/data")

        call_kwargs = mock_request.call_args[1]
        self.assertNotIn("Authorization", call_kwargs["headers"])

    @patch("requests.post")
    @patch("requests.Session.request")
    def test_request_refreshes_on_401(self, mock_request, mock_post):
        """Test that 401 response triggers token refresh."""
        mock_401_response = Mock()
        mock_401_response.status_code = 401

        mock_200_response = Mock()
        mock_200_response.status_code = 200

        mock_request.side_effect = [mock_401_response, mock_200_response]

        mock_refresh_response = Mock()
        mock_refresh_response.status_code = 200
        mock_refresh_response.json.return_value = {
            "access_token": "new_token",
            "id_token": "new_id_token",
        }
        mock_post.return_value = mock_refresh_response

        result = self.session.request("GET", "https://api.example.com/data")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.session.access_token, "new_token")

    @patch("requests.post")
    @patch("requests.Session.request")
    def test_request_falls_back_to_login(self, mock_request, mock_post):
        """Test fallback to password login when refresh fails."""
        self.session.refresh_token = None

        mock_401_response = Mock()
        mock_401_response.status_code = 401

        mock_200_response = Mock()
        mock_200_response.status_code = 200

        mock_request.side_effect = [mock_401_response, mock_200_response]

        mock_login_response = Mock()
        mock_login_response.status_code = 200
        mock_login_response.json.return_value = {
            "access_token": "login_token",
            "id_token": "login_id_token",
        }
        mock_post.return_value = mock_login_response

        result = self.session.request("GET", "https://api.example.com/data")

        self.assertEqual(result.status_code, 200)

        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["json"]["grant_type"], "password")


class TestLogin(unittest.TestCase):
    """Tests for the _login method."""

    def setUp(self):
        """Set up test fixtures."""
        self.session = AutoRefreshingSession(
            username="user@example.com",
            password="secret",
            access_token=None,
            refresh_token=None,
            client_id="client_id",
            redirect_uri="https://example.com",
            token_url="https://auth.example.com/token",
        )

    def test_login_requires_credentials(self):
        """Test that login fails without username/password."""
        self.session.username = None
        self.session.password = None

        with self.assertRaises(Exception) as ctx:
            self.session._login()

        self.assertIn("No login credentials provided", str(ctx.exception))

    @patch("requests.post")
    def test_login_success(self, mock_post):
        """Test successful login updates tokens."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access",
            "id_token": "new_id",
            "refresh_token": "new_refresh",
        }
        mock_post.return_value = mock_response

        self.session._login()

        self.assertEqual(self.session.access_token, "new_access")
        self.assertEqual(self.session.id_token, "new_id")

    @patch("requests.post")
    def test_login_failure(self, mock_post):
        """Test login failure raises exception."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with self.assertRaises(Exception) as ctx:
            self.session._login()

        self.assertIn(
            "Could not obtain a new bearer token", str(ctx.exception)
        )


class TestRefreshAccessToken(unittest.TestCase):
    """Tests for the _refresh_access_token method."""

    def setUp(self):
        """Set up test fixtures."""
        self.session = AutoRefreshingSession(
            username="user",
            password="pass",
            access_token="old_token",
            refresh_token="valid_refresh",
            client_id="client_id",
            redirect_uri="https://example.com",
            token_url="https://auth.example.com/token",
        )

    @patch("requests.post")
    def test_refresh_success(self, mock_post):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "refreshed_token",
            "id_token": "refreshed_id",
        }
        mock_post.return_value = mock_response

        self.session._refresh_access_token()

        self.assertEqual(self.session.access_token, "refreshed_token")

        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["json"]["grant_type"], "refresh_token")

    @patch("requests.post")
    def test_refresh_falls_back_to_login(self, mock_post):
        """Test that failed refresh falls back to login."""
        mock_refresh_fail = Mock()
        mock_refresh_fail.status_code = 401

        mock_login_success = Mock()
        mock_login_success.status_code = 200
        mock_login_success.json.return_value = {
            "access_token": "login_token",
            "id_token": "login_id",
        }

        mock_post.side_effect = [mock_refresh_fail, mock_login_success]

        self.session._refresh_access_token()

        self.assertEqual(self.session.access_token, "login_token")

    def test_refresh_without_token_calls_login(self):
        """Test that refresh without token calls login directly."""
        self.session.refresh_token = None

        with patch.object(self.session, "_login") as mock_login:
            self.session._refresh_access_token()
            mock_login.assert_called_once()


class TestGetAuthInfo(unittest.TestCase):
    """Tests for get_auth_info method."""

    def test_get_auth_info_returns_last_auth(self):
        """Test that get_auth_info returns the last_auth dict."""
        session = AutoRefreshingSession(
            username="user",
            password="pass",
            access_token="token",
            refresh_token="refresh",
            client_id="client",
            redirect_uri="https://example.com",
            token_url="https://auth.example.com",
        )

        auth_info = session.get_auth_info()

        self.assertEqual(auth_info["access_token"], "token")
        self.assertEqual(auth_info["refresh_token"], "refresh")
        self.assertEqual(auth_info["username"], "user")


if __name__ == "__main__":
    unittest.main()
