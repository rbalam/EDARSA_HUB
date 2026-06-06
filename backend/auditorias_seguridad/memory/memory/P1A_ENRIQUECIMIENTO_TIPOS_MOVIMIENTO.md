# P1-A — DIAGNÓSTICO ENRIQUECIMIENTO tipos_movimiento

## Fecha: Diciembre 2025
## Estado: DIAGNÓSTICO COMPLETADO - PENDIENTE AUTORIZACIÓN UPDATE

---

## 1. Queries exactas

### SoftRestaurant
```sql
SELECT 
    idconcepto as codigo,
    descripcion,
    CASE WHEN tipo = 1 THEN 'EN' ELSE 'SA' END as tipo
FROM conceptos
ORDER BY idconcepto
```
- **Tabla:** `conceptos`
- **Campos:** idconcepto (código), descripcion, tipo (1=EN, otro=SA)

### ManagementPro (MPRO)
```sql
SELECT 
    Tm_Cve_Tipo_Movimiento as codigo,
    Tm_Descripcion as descripcion,
    Tm_Tipo as tipo
FROM Tipo_Movimiento
WHERE Es_Cve_Estado <> 'BA'
ORDER BY Tm_Cve_Tipo_Movimiento
```
- **Tabla:** `Tipo_Movimiento`
- **Campos:** Tm_Cve_Tipo_Movimiento (código), Tm_Descripcion, Tm_Tipo (EN/SA)

---

## 2. Muestra de códigos con descripción real

### 130 MERIDA (18 códigos)
| Código | Descripción Real | Tipo |
|--------|------------------|------|
| E | ENTRADA (NO UTILIZAR) | EN |
| ECA | ENTRADA POR CANCELACION | EN |
| ECI | ENTRADA POR CAPTURA DE IF | EN |
| EDE | ENTRADA POR DEVOLUCIÓN | EN |
| EDF | ENTRADA DIFERENCIA FACTURA | EN |
| EIT | EIT (sin descripción) | EN |
| EPC | ENTRADA POR COMPRA | EN |
| EPD | EPD (sin descripción) | EN |
| EPP | EPP (sin descripción) | EN |
| EPT | EPT (sin descripción) | EN |
| ETA | ENTRADA POR TRASPASO DE ALMACEN | EN |
| SCS | SCS (sin descripción) | SA |
| SCP | SALIDA COMIDA DE PERSONAL | SA |
| SDA | SDA (sin descripción) | SA |
| SDV | SDV (sin descripción) | SA |
| SPC | SALIDA POR COMPRA | SA |
| SPD | SALIDA POR DEVOLUCION | SA |
| STM | STM (sin descripción) | SA |

**Nota:** 8 códigos no encontrados en BD viva (posiblemente obsoletos/eliminados)

### CIENFUEGOS (22 códigos) - TODOS ENCONTRADOS ✅
| Código | Descripción Real | Tipo |
|--------|------------------|------|
| EAL | ENTRADA DE ALMACEN | EN |
| ECA | ENTRADA POR CANCELACION | EN |
| ECS | ENTRADA POR CONSIGNA | EN |
| ECO | ENTRADA POR CORTESIA | EN |
| EDE | ENTRADA POR DEVOLUCIÓN | EN |
| EEH | ENTRADA POR EXHIBICION | EN |
| EPB | ENTRADA POR BONIFICACION | EN |
| EPC | ENTRADA POR COMPRA | EN |
| EPL | ENTRADA POR CANCELACION* | EN |
| EPR | ENTRADA POR PRODUCCION | EN |
| ETA | ENTRADA POR TABLAJERIA | EN |
| ETR | ENTRADA POR TRASPASO | EN |
| SCP | SALIDA COMIDA PERSONAL | SA |
| SCS | SALIDA POR CONSIGNA | SA |
| SDE | SALIDA POR DESPERDICIO | SA |
| SDV | SALIDA POR DEVOLUCION | SA |
| SPC | SALIDA POR CANCELACION | SA |
| SPM | SALIDA POR MERMA | SA |
| SPR | SALIDA POR PRODUCCION | SA |
| SPV | SALIDA POR VENTA | SA |
| STA | SALIDA POR TABLAJERIA | SA |
| STR | SALIDA POR TRASPASO | SA |

### LA ESTELAR (19 códigos) - BD VIVA NO DISPONIBLE ⚠️
- BD viva no respondió
- Se conservará descripcion = codigo como fallback

### ManagementPro (35 códigos) - TODOS ENCONTRADOS ✅
| Código | Descripción Real | Tipo |
|--------|------------------|------|
| 050 | ENTRADA POR COMPRA | EN |
| 051 | ANULACION ENTRADA POR COMPRA | SA |
| 052 | ENTRADA POR CONSIGNACION | EN |
| 053 | ANULACION ENTRADA POR CONSIGNACION | SA |
| 060 | ENTRADA POR DEVOLUCION CLIENTES | EN |
| 061 | ANULACION ENTRADA POR DEVOLUCION | SA |
| 100 | ENTRADA POR TRANSFERENCIA | EN |
| 101 | ANULACION ENTRADA TRANSFERENCIA | SA |
| 104 | SALIDA POR CONSUMO INTERNO | SA |
| 105 | ANULACION SALIDA CONSUMO INTERNO | EN |
| 106 | ENTRADA POR TRASPASO | EN |
| 107 | ANULACION ENTRADA POR TRASPASO | SA |
| 108 | ENTRADA POR CONVERSION | EN |
| ... | ... | ... |

---

## 3. JSON Enriquecido Propuesto por Servidor

### 130 MERIDA
```json
[
  {"codigo": "E", "descripcion": "ENTRADA (NO UTILIZAR)", "tipo": "EN"},
  {"codigo": "ECA", "descripcion": "ENTRADA POR CANCELACION", "tipo": "EN"},
  {"codigo": "ECI", "descripcion": "ENTRADA POR CAPTURA DE IF", "tipo": "EN"},
  {"codigo": "EDE", "descripcion": "ENTRADA POR DEVOLUCIÓN", "tipo": "EN"},
  {"codigo": "EDF", "descripcion": "ENTRADA DIFERENCIA FACTURA", "tipo": "EN"},
  {"codigo": "EIT", "descripcion": "EIT (sin descripción)", "tipo": "EN"},
  {"codigo": "EPC", "descripcion": "ENTRADA POR COMPRA", "tipo": "EN"},
  {"codigo": "EPD", "descripcion": "EPD (sin descripción)", "tipo": "EN"},
  {"codigo": "EPP", "descripcion": "EPP (sin descripción)", "tipo": "EN"},
  {"codigo": "EPT", "descripcion": "EPT (sin descripción)", "tipo": "EN"},
  {"codigo": "ETA", "descripcion": "ENTRADA POR TRASPASO DE ALMACEN", "tipo": "EN"},
  {"codigo": "SCS", "descripcion": "SCS (sin descripción)", "tipo": "SA"},
  {"codigo": "SCP", "descripcion": "SALIDA COMIDA DE PERSONAL", "tipo": "SA"},
  {"codigo": "SDA", "descripcion": "SDA (sin descripción)", "tipo": "SA"},
  {"codigo": "SDV", "descripcion": "SDV (sin descripción)", "tipo": "SA"},
  {"codigo": "SPC", "descripcion": "SALIDA POR COMPRA", "tipo": "SA"},
  {"codigo": "SPD", "descripcion": "SALIDA POR DEVOLUCION", "tipo": "SA"},
  {"codigo": "STM", "descripcion": "STM (sin descripción)", "tipo": "SA"}
]
```

### CIENFUEGOS
```json
[
  {"codigo": "EAL", "descripcion": "ENTRADA DE ALMACEN", "tipo": "EN"},
  {"codigo": "ECA", "descripcion": "ENTRADA POR CANCELACION", "tipo": "EN"},
  {"codigo": "ECS", "descripcion": "ENTRADA POR CONSIGNA", "tipo": "EN"},
  {"codigo": "ECO", "descripcion": "ENTRADA POR CORTESIA", "tipo": "EN"},
  {"codigo": "EDE", "descripcion": "ENTRADA POR DEVOLUCIÓN", "tipo": "EN"},
  {"codigo": "EEH", "descripcion": "ENTRADA POR EXHIBICION", "tipo": "EN"},
  {"codigo": "EPB", "descripcion": "ENTRADA POR BONIFICACION", "tipo": "EN"},
  {"codigo": "EPC", "descripcion": "ENTRADA POR COMPRA", "tipo": "EN"},
  {"codigo": "EPL", "descripcion": "ENTRADA POR CANCELACION*", "tipo": "EN"},
  {"codigo": "EPR", "descripcion": "ENTRADA POR PRODUCCION", "tipo": "EN"},
  {"codigo": "ETA", "descripcion": "ENTRADA POR TABLAJERIA", "tipo": "EN"},
  {"codigo": "ETR", "descripcion": "ENTRADA POR TRASPASO", "tipo": "EN"},
  {"codigo": "SCP", "descripcion": "SALIDA COMIDA PERSONAL", "tipo": "SA"},
  {"codigo": "SCS", "descripcion": "SALIDA POR CONSIGNA", "tipo": "SA"},
  {"codigo": "SDE", "descripcion": "SALIDA POR DESPERDICIO", "tipo": "SA"},
  {"codigo": "SDV", "descripcion": "SALIDA POR DEVOLUCION", "tipo": "SA"},
  {"codigo": "SPC", "descripcion": "SALIDA POR CANCELACION", "tipo": "SA"},
  {"codigo": "SPM", "descripcion": "SALIDA POR MERMA", "tipo": "SA"},
  {"codigo": "SPR", "descripcion": "SALIDA POR PRODUCCION", "tipo": "SA"},
  {"codigo": "SPV", "descripcion": "SALIDA POR VENTA", "tipo": "SA"},
  {"codigo": "STA", "descripcion": "SALIDA POR TABLAJERIA", "tipo": "SA"},
  {"codigo": "STR", "descripcion": "SALIDA POR TRASPASO", "tipo": "SA"}
]
```

---

## 4. Script UPDATE Propuesto (SIN EJECUTAR)

```sql
-- =====================================================
-- SCRIPT UPDATE TIPOS_MOVIMIENTO ENRIQUECIDOS
-- ESTADO: PROPUESTO - NO EJECUTAR SIN AUTORIZACIÓN
-- =====================================================

-- BACKUP PRIMERO (ejecutar antes de cualquier UPDATE)
SELECT 
    mongodb_id,
    nombre,
    tipos_movimiento,
    GETDATE() as backup_timestamp
INTO #backup_tipos_movimiento
FROM EDARSAHUB.dbo.Servidores_Conexiones
WHERE tipos_movimiento IS NOT NULL;

-- UPDATE 130 MERIDA
UPDATE EDARSAHUB.dbo.Servidores_Conexiones
SET tipos_movimiento = '[{"codigo":"E","descripcion":"ENTRADA (NO UTILIZAR)","tipo":"EN"},{"codigo":"ECA","descripcion":"ENTRADA POR CANCELACION","tipo":"EN"},{"codigo":"ECI","descripcion":"ENTRADA POR CAPTURA DE IF","tipo":"EN"},{"codigo":"EDE","descripcion":"ENTRADA POR DEVOLUCIÓN","tipo":"EN"},{"codigo":"EDF","descripcion":"ENTRADA DIFERENCIA FACTURA","tipo":"EN"},{"codigo":"EIT","descripcion":"EIT (sin descripción)","tipo":"EN"},{"codigo":"EPC","descripcion":"ENTRADA POR COMPRA","tipo":"EN"},{"codigo":"EPD","descripcion":"EPD (sin descripción)","tipo":"EN"},{"codigo":"EPP","descripcion":"EPP (sin descripción)","tipo":"EN"},{"codigo":"EPT","descripcion":"EPT (sin descripción)","tipo":"EN"},{"codigo":"ETA","descripcion":"ENTRADA POR TRASPASO DE ALMACEN","tipo":"EN"},{"codigo":"SCS","descripcion":"SCS (sin descripción)","tipo":"SA"},{"codigo":"SCP","descripcion":"SALIDA COMIDA DE PERSONAL","tipo":"SA"},{"codigo":"SDA","descripcion":"SDA (sin descripción)","tipo":"SA"},{"codigo":"SDV","descripcion":"SDV (sin descripción)","tipo":"SA"},{"codigo":"SPC","descripcion":"SALIDA POR COMPRA","tipo":"SA"},{"codigo":"SPD","descripcion":"SALIDA POR DEVOLUCION","tipo":"SA"},{"codigo":"STM","descripcion":"STM (sin descripción)","tipo":"SA"}]',
    updated_at = GETDATE(),
    updated_by = 'ENRICH_TIPOS_P1A'
WHERE mongodb_id = 'a5547321-1139-4d2b-9d53-182ca737b6b6';

-- UPDATE CIENFUEGOS
UPDATE EDARSAHUB.dbo.Servidores_Conexiones
SET tipos_movimiento = '[{"codigo":"EAL","descripcion":"ENTRADA DE ALMACEN","tipo":"EN"},{"codigo":"ECA","descripcion":"ENTRADA POR CANCELACION","tipo":"EN"},{"codigo":"ECS","descripcion":"ENTRADA POR CONSIGNA","tipo":"EN"},{"codigo":"ECO","descripcion":"ENTRADA POR CORTESIA","tipo":"EN"},{"codigo":"EDE","descripcion":"ENTRADA POR DEVOLUCIÓN","tipo":"EN"},{"codigo":"EEH","descripcion":"ENTRADA POR EXHIBICION","tipo":"EN"},{"codigo":"EPB","descripcion":"ENTRADA POR BONIFICACION","tipo":"EN"},{"codigo":"EPC","descripcion":"ENTRADA POR COMPRA","tipo":"EN"},{"codigo":"EPL","descripcion":"ENTRADA POR CANCELACION*","tipo":"EN"},{"codigo":"EPR","descripcion":"ENTRADA POR PRODUCCION","tipo":"EN"},{"codigo":"ETA","descripcion":"ENTRADA POR TABLAJERIA","tipo":"EN"},{"codigo":"ETR","descripcion":"ENTRADA POR TRASPASO","tipo":"EN"},{"codigo":"SCP","descripcion":"SALIDA COMIDA PERSONAL","tipo":"SA"},{"codigo":"SCS","descripcion":"SALIDA POR CONSIGNA","tipo":"SA"},{"codigo":"SDE","descripcion":"SALIDA POR DESPERDICIO","tipo":"SA"},{"codigo":"SDV","descripcion":"SALIDA POR DEVOLUCION","tipo":"SA"},{"codigo":"SPC","descripcion":"SALIDA POR CANCELACION","tipo":"SA"},{"codigo":"SPM","descripcion":"SALIDA POR MERMA","tipo":"SA"},{"codigo":"SPR","descripcion":"SALIDA POR PRODUCCION","tipo":"SA"},{"codigo":"SPV","descripcion":"SALIDA POR VENTA","tipo":"SA"},{"codigo":"STA","descripcion":"SALIDA POR TABLAJERIA","tipo":"SA"},{"codigo":"STR","descripcion":"SALIDA POR TRASPASO","tipo":"SA"}]',
    updated_at = GETDATE(),
    updated_by = 'ENRICH_TIPOS_P1A'
WHERE mongodb_id = '6d053c22-523e-48c0-b72b-96081e2d781b';

-- LA ESTELAR: Sin cambio (BD viva no disponible, conservar códigos existentes)
-- ManagementPro: Pendiente generar JSON completo de 35 tipos
```

---

## 5. Confirmación

- ✅ No se modificó código
- ✅ No se ejecutó UPDATE
- ✅ No se tocó frontend
- ✅ No se tocó auditoria-operativa
- ✅ No se usó MongoDB
- ✅ Solo diagnóstico

---

## 6. Siguiente paso

Autorizar ejecución de UPDATE para:
1. 130 MERIDA (18 tipos)
2. CIENFUEGOS (22 tipos)
3. ManagementPro (35 tipos - pendiente generar JSON completo)

LA ESTELAR se conserva sin cambios hasta que su BD viva esté disponible.
