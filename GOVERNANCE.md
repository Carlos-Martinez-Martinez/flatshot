# Governance

FlatShot currently uses a maintainer-led governance model.

## Roles

- **Maintainer:** Carlos Martínez Martínez (`@Carlos-Martinez-Martinez`) sets direction, triages issues, reviews changes, manages releases, and makes final merge and security decisions.
- **Contributors:** anyone submitting issues, documentation, tests, design feedback, or code under the project license and policies.

## Decisions

Routine changes are decided through issue and pull request discussion. Significant changes to image output, data safety, architecture, dependencies, or public APIs should begin with an issue and include alternatives, compatibility impact, and validation evidence.

The maintainer aims for transparent, evidence-based decisions and may decline work that increases operational risk or maintenance burden. If more regular maintainers join, this document will be revised to define nomination, voting, and succession.

## Releases

The maintainer approves releases after CI, the release-version check, portable build, smoke tests, and output-sensitive review are complete. Release notes follow [CHANGELOG.md](CHANGELOG.md).
