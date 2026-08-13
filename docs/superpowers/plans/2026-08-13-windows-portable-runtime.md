# Windows Portable Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce and verify a relocatable Windows one-folder FlatShot portable candidate for version 1.0.1 without changing image output or publishing the release.

**Architecture:** Keep the existing source-copy/venv development portable intact, but route release builds through an explicit PyInstaller spec. The frozen launcher separates writable portable data from bundled resources, while shared candidate and verification scripts enforce checksum, archive-content, environment-isolation, and executable-smoke contracts locally and in fresh GitHub runners.

**Tech Stack:** Python 3.10+, PyInstaller 6.22.0, pywebview 6.2.1, PowerShell/GitHub Actions, pytest.

## Global Constraints

- Do not move, delete, recreate, replace, force, or retag `v1.0.0`.
- Do not publish `v1.0.1` or PyPI and do not merge PR #5 or PR #6.
- Release portable is Windows-only, PyInstaller one-folder, and contains no venv, `pyvenv.cfg`, source pointer, development flags, or builder paths.
- Development portable retains local venv/autosync behavior.
- Mutable data is under the executable directory; bundled resources are read-only.
- `FlatShot.exe --smoke` must exercise the real frontend and bridge without GUI or image export.
- Exported image output must remain unchanged.

---

### Task 1: Define frozen launcher paths and smoke lifecycle

**Files:**
- Modify: `scripts/portable/FlatShot.pyw`
- Test: `tests/test_portable_launcher.py`

**Interfaces:**
- Produces: `portable_root() -> Path`, `resource_root() -> Path`, `run_smoke() -> None`, and `main(argv: list[str] | None = None) -> int`.
- Preserves: non-frozen source autosync and GUI launch.

- [ ] **Step 1: Add failing tests for path boundaries**

```python
def test_frozen_roots_separate_writable_executable_and_bundled_resources(monkeypatch, tmp_path):
    launcher = load_launcher()
    monkeypatch.setattr(launcher.sys, "frozen", True, raising=False)
    monkeypatch.setattr(launcher.sys, "executable", str(tmp_path / "portable" / "FlatShot.exe"))
    monkeypatch.setattr(launcher.sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    assert launcher.portable_root() == (tmp_path / "portable").resolve()
    assert launcher.resource_root() == (tmp_path / "bundle").resolve()
```

- [ ] **Step 2: Run the path tests and confirm missing helpers fail**

Run: `python -m pytest tests/test_portable_launcher.py -q`

- [ ] **Step 3: Implement root helpers and derive all mutable/resource paths from them**

```python
def portable_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent
```

- [ ] **Step 4: Add a failing lifecycle test proving smoke starts, checks, and stops both real server wrappers without opening GUI**

- [ ] **Step 5: Implement `--smoke`, explicit HTTP status checks, useful logging, and guaranteed shutdown**

- [ ] **Step 6: Run launcher tests and commit**

Run: `python -m pytest tests/test_portable_launcher.py -q`

### Task 2: Split development and frozen release builders

**Files:**
- Create: `scripts/portable/FlatShot.spec`
- Modify: `scripts/build_portable.py`
- Modify: `scripts/portable/manifest.py`
- Modify: `requirements-dev.txt`
- Test: `tests/test_build_portable.py`

**Interfaces:**
- Produces: `build_development_portable(...)`, `build_release_portable(...)`, and `validate_release_portable(root: Path, forbidden_roots=())`.
- Release output contract: `FlatShot.exe`, `_internal/`, `data/`, `Abrir FlatShot.vbs`, `Diagnostico FlatShot.bat`, `README_PORTABLE.txt`.

- [ ] **Step 1: Add failing release-layout and forbidden-marker tests**

```python
@pytest.mark.parametrize("entry", ["pyvenv.cfg", "venv/Scripts/python.exe", "venv/Scripts/pythonw.exe"])
def test_release_validation_rejects_venv_entries(tmp_path, entry):
    (tmp_path / entry).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / entry).write_text("bad", encoding="utf-8")
    with pytest.raises(RuntimeError, match="non-relocatable"):
        build_portable.validate_release_portable(tmp_path)
```

- [ ] **Step 2: Run tests and confirm the release contracts fail**

- [ ] **Step 3: Implement an explicit one-folder spec with frontend data and focused GUI exclusions**

```python
a = Analysis(
    [str(project_root / "scripts" / "portable" / "FlatShot.pyw")],
    pathex=[str(project_root / "src"), str(project_root / "scripts" / "portable")],
    datas=[(str(project_root / "apps" / "flatshot-desktop" / "frontend"), "frontend")],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "gtk"],
)
```

- [ ] **Step 4: Route only `--release` through PyInstaller 6.22.0 and generate executable launchers**

- [ ] **Step 5: Validate text/config files for CI and checkout path leaks without scanning arbitrary binaries**

- [ ] **Step 6: Run builder tests and commit**

### Task 3: Create one candidate packager and one relocatability verifier

**Files:**
- Create: `scripts/package_release_candidate.py`
- Create: `scripts/verify_portable_candidate.py`
- Test: `tests/test_portable_candidate.py`

**Interfaces:**
- Produces: deterministic archive naming `FlatShotPortable-v<version>.zip`, `SHA256SUMS.txt`, `verify_candidate(...)`, and sanitized executable invocation.

- [ ] **Step 1: Add failing tests for checksum mismatch, archive layout, forbidden files, path leaks, and sanitized environment**
- [ ] **Step 2: Run candidate tests and confirm expected failures**
- [ ] **Step 3: Implement ZIP/checksum creation using the release builder output**
- [ ] **Step 4: Implement extraction to a supplied path and run only `<extracted>/FlatShotPortable/FlatShot.exe --smoke`**

```python
env = os.environ.copy()
for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
    env.pop(name, None)
env["PATH"] = os.pathsep.join(essential_windows_paths())
```

- [ ] **Step 5: Run candidate tests and commit**

### Task 4: Add fresh-runner publication gates

**Files:**
- Modify: `.github/workflows/release.yml`
- Create: `.github/workflows/release-candidate.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `tests/test_ci_config.py`

**Interfaces:**
- Release sequence: `build -> portable-verification -> publish`.
- Candidate workflow: build/upload and new-runner download/verification, never publish.

- [ ] **Step 1: Add failing workflow-contract tests for separate jobs, artifact download, checksum verification, frozen smoke, and `publish.needs`**
- [ ] **Step 2: Run CI config tests and confirm failures**
- [ ] **Step 3: Update Release to upload candidate and require a new Windows verification runner before publish**
- [ ] **Step 4: Add PR/manual Release Candidate workflow using the same Python scripts**
- [ ] **Step 5: Replace CI's false venv-free build smoke with focused non-release checks**
- [ ] **Step 6: Parse YAML, run CI config tests, and commit**

### Task 5: Version and distribution documentation

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/flatshot/__init__.py`
- Modify: `tests/test_oss_readiness.py`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `apps/flatshot-desktop/README.md`
- Modify: `docs/RELEASE_CHECKLIST.md`
- Modify: `THIRD_PARTY_NOTICES.md`
- Modify: `.github/pull_request_template.md`

**Interfaces:**
- Canonical version: `1.0.1`; intended tag: `v1.0.1`.

- [ ] **Step 1: Update version expectation test first and confirm it fails**
- [ ] **Step 2: Update both canonical versions to 1.0.1**
- [ ] **Step 3: Record v1.0.0 packaging defect and v1.0.1 frozen-runtime fix with no image-output change**
- [ ] **Step 4: Document development versus release builds, candidate generation, smoke, relocation, and pre-tag gates**
- [ ] **Step 5: Record CPython, PyInstaller, pywebview, Python.NET, and bundled license obligations without changing FlatShot's MIT license**
- [ ] **Step 6: Run version, markdown-link, metadata, and documentation checks; commit**

### Task 6: Build, relocate, launch, and publish the PR

**Files:**
- Generated only: `release/`, `dist/`, temporary extraction paths (all ignored)

**Interfaces:**
- Produces: a downloadable PR release-candidate artifact and evidence, not a release.

- [ ] **Step 1: Run `python scripts/check_all.py` and benchmark smoke**
- [ ] **Step 2: Run `python -m build` and `python scripts/package_release_candidate.py --version 1.0.1`**
- [ ] **Step 3: Verify ZIP checksum, contents, path scan, and frozen smoke**
- [ ] **Step 4: Extract to a separate Unicode path with spaces, sanitize Python variables/PATH, and run `FlatShot.exe --smoke`**
- [ ] **Step 5: Launch `Abrir FlatShot.vbs`, verify the window, and close cleanly without image processing**
- [ ] **Step 6: Run `git diff --check`, YAML, Markdown links, credential, personal-path, CODEOWNERS, metadata, and security scans**
- [ ] **Step 7: Commit remaining changes, push `fix/windows-portable-runtime`, and open a ready PR to `main` without merging**
- [ ] **Step 8: Monitor CI, Release Candidate fresh-runner verification, and both CodeQL languages to completion**
- [ ] **Step 9: Re-audit tags, releases, alerts, PR #5/#6, and confirm no `v1.0.1` tag/release exists**
