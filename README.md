# fractal-feature-explorer

[![License](https://img.shields.io/pypi/l/fractal-feature-explorer.svg?color=green)](https://github.com/fractal-analytics-platform/fractal-feature-explorer/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/fractal-feature-explorer.svg?color=green)](https://pypi.org/project/fractal-feature-explorer)
[![Python Version](https://img.shields.io/pypi/pyversions/fractal-feature-explorer.svg?color=green)](https://python.org)
[![CI](https://github.com/fractal-analytics-platform/fractal-feature-explorer/actions/workflows/ci.yml/badge.svg)](https://github.com/fractal-analytics-platform/fractal-feature-explorer/actions/workflows/ci.yml)

## Installation

The easiest way to install the `fractal-feature-explorer` is to use `uv` or `pipx`:

```bash
pipx install fractal-feature-explorer
```

or

```bash
uv tool install fractal-feature-explorer
```

Alternatively, you can install it in a standart Conda/Venv using `pip`:

```bash
pip install fractal-feature-explorer
```

## Usage

You can run the dashboard using the `explorer` command:

```bash
explorer
```

at the first run, it will ask you for permission to create a configuration file in your home directory (`~/.fractal_feature_explorer/config.toml`), which will be used for future runs.

Alternatively, you can expose a configuration file using the `FRACTAL_FEATURE_EXPLORER_CONFIG` environment variable:

```bash
export FRACTAL_FEATURE_EXPLORER_CONFIG=/path/to/config.toml
explorer
```

More details on the configuration file will be availble soon.

## Local development setup

- pixi (lockfile create with pixi 0.47)
- local clone of this repo

## running the dashboard

- using pixi task

    ```bash
    pixi run -e dev explorer-dev
    ```

- from streamlit directly

    ```bash
    pixi run streamlit run src/fractal_feature_explorer/main.py
    ```

## Change log

See [CHANGELOG.md](CHANGELOG.md) for details on changes and updates.

## URL query parameters

- `setup_mode`: either `Plates` or `Images`. This will determine the setup page of the dashboard.
- `zarr_url`: the URL of the zarr file to load.
- `token`: the fractal token to use for authentication (optional).

example URL: `http://localhost:8501/?zarr_url=/Users/locerr/data/20200812-23well&?zarr_url=/Users/locerr/data/20200811-23well`

## Test data

- [Small 2D (~100Mb)](https://zenodo.org/records/13305316/files/20200812-CardiomyocyteDifferentiation14-Cycle1_mip.zarr.zip?download=1)
- [Small 2D (~100Mb) and 3D (~750Mb)](https://zenodo.org/records/13305316)
- [Large 2D (~30Gb)](https://zenodo.org/records/14826000)
- Small data on public URL: <https://raw.githubusercontent.com/tcompa/hosting-ome-zarr-on-github/refs/heads/main/20200812-CardiomyocyteDifferentiation14-Cycle1_mip.zarr>

## Main limitations

- Image preview is not available for 3D images.
- Single images not supported, only plates.

## Troubleshooting

- pixi lock file not supported by your local pixi version:

    ```bash
    $ pixi run explorer
    × Failed to load lock file from `/xxx/fractal-feature-explorer/pixi.lock`
    ╰─▶ found newer lockfile format version 6, but only up to including version 5 is supported
    ```

    If you get an error like this you need to either update your local pixi version (`pixi self-update`) or create a new lock file with your local version of pixi. To do this, delete the `pixi.lock`, a new lock will be created when your run the dashboard again.
