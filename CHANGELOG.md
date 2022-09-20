# Changelog
All notable changes to this project will be documented in this file.

## [1.1.2](https://github.com/JCapriotti/dynamodb-session-flask/tree/v1.1.2) - 2022-09-20

### Fixed

* Fixed an issue in the test library where the fake session would persist across tests.

## [1.1.1](https://github.com/JCapriotti/dynamodb-session-flask/tree/v1.1.1) - 2022-09-18

### Changed

* Related to last updated, needed to add `save()` to the test session interface.
* Removed testing of two clients at the same time, 
  [no longer works in Flask 2.2.0](https://github.com/pallets/flask/issues/4761).
  Theoretically not needed, provided that `DynamoDbSession` never has state.

## [1.1.0](https://github.com/JCapriotti/dynamodb-session-flask/tree/v1.1.0) - 2022-09-09

### Changed

* Added `save()` to the session interface.

## [1.0.2](https://github.com/JCapriotti/dynamodb-session-flask/tree/v1.0.2) - 2022-05-10

### Changed

* Added `abandon()` to the test helper it doesn't attempt to access DynamoDB.

## [1.0.1](https://github.com/JCapriotti/dynamodb-session-flask/tree/v1.0.1) - 2022-05-04

### Changed

* Updated the license file; mistakenly picked the wrong one.

## [1.0.0](https://github.com/JCapriotti/dynamodb-session-flask/tree/v1.0.0) - 2022-05-03

### Breaking Change
* There was a conflict with the `new()` method and Flask's `new` attribute. 
  Renamed `new()` to `create()`.

### Fixed
* The new `new()` method was not clearing data like it should have been.

## [0.7.1](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.7.1) - 2022-04-27

### Fixed
* The new `new()` method was not clearing data like it should have been.

## [0.7.0](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.7.0) - 2022-04-27

### Added
* `abandon()` - Added to the session instance. Immediately deletes the session record.
* `new()` - Added to the session instance. Creates a new session and session ID.

### Changed
* Fixed issue related to last change, 
  the session ID was not being removed from the cookie when `clear()` was called
  and `SESSION_DYNAMODB_USE_HEADER` was `True`.

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
