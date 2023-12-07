# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2023-12-07

### Fixed

- Fix timeout issue ([#7](https://gitlab.urz.uni-heidelberg.de/urz-elabftw/elapi/-/issues/7))

### Added

- elAPI can be run without error when run with no arguments. I.e., running elapi will show the default help message.
- New `version` command.

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
