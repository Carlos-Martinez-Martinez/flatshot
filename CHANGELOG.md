# Changelog

All notable public changes to FlatShot will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- MIT licensing and public contribution, governance, conduct, security, architecture, and roadmap documentation.
- GitHub issue forms, pull request guidance, dependency updates, CodeQL analysis, and tag-based release automation.
- OSS-readiness checks for release versions and Codex for Open Source application answers.

### Security

- Portable desktop sessions now use per-run bridge authorization tokens.
- The local bridge rejects unapproved browser origins, requires JSON media types for request bodies, and bounds active connections with socket timeouts.
- Export source enumeration rejects symlinked PNG inputs.
- Render-cache ownership and cleanup are restricted to FlatShot-managed files.

## [1.0.0] - Unreleased

Planned first public baseline. The repository already uses version `1.0.0`; the release date will be added only when the signed-off tag is published.

[Unreleased]: https://github.com/Carlos-Martinez-Martinez/flatshot/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Carlos-Martinez-Martinez/flatshot/releases/tag/v1.0.0
