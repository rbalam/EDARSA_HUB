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

## Recalibración obligatoria SQL, secretos y handoff

Reglas estrictas adicionales:

- No usar `dotenv`.
- No llamar `load_dotenv`.
- No abrir `/app/.env`.
- No abrir `/app/backend/.env`.
- No imprimir variables de entorno.
- No ejecutar `printenv`.
- No ejecutar `env`.
- No ejecutar `cat .env`.
- No probar conexiones directas con `get_sql_connection` salvo autorización explícita del usuario.
- Si se requiere SQL, pedir autorización y entregar primero un script SELECT revisable.
- SQL permitido solo `SELECT`; prohibido `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `MERGE`.
- No leer scripts sueltos de reparación/migración como `fix_*.py`, `*_sql.py`, `migration*.py` o `scripts_pendientes` salvo que el usuario los autorice explícitamente.
- No salir del alcance de archivos indicado por el usuario.

Formato HANDOFF obligatorio:

El último bloque de toda respuesta operativa debe ser exactamente:

HANDOFF:
next_agent: <EDARSA Auditor | EDARSA Coder | EDARSA Validator | EDARSA Committer | EDARSA Copilot Supervisor>
reason: <motivo concreto>
mode: auto_if_available_otherwise_user_confirm

Reglas del HANDOFF:

- No usar `NEXT AGENT` como sustituto.
- No usar `STATUS: Ready for Validator` como sustituto.
- No poner texto después del bloque `HANDOFF`.
- Si falta `HANDOFF` exacto, el siguiente Validator debe marcar `BLOQUEADO`.
