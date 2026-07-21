# FlatShot Reliability and UX Hardening Design

## Status

Approved by the implementation request that followed the read-only audit on 2026-07-10. This document converts the audit findings into an implementation scope; it does not change the product's image-processing contract.

## Goal

Make FlatShot truthful under failure, atomic at the output boundary, safe under concurrent requests, reversible in the UI, and reproducible as a distributable application while preserving valid exported image appearance and file-output behavior.

## Boundaries

The work is limited to reliability, correctness, persistence, bridge behavior, packaging, accessibility, responsive behavior, and regression coverage. It must not introduce a new image-processing algorithm, alter default visual parameters, overwrite source images, or add a runtime dependency without justification.

## Design decisions

1. **One export result contract.** `ExportJobResult` is authoritative. A job is successful only when every planned item was processed, no error or fatal error exists, and cancellation did not occur. The bridge and CLI must report `processed`, `total`, `errors`, `cancelled`, and `fatal_error` without recomputing them from another field.
2. **Atomic destination commit.** Rendered output and cache hits use the same temporary-file and exclusive-commit path. A cache hit is never copied directly over a final path.
3. **Content-addressed cache validation.** Cache entries include a stable source-content fingerprint and output metadata. Existing entries without the new fingerprint are misses and are regenerated.
4. **Condition-based pause and cancellation.** Pause waits until resume or cancellation; no arbitrary timeout may turn unfinished work into success. Active workers either commit a result that the coordinator accounts for or leave only a cleaned temporary.
5. **Mutating request safety.** Automatic retries are limited to safe reads. Job-creating operations accept an idempotency key and return the existing job for a repeated key.
6. **Draft-based local adjustments.** The selected-image editor keeps a draft snapshot. `Aplicar` commits it; `Cancelar` restores the original override. Preview may render the draft without mutating export state.
7. **Explicit resource and admission limits.** Export dimensions, pixel area, workers, active exports, and active scans are bounded before work starts. Preflight checks every destination volume that will receive output.
8. **Release isolation.** Development portable mode and distributable portable mode are separate. Release output is created in a clean staging directory without source paths, autosync, live reload, user data, or manifests from the checkout.
9. **Rendered UI verification.** Static smoke tests remain, but the workflow gains browser checks for responsive widths, focus, modal state, cancellation semantics, and export error recovery.

## Acceptance criteria

- No path can report completed when `processed != total`.
- A failing executor, prolonged pause, cancellation, cache-copy failure, or stale cache never produces a false successful export.
- A source replacement with unchanged size and mtime cannot reuse the old rendered cache.
- A cache hit cannot overwrite a destination created after preflight.
- `Cancelar` does not retain an un-applied selected-image override.
- Repeating a mutating request does not duplicate a job or OS action.
- Legacy presets migrate even when the new configuration directory already exists.
- Concurrent admission respects configured limits.
- The full suite, CSS contract, frontend static checks, browser smoke checks, and benchmark remain green.
- No valid image appearance, naming, source-file, or destination behavior changes beyond preventing corruption or false reporting.

