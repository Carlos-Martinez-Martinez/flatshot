from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_github_actions_ci_runs_core_quality_gates():
    workflow = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

    text = workflow.read_text(encoding="utf-8")

    assert "python -m pytest" in text
    assert "python -m ruff check ." in text
    assert "python scripts/audit_css.py --check" in text
    assert "python scripts/build_portable.py --skip-venv" in text
