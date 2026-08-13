# Windows Portable Runtime Design

## Problem and invariant

The `v1.0.0` Windows archive copied a conventional virtual environment. Its
`pyvenv.cfg` retained the GitHub runner's absolute Python path, so the launcher
could not resolve `pythonw.exe` on a clean machine. The fix must replace that
release mechanism without changing image processing, presets, encoders,
destinations, export execution, or source-file safety.

## Chosen approach

Release builds use PyInstaller `6.22.0` in one-folder mode. PyInstaller is a
build-only dependency; it bundles the active CPython interpreter, FlatShot,
runtime dependencies, native extensions, and the static frontend. An explicit
`scripts/portable/FlatShot.spec` controls collected data and excludes GUI
toolkits FlatShot does not use. The existing source-copy plus venv workflow
remains available only for development builds.

Alternatives rejected:

- Rewriting or deleting `pyvenv.cfg` cannot make a venv redistributable.
- The official embeddable Python distribution is viable but requires a more
  fragile custom dependency/bootstrap layer than PyInstaller.
- One-file mode adds extraction and diagnostic complexity without benefiting a
  ZIP-based portable distribution.

## Runtime boundaries

The launcher exposes two explicit roots:

- writable portable root: `Path(sys.executable).resolve().parent` when frozen,
  otherwise the launcher directory;
- bundled resource root: `Path(sys._MEIPASS).resolve()` when frozen, otherwise
  the launcher directory.

Mutable configuration, logs, and render cache live under the writable
`data/` directory. The frontend is read from the bundled resource root. Frozen
startup does not use source pointers, autosync, repository paths, or a copied
`flatshot` source tree. Non-frozen development behavior remains unchanged.

## Packaging and validation

`build_portable.py --release` invokes the spec and creates a root containing
`FlatShot.exe`, launch/diagnostic helpers, documentation, `data/`, and
PyInstaller's `_internal/` directory. A shared candidate packager creates the
versioned ZIP and `SHA256SUMS.txt`. A shared verifier rejects venv markers and
builder-path leaks in relevant text/config files, verifies the checksum,
extracts to a different path, sanitizes Python environment variables and PATH,
and executes the frozen `FlatShot.exe --smoke`.

The smoke mode configures portable paths, validates bundled resources, imports
the real bridge/core, starts frontend and bridge loopback servers, requests `/`
and `/health`, and shuts down both servers. It never opens pywebview or a
browser, processes images, or exports files.

## Release gates

The tag workflow builds and uploads a candidate, then a new Windows runner
downloads and verifies that exact archive. Publication depends on the portable
verification job. A separate manual/PR release-candidate workflow uses the same
scripts without publishing, allowing validation before `v1.0.1` is tagged.

## Version and release history

Canonical package/runtime versions become `1.0.1`. The changelog records that
`v1.0.0` remains the first historical release and that only its Windows
packaging was defective. The public `v1.0.0` release keeps its tag and assets
unchanged and carries an upfront known-issue warning. No `v1.0.1` tag, release,
or PyPI upload is created in this work.

## Verification

Unit tests cover frozen/non-frozen path resolution, smoke lifecycle, forbidden
venv entries, path-leak scanning, archive verification, and workflow ordering.
Completion also requires the full quality suite, benchmark, Python package
build, frozen build, direct and relocated frozen smokes, clean extraction
launch, repository audits, CI, CodeQL, and confirmation that exported image
output did not change.
