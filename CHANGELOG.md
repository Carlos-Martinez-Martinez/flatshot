# Changelog

All notable public changes to FlatShot will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - Unreleased

### Fixed

- Replaced the non-relocatable Windows virtual environment from `v1.0.0` with
  a PyInstaller one-folder bundle that includes its own CPython runtime and
  native dependencies.
- Added a frozen `--smoke` mode, archive/path-leak validation, checksum checks,
  relocation testing, and a fresh-runner gate before GitHub release publication.
- Preserved image processing and exported image output without changes.

## [1.0.0] - 2026-08-13

### Added

- MIT licensing and public contribution, governance, conduct, security, architecture, and roadmap documentation.
- GitHub issue forms, pull request guidance, dependency updates, CodeQL analysis, and tag-based release automation.
- OSS-readiness checks for release versions and Codex for Open Source application answers.

### Security

- Portable desktop sessions now use per-run bridge authorization tokens.
- The local bridge rejects unapproved browser origins, requires JSON media types for request bodies, and bounds active connections with socket timeouts.
- Export source enumeration rejects symlinked PNG inputs.
- Render-cache ownership and cleanup are restricted to FlatShot-managed files.

FlatShot's first public release. Its published Windows portable ZIP contained a
conventional venv tied to the GitHub runner and cannot launch on a clean target
machine. The immutable tag and artifacts remain available as release history;
do not use `FlatShotPortable-v1.0.0.zip`. Version `1.0.1` replaces only the
distribution mechanism.

[1.0.1]: https://github.com/Carlos-Martinez-Martinez/flatshot/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Carlos-Martinez-Martinez/flatshot/releases/tag/v1.0.0
