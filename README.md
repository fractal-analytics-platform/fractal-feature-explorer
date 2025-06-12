# fractal-feature-explorer

## Setup

- pixi (lockfile create with pixi 0.47)
- local clone of the ngio dev branch
- local clone of this repo
- make sure that the ngio relative path is correct in the pyproject.toml file

## running the dashboard

- using pixi task

  ```bash
  pixi run explorer
  ```

- from streamlit directly

    ```bash
    pixi run streamlit run src/fractal_feature_explorer/main.py
    ```

- passing cli arguments

    ```bash
    pixi run explorer -- --setup-mode Images
    ```

- Use the dev env for auto-reload

    ```bash
    pixi run -e dev explorer
    ```

## Change log
### v0.1.4

- Fix name of `FRACTAL_FEATURE_EXPLORER_CONFIG` env variable.

### v0.1.1

- Add a config file to allow for fine-tuning the dashboard behavior between centralized and local deployments, see an example in `configs/`.
- config should either be passed as a CLI argument `--config path/to/config.toml`, or set as an environment variable `fractal_feature_explorer_CONFIG=path/to/config.toml`, or saved in the `~/.fractal_feature_explorer/config.toml` file.
- Add guardrails for fractal token usage, now the token is bundled in the request headers only if the url is in the `fractal_token_subdomains`.
- Fix [#28](https://github.com/fractal-analytics-platform/fractal-feature-explorer/issues/28)
- Fix [#29](https://github.com/fractal-analytics-platform/fractal-feature-explorer/issues/29)

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
