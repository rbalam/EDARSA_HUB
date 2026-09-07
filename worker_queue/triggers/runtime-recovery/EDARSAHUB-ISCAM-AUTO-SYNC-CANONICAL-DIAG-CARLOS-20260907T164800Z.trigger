job_id=EDARSAHUB-ISCAM-AUTO-SYNC-CANONICAL-DIAG-CARLOS-20260907T164800Z
requested_by=carlosruz@edarsa.com.mx
request_source=chatgpt
project=V1
production_allowed=false
base_commit=b710d4509e40c16091487dc7efd8942956ac61ce
reason=READ-ONLY DIAGNOSTIC ONLY. Confirm the actual canonical automatic sales synchronization path for Reportes ISCAM / Dashboard Ejecutivo. Do NOT enable or modify legacy inteligencia_comercial_sync, Sistema_SyncPOS_Config, Sync_Sales, Production, or any data. Verify runtime configuration and recent execution evidence for sync_comercial_v2: SCHEDULER_SYNC_COMERCIAL_V2_ENABLED, interval, scheduler registration/active state, and recent Comercial_SyncLog_v2 runs. Explain whether the canonical V2 job is automatically running and why Reportes ISCAM UI can still show only through 2026-09-05 while vw_Comercial_KPIs_Diarios_v2_Runtime already contains 2026-09-06 for ESTELAR. Return evidence only; no writes except this diagnostic trigger.