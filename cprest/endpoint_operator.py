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

    def get_list(self, filter: str = "{}", limit: int = 1000,
                 max_requests: int = 10) -> Optional[list]:
        """Get a list of endpoints.

        Args:
            filter: Conditions written in JSON for extracting items.
            limit: Maximum number of endpoints (1 to 1000) per request.
            max_requests: Maximum number of requests.

        Raises:
            ValueError: The limit or max requests is invalid.

        Returns:
            List of endpoints.
            None means that an error has occurred.
        """
        if not (1 <= limit <= 1000):
            raise ValueError("The limit is invalid.")
        if not (1 <= max_requests):
            raise ValueError("The max requests is invalid.")

        endpoints = []
        for count in range(max_requests):
            # Get endpoints up to the limit.
            r = self.get(
                resource="/endpoint",
                params={
                    "filter": filter,
                    "offset": str(limit * count),
                    "limit": str(limit)})
            # Decode endpoints.
            json = r.json()
            if json and "_embedded" in json and "items" in json["_embedded"]:
                if len(json["_embedded"]["items"]) > 0:
                    # Add endpoints to the list.
                    endpoints += json["_embedded"]["items"]
                else:
                    # No more endpoints.
                    break
            else:
                # Error.
                return None
        return endpoints
