"""
Auto-refreshing OAuth session for Peloton API.

Provides a requests.Session subclass that automatically handles
OAuth Bearer token injection and refresh.
"""

import requests


class AutoRefreshingSession(requests.Session):
    """
    Custom Session that automatically handles OAuth Bearer token injection
    and refreshes the token when a 401 Unauthorized error occurs.

    Extends requests.Session to automatically:
    - Add Authorization header with Bearer token to all requests
    - Refresh the access token when receiving a 401 response
    - Fall back to username/password login if refresh token fails

    Args:
        username: Peloton account username or email.
        password: Peloton account password.
        access_token: Current OAuth access token.
        refresh_token: OAuth refresh token for obtaining new access tokens.
        client_id: OAuth client ID.
        redirect_uri: OAuth redirect URI.
        token_url: OAuth token endpoint URL.
    """

    def __init__(
        self,
        username,
        password,
        access_token,
        refresh_token,
        client_id,
        redirect_uri,
        token_url,
    ):
        super().__init__()
        self.username = username
        self.password = password
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.token_url = token_url
        self.id_token = ""
        self.last_auth = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "username": self.username,
            "password": self.password,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
        }

    def request(self, method, url, *args, **kwargs):
        """
        Make an HTTP request with automatic token handling.

        Injects the Authorization header and retries with a refreshed
        token if the server returns 401 Unauthorized.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL.
            *args: Additional positional arguments for requests.Session.
            **kwargs: Additional keyword arguments for requests.Session.

        Returns:
            requests.Response: The HTTP response.

        Raises:
            Exception: If token refresh fails and request cannot be completed.
        """
        headers = kwargs.get("headers") or {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers

        response = super().request(method, url, *args, **kwargs)

        if response.status_code == 401:
            try:
                self._refresh_access_token()

                kwargs["headers"][
                    "Authorization"
                ] = f"Bearer {self.access_token}"

                response = super().request(method, url, *args, **kwargs)
            except Exception as e:
                raise Exception(f"Could not obtain a new bearer token. {e}")

        return response

    def _login(self):
        """
        Authenticate using username and password.

        Obtains new access and refresh tokens using the password grant.

        Raises:
            Exception: If credentials are missing or login fails.
        """
        if not self.username or not self.password:
            raise Exception(
                "Could not obtain a new bearer token. "
                "No login credentials provided. Update your refresh token."
            )
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "scope": "offline_access openid",
            "username": self.username,
            "password": self.password,
        }
        resp = requests.post(self.token_url, json=payload, timeout=10)

        if resp.status_code != 200:
            raise Exception(
                "Could not obtain a new bearer token. "
                "If using login credentials ensure they are correct. "
                "If using a refresh token please update it."
            )

        data = resp.json()
        data.update(
            {
                "username": self.username,
                "password": self.password,
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
            }
        )
        self.last_auth = data
        self.access_token = data["access_token"]
        self.id_token = data["id_token"]

    def _refresh_access_token(self):
        """
        Refresh the access token using the refresh token.

        If no refresh token is available or refresh fails, falls back
        to username/password login.
        """
        if not self.refresh_token:
            self._login()
            return

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
            "redirect_uri": self.redirect_uri,
        }
        resp = requests.post(self.token_url, json=payload, timeout=10)

        if resp.status_code != 200:
            self._login()
            return
        data = resp.json()
        data.update(
            {
                "username": self.username,
                "password": self.password,
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
            }
        )
        self.last_auth = data
        self.access_token = data["access_token"]
        self.id_token = data["id_token"]

    def get_auth_info(self):
        """
        Get current authentication information.

        Returns:
            dict: Authentication data including tokens and credentials.
        """
        return self.last_auth
