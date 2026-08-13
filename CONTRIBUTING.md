# Contributing to FlatShot

Thank you for helping improve FlatShot. The project favors small, testable changes that preserve production reliability and exported image behavior.

## Before you start

- Search existing issues and discussions before proposing substantial work.
- Open an issue for changes to image processing, export behavior, configuration schemas, or architecture.
- Never include source product images, customer data, credentials, local configuration, generated exports, logs, or caches.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md) and security reporting process in [SECURITY.md](SECURITY.md).

## Development setup

Use Python 3.10 or newer and follow the source setup in the [README](README.md). Create a branch from `main`; keep commits focused and explain why the change is needed.

## Engineering expectations

- Preserve the separation `UI -> services -> core -> persistence/filesystem`.
- Keep heavy work off the UI thread.
- Do not overwrite, move, or delete source images.
- Do not add dependencies without documenting the need, packaging and cross-platform impact, license, security risk, and runtime cost.
- Avoid broad rewrites when a focused extraction or fix is enough.
- Add regression tests before fixing a bug when practical.
- If export code changes, state whether pixels, dimensions, DPI, alpha, formats, quality, naming, or destinations can differ.

## Validation

Before opening a pull request, run:

```bash
python scripts/check_all.py
python scripts/benchmark_shadow_v2.py --smoke --runs 1
python scripts/build_portable.py --skip-venv --release
```

For UI changes, launch the app and manually exercise the affected workflow. For output-sensitive changes, compare representative exports and describe the evidence in the pull request.

## Pull requests

Complete the pull request template, link related issues, include screenshots for visible UI changes, and keep generated artifacts out of Git. A maintainer may ask for a smaller scope or stronger evidence before merging.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
