# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
