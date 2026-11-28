# Universal Worker - Generic READ_ONLY Contract V1

## Purpose
Provide a canonical generic `READ_ONLY` mode for repository certification checks without treating the request as a mutation job.

## Contract
- `mode`: exactly `READ_ONLY`.
- `actions`: exactly `[]`; omission or any action is rejected.
- Allowed checks only: `git_diff_check`, `py_compile`, `pytest`.
- `frontend_build`, `sql_readonly_audit`, mutation actions, arbitrary shell and Production remain forbidden.
- `py_compile` redirects bytecode to `/tmp`.
- `pytest` disables pytest cache and Python bytecode writes inside the repo.
- Dispatcher compares tracked repository state before and after checks and fails closed on any change.

## Terminal success
`status=READ_ONLY_COMPLETE`, `quality_gate=PASS`, `tests=PASS`, `certification=CERTIFIED_READ_ONLY`, `work_completion=COMPLETE`, `percent_complete=100`, `production_touched=false`.

This extends the existing Universal Worker contract; it does not create another executor or queue.
