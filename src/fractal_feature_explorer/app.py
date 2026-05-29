from pathlib import Path
from streamlit.starlette import App
from fractal_feature_explorer import __version__
from ngio import __version__ as ngio_version
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from secure import Secure


async def endpoint_alive(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "alive": True,
            "version": __version__,
            "ngio_version": ngio_version,
        }
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    secure_headers: Secure

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.secure_headers = Secure.with_default_headers()

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        await self.secure_headers.set_headers_async(response)
        return response


app = App(
    Path(__file__).parent / "main.py",
    routes=[Route("/alive", endpoint_alive)],
    middleware=[Middleware(SecurityHeadersMiddleware)],
)
