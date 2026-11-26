import asyncio
import niquests

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

class Client:
    def __init__(self) -> None:
        self.client = niquests.AsyncSession()
        self.requests_history: list[Request] = []

    async def send(self, request: Request) -> Response:
        log.info("Envoi d'une requête", method=request.method, path=request.path)

        try: 
            response = await self.client.request(
                method=request.method,
                url=request.full_url,
                json=request.json
            )
            self.requests_history.append(request)
        except niquests.RequestException as e:
            log.error("Erreur lors de l'envoi de la requête", error=str(e))
            raise
        
        elapsed_ms = response.elapsed.total_seconds() * 1000

        log.info("Réponse reçue", status=response.status_code, http_version=response.http_version, elapsed_ms=elapsed_ms)

        return Response(
            request=request,
            body=response.text,
            status=response.status_code,
            http_version=response.http_version,
            elapsed_ms=elapsed_ms
        )

    async def close(self) -> bool:
        try:
            await self.client.close()
            log.info("Session fermée")
            return True
        except niquests.RequestException as e:
            log.error("Erreur lors de la fermeture de la session", error=str(e))
            return False

async def main() -> None:

    request = Request(
        method="GET",
        base_url="https://cert.cyber.gouv.fr",
        path="/feed/"
    )
    client = Client()
    try:
        response = await client.send(request)

        print(response.status)
        print(response.http_version)
        print(response.elapsed_ms)
        print(response.body)
    finally:
        await client.close()   


if __name__ == "__main__":
    asyncio.run(main())