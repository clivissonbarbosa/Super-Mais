from typing import Any

import requests


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                params=params,
                json=json,
                timeout=self.timeout,
            )
        except requests.RequestException as erro:
            raise ApiError(
                "Não foi possível conectar à API. Confirme se o FastAPI está em execução."
            ) from erro

        if not response.ok:
            try:
                detalhe = response.json().get("detail", response.text)
            except ValueError:
                detalhe = response.text
            raise ApiError(f"API retornou {response.status_code}: {detalhe}")

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, json=json)

    def patch(self, path: str, json: dict[str, Any]) -> Any:
        return self.request("PATCH", path, json=json)
