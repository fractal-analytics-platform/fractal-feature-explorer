# Change log

## v0.1.8

- Restrict access to verified Fractal users.

## v0.1.6

- Correct PyPI metadata

## v0.1.5

- Remove cli arguments
- Reintroduce token input widget for local deployments
- Refactor local config handling
- Save default config to `~/.fractal_feature_explorer/config.toml` on first run
- Add default data service url for local deployments
- Add `explore` cli entry point for local users

## v0.1.4

- Fix name of `FRACTAL_FEATURE_EXPLORER_CONFIG` env variable.

## v0.1.1

- Add a config file to allow for fine-tuning the dashboard behavior between centralized and local deployments, see an example in `configs/`.
- config should either be passed as a CLI argument `--config path/to/config.toml`, or set as an environment variable `fractal_feature_explorer_CONFIG=path/to/config.toml`, or saved in the `~/.fractal_feature_explorer/config.toml` file.
- Add guardrails for fractal token usage, now the token is bundled in the request headers only if the url is in the `fractal_token_subdomains`.
- Fix [#28](https://github.com/fractal-analytics-platform/fractal-feature-explorer/issues/28)
- Fix [#29](https://github.com/fractal-analytics-platform/fractal-feature-explorer/issues/29)
