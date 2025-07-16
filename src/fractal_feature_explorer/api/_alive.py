"""Expose a simple API endpoint using Tornado.

Code adapted from:
https://discuss.streamlit.io/t/streamlit-restful-app/409/19

"""
from tornado.web import Application, RequestHandler
from tornado.routing import Rule, PathMatches
import gc
import streamlit as st


@st.cache_resource()
def setup_api_handler(uri, handler):
    # Get instance of Tornado
    tornado_app = next(o for o in gc.get_referrers(Application) if o.__class__ is Application)

    # Setup custom handler
    tornado_app.wildcard_router.rules.insert(0, Rule(PathMatches(uri), handler))
    
class AliveHandler(RequestHandler):
    """Handler for the /api/alive endpoint."""

    def get(self):
        from fractal_feature_explorer import __version__
        self.write({
            'alive': True,
            'version': __version__,
            })
