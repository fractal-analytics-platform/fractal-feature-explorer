# fractal-feature-explorer

[![License](https://img.shields.io/pypi/l/fractal-feature-explorer.svg?color=green)](https://github.com/fractal-analytics-platform/fractal-feature-explorer/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/fractal-feature-explorer.svg?color=green)](https://pypi.org/project/fractal-feature-explorer)
[![Python Version](https://img.shields.io/pypi/pyversions/fractal-feature-explorer.svg?color=green)](https://python.org)
[![CI](https://github.com/fractal-analytics-platform/fractal-feature-explorer/actions/workflows/ci.yml/badge.svg)](https://github.com/fractal-analytics-platform/fractal-feature-explorer/actions/workflows/ci.yml)


This is the repository that contains the **Fractal feature explorer** dashboard. Find more information about Fractal in general and the other repositories at the [Fractal home page](https://fractal-analytics-platform.github.io).


## Run the dashboard locally

Examples:

1. Via [`uvx`](https://docs.astral.sh/uv/guides/tools/#running-tools):
```bash
pipx run --spec fractal-feature-explorer explorer
```
2. Via [`pipx`](https://pipx.pypa.io/stable/):
```bash
uvx --from fractal-feature-explorer explorer
```
3. Via [`pixi`](pixi.prefix.dev):
Via `pixi`:
```bash
git clone https://github.com/fractal-analytics-platform/fractal-feature-explorer.git
cd fractal-feature-explorer
pixi run explorer
```
4. Via `venv`+`pip`:
```bash
git clone https://github.com/fractal-analytics-platform/fractal-feature-explorer.git
cd fractal-feature-explorer
python3 -m venv venv
source ./venv/bin/activate
python3 -m pip install -e .
explorer
```


## Run the dashboard on a remote server

The most common option is to create a virtual environment and install via `pip`, and then run via `uvicorn`
```bash
python3 -m venv venv

source venv/bin/activate

pip install fractal-feature-explorer

export FRACTAL_FEATURE_EXPLORER_CONFIG="config.toml"

uvicorn \
    fractal_feature_explorer.app:app\
    --no-server-header \
    --host 0.0.0.0 \
    --port 8501 \
```

Configuration-file examples:
- [config.toml](./example-config-files/remote-config.toml)
- [.streamlit/config.toml](./example-config-files/remote-streamlit-config.toml)


## Develoment

```bash
# Clone this repository
git clone https://github.com/fractal-analytics-platform/fractal-feature-explorer.git
# Install the project via pixi
pixi install
# Run the app
export FRACTAL_FEATURE_EXPLORER_CONFIG=./example-config-files/development-config.toml
pixi run uvicorn fractal_feature_explorer.app:app --host 0.0.0.0 --port 8501
```

Note that this [development-config.toml](./example-config-files/development-config.toml) simulates a production deployment and thus it requires Fractal services running locally on a given set of ports (`fractal-server` on port 8000, `fractal-web` on port 5173, `fractal-data` on port 3000).

If you do not need all of this, run via
```bash
export FRACTAL_FEATURE_EXPLORER_CONFIG=./example-config-files/local-config.toml
pixi run uvicorn fractal_feature_explorer.app:app --host 0.0.0.0 --port 8501
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

## Contributing

Releasing a new version on PyPI:

1. Create a new local tag with the format `vX.Y.Z`, where `X.Y.Z` is the new version number.

    ```bash
    git tag v0.1.8 -m "v0.1.8"
    ```

2. Push the tag to the remote repository.

    ```bash
    git push --tags
    ```


## License and contributors

The Fractal project is developed by the [BioVisionCenter](https://www.biovisioncenter.uzh.ch/en.html) at the University of Zurich, who contracts [eXact lab s.r.l.](https://www.exact-lab.it/en/) for software engineering and development support.

Unless otherwise specified, Fractal components are released under the BSD 3-Clause License, and copyright is with the BioVisionCenter at the University of Zurich.