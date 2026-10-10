# RCA — Deploy run 52a4c1de-ac39-4cd4-a5fa-faf6afcbf2be (stock-tracker-990)

## Summary
The redeploy failed at the **deploy_k8s** step. The new pods never became ready because the **backend crashes on boot** with:

```
ModuleNotFoundError: No module named 'tools.mirror_sync'
  from tools.mirror_sync import gate_chain_publisher
  File "/app/backend/modules/worker_ingress/service.py", line 15, in <module>
  ...
  File "/app/backend/server.py", line 16355, in <module>
    from modules.worker_ingress.routes import router as worker_ingress_router
```

nginx then shuts down ("Backend died, shutting down nginx...") and /health returns connection-refused, so readiness never passes → `deployment failed to become ready: timeout waiting for the condition`.

## Root cause (reproduced in sandbox)
This is a **source-level Python import-path bug**, not a secret/tier/manifest/infra issue.

- `backend/server.py:16355` imports `modules.worker_ingress`, whose `service.py` (lines 15–18) does:
  - `from tools.mirror_sync import gate_chain_publisher`
  - `from tools.mirror_sync.worker_job_factory import canonicalize_job`
  - `from tools.mirror_sync.worker_result_reader import read_canonical_result`
  - `from tools.mirror_sync.worker_result_status import build_job_status`
- Those modules **do exist**, but at the **repo root**: `/app/tools/mirror_sync/` (gate_chain_publisher.py, worker_job_factory.py, worker_result_reader.py, worker_result_status.py are all present).
- They are **NOT** under `/app/backend/tools/` (which contains unrelated scripts and has no `mirror_sync`).
- In production the entrypoint runs `uvicorn server:app` with working dir `/app/backend`, so `sys.path[0] = /app/backend`. `import tools` therefore resolves to `/app/backend/tools` (no `mirror_sync`) and fails. The repo-root `/app/tools` is not on `sys.path`, and `server.py` performs no `sys.path`/`PYTHONPATH` manipulation to add it.
- Additionally, neither `/app/tools/__init__.py` nor `/app/tools/mirror_sync/__init__.py` exist (relies on namespace packages).

### Proof (eph sandbox, this run's source)
- `cd /app/backend && python3 -c 'import tools.mirror_sync.gate_chain_publisher'` → `ModuleNotFoundError: No module named 'tools.mirror_sync'` (matches prod crash).
- `cd /app/backend && PYTHONPATH=/app python3 -c 'import tools.mirror_sync.gate_chain_publisher'` → **IMPORT OK**.

This is why it worked in preview (preview runs with the repo root reachable on the path via the worker/supervisor setup) but fails in the production image where uvicorn starts from `/app/backend` without repo root on the path.

## Suggested fix (Code — E1)
Pick one, in order of preference:
1. **Relocate the package** so it's importable from the backend: move `tools/mirror_sync/` → `backend/tools/mirror_sync/` and add `__init__.py` to both `backend/tools/` and `backend/tools/mirror_sync/`. Keep the import `from tools.mirror_sync import ...`.
2. **Make the path explicit in source**: at the top of `backend/server.py` (before importing `worker_ingress`), add the repo root to the path, e.g. `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`, and add the missing `__init__.py` files to `tools/` and `tools/mirror_sync/` so they import as a real package.
3. **Make the worker_ingress import lazy/optional** so a missing/misplaced `tools.mirror_sync` does not crash backend boot (guard the `include_router` behind a try/except).

After the code fix, redeploy.

## What it is NOT
- Not a missing dependency in requirements.txt (the code exists, it's a path issue).
- Not a secret/env problem, not a tier/OOM issue, not a manifest/template bug (prior runs on the same FARM template + entrypoint deployed fine; the breakage was introduced by the new `worker_ingress` module and its repo-root imports).
