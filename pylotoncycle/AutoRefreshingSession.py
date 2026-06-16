from typing import Any, Dict, Optional

import requests

from .exceptions import PelotonAuthError


class AutoRefreshingSession(requests.Session):
    """Custom Session that automatically handles OAuth token management.

    It handles OAuth Bearer token injection and refreshes the token when
    a 401 Unauthorized error occurs.
    """

    def __init__(
        self,
        username: Optional[str],
        password: Optional[str],
        access_token: Optional[str],
        refresh_token: Optional[str],
        client_id: str,
        redirect_uri: str,
        token_url: str,
    ) -> None:
        """Initializes the session with authentication credentials.

        Args:
            username: Peloton username or email.
            password: Peloton password.
            access_token: Existing OAuth access token.
            refresh_token: Existing OAuth refresh token.
            client_id: OAuth client ID.
            redirect_uri: OAuth redirect URI.
            token_url: OAuth token endpoint URL.
        """
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

    def request(
        self, method: str, url: str, *args: Any, **kwargs: Any
    ) -> requests.Response:
        """Constructs and sends a Request.

        Automatically injects the Authorization header and retries on 401.

        Args:
            method: Method for the new Request object.
            url: URL for the new Request object.
            *args: Optional arguments that ``request`` takes.
            **kwargs: Optional keyword arguments that ``request`` takes.

        Returns:
            The Response object.
        """
        # Inject the Authorization header automatically
        headers = kwargs.get("headers") or {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers

        response = super().request(method, url, *args, **kwargs)

        # auto retry on 401
        if response.status_code == 401:
            try:
                # print("Access Token expired. Obtaining New Token")
                self._refresh_access_token()

                # Update the header with the new token
                kwargs["headers"][
                    "Authorization"
                ] = f"Bearer {self.access_token}"

                # Retry the original request
                response = super().request(method, url, *args, **kwargs)
            except Exception as e:
                # print(f"Token refresh failed: {e}")
                # If refresh fails, we return the original 401 response
                # so the caller knows authentication is truly broken.
                raise PelotonAuthError(
                    f"Could not obtain a new bearer token. {e}"
                ) from e

        return response

    def _post_token_request(
        self, payload: Dict[str, Any], error_message: str
    ) -> requests.Response:
        """Sends a POST request to the token endpoint.

        Args:
            payload: The JSON payload for the POST request.
            error_message: Error message to use if the request fails.

        Returns:
            The Response object.
        """
        try:
            return requests.post(self.token_url, json=payload, timeout=10)
        except requests.RequestException as e:
            raise PelotonAuthError(error_message) from e

    def _parse_token_response(
        self, resp: requests.Response, error_message: str
    ) -> Dict[str, Any]:
        """Parses the JSON response from the token endpoint.

        Args:
            resp: The Response object.
            error_message: Error message to use if parsing fails.

        Returns:
            The parsed JSON data.
        """
        try:
            data = resp.json()
        except ValueError as e:
            raise PelotonAuthError(error_message) from e

        missing_fields = [
            field
            for field in ("access_token", "id_token")
            if not data.get(field)
        ]
        if missing_fields:
            fields_str = ", ".join(missing_fields)
            raise PelotonAuthError(
                f"{error_message} Missing expected field(s): " f"{fields_str}"
            )

        return data

    def _update_auth_from_token_data(self, data: Dict[str, Any]) -> None:
        """Updates internal auth state from token response data.

        Args:
            data: The parsed token response data.
        """
        self.last_auth = data
        self.access_token = data["access_token"]
        self.id_token = data["id_token"]

    def _login(self) -> None:
        """Authenticates using username and password to obtain tokens."""
        if not self.username or not self.password:
            raise PelotonAuthError(
                "Could not obtain a new bearer token. "
                "No login credentials provided. "
                "Update your refresh token."
            )
        # print ("Attempting using Username/Password")
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "scope": "offline_access openid",
            "username": self.username,
            "password": self.password,
        }
        error_message = (
            "Could not obtain a new bearer token. If using login "
            "credentials ensure they are correct. If using a refresh token "
            "please update it."
        )
        resp = self._post_token_request(payload, error_message)

        if resp.status_code != 200:
            raise PelotonAuthError(error_message)

        data = self._parse_token_response(resp, error_message)
        data.update(
            {
                "username": self.username,
                "password": self.password,
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
            }
        )
        self._update_auth_from_token_data(data)

    def _refresh_access_token(self) -> None:
        """Refreshes the access token using the refresh token."""
        if not self.refresh_token:
            self._login()
            return
        # print("Attempting using Refresh Token")
        # Calls the API to get a new access token using the refresh token.
        # We use a standard requests.post here to avoid infinite recursion
        # if the refresh endpoint itself returns a 401.
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
            "redirect_uri": self.redirect_uri,
        }
        error_message = "Could not refresh access token."
        resp = self._post_token_request(payload, error_message)

        if resp.status_code != 200:
            try:
                self._login()
            except PelotonAuthError as e:
                raise PelotonAuthError(
                    "Could not refresh access token and fallback login failed."
                ) from e
            return
        data = self._parse_token_response(resp, error_message)
        data.update(
            {
                "username": self.username,
                "password": self.password,
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
            }
        )
        self._update_auth_from_token_data(data)

    def get_auth_info(self) -> Dict[str, Any]:
        """Returns the last successfully obtained authentication info.

        Returns:
            A dictionary containing authentication tokens and credentials.
        """
        return self.last_auth
