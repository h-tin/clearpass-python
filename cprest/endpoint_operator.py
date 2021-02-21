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

from typing import Optional
from cprest.client import Client


class EndpointOperator(Client):

    def get_list(self, **kwargs) -> Optional[list]:
        """Get a list of endpoints.

        Keyword Args:
            filter (str): Conditions written in JSON for extracting items, default "{}".
            limit (int): Maximum number of sessions (1 to 1000) per request, default 1000.
            max_requests (int): Maximum number of requests, default 10.

        Raises:
            ValueError: The limit or max requests is invalid.

        Returns:
            List of endpoints.
            None means that an error has occurred.
        """
        filter = kwargs["filter"] if "filter" in kwargs else "{}"
        limit = kwargs["limit"] if "limit" in kwargs else 1000
        max_requests = kwargs["max_requests"] if "max_requests" in kwargs else 10

        if not (1 <= limit <= 1000):
            raise ValueError("The limit is invalid.")
        if not (1 <= max_requests):
            raise ValueError("The max requests is invalid.")

        endpoints = []
        for count in range(max_requests):
            rsp = self.get(
                resource="/endpoint",
                params={
                    "filter": filter,
                    "offset": str(limit * count),
                    "limit": str(limit)})
            if rsp.status_code == 200:
                json = rsp.json()
                if json and "_embedded" in json and "items" in json["_embedded"]:
                    if len(json["_embedded"]["items"]) > 0:
                        endpoints += json["_embedded"]["items"]
                    else:
                        # No more endpoints.
                        break
                else:
                    # Bad response.
                    return None
            else:
                return None
        return endpoints

    def create(self, *, mac_address: str, status: str, **kwargs) -> Optional[dict]:
        """Create an endpoint.

        Args:
            mac_address: MAC address of the entpoint.
            status (str): Status of the endpoint, one of "Known", "Unknown", "Disabled".

        Keyword Args:
            description (str): Description of the endpoint.
            device_insight_tags (str): List of Device Insight Tags.
            attributes (dict): Additional attributes(key/value pairs) of the endpoint.

        Raises:
            ValueError: One or more invalid arguments were passed.

        Returns:
            The endpoint.
            None means that an error has occurred.
        """
        if status not in ["Known", "Unknown", "Disabled"]:
            raise ValueError("Unsupported status.")

        body = {"mac_address": mac_address, "status": status}
        for key in ["description", "device_insight_tags", "attributes"]:
            if key in kwargs:
                body[key] = kwargs[key]

        rsp = self.post(resource="/endpoint", body=body)
        if rsp.status_code == 201:
            return rsp.json()

    def update_fields_by_mac(self, *, mac_address: str, **kwargs) -> Optional[dict]:
        """Update fields of an endpoint.

        Args:
            mac_address: MAC address of the entpoint.

        Keyword Args:
            description (str): Description of the endpoint.
            status (str): Status of the endpoint, one of "Known", "Unknown", "Disabled".
            device_insight_tags (str): List of Device Insight Tags.
            attributes (dict): Additional attributes(key/value pairs) of the endpoint.

        Returns:
            The endpoint.
            None means that an error has occurred.
        """
        body = {}
        for key in ["description", "status", "device_insight_tags", "attributes"]:
            if key in kwargs:
                body[key] = kwargs[key]

        rsp = self.patch(
            resource="/endpoint/mac-address/" + mac_address,
            body=body)
        if rsp.status_code == 200:
            return rsp.json()
