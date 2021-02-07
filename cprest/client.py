#
#   Copyright 2021 h-tin
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import time
from typing import Optional, Tuple, Union
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)


class Client:
    """ClearPass RESTful API Client."""

    def __init__(self, host: str = "", port: int = 443,
                 timeout: Union[Tuple[float, float], float] = 30.0,
                 verify_cert: bool = False):
        """Constructor.

        Args:
            host: API Server hostname or IP address.
            port: API Server listening port number between 1 and 65535.
            timeout: Timeout seconds to wait for server connection and server response.
                     A float value is set to the same value for both.
            verify_cert: Enable SSL certificate validation.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.verify_cert = verify_cert
        self._authorized_at = None
        self._access_token = None
        self._token_type = None
        self._expires_in = None
        self._refresh_token = None

    @property
    def is_authorized(self) -> bool:
        """Whether the client is authorized (expiration is not considered)."""
        return True if self._access_token else False

    @property
    def authorization_header(self) -> Optional[str]:
        """Authorization header.
           None means that the client has not yet been authorized.
        """
        if self.is_authorized:
            return " ".join([self._token_type, self._access_token])

    @property
    def expiration_time(self) -> Optional[float]:
        """Expiration time in seconds.
           None means that the client has not yet been authorized.
        """
        if self._authorized_at and self._expires_in:
            return self._authorized_at + self._expires_in

    @property
    def refresh_token(self) -> Optional[str]:
        """Refresh token.
           None means that no refresh token has been issued.
        """
        return self._refresh_token

    @property
    def base_url(self) -> str:
        """Base URL."""
        if self.port == 443:
            return "".join(["https://", self.host, "/api"])
        else:
            return "".join(["https://", self.host, ":", str(self.port), "/api"])

    def request(self, method: str, resource: str,
                params={}, body={}) -> requests.Response:
        """Invoke an API requerst.

        Args:
            method: HTTP request method. One of GET, POST, PATCH, PUT, DELETE.
            resource: Target resource.
            params: Query parameters added to the URL, e.g. ?key1=value1&key2=value2&...
            body: Request body sent as JSON, e.g. {"key1":"value1","key2":"value2",...}

        Raises:
            RequestException: There was an ambiguous exception that occurred while handling your request.
            ConnectionError: A Connection error occurred.
            HTTPError: An HTTP error occurred.
            URLRequired: A valid URL is required to make a request.
            TooManyRedirects: Too many redirects.
            ConnectTimeout: The request timed out while trying to connect to the remote server.
            ReadTimeout: The server did not send any data in the allotted amount of time.
            Timeout: The request timed out.
            ValueError: One or more invalid arguments were passed.

        Returns:
            requests.Response: HTTP response from the server.
        """
        if method not in ["GET", "POST", "PATCH", "PUT", "DELETE"]:
            raise ValueError("Unsupported method.")

        # Request header.
        headers = {}
        if self.is_authorized:
            headers["Authorization"] = self.authorization_header
        if len(body) > 0:
            headers["Content-Type"] = "application/json"

        # Invoke request.
        return requests.request(
            method=method, url=self.base_url + resource,
            params=params, headers=headers, json=body,
            timeout=self.timeout, verify=self.verify_cert)

    def get(self, resource: str, params={}) -> requests.Response:
        """Call self.request() with GET method."""
        return self.request(
            method="GET", resource=resource, params=params)

    def post(self, resource: str, params={}, body={}) -> requests.Response:
        """Call self.request() with POST method."""
        return self.request(
            method="POST", resource=resource, params=params, body=body)

    def patch(self, resource: str, params={}, body={}) -> requests.Response:
        """Call self.request() with PATCH method."""
        return self.request(
            method="PATCH", resource=resource, params=params, body=body)

    def put(self, resource: str, params={}, body={}) -> requests.Response:
        """Call self.request() with PUT method."""
        return self.request(
            method="PUT", resource=resource, params=params, body=body)

    def delete(self, resource: str, params={}) -> requests.Response:
        """Call self.request() with DELETE method."""
        return self.request(
            method="DELETE", resource=resource, params=params)

    def authenticate(self, grant_type: str, client_id: str,
                     client_secret: str = "",
                     username: str = "", password: str = "",
                     refresh_token: str = "") -> requests.Response:
        """OAuth2.0 authentication.

        Args:
            grant_type (str): One of "client_credentials", "password", "refresh_token".
            client_id (str): API client identifier on ClearPass.
            client_secret (str): Client secret.
            username (str): Username for password grant type.
            password (str): Password for password authentication.
            refresh_token (str): Refresh token for refresh token grant type.

        Raises:
            RequestException: There was an ambiguous exception that occurred while handling your request.
            ConnectionError: A Connection error occurred.
            HTTPError: An HTTP error occurred.
            URLRequired: A valid URL is required to make a request.
            TooManyRedirects: Too many redirects.
            ConnectTimeout: The request timed out while trying to connect to the remote server.
            ReadTimeout: The server did not send any data in the allotted amount of time.
            Timeout: The request timed out.
            ValueError: One or more invalid arguments were passed.

        Returns:
            None means no error.
            requests.Response if an error has occurred.
        """
        # Request body.
        body = {"grant_type": grant_type, "client_id": client_id}
        if grant_type == "client_credentials":
            body["client_secret"] = client_secret
        elif grant_type == "password":
            body["username"] = username
            body["password"] = password
            if client_secret != "":
                body["client_secret"] = client_secret
        elif grant_type == "refresh_token":
            body["refresh_token"] = refresh_token
        else:
            raise ValueError("Unsupported grant type.")

        # Authentication request.
        rsp = self.post("/oauth", body=body)
        if rsp.status_code == 200:
            # Current time.
            self._authorized_at = time.time()
            # Decode access token and lifetime.
            json = rsp.json()
            self._access_token = json["access_token"]
            self._token_type = json["token_type"]
            self._expires_in = json["expires_in"]
            # Decode refresh token if included.
            if "refresh_token" in json:
                self._refresh_token = json["refresh_token"]
        else:
            # Error.
            return rsp