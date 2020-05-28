# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Optional metadata argument for method calls [@jayrbolton](https://github.com/jayrbolton)
- Optional jsonschema parameter validation for method calls [@jayrbolton](https://github.com/jayrbolton)

### Removed
- Removed param validation in favor of using jsonschema [@jayrbolton](https://github.com/jayrbolton)
- Removed support for JSON-RPC v1.0, only supporting 1.1 and 2.0 [@jayrbolton](https://github.com/jayrbolton)

### Changed
- Converted from nose tests to pytest and add coverage tracking [@jayrbolton](https://github.com/jayrbolton)
- Get to 100% test coverage [@jayrbolton](https://github.com/jayrbolton)
- Converted dependency/publish management to poetry by [@jayrbolton](https://github.com/jayrbolton)
- Reorganized repo structure to be more standardized by [@jayrbolton](https://github.com/jayrbolton)
- Removed docker files and added `make test` command by [@jayrbolton](https://github.com/jayrbolton)
- Removed CircleCI workflow by [@jayrbolton](https://github.com/jayrbolton)
- Convert changelog.rst to CHANGELOG.md using keepachangelog.com format by [@jayrbolton](https://github.com/jayrbolton)
- Convert and update readme.rst to README.md by [@jayrbolton](https://github.com/jayrbolton)

## [0.1.2] - 2012-03-08
### Fixed
- Fixed argument validation logic when using instance methods and no arguments (mlewellyn)
