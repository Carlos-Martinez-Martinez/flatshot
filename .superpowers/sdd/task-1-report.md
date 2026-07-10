# Task 1 report — truthful export results and pause safety

## Implementation

- Added `fatal_error` to `ExportJobResult` while preserving positional compatibility.
- Made `ExportRunner` success require no cancellation, no fatal error, zero worker errors, and `processed == total`.
- Propagated fatal executor/runner failures through bridge result serialization.
- Corrected bridge aggregation to add `result.processed`, not `result.total`.
- Made CLI failures print an incomplete result and exit with code 1 instead of printing success.
- Made export pause waits condition-based when execution supplies `timeout=None`; cancellation wakes the wait.

## TDD evidence

- RED: `python -m pytest tests/test_export_runner.py::test_export_runner_reports_executor_construction_failure_as_fatal tests/test_export_runner.py::test_export_runner_cancellation_wakes_a_paused_pending_export tests/test_bridge_service.py::test_bridge_start_export_keeps_zero_processed_result_at_zero tests/test_cli.py::test_process_failure_exits_nonzero_without_success_marker -q` → `3 failed, 1 passed`; failures were false success, inflated processed count, and missing `fatal_error` contract.
- GREEN: same command → `4 passed in 0.76s`.
- Affected suite: `python -m pytest tests/test_export_runner.py tests/test_cli.py tests/test_bridge_service.py -q` → `117 passed in 4.38s`.
- Ruff focused check → `All checks passed!`.

## Files

- Modified production contracts, pause control, runner, bridge job aggregation/serialization, and CLI result handling.
- Modified focused tests for fatal executor failure, cancellation while paused, bridge processed count, and CLI exit behavior.

## Self-review

- Existing bounded `PauseToken.wait_if_paused(timeout=...)` behavior remains available for diagnostics; production export calls the unbounded condition path with cancellation.
- Existing positional `ExportJobResult` constructors remain valid because the new field is appended with a default.
- No image-processing algorithm or valid successful output path was changed.
