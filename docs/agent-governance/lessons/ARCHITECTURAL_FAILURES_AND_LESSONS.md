# EDARSAHUB - Architectural Failures and Lessons

## No asumir schema
Auditar sys.columns / INFORMATION_SCHEMA antes de usar columnas desconocidas.

## No source backend/.env
Nunca tratar .env como script Bash.

## No inventar imports
Buscar la implementación real antes de importar helpers/factories.

## No fallback de identidad
Identidad/autorizador no resuelto => fail-closed.

## No crear acciones sin auditar
Se propuso LIBERAR sin auditar Usuario_Acciones.
EJECUTAR ya existe y debe reutilizarse cuando corresponda.

## No perder evidencia entre sesiones
Hashes, contratos, decisiones y NEXT deben persistirse en el repo.

## No repetir auditorías después de reconexión
Leer CURRENT.md y continuar desde NEXT.

## No MongoDB paralelo
SQL EDARSAHUB es fuente canónica.

## Backend authoritative
No duplicar reglas críticas en frontend.

## No fuentes paralelas
Una única fuente canónica por dominio.

## No patches a ciegas
Error + archivo/línea + causa + evidencia antes de parchear.

## Workspace compartido
No reset/clean/stash global.

## Schema no implica runtime
Separar SCHEMA_EXISTS de RUNTIME_CONSUMER_EXISTS.

## Queue no implica worker
Comprobar consumidor, retries, locks e idempotencia.

## Estados abiertos
Un resultado desconocido nunca debe convertirse implícitamente en éxito.

## Propagar overrides Git useHttpPath en publishers
Si git credential reject borra credenciales con path y queda entrada host-only, los publishers deben propagar credential.<url>.useHttpPath=false sin tocar credenciales.

## Dos venvs Python en MCP vs Backend
Backend y Worker usan /root/.venv; edarsahub-worker-mcp y Gate2B usan /app/.runtime/worker_mcp/venv (mcp 2.x con ToolAnnotations snake_case).

## Aislamiento de stubs en pruebas de gateway MCP
Nunca mutar atributos de gateway_router sin restaurar en finally; stubs async deben reflejar Discovery V2 y scopes worker:status/worker:submit.

## Claims huerfanos queue-publisher-* bloquean worker_queue_publication
reconcile_agent_guard_orphans debe reconocer tanto prefijo worker-* como queue-publisher-* y remover solo worktrees limpios para evitar bloqueos transversales entre dominios.

## Indice en memoria invalidado por firma de directorios en resolve_go_context
resolve_go_context no debe re-parsear miles de archivos JSON en cada llamada; usar snapshot cache invalidado por mtime/conteo de directorios evita timeouts HTTP 504 en MCP multichat.

## Familia de incidentes de errores internos del conector MCP
Errores internos del conector MCP (504 timeout, 502/503 upstream, JSON-RPC -32603, protocolo) se registran sin secretos en mcp_connector_incidents.jsonl, se clasifican en la taxonomia canonica y se aislan por herramienta/dominio sin detener todo el proyecto.

## Autoconvergencia permanente del runtime sin intervencion externa
universal_job_worker.sh debe registrar HEAD:tools/mirror_sync en runtime/active_worker_code_tree_sha al iniciar, worker_control_plane.py debe auto-converger Worker/Mirror/Backend/MCP cuando el arbol de codigo cambia sin jobs activos, y edarsahub_bootstrap_watchdog.py debe incluir worker_lifecycle_recovery.py, git_divergence_guard.py, worker_repair_auto_loop.py y worker_runtime_fingerprint.py en CONTROL_PLANE_IDENTITY_PATHS.

## Indice incremental persistente en disco para cold-cache MCP
Un cache solo en memoria sigue provocando latencia alta tras reinicios de backend o MCP cuando existen miles de resultados historicos (~230 MB); persistir runtime/go_context_snapshot_index.v1.json validado por (mtime_ns, size) y evitar parsear resultados sin bounded_context reduce cold-cache en mas de 10x sin servir datos obsoletos.

## Incidente transversal: interrupcion de sesion del agente y recuperacion via checkpoints persistentes
Cuando una sesion de agente se interrumpe antes de integrar cambios preparados (por ejemplo al detenerse un intento de push directo a Edarsahub_Desarrollo), la recuperacion debe preservar el estado sin reset/stash/checkout destructivos, registrar el incidente transversal en maintenance/session_interruption_incidents.jsonl, evaluar elegibilidad fail-closed contra el checkpoint persistente y la autorizacion materializada vigente (evaluate_interrupted_objective_recovery), y entregar el cambio exclusivamente via gate_chain_publisher.submit() para ejecucion y certificacion en Universal Worker V4.

## Coordinacion multichat y handoff autonomo entre dominios sin escalacion de privilegios
Para eliminar al usuario como intermediario manual entre chats de dominios distintos sin crear infraestructura paralela ni ampliar las 6 herramientas MCP autorizadas, el registro de necesidades transversales vive como capacidad declarativa (`CROSS_DOMAIN_HANDOFF_REGISTER`) en el Capability Registry existente con persistencia canonica unica en `.git/universal-worker-queue/maintenance/handoffs/`. Una solicitud entre dominios nunca concede permisos al dominio receptor (`grants_target_permissions=False`), el desarrollo funcional nunca se traslada a Worker, toda publicacion pasa exclusivamente por `gate_chain_publisher.submit()`, y las resoluciones certificadas se devuelven automaticamente en `get_go_context` y Centro de Control (`/api/centro-control/worker-handoffs`).
