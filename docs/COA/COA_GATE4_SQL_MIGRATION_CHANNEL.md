# COA Gate 4 - SQL Migration Channel

## Scope
Gate 4A prepares the controlled Development-only physical SQL migration channel. It does not trigger execution by itself.

## Certified inputs
- Gate 3B-R2 DDL: CERTIFIED 100%.
- Gate 3D final preflight: CERTIFIED_READ_ONLY 100% PASS.

## Execution guards
- Branch: Edarsahub_Desarrollo only.
- GitHub environment: development.
- Edarsahub_Produccion does not participate.
- Preflight and postcheck use HRLectura.
- Physical DDL requires EDARSAHUB_SQL_MIGRATION_USER / EDARSAHUB_SQL_MIGRATION_PASSWORD. HRLectura is not accepted as writer.
- Runner requires EDARSAHUB_ALLOW_MIGRATIONS=true.
- Migration is wrapped in XACT_ABORT + explicit transaction + TRY/CATCH rollback.
- Postcheck requires exactly 7 COA tables, 7 PK, 12 named IX_COA indexes, 38 FK and zero rows.
- Failed postcheck invokes rollback script automatically. Rollback refuses to drop tables if any COA table contains rows.
- Evidence artifact includes preflight, writer permission check, migration output, postcheck and rollback output when applicable.

## Trigger
Gate 4B will create `ops/migrations/requests/COA-CORE-20260909.execute` only after Gate 4A is certified. That push triggers `.github/workflows/coa-core-development-migration.yml`.

## Commission contract
No commission percentage is seeded. 6.5% is not a default or constant. COA rules remain configurable data.
