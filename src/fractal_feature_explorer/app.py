from pathlib import Path
from streamlit.starlette import App
from fractal_feature_explorer import __version__
from ngio import __version__ as ngio_version
from starlette.routing import Route
from starlette.responses import Response
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from secure import Secure
from secure.headers import (
    CrossOriginOpenerPolicy,
    CrossOriginResourcePolicy,
    StrictTransportSecurity,
    PermissionsPolicy,
    ReferrerPolicy,
    Server,
    XContentTypeOptions,
    XFrameOptions,
    ContentSecurityPolicy,
)


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

        csp = (
            ContentSecurityPolicy()
            # Fallback policy: forbid what is not defined
            .default_src("'none'")
            # Control fetch requests and WebSocket connections
            .connect_src("'self'")
            # Forbid uri in <base> tag
            .base_uri("'none'")
            # Fonts
            .font_src("'self'", "https:", "data:")
            # Restrict form submissions
            .form_action("'self'")
            # Forbid frames
            .frame_ancestors("'none'")
            # Load images from self and images with src="data:image/..."
            .img_src("'self'", "data:")
            # Forbid <object> and <embed> tag
            .object_src("'none'")
            # NOTE: unsafe-eval needed to display plots - see also
            # https://github.com/plotly/dash/issues/1794
            .script_src("'self'", "'unsafe-eval'")
            # Sources for JavaScript inline event handlers
            .script_src_attr("'none'")
            # Styles (CSS) - see also
            # https://github.com/plotly/dash/issues/1794
            .style_src("'self'", "https:", "'unsafe-inline'")
        )

        self.secure_headers = Secure(
            coop=CrossOriginOpenerPolicy().same_origin(),
            corp=CrossOriginResourcePolicy().same_origin(),
            csp=csp,
            hsts=StrictTransportSecurity().max_age(31536000).include_subdomains(),
            permissions=PermissionsPolicy().geolocation().microphone().camera(),
            referrer=ReferrerPolicy().strict_origin_when_cross_origin(),
            server=Server().set(""),
            xcto=XContentTypeOptions().nosniff(),
            xfo=XFrameOptions().deny(),
        )

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        await self.secure_headers.set_headers_async(response)
        return response


app = App(
    Path(__file__).parent / "main.py",
    routes=[Route("/alive", endpoint_alive)],
    middleware=[Middleware(SecurityHeadersMiddleware)],
)
