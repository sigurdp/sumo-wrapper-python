import logging

import requests

from ._new_auth import NewAuth
from ._request_error import raise_request_error_exception
from .config import AGG_APP_REGISTRATION, TENANT_ID

logger = logging.getLogger("sumo.wrapper")


class SumoAggregationClient:
    def __init__(
        self,
        env: str,
        interactive: bool = False,
        verbosity: str = "CRITICAL",
    ):
        """Initialize a new Sumo Aggregation object
        Args:
            env: Sumo environment
            token: Access token or refresh token.
            interactive: Enable interactive authentication (in browser).
                If not enabled, code grant flow will be used.
            verbosity: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """

        logger.setLevel(verbosity)

        if env not in AGG_APP_REGISTRATION:
            raise ValueError(f"Invalid environment: {env}")

        self.auth = NewAuth(
            client_id=AGG_APP_REGISTRATION[env]["CLIENT_ID"],
            resource_id=AGG_APP_REGISTRATION[env]["RESOURCE_ID"],
            tenant_id=TENANT_ID,
            interactive=interactive,
            verbosity=verbosity,
        )

        if env == "localhost":
            self.base_url = (
                "https://main-sumo-surface-aggregation-service-preview"
                + ".radix.equinor.com"
            )
        else:
            self.base_url = (
                f"https://main-sumo-surface-aggregation-service-{env}"
                + ".radix.equinor.com"
            )

    def get_aggregate(self, json: dict):
        """
        Performs a POST-request to Sumo Aggregation API /fastaggregation.

        Takes json as a payload
        Args:
            json: Json payload
        Returns:
            Sumo aggregate response object
        """
        token = self.auth.get_token()

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "Content-Length": str(len(json)),
        }

        try:
            response = requests.post(
                f"{self.base_url}/fastaggregation", json=json, headers=headers
            )
        except requests.exceptions.ProxyError as err:
            raise_request_error_exception(503, err)

        if not response.ok:
            raise_request_error_exception(response.status_code, response.text)

        return response
