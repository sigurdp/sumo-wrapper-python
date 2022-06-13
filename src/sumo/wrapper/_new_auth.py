import atexit
import msal
import os
import sys
import json
import logging
from .config import AUTHORITY_HOST_URI

HOME_DIR = os.path.expanduser("~")

logger = logging.getLogger("sumo.wrapper")


class NewAuth:
    """Sumo connection

    Establish a connection with a Sumo environment.

    Attributes:
        client_id: App registration id
        resource_id: App registration resource id
        tenant_id: AD tenant
        interactive: Enable interactive authentication (in browser)
        refresh_token: Use outside refresh token to acquire access token
        verbosity: Logging level
    """

    def __init__(
        self,
        client_id,
        resource_id,
        tenant_id,
        interactive=False,
        refresh_token=None,
        verbosity="CRITICAL",
    ):
        logger.setLevel(verbosity)

        self.interactive = interactive
        self.scope = resource_id + "/.default"
        self.refresh_token = refresh_token

        self.token_path = os.path.join(HOME_DIR, ".sumo", str(resource_id) + ".token")

        self.cache = None

        if not self.refresh_token:
            self.cache = self.__load_cache()
            atexit.register(self.__save_cache)

        self.msal = msal.PublicClientApplication(
            client_id=client_id,
            authority=f"{AUTHORITY_HOST_URI}/{tenant_id}",
            token_cache=self.cache,
        )

    def get_token(self):
        """Gets a token.

        Will first attempt to retrieve a token silently.
        If a user provided refresh token exists, attempt to aquire token by refresh token.

        If we are unable to retrieve a token silently and no refresh token has been provided by the caller,
        we either initiate a device flow or interactive flow based on the `interactive` attribute.

        Returns:
            A Json Web Token
        """

        accounts = self.msal.get_accounts()
        result = None

        if accounts:
            result = self.msal.acquire_token_silent([self.scope], account=accounts[0])

        if not result:
            if self.refresh_token:
                result = self.msal.acquire_token_by_refresh_token(
                    self.refresh_token, [self.scope]
                )

                if "error" in result:
                    raise ValueError(
                        "Failed to acquire token by refresh token. Err: %s"
                        % json.dumps(result, indent=4)
                    )
            else:
                if self.interactive:
                    result = self.msal.acquire_token_interactive([self.scope])

                    if "error" in result:
                        raise ValueError(
                            "Failed to acquire token interactively. Err: %s"
                            % json.dumps(result, indent=4)
                        )
                else:
                    flow = self.msal.initiate_device_flow([self.scope])

                    if "error" in flow:
                        raise ValueError(
                            "Failed to create device flow. Err: %s"
                            % json.dumps(flow, indent=4)
                        )

                    print(flow["message"])
                    result = self.msal.acquire_token_by_device_flow(flow)

                    if "error" in result:
                        raise ValueError(
                            "Failed to acquire token by device flow. Err: %s"
                            % json.dumps(result, indent=4)
                        )

        self.__save_cache()

        return result["access_token"]

    def __load_cache(self):
        """Load token cache from file.

        Returns:
            A msal friendly token cache object
        """

        cache = msal.SerializableTokenCache()

        if os.path.isfile(self.token_path):
            with open(self.token_path, "r") as file:
                cache.deserialize(file.read())

        return cache

    def __save_cache(self):
        """Write token cache to file."""

        if self.cache.has_state_changed:
            old_mask = os.umask(0o077)

            dir_path = os.path.dirname(self.token_path)
            os.makedirs(dir_path, exist_ok=True)

            with open(self.token_path, "w") as file:
                file.write(self.cache.serialize())

            if not sys.platform.lower().startswith("win"):
                os.chmod(self.token_path, 0o600)
                os.chmod(dir_path, 0o700)

            os.umask(old_mask)
