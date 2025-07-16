"""Expose a simple API endpoint using Tornado.

Code adapted from:
https://discuss.streamlit.io/t/streamlit-restful-app/409/19

"""
from tornado.web import Application, RequestHandler
from tornado.routing import Rule, PathMatches
import gc
import streamlit as st
from streamlit.logger import get_logger

logger = get_logger(__name__)


@st.cache_resource()
def setup_api_handler(uri, handler):
    # Get instance of Tornado
    applications = [o for o in gc.get_referrers(Application) if o.__class__ is Application]

    if len(applications) == 0:
        logger.warning("No Tornado application found. The API endpoint will not be set up.")
        return None
    if len(applications) > 1:
        logger.error(f"Multiple Tornado applications found: {len(applications)}")
        raise RuntimeError("Multiple Tornado applications found.")

    # Setup custom handler
    tornado_app = applications[0]
    tornado_app.wildcard_router.rules.insert(0, Rule(PathMatches(uri), handler))
    logger.info(f"API endpoint {uri} set up with handler {handler.__name__}")
    
class AliveHandler(RequestHandler):
    """Handler for the /api/alive endpoint."""

    def get(self):
        from fractal_feature_explorer import __version__
        self.write({
            'alive': True,
            'version': __version__,
            })
