"""Tests for pylotoncycle.AutoRefreshingSession module."""

import unittest
from unittest.mock import Mock, patch
from pylotoncycle.AutoRefreshingSession import AutoRefreshingSession


def _create_session(**overrides):
    """Helper to create a session with default test values."""
    defaults = {
        "username": "user",
        "password": "pass",
        "access_token": "token",
        "refresh_token": "refresh",
        "client_id": "client",
        "redirect_uri": "https://example.com",
        "token_url": "https://auth.example.com/token",
    }
    defaults.update(overrides)
    return AutoRefreshingSession(**defaults)


class TestAutoRefreshingSessionInit(unittest.TestCase):

    def test_stores_credentials(self):
        session = _create_session(
            username="user@example.com",
            password="secret123",
            access_token="access_abc",
            refresh_token="refresh_xyz",
            client_id="client_123",
        )

        self.assertEqual(session.username, "user@example.com")
        self.assertEqual(session.password, "secret123")
        self.assertEqual(session.access_token, "access_abc")
        self.assertEqual(session.refresh_token, "refresh_xyz")
        self.assertEqual(session.client_id, "client_123")

    def test_creates_last_auth(self):
        session = _create_session()

        self.assertIn("access_token", session.last_auth)
        self.assertIn("refresh_token", session.last_auth)
        self.assertIn("username", session.last_auth)


class TestAutoRefreshingSessionRequest(unittest.TestCase):

    def setUp(self):
        self.session = _create_session(access_token="valid_token")

    @patch("requests.Session.request")
    def test_adds_auth_header(self, mock_request):
        mock_response = Mock(status_code=200)
        mock_request.return_value = mock_response

        self.session.request("GET", "https://api.example.com/data")

        call_kwargs = mock_request.call_args[1]
        self.assertIn("Authorization", call_kwargs["headers"])
        self.assertEqual(
            call_kwargs["headers"]["Authorization"], "Bearer valid_token"
        )

    @patch("requests.Session.request")
    def test_no_auth_header_without_token(self, mock_request):
        self.session.access_token = None
        mock_request.return_value = Mock(status_code=200)

        self.session.request("GET", "https://api.example.com/data")

        call_kwargs = mock_request.call_args[1]
        self.assertNotIn("Authorization", call_kwargs["headers"])

    @patch("requests.post")
    @patch("requests.Session.request")
    def test_refreshes_on_401(self, mock_request, mock_post):
        mock_request.side_effect = [
            Mock(status_code=401),
            Mock(status_code=200),
        ]
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "access_token": "new_token",
                    "id_token": "new_id_token",
                }
            ),
        )

        result = self.session.request("GET", "https://api.example.com/data")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.session.access_token, "new_token")

    @patch("requests.post")
    @patch("requests.Session.request")
    def test_falls_back_to_login(self, mock_request, mock_post):
        self.session.refresh_token = None
        mock_request.side_effect = [
            Mock(status_code=401),
            Mock(status_code=200),
        ]
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "access_token": "login_token",
                    "id_token": "login_id_token",
                }
            ),
        )

        result = self.session.request("GET", "https://api.example.com/data")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            mock_post.call_args[1]["json"]["grant_type"], "password"
        )


class TestLogin(unittest.TestCase):

    def setUp(self):
        self.session = _create_session(access_token=None, refresh_token=None)

    def test_requires_credentials(self):
        self.session.username = None
        self.session.password = None

        with self.assertRaises(Exception) as ctx:
            self.session._login()

        self.assertIn("No login credentials provided", str(ctx.exception))

    @patch("requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "access_token": "new_access",
                    "id_token": "new_id",
                    "refresh_token": "new_refresh",
                }
            ),
        )

        self.session._login()

        self.assertEqual(self.session.access_token, "new_access")
        self.assertEqual(self.session.id_token, "new_id")

    @patch("requests.post")
    def test_failure(self, mock_post):
        mock_post.return_value = Mock(status_code=401)

        with self.assertRaises(Exception) as ctx:
            self.session._login()

        self.assertIn(
            "Could not obtain a new bearer token", str(ctx.exception)
        )


class TestRefreshAccessToken(unittest.TestCase):

    def setUp(self):
        self.session = _create_session(
            access_token="old_token",
            refresh_token="valid_refresh",
        )

    @patch("requests.post")
    def test_success(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "access_token": "refreshed_token",
                    "id_token": "refreshed_id",
                }
            ),
        )

        self.session._refresh_access_token()

        self.assertEqual(self.session.access_token, "refreshed_token")
        self.assertEqual(
            mock_post.call_args[1]["json"]["grant_type"], "refresh_token"
        )

    @patch("requests.post")
    def test_falls_back_to_login(self, mock_post):
        mock_post.side_effect = [
            Mock(status_code=401),
            Mock(
                status_code=200,
                json=Mock(
                    return_value={
                        "access_token": "login_token",
                        "id_token": "login_id",
                    }
                ),
            ),
        ]

        self.session._refresh_access_token()

        self.assertEqual(self.session.access_token, "login_token")

    def test_without_token_calls_login(self):
        self.session.refresh_token = None

        with patch.object(self.session, "_login") as mock_login:
            self.session._refresh_access_token()
            mock_login.assert_called_once()


class TestGetAuthInfo(unittest.TestCase):

    def test_returns_last_auth(self):
        session = _create_session()

        auth_info = session.get_auth_info()

        self.assertEqual(auth_info["access_token"], "token")
        self.assertEqual(auth_info["refresh_token"], "refresh")
        self.assertEqual(auth_info["username"], "user")


if __name__ == "__main__":
    unittest.main()
