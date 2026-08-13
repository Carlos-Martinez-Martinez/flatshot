# Codex for Open Source application draft

These answers are prepared for the [official Codex for Open Source application](https://openai.com/form/codex-for-oss/). Recheck the live form before submitting. The three free-text answers are validated at 500 characters or fewer by `python scripts/check_application_answers.py`.

## 1. Maintainer role

Primary maintainer — creator and sole current maintainer of FlatShot.

I define the product and architecture, implement and review changes, maintain the image pipeline and desktop UI, investigate regressions, run releases, handle security reports, and support contributors.

## 2. Why is this repository eligible?

<!-- answer-1-start -->
FlatShot is an open-source, local-first desktop tool for consistent batch processing and export of product photography. It grew from a real e-commerce production workflow and combines scanning, presets, per-image review, previews, safe destination planning, progress controls, and portable packaging. It is entering public adoption with an established test suite, CI, security policy, contributor guidance, and a strict promise never to modify source images.
<!-- answer-1-end -->

## 3. How would you use API credits for your project?

<!-- answer-2-start -->
API credits would support carefully scoped maintainer automation: issue triage and duplicate detection, PR and CI-failure summaries, regression-test suggestions, documentation maintenance, release-note preparation, and security-finding triage. Product photographs would not be sent to external services by default. Every proposed code change, merge, security decision, and release would remain human-reviewed and least-privileged.
<!-- answer-2-end -->

## 4. Anything else we should consider?

<!-- answer-3-start -->
FlatShot has substantial engineering and more than 700 automated tests, but its public adoption is still at an early stage; I am not claiming users, downloads, or community scale that do not yet exist. Codex support would help one maintainer review cross-layer changes, protect filesystem and image-output invariants, improve contributor onboarding, and turn real production lessons into a dependable public tool for studios, photographers, small brands, and e-commerce teams.
<!-- answer-3-end -->

## 5. Recommended “I'm interested in...” options

- Codex Security, for evidence-based review of local bridge, filesystem, dependency, and release boundaries.
- API credits, for the human-in-the-loop maintenance uses described above.

Select only options with equivalent wording in the live form; do not infer additional program benefits.

## 6. Maintainer and organization details

- Maintainer: Carlos Martínez Martínez
- GitHub: `@Carlos-Martinez-Martinez`
- Role: creator and sole current maintainer
- Repository: `https://github.com/Carlos-Martinez-Martinez/flatshot`

To find the OpenAI Organization ID, sign in to the [OpenAI Platform organization settings](https://platform.openai.com/settings/organization/general), select the intended organization, and copy the value beginning with `org-`. Paste it directly into the application form. Do not put API keys or other credentials in this file or in Git history.

Before submission, rerun the character checker, verify the repository URL and maintainer role, and update the public-adoption wording if the release status has changed.
