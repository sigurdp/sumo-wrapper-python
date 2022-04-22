import atexit
import msal
import os
import sys
import json
from .config import AUTHORITY_HOST_URI

HOME_DIR = os.path.expanduser("~")

class NewAuth:
    def __init__(
        self,
        client_id,
        resource_id,
        tenant_id,
        interactive=False
    ):
        self.client_id = client_id
        self.resource_id = resource_id
        self.tenant_id = tenant_id
        self.interactive = interactive
        self.scope = self.resource_id + "/.default"

        self.token_path = os.path.join(
            HOME_DIR, ".sumo", str(self.resource_id) + ".token"
        )

        self.cache = self.__load_cache()
        self.msal = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=f"{AUTHORITY_HOST_URI}/{self.tenant_id}", 
            token_cache=self.cache
        )

        atexit.register(self.__save_cache)


    def get_token(self):
        accounts = self.msal.get_accounts()
        result = None

        if accounts:
            result = self.msal.acquire_token_silent([self.scope], account=accounts[0])

        if not result:
            if self.interactive:
                result = self.msal.acquire_token_interactive([self.scope])

                if "error" in result:
                    raise ValueError(
                        "Fail to acquire token interactively. Err: %s" % json.dumps(flow, indent=4)
                    )
            else:
                flow = self.msal.initiate_device_flow([self.scope])

                if "user_code" not in flow:
                    raise ValueError(
                        "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4)
                    )

                print(flow["message"])
                result = self.msal.acquire_token_by_device_flow(flow)

        return result["access_token"]


    def __load_cache(self):
        cache = msal.SerializableTokenCache()

        if os.path.isfile(self.token_path):
            with open(self.token_path, "r") as file:
                cache.deserialize(file.read())

        return cache

    
    def __save_cache(self):
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