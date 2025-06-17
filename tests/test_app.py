"""Testing Placeholder for the Fractal Feature Explorer App.

TODO This is just a placeholder for the app testing. TBD what to test.

"""

from streamlit.testing.v1 import AppTest


def test_app():
    """
    Basic Workflow Test for the Fractal Feature Explorer App.
    """
    app = AppTest.from_file("src/fractal_feature_explorer/main.py")
    app.run(timeout=15)

    assert not app.exception, "App raised an exception during execution."
