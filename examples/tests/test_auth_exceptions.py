import unittest
from unittest.mock import patch
import importlib

import requests

from pylotoncycle import PelotonAuthError
from pylotoncycle.AutoRefreshingSession import AutoRefreshingSession

auth_session_module = importlib.import_module(
    "pylotoncycle.AutoRefreshingSession"
)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self):
        return self._json_data


class InvalidJsonResponse(FakeResponse):
    def json(self):
        raise ValueError("not json")


class TestAutoRefreshingSession(unittest.TestCase):
    def _make_session(self, **kwargs):
        defaults = {
            "username": "user",
            "password": "pass",
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "client_id": "client",
            "redirect_uri": "https://example.com/callback",
            "token_url": "https://example.com/token",
        }
        defaults.update(kwargs)
        return AutoRefreshingSession(**defaults)

    def test_login_without_credentials_raises_auth_error(self):
        session = self._make_session(username=None, password=None)

        with self.assertRaises(PelotonAuthError):
            session._login()

    @patch.object(auth_session_module.requests, "post")
    def test_login_with_non_200_raises_auth_error(self, mock_post):
        mock_post.return_value = FakeResponse(status_code=400)
        session = self._make_session()

        with self.assertRaises(PelotonAuthError):
            session._login()

    @patch.object(auth_session_module.requests, "post")
    def test_login_with_request_failure_raises_auth_error(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("network down")
        session = self._make_session()

        with self.assertRaises(PelotonAuthError):
            session._login()

    @patch.object(auth_session_module.requests, "post")
    def test_login_with_invalid_json_raises_auth_error(self, mock_post):
        mock_post.return_value = InvalidJsonResponse()
        session = self._make_session()

        with self.assertRaises(PelotonAuthError):
            session._login()

    @patch.object(auth_session_module.requests, "post")
    def test_login_with_missing_token_fields_raises_auth_error(
        self,
        mock_post,
    ):
        mock_post.return_value = FakeResponse(
            json_data={"access_token": "new-access"}
        )
        session = self._make_session()

        with self.assertRaises(PelotonAuthError):
            session._login()

    @patch.object(auth_session_module.requests, "post")
    def test_login_updates_auth_state(self, mock_post):
        mock_post.return_value = FakeResponse(
            json_data={
                "access_token": "new-access",
                "id_token": "new-id",
                "refresh_token": "new-refresh",
            }
        )
        session = self._make_session()

        session._login()

        self.assertEqual(session.access_token, "new-access")
        self.assertEqual(session.id_token, "new-id")
        self.assertEqual(session.last_auth["username"], "user")
        self.assertEqual(session.last_auth["client_id"], "client")

    @patch.object(auth_session_module.requests, "post")
    def test_refresh_token_falls_back_to_login_failure(self, mock_post):
        mock_post.return_value = FakeResponse(status_code=400)
        session = self._make_session(refresh_token="refresh-token")

        with self.assertRaises(PelotonAuthError):
            session._refresh_access_token()

    @patch.object(auth_session_module.requests, "post")
    def test_refresh_token_with_request_failure_raises_auth_error(
        self,
        mock_post,
    ):
        mock_post.side_effect = requests.Timeout("timed out")
        session = self._make_session(refresh_token="refresh-token")

        with self.assertRaises(PelotonAuthError):
            session._refresh_access_token()

    @patch.object(auth_session_module.requests, "post")
    def test_refresh_token_with_invalid_json_raises_auth_error(
        self,
        mock_post,
    ):
        mock_post.return_value = InvalidJsonResponse()
        session = self._make_session(refresh_token="refresh-token")

        with self.assertRaises(PelotonAuthError):
            session._refresh_access_token()

    @patch.object(auth_session_module.requests, "post")
    def test_refresh_token_with_missing_token_fields_raises_auth_error(
        self,
        mock_post,
    ):
        mock_post.return_value = FakeResponse(
            json_data={"access_token": "new-access"}
        )
        session = self._make_session(refresh_token="refresh-token")

        with self.assertRaises(PelotonAuthError):
            session._refresh_access_token()

    @patch.object(auth_session_module.requests, "post")
    def test_refresh_token_updates_auth_state(self, mock_post):
        mock_post.return_value = FakeResponse(
            json_data={
                "access_token": "new-access",
                "id_token": "new-id",
                "refresh_token": "new-refresh",
            }
        )
        session = self._make_session(refresh_token="refresh-token")

        session._refresh_access_token()

        self.assertEqual(session.access_token, "new-access")
        self.assertEqual(session.id_token, "new-id")
        self.assertEqual(session.last_auth["refresh_token"], "refresh-token")
        self.assertEqual(session.last_auth["client_id"], "client")

    @patch.object(auth_session_module.requests, "post")
    @patch.object(requests.Session, "request")
    def test_request_401_wraps_refresh_failure(
        self, mock_super_request, mock_post
    ):
        mock_super_request.return_value = FakeResponse(status_code=401)
        mock_post.return_value = FakeResponse(status_code=400)
        session = self._make_session(refresh_token="refresh-token")

        with self.assertRaises(PelotonAuthError):
            session.request("GET", "https://example.com/api")


if __name__ == "__main__":
    unittest.main()
