from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_github_actions_ci_runs_core_quality_gates():
    workflow = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

    text = workflow.read_text(encoding="utf-8")

    assert "python -m pytest" in text
    assert "python -m ruff check ." in text
    assert "python scripts/audit_css.py --check" in text
    assert "python scripts/build_portable.py --skip-venv" in text
    assert "python-version: [\"3.10\", \"3.11\", \"3.12\", \"3.13\"]" in text
    assert "requirements.lock" in text


def test_local_check_script_runs_frontend_e2e_smoke():
    script = PROJECT_ROOT / "scripts" / "check_all.py"

    text = script.read_text(encoding="utf-8")

    assert "scripts/e2e_smoke.py" in text


def test_local_check_script_runs_visual_regression_smoke():
    script = PROJECT_ROOT / "scripts" / "check_all.py"

    text = script.read_text(encoding="utf-8")

    assert "scripts/visual_regression_smoke.py" in text


def test_release_checklist_documents_required_quality_gates():
    checklist = PROJECT_ROOT / "docs" / "RELEASE_CHECKLIST.md"

    text = checklist.read_text(encoding="utf-8")

    required_items = [
        "python -m pytest",
        "python -m ruff check .",
        "python scripts/audit_css.py --check",
        "python scripts/visual_regression_smoke.py",
        "python scripts/build_portable.py --skip-venv --release",
        "Exported image output changed",
    ]
    for item in required_items:
        assert item in text


def test_release_workflow_requires_fresh_runner_portable_verification_before_publish():
    text = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "portable-verification:" in text
    assert "needs: portable-verification" in text
    assert "actions/download-artifact@v8" in text
    assert "scripts/verify_portable_candidate.py" in text
    assert "FlatShot.exe --smoke" not in text  # the shared verifier owns the executable contract
    assert text.index("portable-verification:") < text.index("publish:")


def test_release_candidate_workflow_builds_and_verifies_without_publishing():
    text = (PROJECT_ROOT / ".github" / "workflows" / "release-candidate.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "pull_request:" in text
    assert "build:" in text
    assert "portable-verification:" in text
    assert "scripts/package_release_candidate.py" in text
    assert "scripts/verify_portable_candidate.py" in text
    assert "actions/upload-artifact@v7" in text
    assert "actions/download-artifact@v8" in text
    assert "gh release create" not in text
    assert "publish:" not in text
