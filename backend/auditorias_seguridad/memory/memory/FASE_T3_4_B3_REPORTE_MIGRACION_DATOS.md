# FASE T3.4-B3 — Reporte: Migración de tipos_movimiento a EDARSAHUB

**Fecha:** 14-Mayo-2026  
**Estado:** COMPLETADO  
**Autorizado por:** Usuario (AUTORIZACIÓN CONTROLADA)

---

## 1. IDs de los 4 Servidores Actualizados

| Servidor | mongodb_id | Nombre SQL |
|----------|------------|------------|
| CIENFUEGOS | `6d053c22-523e-48c0-b72b-96081e2d781b` | CIENFUEGOS |
| LA ESTELAR | `a5ff0e25-f029-43db-b634-d4ac814c904f` | LA ESTELAR |
| 130 MERIDA | `a5547321-1139-4d2b-9d53-182ca737b6b6` | 130° MERIDA |
| ManagementPro | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | ManagmentPro |

---

## 2. Valores Migrados por Servidor

### CIENFUEGOS (SoftRestaurant)
```json
["EAL", "ECA", "ECS", "ECO", "EDE", "EEH", "EPB", "EPC", "EPL", "EPR", "ETA", "ETR", "SCP", "SCS", "SDE", "SDV", "SPC", "SPM", "SPR", "SPV", "STA", "STR"]
```

### LA ESTELAR (SoftRestaurant)
```json
["ECA", "ECS", "ECI", "EDA", "EPC", "EPD", "EPP", "EPT", "ETA", "SCS", "SCP", "SDA", "SDV", "SPC", "SPM", "SPD", "SPP", "SPT", "STA"]
```

### 130° MERIDA (SoftRestaurant)
```json
["ECA", "EDE", "EIE", "EPA", "EPB", "EPC", "EPCON", "EPL", "ETA", "ETB", "SCP", "SDE", "SIE", "SPC", "SPD", "SPM", "STA", "STB"]
```

### ManagmentPro (MPRO)
```json
["050", "100", "106", "108", "112", "202", "400", "500", "506", "508", "510", "512", "514", "942", "051", "101", "107", "113", "203", "401", "501", "507", "509", "511", "513", "515", "943", "052", "053", "060", "061", "104", "105", "114", "115"]
```

---

## 3. Conteo de Tipos por Servidor

| Servidor | Conteo | Esperado | Estado |
|----------|--------|----------|--------|
| CIENFUEGOS | 22 | 22 | ✅ |
| LA ESTELAR | 19 | 19 | ✅ |
| 130 MERIDA | 18 | 18 | ✅ |
| ManagementPro | 35 | 35 | ✅ |

---

## 4. Confirmación de JSON Válido

Todos los valores fueron almacenados como JSON array válido:
- ✅ CIENFUEGOS: `json.loads()` exitoso, tipo `list`
- ✅ LA ESTELAR: `json.loads()` exitoso, tipo `list`
- ✅ 130 MERIDA: `json.loads()` exitoso, tipo `list`
- ✅ ManagementPro: `json.loads()` exitoso, tipo `list`

---

## 5. Backup Realizado

| Campo | Valor |
|-------|-------|
| Tabla backup | `Servidores_Conexiones_backup_tipos_mov_20260513_0729` |
| Registros respaldados | 4 |
| Campos incluidos | Todos + `fecha_backup` + `fase_migracion` |
| Fase | `T3_4_B3_TIPOS_MOVIMIENTO` |

**Script de rollback:**
```sql
-- Restaurar desde backup
UPDATE sc
SET sc.tipos_movimiento = bk.tipos_movimiento
FROM Servidores_Conexiones sc
INNER JOIN Servidores_Conexiones_backup_tipos_mov_20260513_0729 bk
  ON sc.mongodb_id = bk.mongodb_id;
```

---

## 6. Confirmación: Solo se Actualizó tipos_movimiento

- ✅ No se modificó `nombre`
- ✅ No se modificó `host`
- ✅ No se modificó `port`
- ✅ No se modificó `database_name`
- ✅ No se modificó `username`
- ✅ No se modificó `password`
- ✅ No se modificó `activo`
- ✅ No se modificó `visible_en_operaciones`

---

## 7. Confirmación: No se Modificó Código

- ✅ **NO se modificó** `/app/backend/server.py`
- ✅ **NO se modificó** `/app/backend/core/server_registry.py`
- ✅ **NO se modificó** `auditoria-operativa`
- ✅ **NO se modificó** ningún archivo de código

---

## 8. No Regresión

| Área | Endpoint | Resultado |
|------|----------|-----------|
| Finanzas | `GET /api/finanzas/tesoreria/sucursales` | ✅ HTTP 200 - 4 sucursales |
| Compras | `GET /api/compras/inventarios-fisicos/{server_id}` | ✅ HTTP 200 |
| server_registry | `list_unidades_negocio()` | ✅ OK - 5 unidades |

---

## 9. Confirmación: MongoDB Solo Como Fuente Temporal

- ✅ MongoDB se usó ÚNICAMENTE para leer `tipos_movimiento` durante esta migración
- ✅ Los datos ahora residen en EDARSAHUB SQL
- ✅ `auditoria-operativa` aún usa MongoDB (pendiente T3.4-B5)
- ✅ Después de T3.4-B4/B5, MongoDB ya no será fuente funcional

---

## 10. Estado Post-Migración

| Métrica | Valor |
|---------|-------|
| Total registros en Servidores_Conexiones | 19 |
| Con tipos_movimiento (migrados) | 4 |
| Sin tipos_movimiento (NULL) | 15 |

---

## 11. Siguiente Paso Propuesto

**FASE T3.4-B4:** Actualizar `/app/backend/core/server_registry.py` para:

1. Incluir `tipos_movimiento` en la función `_sql_row_to_server_dict()`
2. Incluir `tipos_movimiento` en el retorno de `get_server_connection_info()`
3. Parsear el JSON automáticamente

Esto permitirá que `auditoria-operativa` obtenga `tipos_movimiento` desde EDARSAHUB en lugar de MongoDB.

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1  
**Pendiente:** Autorización para FASE T3.4-B4 (actualizar server_registry.py)
