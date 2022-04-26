# Changelog
All notable changes to this project will be documented in this file.

## [0.6.1](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.6.1) - 2022-04-26

### Changed
* Related to last change, we need to set the session ID in the cookie even if `SESSION_DYNAMODB_USE_HEADER` is `True`.

## [0.6.0](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.6.0) - 2022-04-25

### Changed
* If `SESSION_DYNAMODB_USE_HEADER` is `True`, also allow the session ID to be sent via cookie.

## [0.5.3](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.5.3) - 2022-04-11

### Added
* Forgot to include the `py.typed` file for mypy.

## [0.5.2](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.5.2) - 2022-04-10

### Added

* A `failed_sid` attribute on the session instance. 
  This is the hext digest of the SHA-512 hash of a session ID that failed to load. 
  Allows clients to log the failure.

## [0.5.1](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.5.1) - 2022-03-24

Main usable version.
