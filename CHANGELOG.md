# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.7.dev6] - 2024-06-26

Part of an important change (making `bill-teams` plugin
optional [!53](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/53)) in previous
version `1.0.7.dev5` unfortunately did not
work as expected. Running `pipx install "elapi[uhd-urz]==1.0.7.dev5"` did not install the optional packages defined
under `uhd-urz` in `pyproject.toml`. We rename the keyword to `uhd_urz` in this
hotfix release.

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
  fields: `enable_http2`, `verify_ssl`, `timeout` [#55](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/merge_requests/55)
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
  APIs ([`1da3bb`](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/commit/1da3bb1a2bf6f97aea3106e628bf50ef065cf838))

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
