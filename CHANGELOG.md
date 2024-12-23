# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2024-12-21

This release mainly revamps and completes the `bill-teams` plugin that is used for billing eLabFTW usage at the
[University of Heidelberg](https://www.uni-heidelberg.de/en). It also addresses one important issue with third-party
plugins about version Python version mismatch.

### Added

- Revamped `bill-teams` plugins with `generate-table` and `registry` commands
- Add `TXT` format support for `--format` wherever `--format` is supported

### Fixed

- Fix response format being incorrectly fallback-ing to `TXT` (GH #143)
- Fix plugins using packages that use binary builds failing (GH #145)

### Changes

- Improved how internal logic for `--export` acting as a both boolean and a string (e.g., a file path)
- A third-party plugin that uses a virtual environment must use the same Python version as elAPI's own (GH #146)

## [2.2.0] - 2024-09-04

This release brings some general bugfixes, improvements, and new library APIs.

### Added

- New sub-endpoint `/users/{id}/uploads` (GH #136)
- Better support for third-party plugins (GH #136)
- New `plugins` configuration field for plugin-specific settings (GH #136)
- Introduce `project_dir` to plugin metadata file `elapi_plugin_metadata.yml` (GH #136, 191a049)
- Aggressive logging support for `elapi.loggers.add_message`; add `change_logger_state` that controls logger class
  state (4aea161, 5a68585)
- New and improved HTTP APIs: shared client support, `SimpleClient`, `GlobalSharedSession` (GH #137)
- elAPI specific user-agent string `elAPI/<elAPI version> python-httpx/<HTTPX version>` (4bde6cd)
- Improved `BaseFormat` with `package_identifier` attribute; better plugin formatter class support (GH #138)
- Add `get_active_host_url_without_api_suffix` that compliments `get_active_host` (6e42a9c)
- Add new elAPI logo (4ca1f1f)

### Fixed

- Fix configuration not being validated when `developer_mode` is missing (GH #133)
- Fix third-party plugins breaking if they used relative imports (GH #134)

### Changed

- Disable `--OC/--override-config` support for `development_mode` (GH #136)
- All public CLI commands now use `GlobalSharedSession` (GH #137)
- Use `uvloop` instead of built-in `asyncio` event loop for `bill-teams` plugin (8c3750b); add `uvloop` as an optional
  dependency to `uhd-urz`
- Bump versions of following dependencies and optional dependencies: `rich` to `13.8.0`, `tenacity` to `9.0`,
  `python-dateutil` to `2.9.0.post0`

### Removed

- Remove `keep_session_argument` parameter from HTTP APIs, which is replaced with `shared_client` parameter (GH #137)

In collaboration with @alexander-haller.

## [2.1.0] - 2024-07-29

This release brings some general bugfix and improvements.

### Added

- Add optional CLI argument `--highlight`/`-H` (GH #129, 9986f8a)

### Fixed

- Fix optional validation causing `TypeError` for when elAPI is used inside a script (GH #126)
- Fix long JSON text not being shown (GH #128)
- Fix highlighted output breaking `jq` (GH #127)
- Fix minor bugs (GH #125)

### Changed

- Use `__aclose__` and `__acall__` for async HTTP APIs via abstract class `APIRequest` instead of `__call__`
  and `__close__` (1a88b00)
- Always validate configuration, and validate only once (GH #129, 8996143)

### Removed

- Remove CLI `--format` type option `text` (da6f511)

In collaboration with @alexander-haller.

## [2.0.2] - 2024-07-04

Hot-fix for `README.md`.

### Fixed

- `README.md` (see commits: 588d8f5, 2780e1c)

## [2.0.1] - 2024-07-04

Mainly a few hotfixes found during [FDM Münster](https://fdm-nrw.coscine.de/#/IG%20ELB%20Technische%20Aspekte) workshop.

### Added

- `INFO` message for when a plugin metadata file ending in `.yaml` extension is found (#120)

### Fixed

- Fix elAPI plugin metadata file related issues (#118, #119)
- Fix `README.md` PyPI version badge not displaying new version

## [2.0.0] - 2024-07-03

The first-iteration of our long-awaited 2.0.

### Added

- File path support for `--OC`, `--data`, `--headers`, `--query`, `--file` (#112)
- Third-party plugin support (#111)
- Third-party plugin support with virtual environments (#114)

### Fixed

- Fix printing misleading success message (#35)
- Fix `bill-teams` involving plugin issue (#51)

### Changed

- Default `timeout` is increased to `90`s (52)

## [1.0.7.dev8] - 2024-06-26

Part of an important change (making `bill-teams` plugin
optional [!53](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/53)) unfortunately did not
work as expected. We release a quick fix in this development version.

## [1.0.7.dev5] - 2024-06-25

The fourth development release was not the penultimate one before the final release. We now release the fifth
development version. This release brings lots of bug fixes, improvements, new features and architectural changes
necessary for upcoming 3rd-part plugin support.

### Added

- Refactor and restructure design pattern; current design pattern observably follows "simple layered design
  pattern" that allows proper 3rd-party plugin
  support [!55](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/55)
- New global
  option `--override-config/--OC` [!55](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/55)
- Add support for new configuration
  fields: `enable_http2`, `verify_ssl`,
  `timeout` [#55](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/55)
- Add startup callback
  function `cli_startup` [!55](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/55)
    - Validate configuration during startup
- Add `typer.Typer` overloaded
  class `elapi.plugins.commons.Typer`  [!55](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/55)
- Add singleton class `MinimalActiveConfiguration` in `elapi.configuration` that can always be used to get overloaded
  configuration values [!55](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/55)
- Make all HTTP client APIs
  configurable [!55](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/55)
- Add `generate-table` sub-command for `bill-teams` plugin

### Fixed

- Fix too many `INFO` messages [#42](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/42)
- Fix logger throwing an exception [#45](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/45)
- Fix configuration not being validated [#30](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/30)
- Fix "current" as valid endpoint ID [#49](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/49)
- Fix JSON input parser issue [#48](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/48)

### Changed

- Move raw command panel to `RAW API commands` panel
- Make `bill-teams` plugin optional. This plugin can only be installed
  with `pipx install elapi[uhd-urz]`  [!53](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/53)
- Move `api.py`, `endpoint.py` to its own package directory `api/`
- Relocate validator classes; add `validators.py` that aggregates all necessary validators to retain backward
  compatibility
- Increased default timeout to 30
  seconds [!59](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/59)
- Remove default keyword arguments (`timeout`) from HTTP clients

## [1.0.7.dev4] - 2024-06-06

Fourth development release before the next stable version. This is mainly a hot-patch release. Big thanks to
@AlexanderHaller for discovering the critical bug in due time (not the first time of course).

### Fixed

- Fix `elapi init` generating bad configuration
  file ([#37](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/37))
- Fix `--get-loc`
  for `elapi post items_types` ([#38](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/38))

## [1.0.7.dev3] - 2024-06-04

Third development release before the next stable version. This release adds a number of improvements and bug fixes.

### Added

- New `--overwrite` argument
  for `--export/-E` ([!42](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/42))
- Add `ValidationError` subclass `PathValidationError` for path related validation errors only
- Add `verbose` optional parameter to `ProperPath` class's `create`
  method for less noisy log messages ([!44](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/44))

### Fixed

- Fix `experiments` plugin not recognizing uppercase experiment `--format/-F`
  name ([#33](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/33))

### Changed

- Version numbers will follow the following format: `Major.Minor.Patch.dev<Integer>`. Previously, we were
  using `-dev<Integer>` instead of `.dev<Integer>`. `.dev<Integer>` is consistent with the versioning format
  [normalized](https://sethmlarson.dev/pep-440#delimiter-normalization) by pip (`pip show elapi`).
- elAPI only shows `An attempt to create directory <path> will be made` warning when `<path>` is a directory.

## [1.0.7-dev2] - 2024-04-15

Second development release before the next stable version. This release adds a number of improvements and bug fixes.
Mostly, this release introduces the new `bill-teams` plugin.

## [1.0.7-dev1] - 2024-03-19

Development release. This release adds a tons of new changes and improvements.

## [1.0.7] - 2024-01-26

### Added

- New `PATCH` command ([!24](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/24))
- New style
  APIs ([
  `1da3bb`](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/commit/1da3bb1a2bf6f97aea3106e628bf50ef065cf838))

### Fixed

- Add warning in `README.md` about installing elapi outside virtual
  environment ([#11](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/11))
- Fix errors not being sent to `STDERR` ([#10](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/10))
- Fixed typos in CLI documentation

### Changed

- `DEFAULT_EXPORT_DATA_FORMAT` is no longer hard-coded, and can be overloaded from `configuration` submodule

## [1.0.5] - 2023-12-07

### Added

- elAPI can be run without error when run with no arguments. I.e., running elapi will show the default help message.
- New `version` command.
- Formatter APIs (including base API `BaseFormat`) now supports multiple conventional names for formats. E.g., `yaml`
  and `yml` conventions for `YAMLFormat`.

### Fixed

- Fix timeout issue ([#7](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/7))

### Changed

- Change default export file extension from `.yaml` to `.yml` to align with eLabFTW convention
- Change `generate-invoice`'s default `bill-teams` information format from `YAML` to `JSON`

## [1.0.2] - 2023-11-16

### Fixed

- Fix installation command line ([#5](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/5)).
- Hot-fixed initial Python 3.9 compatibility
  issues ([#3](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/3), [#4](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/4)).

### Deprecated

- Passing data as arguments to `elapi post` has been deprecated due to possible incompatibility between `typer.Context`
  and
  Python 3.9.

## [1.0.0] - 2023-11-15

Initial stable release to PyPI.

### Added

- Extensible architecture with support for plugins.
- `bill-teams` plugin to generate billing data and invoice for elabFTW teams.
- Retry method for `bill-teams`.
- `show-config` plugin that gives an overview of detected configuration.
- `get` and `post` commands that send `GET` and `POST` requests respectively.
- Configuration overloading across three locations.
- Support for validation before sending requests.
- Logging to STDERR and log file.
- Prettified text to terminal.

### Fixed

- Fix all kinds of early stage bugs. Details can be found in GitLab repository.

### Deprecated

- `cleanup` command.

### Removed

- Storing temporary data in `/var/tmp/elapi`.
