# RCA — Build failure, run 78af6e0e-4ced-4c9a-80b3-b225de2b253b (stock-tracker-990)

## Outcome
Redeploy FAILED at `build_image` (Cloud Build step #8 `frontend-build-push`). Not promoted — the previous healthy run (`123e1c01-...`) is still live. This is a **source-level dependency fault**, not a manifest/infra fault, so it must be fixed in the frontend source and re-triggered.

## Failure
Cloud Build step #8 `frontend-build-push` exited status 1 during `yarn install`:

```
error @eslint/js@10.0.1: The engine "node" is incompatible with this module.
       Expected version "^20.19.0 || ^22.13.0 || >=24". Got "20.18.1"
error Found incompatible module.
error Command failed with exit code 1.
```

The failing command is the frontend `prebuild` script (runs before `yarn build`):
`yarn validate:navigation && yarn install --frozen-lockfile --non-interactive --ignore-scripts --prefer-offline`

## Root cause
`frontend/package.json` pins **`"@eslint/js": "^10.0.1"`** (devDependencies, line 86), which resolves to `@eslint/js@10.0.1`. That version's `engines.node` is `^20.19.0 || ^22.13.0 || >=24`. The platform's frontend build image (`customer-apps-node-base:v0.3.77`) ships **node 20.18.1**, which does NOT satisfy that range, so `yarn install` aborts with a hard engine error.

The pin is also internally inconsistent: `eslint` itself is `9.23.0`, whose companion package should be `@eslint/js@9.23.0`. The `^10.0.1` was a mismatched major bump. Verified in-pod:
- `npm view @eslint/js@10.0.1 engines` → `{ node: '^20.19.0 || ^22.13.0 || >=24' }`  (incompatible with 20.18.1)
- `npm view @eslint/js@9.23.0  engines` → `{ node: '^18.18.0 || ^20.9.0 || >=21.1.0' }` (compatible with 20.18.1)
- `frontend/yarn.lock` ALREADY contains a `@eslint/js@9.23.0` resolution (pulled in transitively by `eslint@9.23.0`), so downgrading the direct dep reuses an existing, resolved version.

## Fix (apply in the source environment)
1. In `frontend/package.json`, change the devDependency:
   - from `"@eslint/js": "^10.0.1"`
   - to   `"@eslint/js": "9.23.0"`   (match `eslint@9.23.0`)
2. Regenerate the lockfile so the `frozen-lockfile` install in `prebuild` stays consistent: run `yarn install` inside `frontend/` and commit the updated `frontend/yarn.lock` (the orphaned `@eslint/js@^10.0.1` block gets pruned; the direct dep folds into the existing `@eslint/js@9.23.0` entry).
3. Re-trigger the deploy.

## Verification status
- Confirmed the exact engine mismatch and both versions' `engines.node` ranges in the eph sandbox.
- Applied the `package.json` edit (`@eslint/js` → `9.23.0`) successfully in-pod.
- Full `yarn install` lockfile regeneration could NOT be completed in the sandbox: `yarn install` was OOM-killed (exit 137) and the throwaway pod became unstable. This is a sandbox resource limit, NOT a problem with the fix. Please run the `yarn install` regeneration (step 2) in the source environment, which has adequate resources.

## Do not
- Do not retry the deploy on unchanged source — it will fail identically at step #8.
- This is not fixable via deployment manifests: the node base image version is platform-injected and must not be pinned/overridden in `config.yaml`.
