# EDARSAHUB V1.0 — Agent Operating Protocol

## Prioridad de herramientas

Prioridad operativa:
1. Antigravity
2. Codex
3. VS Code custom agents
4. Claude minimizado

No usar `.claude/agents` como fuente principal de configuración. Excepción permitida: únicamente `.claude/agents/edarsa-claude-haiku-auditor.md` como auditor Claude Haiku de solo lectura, uso excepcional y bajo autorización explícita.

## Rama y entorno

- Trabajar desde la raíz del checkout verificado mediante
  `git rev-parse --show-toplevel`.
- En Preview puede usarse `/app`. Cuando `/app` no esté disponible, se permite
  un checkout limpio en el workspace, siempre que la rama sea
  `Edarsahub_Desarrollo`, el HEAD haya sido verificado y no se realicen cambios
  remotos sin autorización explícita.
- Rama obligatoria: `Edarsahub_Desarrollo`.
- No trabajar directo en `Edarsahub_Produccion`.
- No hacer push, deploy, redeploy ni cambios remotos sin autorización explícita.
- Antes de cualquier modificación:
  - `git branch --show-current`
  - `git status --short`

## Roles obligatorios

### EDARSA Auditor

Función:
- Auditar.
- Leer código.
- Leer SQL solo con `SELECT`.
- Encontrar evidencia.
- Reportar archivos y líneas exactas.

Prohibido:
- Modificar archivos.
- Crear parches.
- Ejecutar DDL/DML.
- Crear tablas, columnas, endpoints o fuentes.
- Asumir estructura sin evidencia.

Salida mínima:
- Archivos revisados.
- Líneas exactas.
- Fuente de datos detectada.
- Riesgos.
- Recomendación sin patch.
- Scripts de validación sugeridos.

### EDARSA Coder

Función:
- Implementar cambios mínimos basados en evidencia previa.
- Modificar solo archivos necesarios.
- Mantener contratos existentes salvo autorización explícita.

Prohibido:
- Tocar producción.
- Hacer push/deploy.
- Crear tablas/columnas/migraciones sin autorización.
- Tocar backups.
- Debilitar RBAC.
- Usar mocks.
- Usar hardcodes.
- Usar MongoDB en módulos críticos.
- Crear fuentes paralelas.

Salida mínima:
- Archivos modificados.
- Diff resumido.
- Validaciones ejecutadas.
- Riesgos restantes.
- No hacer commit salvo instrucción explícita.

### EDARSA Validator

Función:
- Validar de forma independiente.
- Revisar diff.
- Ejecutar pruebas/build/checks.
- Bloquear cambios inseguros.

Prohibido:
- Implementar features.
- Modificar archivos salvo autorización explícita.
- Hacer commit/push/deploy.

Salida mínima:
- Resultado: APROBADO o BLOQUEADO.
- Evidencia.
- Validaciones ejecutadas.
- Riesgos restantes.
- Recomendación: commit, corregir o revertir.

## Base de datos

Regla general:
- Agentes solo pueden auditar con `SELECT`.
- Prohibido ejecutar:
  - `DROP`
  - `TRUNCATE`
  - `ALTER`
  - `CREATE TABLE`
  - `DELETE`
  - `UPDATE`
  - `INSERT`
  - `MERGE`
  - `EXEC`
  - `sp_`
- No imprimir secretos.
- No exponer `.env`.
- No usar credenciales de escritura para agentes.

## Comercial / Inteligencia / Ejecutivo

Reglas obligatorias:
- KPI `Ventas` = `ventas_total` con IVA.
- No usar `ventas_sin_propina`, subtotal, venta neta o venta sin IVA como venta principal.
- `cheque_promedio` = `ventas_total / tickets_total` o `ventas_total / cheques_total`.
- Consumo por persona = `ventas_total / pax_total`.
- No existe KPI válido `pax_promedio = pax / tickets`.
- Backend calcula KPIs.
- Frontend solo pinta valores del backend.

## Unidad de negocio

Fuente canónica:
- `dbo.Unidades_Negocio`.

Servicio canónico:
- `core.unidades_service.UnidadesService`.
- `core.corporate_filters.service.CorporateFilterService`.

Llave operativa:
- `unidad_negocio_pk`.

Reglas:
- `codigo` es compatibilidad/display legacy.
- `nombre` es display, no llave primaria.
- No filtrar por `unidad_negocio_nombre` como llave principal.
- No derivar filtros desde vistas runtime, ventas, KPIs, `SELECT DISTINCT` operativo ni datos del periodo.
- `ORIGEN` solo puede aparecer si existe activo en `dbo.Unidades_Negocio`.

## Fuentes prohibidas para módulos críticos

- MongoDB.
- Conexiones live para endpoints/tableros/reportes de usuario.
- Mocks.
- Hardcodes.
- Fuentes paralelas.
- Tablas duplicadas.
- Columnas duplicadas.
- Backups como fuente funcional.

## Flujo obligatorio

1. Auditor produce evidencia.
2. Usuario autoriza alcance.
3. Coder aplica patch mínimo.
4. Validator valida.
5. Usuario decide commit.
6. Deploy solo con autorización explícita.

## Validaciones mínimas

Siempre que aplique:
- `git diff --check`
- `python -m py_compile` en Python modificado
- build frontend si se tocó frontend
- revisión de `git diff --stat`
- revisión de riesgos DB/RBAC/canónico

## Regla de bloqueo

Si hay duda sobre fuente canónica, permisos, RBAC, DB o producción:
- detener
- reportar evidencia
- no modificar


## GitHub Copilot / VS Code

GitHub Copilot tambien es agente operativo dentro de VS Code.

### EDARSA Copilot Supervisor

Función:
- Coordinar Auditor, Coder y Validator.
- Mantener alcance.
- Pedir evidencia.
- Bloquear acciones inseguras.

Prohibido:
- No modificar archivos.
- No hacer patch.
- No commit.
- No push.
- No deploy.
- No SQL destructivo.

Uso recomendado:
1. Copilot Supervisor recibe la solicitud.
2. Supervisor manda a Auditor si falta evidencia.
3. Supervisor manda a Coder solo si hay autorización.
4. Supervisor manda a Validator para aprobar o bloquear.

### EDARSA Committer

Committer controlado. Solo crea commits locales despues de `EDARSA Validator` con veredicto `APROBADO`.

Reglas:

- No push.
- No deploy.
- No Produccion.
- No reset.
- No checkout destructivo.
- No SQL.
- No secretos.
- Stage solo archivos aprobados.
- Commit local con mensaje convencional.

### Flujo autonomo entre agentes

Cadena por defecto:

`Supervisor -> Auditor -> Coder dry-run -> Validator pre-patch -> Coder patch -> Validator final -> Committer -> Supervisor`

Cada agente debe emitir bloque `HANDOFF` con `next_agent`, `reason` y `mode`.
