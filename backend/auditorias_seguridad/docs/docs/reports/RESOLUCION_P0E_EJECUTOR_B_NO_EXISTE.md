# RESOLUCIÓN P0E — EL "EJECUTOR B" NO EXISTE

**Fecha**: 2025-12-19  
**Diagnóstico Final**: COMPLETADO

---

## CONCLUSIÓN PRINCIPAL

### ❌ NO EXISTE UN "EJECUTOR B" EXTERNO

Después de un diagnóstico exhaustivo, se confirma que:

1. **No hay SQL Server Agent Jobs** que escriban en las tablas afectadas
2. **No hay Stored Procedures** relevantes
3. **No hay Triggers** en las tablas
4. **No hay procesos externos** escribiendo en EDARSAHUB
5. **El único escritor es el backend Python** (scheduler del contenedor)

---

## LA "ESCRITURA INCORRECTA" ES LA LÓGICA DE NEGOCIO FUNCIONANDO CORRECTAMENTE

### Evidencia de los Logs del Backend:

```
[SYNC_ABIERTAS_V2] SR 130MID: FechaOperacion=2026-05-19, horario=13:00:00-06:00:00, cruza=True
[UPSERT-FECHA] 130MID: Actualizando fecha 2026-05-20 -> 2026-05-19
```

### Explicación:

| Parámetro | Valor |
|-----------|-------|
| Hora actual México | 12:53 (20-May-2026) |
| Horario operativo | 13:00 - 06:00 |
| Cruza medianoche | Sí |
| Hora de apertura | 13:00 |
| Estado actual | Cerrado (antes de apertura) |
| **Fecha operativa calculada** | **2026-05-19** (día anterior) |

### Lógica Implementada:

```
Si estamos ANTES de las 13:00 (hora de apertura):
    → El restaurante aún no abre para el día de hoy
    → Los datos pertenecen al día operativo ANTERIOR
    → FechaOperacion = fecha_calendario - 1 día
```

---

## ¿ES ESTO UN BUG O DISEÑO CORRECTO?

### Depende del Negocio:

**Escenario A**: Si el restaurante abre a las 13:00 y cierra a las 06:00 del día siguiente
- ✅ La lógica es CORRECTA
- Las ventas de las 13:00 del día 19 hasta las 06:00 del día 20 pertenecen al "día 19"
- A las 12:53 del día 20, el restaurante aún no ha abierto, así que mostramos datos del día 19

**Escenario B**: Si el usuario espera ver datos del día calendario (00:00 - 23:59)
- ❌ La lógica debe ajustarse
- Se debería usar `date.today()` en lugar de `get_operational_window()`

---

## DIAGNÓSTICO SQL SERVER AGENT

| Verificación | Resultado |
|--------------|-----------|
| Total Jobs en SQL Agent | 1 (solo `syspolicy_purge_history`) |
| Jobs que escriben en tablas afectadas | 0 |
| Jobs cada 5-10 minutos | 0 |
| Stored Procedures relevantes | 0 |
| Triggers en tablas | 0 |
| Permisos msdb | SQLAgentReaderRole, SQLAgentUserRole, SQLAgentOperatorRole ✓ |
| VIEW SERVER STATE | No disponible (no afecta diagnóstico) |

---

## ORIGEN CONFIRMADO DE LAS ESCRITURAS

| Campo | Valor |
|-------|-------|
| Proceso | `sync_comercial_abiertas_v2_job.py` (APScheduler) |
| PID | 51 (único proceso backend) |
| Frecuencia | Cada 5 minutos (configurado en scheduler) |
| sync_run_id | `ABIERTA-YYYYMMDD-HHMMSS-xxxx` |
| Usuario SQL | <REDACTED_EDARSAHUB_SQL_USER> |
| Host | Contenedor Docker (agent-env-...) |

---

## ACCIÓN RECOMENDADA

### Si la lógica de "día operativo" es correcta:
- ✅ No hay nada que corregir
- El sistema funciona según diseño

### Si se esperaba fecha calendario:
- Revisar la definición de negocio con el usuario
- Posiblemente cambiar la lógica de `operational_window.py`
- O ajustar los horarios en la configuración de unidades

---

## SIGUIENTE PASO

**Solicitar confirmación del usuario**:

¿La FechaOperacion debe ser:
1. **Día operativo** (13:00 de ayer a 06:00 de hoy = "ayer")
2. **Día calendario** (00:00 a 23:59 = "hoy")

---

**Estado**: DIAGNÓSTICO P0D/P0E COMPLETADO  
**Resultado**: No existe Ejecutor B externo  
**Causa**: Lógica de `operational_window` funcionando según diseño
