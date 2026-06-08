# P1B — Sync POS Canónico Configurable (implementación corregida)

**Fecha:** 2026-06-08
**Autor:** Agente E1 (continuación). Implementación MANUAL corregida tras auditar el script `.sh` del usuario.

## Objetivo
Eliminar el hardcode `UNIDADES_CONFIG` del job de Inteligencia Comercial y migrar a fuente
canónica SQL (`dbo.Unidades_Negocio` + `dbo.Servidores_Conexiones`), con sincronización
automática **controlada por SQL** y en **modo seguro por defecto** (no conecta al POS).

## Por qué NO se ejecutó el `.sh` del usuario (dictamen de auditoría)
| # | Bloqueante | Detalle | Estado en versión corregida |
|---|-----------|---------|------------------------------|
| A | NameError `tipo_ejecucion` (CRÍTICO) | El patch buscaba la firma vieja (`sig_old` sin `dry_run`), ya modificada en sesión previa → no agregaba el parámetro pero sí insertaba el gate que lo usa. `py_compile` no lo detecta. Rompía el cron horario. | Corregido: `tipo_ejecucion: str = "AUTO"` agregado correctamente. |
| B | `Venta_Detalle.PIC_*` inexistente (CRÍTICO) | `detectar_faltantes_syncpos` consultaba columnas `PIC_*` que **no existen en NINGUNA tabla** de EDARSAHUB. Fallaba en dry-run y auditoría (oculto por `\|\| true`). | Corregido: detección **DIFERIDA** por decisión del usuario; devuelve `SIN_DETALLE_HISTORICO_DISPONIBLE` sin consultar tablas inexistentes. |
| C | Doble bloque `if dry_run:` | El patch insertaba un segundo bloque dejando el viejo como código muerto. | Corregido: un solo bloque dry-run limpio. |
| Gov | Seed encendido | El `.sh` sembraba `Habilitado=1` + `PermitirPOSAutomatico=1` → conexión POS automática. | **MODO SEGURO**: `Habilitado=0`, `PermitirPOSAutomatico=0`, `BackfillAutomaticoHabilitado=0`. |

## Cambios aplicados
### SQL (migración idempotente `backend/migrations/p1b_sync_pos_config.py`)
Crea en EDARSAHUB (si no existen):
- `dbo.Sistema_SyncPOS_Config` (control: Habilitado / PermitirPOSAutomatico / FrecuenciaMinutos / etc.)
- `dbo.Sistema_SyncPOS_EstadoUnidad`
- `dbo.Sistema_SyncPOS_Faltantes`
- `dbo.Sistema_SyncPOS_Bitacora`

Seed `INTELIGENCIA_COMERCIAL_POS` en **MODO SEGURO** (Habilitado=0, PermitirPOSAutomatico=0,
BackfillAutomaticoHabilitado=0, FrecuenciaMinutos=60).

### Código (`backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py`)
- `UNIDADES_CONFIG` deprecado a `{}` (eliminados hosts `.ddns.net`, usuarios `sa`, `*_DB_PASS`, `EDARSAHUB_SQL_PASSWORD`).
- Helpers canónicos nuevos: `get_syncpos_config`, `should_run_syncpos_now`, `get_unidades_negocio_pos`,
  `get_pos_config_for_unidad` (reúsa `get_server_connection_config` de Comercial V2; NO duplica desencriptado),
  `audit_syncpos_canonical_configs`, `detectar_faltantes_syncpos` (diferido), `registrar_syncpos_bitacora`,
  `actualizar_syncpos_config_estado`.
- Gate de control en el job: si `tipo_ejecucion="AUTO"` y la config está deshabilitada → SKIPPED (bitácora) sin tocar POS.
- Firma extendida con `tipo_ejecucion` (compatible con el cron que llama `dias_atras=1`).

### Scripts
- `backend/scripts/auditar_sync_pos_canonico.py` — auditoría SEGURA (sin secretos).
- `backend/scripts/guardrail_sync_pos_secrets.py` — guardrail anti-hardcode.
- `backend/scripts/backfill_inteligencia_comercial_pos.py` — actualizado con `tipo_ejecucion`.

## Validaciones ejecutadas (sin testing_agent)
- Migración: OK idempotente. Seed MODO SEGURO confirmado.
- `py_compile`: OK en los 5 archivos.
- Guardrail secretos: **OK** (sin hardcodes POS críticos en el job).
- Lint Python: sin issues bloqueantes.
- Auditoría dry-run: 5/5 unidades resueltas canónicamente (`resolved:true`), `has_password` bool (sin exponer password), `can_run_now:false`.
- AUTO (como el cron): `skipped:true` reason "Habilitado=0" — **NO conecta al POS**.
- Import scheduler→job: OK. Backend health: 200. Bitácora registró SKIPPED.

## Cómo activar (cuando el usuario autorice, por SQL)
```sql
-- Encender sync automático + permitir conexión POS
UPDATE dbo.Sistema_SyncPOS_Config
SET Habilitado = 1, PermitirPOSAutomatico = 1, FechaActualizacion = SYSUTCDATETIME()
WHERE Codigo = 'INTELIGENCIA_COMERCIAL_POS';

-- Cambiar frecuencia (ej. cada 30 min)
UPDATE dbo.Sistema_SyncPOS_Config
SET FrecuenciaMinutos = 30, FechaActualizacion = SYSUTCDATETIME()
WHERE Codigo = 'INTELIGENCIA_COMERCIAL_POS';
```

## Pendiente (decisión del usuario)
- **Tabla final de detalle de producto** para detección de faltantes (Venta_Detalle vs
  `Comercial_Inteligencia_VentasDetalleProducto`). Hasta definirla, faltantes queda diferido.
- **Issue 1 (histórico)**: Opción A (conexión POS en vivo) vs Opción B (dump SQL manual).
- **Validar conectividad real al POS** desde el pod antes de encender.
