"""CLI for the Fractal Feature Explorer."""

import sys
import runpy

from pathlib import Path

CLI_ARGS = [
    "--theme.primaryColor=#0099ff",
    "--theme.backgroundColor=#FFFFFF",
    "--theme.secondaryBackgroundColor=#F0F2F6",
    "--theme.textColor=#31333F",
    "--logger.level=info",
    '--logger.messageFormat="%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"',
    #'--server.headless=true',
    "--server.runOnSave=false",
    #'--server.enableCORS=true',
    #'--server.enableXsrfProtection=true',
    "--server.fileWatcherType=none",
    "--browser.gatherUsageStats=false",
    "--client.toolbarMode=minimal",
]


def cli():
    """Run the Fractal Feature Explorer CLI."""
    main_file = Path(__file__).parent / "main.py"
    sys.argv = ["streamlit", "run", str(main_file)] + CLI_ARGS
    runpy.run_module("streamlit", run_name="__main__")


if __name__ == "__main__":
    cli()
