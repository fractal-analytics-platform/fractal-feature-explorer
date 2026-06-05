"""CLI for the Fractal Feature Explorer."""

import uvicorn


def cli():
    """Run the Fractal Feature Explorer CLI."""
    uvicorn.run(
        "fractal_feature_explorer.app:app",
        host="localhost",
        port=8501,
    )


if __name__ == "__main__":
    cli()
