### Task 1: Make export results truthful and pause-safe

**Files:**
- Modify: `src/flatshot/application/export_runner.py`, `src/flatshot/application/execution_control.py`, `src/flatshot/bridge/export_jobs.py`, `src/flatshot/cli.py`
- Test: `tests/test_export_runner.py`, `tests/test_cli.py`, `tests/test_bridge_service.py`

**Interfaces:**
- `ExportRunner.run()` continues returning `ExportJobResult`.
- `ExportJobResult.success` is derived from `processed == total`, zero errors, no fatal error, and not cancelled.
- `ExecutionControl.wait_if_paused()` blocks until resume or cancellation and returns a boolean cancellation signal.

- [ ] Write a test where executor construction raises and assert `success is False`, `fatal_error` is present, and `processed == 0`.
- [ ] Write a test with pending work and a paused token whose wait expires; assert the runner does not return success until resumed or cancelled.
- [ ] Write a test for a `0/3` bridge result and assert the payload reports `processed=0`, not `3`.
- [ ] Write a CLI test for a collision/failure and assert a non-zero exit code with no success marker.
- [ ] Run the focused tests and observe the failures against the current implementation.
- [ ] Implement the smallest result invariant and condition-based pause changes.
- [ ] Run the focused tests and then `pytest tests/test_export_runner.py tests/test_cli.py tests/test_bridge_service.py`.

Global constraints: preserve valid image output, keep long work outside the UI thread, use TDD, and do not add dependencies.
