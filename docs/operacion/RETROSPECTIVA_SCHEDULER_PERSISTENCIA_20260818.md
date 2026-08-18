# Retrospectiva técnica — Scheduler persistent pause — 2026-08-18

## Propósito

Registrar errores, falsas hipótesis, bloqueos y correcciones encontrados durante
la implementación de pausa administrativa persistente para que futuros humanos
y agentes no repitan la misma investigación.

## Matriz de aprendizaje

| Error / riesgo observado | Causa | Regla permanente |
|---|---|---|
| `pause_job()` solo pausaba APScheduler | Estado únicamente en memoria | Toda decisión administrativa que deba sobrevivir restart necesita persistencia canónica |
| Intentar reutilizar `Sys_Scheduler_Jobs` | Confundir catálogo legacy con runtime actual | No converger tablas legacy solo para resolver estado runtime |
| Catálogo SQL con IDs sin implementación actual | Identidad histórica != job ejecutable | Antes de reutilizar catálogo, demostrar registro runtime y consumidor actual |
| Escribir tabla directamente desde Python | Acoplamiento y privilegios amplios | Usar procedimiento controlado / interfaz estrecha |
| Arrancar ignorando fallo de lectura persistente | Fallback silencioso | Startup de estado administrativo es fail-closed |
| Pausar runtime y fallar SQL dejando estados divergentes | Operaciones no coordinadas | Revertir runtime cuando falla persistencia |
| Reanudar runtime y fallar SQL | Mismo problema inverso | Reaplicar pausa runtime si persistencia de resume falla |
| Probar código nuevo con backend viejo | Proceso inició antes del mtime de archivos | Comparar proceso vs archivos y reiniciar controladamente antes de E2E |
| Intentar pausar un job mientras estaba ejecutándose | Lock activo | Auditar lock y esperar a que termine antes de pruebas administrativas |
| Interpretar 404 sin auditar rutas | Endpoint supuesto | Localizar ruta real antes de probar |
| Interpretar 401 como fallo de endpoint | Ruta correcta pero protegida | Separar routing de autenticación/RBAC |
| Pedir password repetidamente | Validación HTTP usada para todo | No pedir password para diagnósticos que puedan resolverse server-side |
| Ejecutar pytest desde `/app` | `tests` resolvía mal | Usar rootdir canónico `/app/backend` cuando corresponda |
| Test `assert "mongo" not in text.lower()` | Assert textual demasiado amplio | Probar imports, llamadas y contratos; comentarios no son dependencias |
| Test `assert "Sys_Scheduler_Jobs" not in text` | Comentario legítimo causó falso positivo | Evitar asserts de substrings no semánticos |
| Worktree limpio sin `.env` | El archivo no pertenece al checkout | Cargar configuración canónica en memoria; nunca copiar secretos al worktree |
| Regresión dependía de tests untracked | Working tree contaminaba la percepción | Validar commit en worktree limpio y ejecutar solo tests realmente pertenecientes al árbol |
| `git add` falló por `index.lock` antiguo | Lock huérfano + procesos lectores `git status` | Auditar owner con lsof/fuser y distinguir Git lector de Git mutante |
| Índice ya tenía cambios de otros frentes | Workspace compartido | Nunca `git reset` global ni `git add .`; preservar blobs staged ajenos |
| Commit desde `/app` bloqueado por logs | Outputs reproducibles en raíz persistente | Outputs temporales van a `/tmp/edarsahub-agents/<agent>/outputs/` |
| Commit desde worktree manual | Agent Guard no lo conocía | Usar worktree oficial registrado y claim |
| Worktree agente después de release | Agente sin claim no puede operar | Claim durante trabajo; release al integrar |
| Push desde `/app` | Storage guard inspecciona filesystem local | Publicar desde integrator limpio registrado cuando main contiene basura ajena |
| Intentar resolver hooks con `--no-verify` | Tentación de bypass | Prohibido; corregir entorno, no desactivar controles |
| Asumir remote HEAD | Riesgo de pisar trabajo concurrente | `ls-remote` inmediatamente antes del push |
| Push genérico | Puede publicar más de lo previsto | Publicar ref/commit exactos y validar remote después |
| Confundir palabra Mongo con dependencia Mongo | Grep sin clasificación | Clasificar import runtime, stub, comentario, test y documentación |
| Reauditar referencias ya clasificadas | Falta de memoria técnica | Mantener documento de referencias no-runtime con condiciones explícitas de reapertura |

## Regla de diagnóstico

Nunca adivinar.

Orden obligatorio:

1. evidencia exacta;
2. archivo / línea / proceso / tabla;
3. causa;
4. cambio mínimo;
5. validación;
6. rollback o reversibilidad;
7. integración aislada.

## Git y worktrees

El workspace principal puede contener trabajo de múltiples frentes.

Por lo tanto:

- preservar index ajeno;
- no usar reset global;
- no usar stash global;
- no borrar worktrees ajenos;
- no matar procesos Git por nombre sin saber si son lectores o mutantes;
- usar Agent Guard;
- usar claims;
- liberar claims al finalizar;
- retirar worktrees solo cuando estén limpios e integrados;
- no usar `--no-verify`.

## Outputs y reportes

La práctica histórica de generar `.txt` de auditoría en `/app` queda sustituida
por la política de almacenamiento vigente.

Usar:

`/tmp/edarsahub-agents/<agent>/outputs/`

No crear nuevos dumps, auditorías, logs ni reportes reproducibles en la raíz
persistente del repositorio.

## Criterio de cierre

Un frente no está cerrado solo porque el unit test pase.

Para este tipo de cambio se requirió:

- contrato;
- tests;
- SQL;
- E2E real;
- restart real;
- regresión;
- commit limpio;
- hooks;
- integración;
- push;
- verificación del remoto;
- housekeeping;
- documentación.
