from typing import Any

import requests


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
        access_token: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.access_token = access_token

    def set_token(self, access_token: str | None) -> None:
        self.access_token = access_token

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> Any:
        headers: dict[str, str] = {}
        if authenticated and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                params=params,
                json=json,
                data=data,
                headers=headers or None,
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

    def login(self, username: str, password: str) -> dict[str, Any]:
        return self.request(
            "POST",
            "/users/login",
            data={"username": username, "password": password},
            authenticated=False,
        )

    def login_google(self, id_token: str) -> dict[str, Any]:
        return self.request(
            "POST",
            "/users/google",
            json={"id_token": id_token},
            authenticated=False,
        )

    def register_user(
        self,
        *,
        nome: str,
        login: str,
        senha: str,
        id_unidade: int | None = None,
    ) -> dict[str, Any]:
        return self.request(
            "POST",
            "/users/",
            json={
                "nome": nome,
                "login": login,
                "senha": senha,
                "id_unidade": id_unidade,
            },
            authenticated=False,
        )

    def get_me(self) -> dict[str, Any]:
        return self.get("/users/me")

    def patch(self, path: str, json: dict[str, Any]) -> Any:
        return self.request("PATCH", path, json=json)

    def put(self, path: str, json: dict[str, Any]) -> Any:
        return self.request("PUT", path, json=json)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)
