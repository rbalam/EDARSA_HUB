# EDARSAHUB Codex Instructions

Before making changes in this repository, read:

- `docs/EDARSAHUB_CODEX_CONTEXT.md`

Critical rules:

- Work in `Edarsahub_Desarrollo`; do not work directly in `Edarsahub_Produccion`.
- Production receives only validated changes from Desarrollo.
- Do not remove RBAC. Menu is not a permissions source; menu consumes effective RBAC permissions.
- Do not use live POS/SoftRestaurant/MPRO connections from user-facing report endpoints. Use EDARSAHUB canonical/sync tables.
- Do not invent data or create duplicate flows/modules to bypass the existing architecture.
- Use short, targeted diagnostics before code changes.
- Validate backend and frontend before commit when touched.
- For SQL/audit work, use read-only review paths; no manual productive writes unless explicitly approved.

