import requests

from .exceptions import PelotonAuthError


class AutoRefreshingSession(requests.Session):
    """
    Custom Session that automatically handles OAuth Bearer token injection
    and refreshes the token when a 401 Unauthorized error occurs.
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

    def _login(self):
        if not self.username or not self.password:
            raise PelotonAuthError(
                "Could not obtain a new bearer token. No login credentials provided. Update your refresh token."
            )
        # print ("Attempting using Username/Password")
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "scope": "offline_access openid",
            "username": self.username,
            "password": self.password,
        }
        resp = requests.post(self.token_url, json=payload, timeout=10)

        if resp.status_code != 200:
            raise PelotonAuthError(
                "Could not obtain a new bearer token. If using login credentials ensure they are correct. If using a refresh token please update it."
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
        resp = requests.post(self.token_url, json=payload, timeout=10)

        if resp.status_code != 200:
            try:
                self._login()
            except PelotonAuthError as e:
                raise PelotonAuthError(
                    "Could not refresh access token and fallback login failed."
                ) from e
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
        return self.last_auth
