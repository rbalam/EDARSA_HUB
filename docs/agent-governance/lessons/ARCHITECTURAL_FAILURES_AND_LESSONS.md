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
