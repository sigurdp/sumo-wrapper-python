import requests

from .config import APP_REGISTRATION, TENANT_ID
from ._new_auth import NewAuth
from ._request_error import AuthenticationError, TransientError, PermanentError

class SumoClient:
    def __init__(
        self,
        env,
        access_token=None,
        interactive=False
    ):
        self.access_token = access_token

        if env not in APP_REGISTRATION:
            raise ValueError(f"Invalid environment: {env}")
        
        self.auth = NewAuth(
            client_id=APP_REGISTRATION[env]['CLIENT_ID'],
            resource_id=APP_REGISTRATION[env]['RESOURCE_ID'],
            tenant_id=TENANT_ID,
            interactive=interactive
        )

        if env == "localhost":
            self.base_url = f"http://localhost:8084/api/v1"
        else:
            self.base_url = f"https://main-sumo-{env}.radix.equinor.com/api/v1"

    def _retrieve_token(self):
        if self.access_token:
            return self.access_token

        return self.auth.get_token()

    def _process_params(self, params_dict):
        prefixed_params = {}

        for param_key in params_dict:
            prefixed_params[f"${param_key}"] = params_dict[param_key]

        return None if prefixed_params == {} else prefixed_params


    def get(self, path, **params):
        token = self._retrieve_token()

        headers = {
            "Content-Type": "application/json",
            "authorization": f'Bearer {token}'
        }

        response = requests.get(
            f'{self.base_url}{path}',
            params=self._process_params(params),
            headers=headers
        )

        if not response.ok:
            self._raise_request_error_exception(
                response.status_code, response.text)

        if "/blob" in path:
            return response.content

        return response.json()

    def post(self, path, blob=None, json=None):
        token = self._retrieve_token()

        if blob and json:
            raise ValueError(
                "Both blob and json given to post - can only have one at the time.")

        content_type = "application/json" if json is not None else "application/octet-stream"

        headers = {
            "Content-Type": content_type,
            "authorization": f'Bearer {token}',
            "Content-Length": str(len(json) if json else len(blob)),
        }

        try:
            response = requests.post(
                f'{self.base_url}{path}',
                data=blob,
                json=json,
                headers=headers
            )
        except requests.exceptions.ProxyError as err:
            self._raise_request_error_exception(503, err)

        if not response.ok:
            self._raise_request_error_exception(
                response.status_code, response.text)

        return response

    def put(self, path, blob=None, json=None):
        token = self._retrieve_token()

        if blob and json:
            raise ValueError(
                "Both blob and json given to post - can only have one at the time.")

        content_type = "application/json" if json is not None else "application/octet-stream"

        headers = {
            "Content-Type": content_type,
            "authorization": f'Bearer {token}',
            "Content-Length": str(len(json) if json else len(blob)),
        }

        try:
            response = requests.put(
                f'{self.base_url}{path}',
                data=blob,
                json=json,
                headers=headers
            )
        except requests.exceptions.ProxyError as err:
            self. _raise_request_error_exception(503, err)

        if not response.ok:
            self._raise_request_error_exception(
                response.status_code, response.text)

        return response

    def delete(self, path):
        token = self._retrieve_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {token}',
        }

        response = requests.delete(f'{self.base_url}{path}', headers=headers)

        if not response.ok:
            self._raise_request_error_exception(
                response.status_code, response.text)

        return response.json()

    def _raise_request_error_exception(self, code, message):
        """
        Raise the proper authentication error according to the code received from sumo.
        """

        if 503 <= code <= 504 or code == 404 or code == 500:
            raise TransientError(code, message)
        elif 401 <= code <= 403:
            raise AuthenticationError(code, message)
        else:
            raise PermanentError(code, message)
