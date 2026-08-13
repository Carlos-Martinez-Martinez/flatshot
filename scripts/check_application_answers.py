"""Validate the bounded answers in the Codex for Open Source draft."""
from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APPLICATION_PATH = PROJECT_ROOT / "docs" / "CODEX_FOR_OSS_APPLICATION.md"
ANSWER_LIMIT = 500
ANSWER_COUNT = 3


def extract_answers(text: str) -> list[str]:
    answers = []
    for index in range(1, ANSWER_COUNT + 1):
        pattern = rf"<!-- answer-{index}-start -->\s*(.*?)\s*<!-- answer-{index}-end -->"
        match = re.search(pattern, text, flags=re.DOTALL)
        if match is None:
            raise ValueError(f"Missing answer {index} markers.")
        answers.append(" ".join(match.group(1).split()))
    return answers


def main() -> int:
    answers = extract_answers(APPLICATION_PATH.read_text(encoding="utf-8"))
    invalid = [(index, len(answer)) for index, answer in enumerate(answers, start=1) if len(answer) > ANSWER_LIMIT]
    for index, answer in enumerate(answers, start=1):
        print(f"Answer {index}: {len(answer)}/{ANSWER_LIMIT} characters")
    if invalid:
        return 1
    print(f"{len(answers)} answers valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
