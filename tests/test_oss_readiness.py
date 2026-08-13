from __future__ import annotations

import importlib.util
import subprocess
import sys
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_public_repository_files_are_present():
    required = {
        "LICENSE",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "GOVERNANCE.md",
        "CHANGELOG.md",
        "ROADMAP.md",
        "THIRD_PARTY_NOTICES.md",
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".github/pull_request_template.md",
        ".github/workflows/codeql.yml",
        ".github/workflows/release.yml",
        "docs/ARCHITECTURE.md",
        "docs/MAINTAINER_AUTOMATION.md",
        "docs/CODEX_FOR_OSS_APPLICATION.md",
    }

    missing = sorted(path for path in required if not (PROJECT_ROOT / path).is_file())

    assert missing == []


def test_package_metadata_declares_mit_and_public_urls():
    metadata = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert metadata["license"] == "MIT"
    assert metadata["requires-python"] == ">=3.10"
    assert metadata["urls"]["Repository"] == "https://github.com/Carlos-Martinez-Martinez/flatshot"
    assert "Programming Language :: Python :: 3.13" in metadata["classifiers"]


def test_codex_application_answers_are_within_form_limit():
    result = subprocess.run(
        [sys.executable, "scripts/check_application_answers.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "3 answers valid" in result.stdout

    draft = (PROJECT_ROOT / "docs" / "CODEX_FOR_OSS_APPLICATION.md").read_text(
        encoding="utf-8"
    )
    assert "Maintainer role" in draft
    assert "Why is this repository eligible?" in draft
    assert "How would you use API credits for your project?" in draft
    assert "Anything else we should consider?" in draft
    assert "I'm interested in" in draft
    assert "Organization ID" in draft


def test_release_version_checker_accepts_current_tree():
    spec = importlib.util.spec_from_file_location(
        "check_release_version",
        PROJECT_ROOT / "scripts" / "check_release_version.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.validate_release_version(PROJECT_ROOT, "v1.0.0") == "1.0.0"


def test_release_workflow_separates_build_from_privileged_publication():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert "permissions:\n  contents: read" in workflow
    assert "persist-credentials: false" in workflow
    assert "git merge-base --is-ancestor" in workflow
    assert "publish:" in workflow
    assert "environment: release" in workflow
    assert "contents: write" in workflow


def test_release_workflow_never_interpolates_tag_name_into_shell_source():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )

    assert workflow.count("${{ github.ref_name }}") == 1
    assert "RELEASE_TAG: ${{ github.ref_name }}" in workflow
