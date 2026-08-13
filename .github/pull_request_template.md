## Summary

Describe the problem and the smallest coherent change that solves it.

## Validation

- [ ] Relevant tests were added or updated.
- [ ] `python scripts/check_all.py`
- [ ] `python scripts/benchmark_shadow_v2.py --smoke --runs 1` when processing is affected.
- [ ] `python scripts/build_portable.py --skip-venv --release` when packaging is affected.
- [ ] Manual checks are described below, or marked not applicable.

## Safety and compatibility

- [ ] Source images are never overwritten, moved, or deleted.
- [ ] No secrets, personal paths, generated exports, logs, caches, or local configuration are included.
- [ ] Configuration changes are backward-compatible or include a safe migration.
- [ ] New dependencies, if any, are justified for packaging, portability, licensing, security, and runtime cost.

Exported image output changed: **NO**

If **YES**, explain every expected difference in pixels, alpha, dimensions, DPI, encoding, quality, naming, or destination and attach comparison evidence.

## Manual checks and limitations

List the workflows exercised, environment used, screenshots or export comparisons, and anything not verified.
