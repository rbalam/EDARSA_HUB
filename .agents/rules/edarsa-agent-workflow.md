# EDARSA Agent Workflow

Flujo autonomo objetivo:

1. EDARSA Copilot Supervisor
   - Clasifica tarea.
   - Decide agente inicial.
   - No edita.

2. EDARSA Auditor
   - Lee codigo activo.
   - Entrega evidencia `archivo:linea`.
   - Declara `BLOQUEADO` si falta Network, SQL SELECT o evidencia.
   - No propone patch.

3. EDARSA Coder
   - Primero dry-run.
   - Solo aplica patch con evidencia y autorizacion explicita.
   - Patch minimo.
   - No commit.

4. EDARSA Validator
   - Valida diff, pruebas, RBAC, SQL, fuentes canonicas y alcance.
   - Emite `APROBADO` o `BLOQUEADO`.

5. EDARSA Committer
   - Solo actua si Validator emitio `APROBADO`.
   - Crea commit local.
   - No push.
   - No deploy.

## Handoff obligatorio

Cada agente debe terminar con:

HANDOFF:
next_agent: <nombre exacto del siguiente agente>
reason: <motivo>
mode: auto_if_available_otherwise_user_confirm

## Cadena por defecto

Supervisor -> Auditor -> Coder dry-run -> Validator pre-patch -> Coder patch -> Validator final -> Committer -> Supervisor

## Bloqueos

Cualquier agente debe detener el flujo si detecta:

- rama distinta de `Edarsahub_Desarrollo`
- placeholders `%JETSKI_CCI_*%`
- falta de `archivo:linea`
- lectura de backups como fuente activa
- falta de Network en fallos HTTP
- RBAC debilitado
- SQL destructivo
- Produccion
- secretos
