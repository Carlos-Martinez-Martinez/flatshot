# Roadmap

This roadmap describes direction, not delivery promises. Reliability, deterministic output, and source-image safety take priority over feature volume.

## Public v1.0 baseline

- Complete repository policy, security, CI, and release infrastructure.
- Validate the Windows portable artifact from a clean checkout.
- Perform representative manual image and export checks.
- Publish `v1.0.0` only from a reviewed `main` commit after the release checklist is signed off.

## Maintenance and quality

- Keep Python 3.10–3.13, locked dependencies, CodeQL, and regression gates healthy.
- Strengthen destination handling against concurrent filesystem changes.
- Expand reproducible visual fixtures and documented output comparisons.
- Add concise architecture decision records when a change affects public contracts.

## Portability

- Increase cross-platform core, service, and CLI coverage without weakening the Windows desktop workflow.
- Evaluate additional desktop shells only when they can reuse existing serializable service contracts.
- Document platform-specific packaging gaps before claiming support.

## UX and accessibility

- Continue compact, progressive-disclosure improvements based on real batch workflows.
- Preserve visible focus, clear status text, stable layouts, and keyboard navigation.
- Improve first-run and error recovery without hiding technical diagnostics from operators.

## Interoperability and automation

- Stabilize adapter-friendly CLI and service boundaries for external workflow tools.
- Explore import/export of presets and job summaries through documented, versioned formats.
- Consider opt-in integrations with DAM, catalog, or commerce tooling only when local file authority and privacy remain explicit.
- Use AI only for maintainer assistance such as issue triage, CI analysis, documentation, and release notes; generative AI is not a product requirement.

Requests are welcome, but new product concepts should begin with an issue and a clear user, safety, and maintenance case.
