"""Testing Placeholder for the Fractal Feature Explorer App.

TODO This is just a placeholder for the app testing. TBD what to test.

"""

import os
from streamlit.testing.v1 import AppTest


def test_app():
    """
    Basic Workflow Test for the Fractal Feature Explorer App.
    """
    config_path = "tests/configs/local.toml"
    if not os.path.exists(config_path):
        raise FileNotFoundError("Test configuration file not found.")

    os.environ["FRACTAL_FEATURE_EXPLORER_CONFIG"] = config_path

    app = AppTest.from_file("src/fractal_feature_explorer/main.py")
    app.run(timeout=15)

    assert not app.exception, "App raised an exception during execution."
