import asyncio
import base64
import niquests

import json
import xmltodict

from typing import Any, Literal

import structlog

log = structlog.get_logger()

Method = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]

class Request:
    def __init__( 
            self, 
            method: Method,
            base_url: str, 
            path: str, 
            json: dict | 
            None = None
    ) -> None:
        self.method = method
        self.base_url = base_url
        self.path = path
        self.full_url = base_url + path
        self.json = json

class Response:
    def __init__(
        self,
        request: Request,
        status: int,
        http_version: int,
        elapsed_ms: float,
        body: Any
    ) -> None:
        
        self.request = request
        self.status = status
        self.http_version = http_version
        self.elapsed_ms = elapsed_ms
        self.body = body


def parse_response_body(r: niquests.Response) -> Any:
    content_type = r.headers.get("Content-Type", "")
    if "application/json" in content_type:
        return r.json()
    elif "application/xml" in content_type or "text/xml" in content_type:
        return xmltodict.parse(r.text)
    else:
        return r.text

    

class Client:
    def __init__(self, username: str, password: str) -> None:
        self.client = niquests.AsyncSession()
        self.requests_history: list[Request] = []
        self.token: str = ""
        self.username: str = username
        self.password: str = password

    def _auth_headers(self) -> dict[str, str]:
        if self.token:
            log.info("Token d'authentification trouvé, utilisation de l'authentification Bearer.")
            return {"Authorization": f"Bearer {self.token}"}
        if self.username and self.password:
            log.info("Nom d'utilisateur et mot de passe trouvés, utilisation de l'authentification Basic.")
            creds = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            return {"Authorization": f"Basic {creds}"}
        log.warning("Aucun token ou nom d'utilisateur/mot de passe trouvé, la requête sera envoyée sans authentification.")
        return {}

    async def send(self, request: Request) -> Response:
        log.info("Envoi d'une requête", method=request.method, path=request.path)

        try: 
            response = await self.client.request(
                method=request.method,
                url=request.full_url,
                json=request.json,
                headers=self._auth_headers()
            )
            self.requests_history.append(request)
        except niquests.RequestException as e:
            log.error("Erreur lors de l'envoi de la requête", error=str(e))
            raise

        elapsed_ms = response.elapsed.total_seconds() * 1000

        log.info("Réponse reçue", status=response.status_code, http_version=response.http_version, elapsed_ms=elapsed_ms)

        return Response(
            request=request,
            body=parse_response_body(response),
            status=response.status_code,
            http_version=response.http_version,
            elapsed_ms=elapsed_ms
        )

    async def login(self, base_url: str) -> None:
        response = await self.send(Request(
            method="POST",
            base_url=base_url,
            path="/auth/login",
            json={"username": self.username, "password": self.password},
        ))
        if response.status != 200:
            raise RuntimeError(f"Login échoué ({response.status}) : {response.body}")
        self.token = response.body["accessToken"]
        log.info("Login réussi, token récupéré.")

    async def close(self) -> bool:
        try:
            await self.client.close()
            log.info("Session fermée")
            return True
        except niquests.RequestException as e:
            log.error("Erreur lors de la fermeture de la session", error=str(e))
            return False

async def main() -> None:

    client = Client(
        username="emilys",
        password="emilyspass"
    )

    try:
        await client.login("https://dummyjson.com")

        response = await client.send(Request(          
            method="GET",
            base_url="https://dummyjson.com",
            path="/auth/me",
        ))

        print("Response:")
        print(f"Status: {response.status}")
        print(f"HTTP Version: {response.http_version}")
        print(f"Elapsed Time: {response.elapsed_ms} ms")
        print(f"Body: {response.body}")

    finally:
        await client.close()   


if __name__ == "__main__":
    asyncio.run(main())