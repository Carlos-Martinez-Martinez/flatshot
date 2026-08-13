# Maintainer automation

Automation, including AI coding agents, may help maintain FlatShot when it operates under the same review and safety constraints as a human contributor.

## Principles

1. Inspect before editing. Establish repository state, relevant contracts, and the smallest safe boundary.
2. Preserve source-image immutability and exported image behavior unless a change is explicitly approved.
3. Keep business logic outside the UI and long-running work outside the UI thread.
4. Prefer focused diffs, regression tests, and reversible operations.
5. Treat paths, local files, configuration, logs, and images as potentially sensitive.
6. Never publish, merge, release, disclose a vulnerability, or change repository settings without explicit maintainer authorization.
7. Report evidence precisely; distinguish automated checks from manual visual or platform validation.

## Suggested agent workflow

- Read `AGENTS.md`, `CONTRIBUTING.md`, and relevant architecture or security documentation.
- Inspect the full affected flow and existing tests.
- Add a failing regression test for code behavior when practical.
- Make one coherent change and run proportional checks.
- Review the complete diff for secrets, personal paths, generated files, and unintended output changes.
- Leave a human-readable handoff listing files, behavior, preservation claims, tests, manual checks, limitations, and output impact.

AI-generated contributions are reviewed and owned by the submitting human. Generated text or code must not introduce material copied under incompatible terms, fabricated test results, invented project metrics, or unverified security claims.
