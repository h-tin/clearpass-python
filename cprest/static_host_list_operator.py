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


class StaticHostListOperator(Client):

    def get_host_entries(self, name: str) -> Optional[list]:
        """Get the host entries in the Static Host List from the server.

        Args:
            name: Name of the Static Host List.

        Returns:
            List of host entries.
            None means that an error has occurred.
        """
        r = self.get(resource="/static-host-list/name/" + name)
        json = r.json()
        if json and "host_entries" in json:
            return json["host_entries"]

    def replace_host_entries(self, name: str, host_entries: list):
        """Replace the host entries in the Static Host List on the server.

        Args:
            name: Name of the Static Host List.
            host_entries: The new host entries.

        Raises:
            ValueError: One or more invalid arguments were passed.

        Returns:
            List of host entries after the replacement.
            None means that an error has occurred.
        """
        # Static Host List requires at least one host entry.
        if len(host_entries) < 1:
            raise ValueError("The host entriy is empty.")

        r = self.patch(
            resource="/static-host-list/name/" + name,
            body={"host_entries": host_entries})
        json = r.json()
        if json and "host_entries" in json:
            return json["host_entries"]
