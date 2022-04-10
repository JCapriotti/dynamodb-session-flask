# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.5.2](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.5.2) - 2022-04-10

### Added

* A `failed_sid` attribute on the session instance. 
  This is the hext digest of the SHA-512 hash of a session ID that failed to load. 
  Allows clients to log the failure.

## [0.5.1](https://github.com/JCapriotti/dynamodb-session-flask/tree/v0.5.1) - 2022-03-24

Main usable version.
