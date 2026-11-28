{
  "schema": "edarsahub.runtime-recovery-trigger.v1",
  "reason": "Recover canonical Universal Worker runtime/intake for existing PRIMARY-INDUSTRIES-GATE0A-SQL-CANONICAL-DISCOVERY-20260913. Do not create a new Primary Industries job. Use authoritative /api/internal/worker/wake flow, preserve fail-closed convergence rules, consume the existing Gate0A from worker_queue/inbox, and produce its terminal result. Production must not be touched.",
  "existing_job_id": "PRIMARY-INDUSTRIES-GATE0A-SQL-CANONICAL-DISCOVERY-20260913",
  "production_touched": false
}
