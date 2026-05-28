from pathlib import Path
from streamlit.starlette import App
from fractal_feature_explorer import __version__
from ngio import __version__ as ngio_version
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware


async def endpoint_alive(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "version": __version__,
            "ngio_version": ngio_version,
        }
    )


class MockMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["mock-header-name"] = "mock-header-value"
        return response


app = App(
    Path(__file__).parent / "main.py",
    routes=[Route("/alive", endpoint_alive)],
    middleware=[Middleware(MockMiddleware)],
)
