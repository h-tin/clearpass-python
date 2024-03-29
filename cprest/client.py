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
from logging import getLogger
from typing import Optional, Tuple, Union

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

logger = getLogger(__name__)


class Client:
    """ClearPass RESTful API Client.

    Attributes:
        host (str): API Server hostname or IP address, default empty.
        port (int): API Server port number between 1 and 65535, default 443.
        timeout (Union[float, Tuple[float, float]]): Timeout seconds to wait for
            server connection and server response, default 30.0. Tuples set them
            different values.
        verify_cert (bool): Enable SSL certificate validation, default False.
    """

    def __init__(self, **kwargs):
        """Initializes Client.

        Args:
            **kwargs: Arbitrary keyword arguments that initialize attributes.
        """
        self.host = kwargs.get("host", "")
        self.port = kwargs.get("port", 443)
        self.timeout = kwargs.get("timeout", 30.0)
        self.verify_cert = kwargs.get("verify_cert", False)
        self._authorized_at = 0.0
        self._access_token = ""
        self._token_type = ""
        self._expires_in = 0
        self._refresh_token = ""

    @property
    def is_authorized(self) -> bool:
        """Whether the client is authorized. Expiration is not considered."""
        return True if self._access_token else False

    @property
    def authorization_header(self) -> Optional[str]:
        """Authorization header.
           None means that the client has not yet been authorized.
        """
        if self._token_type and self._access_token:
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
        """Refresh token. None means that no refresh token has been issued."""
        return self._refresh_token

    @property
    def base_url(self) -> str:
        """Base URL."""
        return "".join(["https://", self.host, ":", str(self.port), "/api"])

    def request(self, *, method: str, resource: str, **kwargs) -> requests.Response:
        """Invoke an API request.

        Args:
            method (str): HTTP method, one of "GET", "POST", "PATCH", "PUT", "DELETE".
            resource (str): Target resource.

        Keyword Args:
            params (dict): Query parameters added to the URL, default empty.
                {"key1"":"value1","key2":"value2"} -> ?key1=value1&key2=value2
            body (dict): Request body sent as JSON, default empty.

        Raises:
            RequestException: There was an ambiguous exception that occurred while
                handling your request.
            ConnectionError: A Connection error occurred.
            HTTPError: An HTTP error occurred.
            URLRequired: A valid URL is required to make a request.
            TooManyRedirects: Too many redirects.
            ConnectTimeout: The request timed out while trying to connect to the
                remote server.
            ReadTimeout: The server did not send any data in the allotted amount
                of time.
            Timeout: The request timed out.
            ValueError: One or more invalid arguments were passed.

        Returns:
            requests.Response: HTTP response from the server.
        """
        if method not in ["GET", "POST", "PATCH", "PUT", "DELETE"]:
            logger.error("The HTTP method of %s is not supported.", method)
            raise ValueError("Unsupported method.")

        # Request header.
        headers = {}
        if self.is_authorized:
            headers["Authorization"] = self.authorization_header
            logger.debug("Authorization Header: %s", self.authorization_header)
        if len(kwargs.get("body", "")) > 0:
            headers["Content-Type"] = "application/json"
            logger.debug("Content-Type: %s", "application/json")

        # Invoke request.
        return requests.request(
            method=method,
            url=self.base_url + resource,
            params=kwargs.get("params", {}),
            headers=headers,
            json=kwargs.get("body", {}),
            timeout=self.timeout,
            verify=self.verify_cert)

    def get(self, *, resource: str, **kwargs) -> requests.Response:
        """Call self.request() with GET method."""
        return self.request(method="GET", resource=resource, **kwargs)

    def post(self, *, resource: str, **kwargs) -> requests.Response:
        """Call self.request() with POST method."""
        return self.request(method="POST", resource=resource, **kwargs)

    def patch(self, *, resource: str, **kwargs) -> requests.Response:
        """Call self.request() with PATCH method."""
        return self.request(method="PATCH", resource=resource, **kwargs)

    def put(self, *, resource: str, **kwargs) -> requests.Response:
        """Call self.request() with PUT method."""
        return self.request(method="PUT", resource=resource, **kwargs)

    def delete(self, *, resource: str, **kwargs) -> requests.Response:
        """Call self.request() with DELETE method."""
        return self.request(method="DELETE", resource=resource, **kwargs)

    def authenticate(self, *, grant_type: str, client_id: str, **kwargs) -> requests.Response:
        """OAuth2.0 authentication.

        Args:
            grant_type (str): One of "client_credentials", "password", "refresh_token".
            client_id (str): API client identifier on ClearPass.

        Keyword Args:
            client_secret (str): Client secret, default empty.
            username (str): Username for password grant type, default empty.
            password (str): Password for password authentication, default empty.
            refresh_token (str): Refresh token for refresh token grant type, default empty.

        Raises:
            Same as self.request() method.

        Returns:
            None means no error.
            requests.Response if an error has occurred.
        """
        # Request body.
        body = {"grant_type": grant_type, "client_id": client_id}
        if grant_type == "client_credentials":
            body["client_secret"] = kwargs.get("client_secret", "")
        elif grant_type == "password":
            body["username"] = kwargs.get("username", "")
            body["password"] = kwargs.get("password", "")
            if "client_secret" in kwargs and kwargs["client_secret"] != "":
                body["client_secret"] = kwargs["client_secret"]
        elif grant_type == "refresh_token":
            body["refresh_token"] = kwargs.get("refresh_token", "")
        else:
            logger.error("The grant type of %s is not supported.", grant_type)
            raise ValueError("Unsupported grant type.")

        # Authentication request.
        r = self.post(resource="/oauth", body=body)
        if r.status_code == 200:
            # Current time.
            self._authorized_at = time.time()
            # Decode access token and lifetime.
            json = r.json()
            self._access_token = json["access_token"]
            self._token_type = json["token_type"]
            self._expires_in = json["expires_in"]
            logger.info(
                "The access token is valid for %s seconds.", self._expires_in)
            # Decode refresh token if included.
            if "refresh_token" in json:
                self._refresh_token = json["refresh_token"]
        else:
            # Error.
            logger.error("Authentication failure.")
            return r
