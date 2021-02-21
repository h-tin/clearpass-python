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


class ActiveSessionOperator(Client):

    def get_list(self, **kwargs) -> Optional[list]:
        """Get a list of active sessions.

        Keyword Args:
            filter (str): Conditions written in JSON for extracting items,
                default '{"acctstoptime":{"$exists":false}}'.
            sort (str): Sort ordering, default "-id"
            limit (int): Maximum number of sessions (1 to 1000) per request, default 1000.
            max_requests (int): Maximum number of requests, default 10.

        Raises:
            ValueError: The limit or max requests is invalid.

        Returns:
            List of active sessions.
            None means that an error has occurred.
        """
        filter = kwargs["filter"] if "filter" in kwargs else '{"acctstoptime":{"$exists":false}}'
        sort = kwargs["sort"] if "sort" in kwargs else "-id"
        limit = kwargs["limit"] if "limit" in kwargs else 1000
        max_requests = kwargs["max_requests"] if "max_requests" in kwargs else 10

        if not (1 <= limit <= 1000):
            raise ValueError("The limit is invalid.")
        if not (1 <= max_requests):
            raise ValueError("The max requests is invalid.")

        sessions = []
        for count in range(max_requests):
            rsp = self.get(
                resource="/session",
                params={
                    "filter": filter,
                    "sort": sort,
                    "offset": str(limit * count),
                    "limit": str(limit)})
            if rsp.status_code == 200:
                json = rsp.json()
                if json and "_embedded" in json and "items" in json["_embedded"]:
                    if len(json["_embedded"]["items"]) > 0:
                        sessions += json["_embedded"]["items"]
                    else:
                        # No more sessions.
                        break
                else:
                    # Bad response.
                    return None
            else:
                return None
        return sessions

    def disconnect(self, session_id: str) -> Optional[dict]:
        """Disconnect an active session.

        Args:
            session_id: Active session identifier.

        Returns:
            JSON data from the server.
            None means that an error has occurred.
        """
        rsp = self.post(
            resource="/session/" + session_id + "/disconnect",
            body={
                "id": session_id,
                "confirm_disconnect": "true"})
        if rsp.status_code == 200:
            return rsp.json()

    def reauthorize(self, session_id: str, profile: str) -> Optional[dict]:
        """Reauthorize an active session.

        Args:
            session_id: Active session identifier.
            profile: Requthorize profile.

        Returns:
            JSON data from the server.
            None means that an error has occurred.
        """
        rsp = self.post(
            resource="/session/" + session_id + "/reauthorize",
            body={
                "id": session_id,
                "confirm_reauthorize": "true",
                "reauthorize_profile": profile})
        if rsp.status_code == 200:
            return rsp.json()
