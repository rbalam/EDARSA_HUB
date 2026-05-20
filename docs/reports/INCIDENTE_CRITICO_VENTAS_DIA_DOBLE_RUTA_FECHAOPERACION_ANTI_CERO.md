# INCIDENTE CRÍTICO: Ventas del Día - Doble Ruta, FechaOperacion y Anti-$0

**Fecha:** 2026-05-20  
**Prioridad:** P0  
**Estado:** EN PROGRESO - PARCIALMENTE CORREGIDO

---

## 1. Causa Raíz Real

### Problema Principal: Dos Jobs Corriendo en Paralelo

Se detectaron DOS ejecuciones casi simultáneas del job `sync_comercial_abiertas_v2_job.py`:

| RunID | Hora (UTC) | FechaInicio | Estado |
|-------|------------|-------------|--------|
| `ABIERTA-20260520-011330-6c96` | 01:13:30 | **2026-05-19** | ✅ CORRECTO |
| `ABIERTA-20260520-011200-b691` | 01:12:00 | 2026-05-20 | ❌ INCORRECTO |

### Causa: Procesos Zombie y Hot-Reload

1. El backend corre con `--reload` (WatchFiles)
2. Durante los restarts, procesos uvicorn antiguos quedan como zombies
3. Estos procesos zombie siguen ejecutando el scheduler con código antiguo
4. Resultado: Dos jobs escriben la misma tabla con fechas diferentes

---

## 2. Correcciones Implementadas

### A) Anti-$0 Falso (IMPLEMENTADO)
**Archivo:** `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py`

```python
# REGLA 1: Si fecha_operacion es DIFERENTE, SIEMPRE actualizar
if existing_fecha != new_fecha:
    logger.warning(f"[UPSERT-FECHA] Actualizando fecha {existing_fecha} -> {new_fecha}")
    # Continuar con UPDATE

# REGLA 2: ANTI-$0 FALSO (solo aplica si MISMA fecha_operacion)
elif ventas.total_estimado_dia == 0 and existing_total > 0:
    return {'action': 'SKIP_ANTI_ZERO', ...}
```

### B) Logging Diagnóstico (IMPLEMENTADO)
**Archivo:** `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`

```python
logger.warning(
    f"[SYNC_ABIERTAS_V2] DIAG: run_id={run_id}, "
    f"UTC={start_time}, México={now_mexico}, "
    f"fecha_hoy={fecha_hoy}, pid={os.getpid()}"
)
```

### C) Eliminación de Procesos Zombie (EJECUTADO)
```bash
pkill -9 -f "uvicorn server:app"
sudo supervisorctl restart backend
```

---

## 3. Estado Actual Post-Fix

| Unidad | FechaOp | Total | RunID | Estado |
|--------|---------|-------|-------|--------|
| 130MID | **2026-05-19** ✅ | $28,539 | 011330 | ✅ CORREGIDO |
| 130QRO | 2026-05-20 ❌ | $0 | 011200 | ⚠️ Pendiente |
| ORIGEN | 2026-05-20 ❌ | $17,563 | 011200 | ⚠️ Pendiente |
| CIENFUEGOS | 2026-05-20 ❌ | $0 | 011200 | ⚠️ Error conexión SQL |
| ESTELAR | 2026-05-20 ❌ | $6,920 | 011200 | ⚠️ Error conexión SQL |

### Comparación con Referencia Operativa (hace ~30 min)

| Unidad | Referencia | Actual | Diferencia |
|--------|------------|--------|------------|
| 130QRO | $78,825 | $0 | ❌ -$78,825 |
| CIENFUEGOS | $58,759 | $0 | ❌ -$58,759 |
| ESTELAR | $4,965 | $6,920 | ✅ +$1,955 |
| ORIGEN | $26,846 | $17,563 | ⚠️ -$9,283 |
| 130MID | N/A | $28,539 | N/A |

---

## 4. Problemas Pendientes

### 4.1 SoftRestaurant (CIENFUEGOS, ESTELAR)
**Error:** `Query retornó...` - Conexión SQL fallida
**Causa probable:** Pool de conexión o credenciales

### 4.2 MPRO (130QRO, ORIGEN)
**Error:** `No se encontró API local` o `No se encontró configuración`
**Causa probable:** SERVER_SECRET_KEY no configurada para descifrar API keys

### 4.3 Datos Históricos con Fecha Incorrecta
Los registros con `fecha_operacion = 2026-05-20` necesitan ser actualizados cuando el job ejecute correctamente.

---

## 5. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py` | Anti-$0 y logging |
| `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` | Logging diagnóstico |

---

## 6. Validaciones Realizadas

- [x] Backend reiniciado sin procesos zombie
- [x] Un solo PID del backend (1734/1736)
- [x] Job ejecuta con código nuevo (RunID 011330)
- [x] 130MID corregido a FechaOp=2026-05-19
- [x] Helper `get_operational_window()` calcula correctamente
- [ ] CIENFUEGOS - Pendiente resolver conexión SQL
- [ ] ESTELAR - Pendiente resolver conexión SQL
- [ ] 130QRO - Pendiente resolver API local
- [ ] ORIGEN - Pendiente resolver API local

---

## 7. Próximos Pasos

1. **Investigar conexiones SoftRestaurant** (CIENFUEGOS, ESTELAR)
   - Verificar credenciales en Servidores_Conexiones
   - Verificar conectividad a los servidores

2. **Investigar API Local MPRO** (130QRO, ORIGEN)
   - Verificar SERVER_SECRET_KEY
   - Verificar que el job usa la misma lógica que la UI de Servidores

3. **Esperar siguiente ciclo del job** (5 minutos)
   - Verificar que todas las unidades se actualicen con fecha correcta

---

## 8. Endpoint del Tablero

El endpoint `/api/v2/comercial/ventas-dia`:
- ✅ Lee de EDARSAHUB SQL
- ✅ Usa fecha operativa 2026-05-19
- ⚠️ Muestra datos parciales por errores de sincronización

---

*Reporte generado: 2026-05-20 01:15 UTC*
*Autor: Agente E1*
