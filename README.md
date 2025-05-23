# fractal-explorer

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
    pixi run streamlit run src/fractal_explorer/main.py
    ```

- passing cli arguments

    ```bash
    pixi run explorer -- --setup-mode Images
    ```

- Use the dev env for auto-reload

    ```bash
    pixi run -e dev explorer
    ```

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
    × Failed to load lock file from `/xxx/fractal-explorer/pixi.lock`
    ╰─▶ found newer lockfile format version 6, but only up to including version 5 is supported
    ```

    If you get an error like this you need to either update your local pixi version (`pixi self-update`) or create a new lock file with your local version of pixi. To do this, delete the `pixi.lock`, a new lock will be created when your run the dashboard again.
