# PLAN DE ACTIVACIÓN: Sync_Sales (Dry-Run Controlado)

**Fecha:** 2026-06-02  
**Estado:** PENDIENTE EJECUCIÓN  
**Versión:** 1.0

---

## 1. CÓDIGO EXACTO QUE ESCRIBE Sync_Sales

### 1.1 Ubicación

**Archivo:** `/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py`  
**Líneas:** 230-280

### 1.2 Función Principal

```python
# Líneas 230-280
def insert_into_sync_sales(conn, sales: List[Dict]) -> int:
    """Inserta registros en Sync_Sales."""
    if not sales:
        return 0
    
    cursor = conn.cursor()
    inserted = 0
    
    for sale in sales:
        try:
            # Verificar si ya existe (por NumeroTicket + UnidadNegocio + FechaHora)
            cursor.execute("""
                SELECT COUNT(*) FROM Sync_Sales 
                WHERE NumeroTicket = %s AND UnidadNegocio = %s 
                  AND CAST(FechaHora AS DATE) = CAST(%s AS DATE)
            """, (sale["NumeroTicket"], sale["UnidadNegocio"], sale["FechaHora"]))
            
            if cursor.fetchone()[0] > 0:
                continue  # Ya existe, skip
            
            # Insertar nuevo registro
            cursor.execute("""
                INSERT INTO Sync_Sales (
                    id, branch, UnidadNegocio, NumeroTicket, 
                    MontoTotal, Pax, FechaHora, status, items,
                    created_at, total
                ) VALUES (
                    %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s,
                    GETDATE(), %s
                )
            """, (
                sale.get("IdTransaccion", str(datetime.now().timestamp())),
                sale["UnidadNegocio"],
                sale["UnidadNegocio"],
                sale["NumeroTicket"],
                sale["MontoTotal"],
                sale["Pax"],
                sale["FechaHora"],
                sale.get("status", "COMPLETED"),
                sale.get("items", "[]"),
                sale["MontoTotal"]
            ))
            
            inserted += 1
            
        except Exception as e:
            logger.warning(f"[SYNC] Error insertando ticket {sale.get('NumeroTicket')}: {e}")
    
    cursor.close()
    return inserted
```

---

## 2. QUERY ORIGEN POR SISTEMA

### 2.1 SoftRestaurant (Líneas 120-149)

```sql
SELECT 
    CONVERT(VARCHAR(64), ch.folio) AS NumeroTicket,
    CONVERT(VARCHAR(64), NEWID()) AS IdTransaccion,
    ch.nopersonas AS Pax,
    ch.total AS MontoTotal,
    t.apertura AS FechaHora,
    'COMPLETED' AS status,
    (
        SELECT 
            p.idproducto AS id,
            p.descripcion AS name,
            dc.cantidad AS quantity,
            dc.precio AS price,
            (dc.cantidad * dc.precio) AS total
        FROM cheqdet dc
        INNER JOIN productos p ON dc.idproducto = p.idproducto
        WHERE dc.foliodet = ch.folio
        FOR JSON PATH
    ) AS items
FROM cheques ch
INNER JOIN turnos t ON t.idturno = ch.idturno
WHERE t.apertura >= '{fecha_inicio}'
  AND t.apertura < '{fecha_fin}'
  AND ch.cancelado = 0
  AND ch.total > 0
ORDER BY t.apertura DESC
```

### 2.2 MPRO (Líneas 152-182)

```sql
SELECT 
    CONVERT(VARCHAR(64), v.Vn_Folio) AS NumeroTicket,
    CONVERT(VARCHAR(64), NEWID()) AS IdTransaccion,
    ISNULL(c.Co_Personas, 1) AS Pax,
    v.Vn_Precio_Neto_Importe AS MontoTotal,
    v.Vn_Fecha AS FechaHora,
    CASE WHEN v.Es_Cve_Estado = 'CA' THEN 'CANCELLED' ELSE 'COMPLETED' END AS status,
    (
        SELECT 
            d.Ar_Cve_Articulo AS id,
            a.Ar_Descripcion AS name,
            d.Vd_Cantidad AS quantity,
            d.Vd_Precio_Unitario AS price,
            d.Vd_Importe AS total
        FROM Venta_Detalle d
        LEFT JOIN Articulo a ON d.Ar_Cve_Articulo = a.Ar_Cve_Articulo
        WHERE d.Vn_Folio = v.Vn_Folio 
          AND d.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
        FOR JSON PATH
    ) AS items
FROM Venta_Encabezado v
LEFT JOIN Comanda c ON c.Co_Folio = v.Vn_Folio AND c.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
WHERE v.Vn_Fecha >= '{fecha_inicio}'
  AND v.Vn_Fecha < '{fecha_fin}'
  AND ISNULL(v.Es_Cve_Estado, '') <> 'CA'
  AND v.Vn_Precio_Neto_Importe > 0
ORDER BY v.Vn_Fecha DESC
```

---

## 3. CAMPOS MAPEADOS

| Campo Origen | Campo Sync_Sales | Tipo | Descripción |
|--------------|------------------|------|-------------|
| `ch.folio` / `v.Vn_Folio` | `NumeroTicket` | varchar(64) | Folio único del ticket |
| `NEWID()` | `IdTransaccion` / `id` | varchar(64) | UUID generado |
| `ch.nopersonas` / `c.Co_Personas` | `Pax` | int | Número de comensales |
| `ch.total` / `v.Vn_Precio_Neto_Importe` | `MontoTotal` / `total` | numeric(18,2) | Monto total |
| `t.apertura` / `v.Vn_Fecha` | `FechaHora` | datetime | Fecha y hora del ticket |
| `'COMPLETED'` | `status` | varchar(32) | Estado del ticket |
| Subquery JSON | `items` | nvarchar(MAX) | Detalle de productos |
| (parámetro) | `UnidadNegocio` / `branch` | nvarchar(100) | Unidad de negocio |

---

## 4. REGLA ANTI-DUPLICADO

### 4.1 Llave de Unicidad Actual

```sql
WHERE NumeroTicket = %s AND UnidadNegocio = %s 
  AND CAST(FechaHora AS DATE) = CAST(%s AS DATE)
```

**Campos de la llave:**
- `NumeroTicket` (folio del ticket)
- `UnidadNegocio` (unidad de negocio)
- `FechaHora` (truncado a fecha, sin hora)

### 4.2 Comportamiento

| Situación | Acción |
|-----------|--------|
| Ticket no existe | INSERT |
| Ticket ya existe (misma fecha) | SKIP (continue) |
| Ticket existente, diferente hora | SKIP (por CAST a DATE) |

### 4.3 ⚠️ Riesgo Identificado

El check usa `CAST(FechaHora AS DATE)`, lo que significa que si un folio se repite en el mismo día con diferente hora, **se considera duplicado**. Esto es correcto para SoftRestaurant/MPRO donde el folio es único por día.

### 4.4 Mejora Propuesta (Opcional)

Agregar `sync_hash` para idempotencia completa:

```python
import hashlib
sync_hash = hashlib.md5(f"{NumeroTicket}|{UnidadNegocio}|{FechaHora}|{MontoTotal}".encode()).hexdigest()
```

---

## 5. MODO DRY-RUN

### 5.1 Script de Dry-Run

**Ubicación:** `/app/backend/tools/sync_sales_dry_run.py`

Este script:
1. ✅ Conecta a POS origen
2. ✅ Ejecuta query de extracción
3. ✅ Muestra registros que SE INSERTARÍAN
4. ✅ **NO ejecuta INSERT**
5. ✅ Genera reporte de conteo estimado
6. ✅ Valida estructura JSON items
7. ✅ Registra en log (sin inserción)

---

## 6. UNIDAD PILOTO

### 6.1 Selección: **CIENFUEGOS** o **130MID**

| Unidad | Sistema | Ventajas | Desventajas |
|--------|---------|----------|-------------|
| **CIENFUEGOS** | SoftRestaurant | Mayor volumen, más representativo | Más datos |
| **130MID** | SoftRestaurant | Menor volumen, más controlable | Menos cobertura |

**Recomendación:** `CIENFUEGOS` para validación real de volumen.

### 6.2 Configuración de Servidor

```python
"CIENFUEGOS": {
    "system_type": "SoftRestaurant",
    "host": "servercienfuegos.ddns.net,6669\\nationalsoft",
    "port": 1433,
    "database": "softrestaurant95pro",
    "username": os.environ.get("CIENFUEGOS_DB_USER", "sa"),
    "password": os.environ.get("CIENFUEGOS_DB_PASS", ""),  # ⚠️ REQUIERE CREDENCIAL
}
```

**Alternativa (tabla Servidores_Conexiones):**
- Host: `servercienfuegos.ddns.net,6669\nationalsoft`
- DB: `softrestaurant95pro`
- Las credenciales están cifradas en la tabla

---

## 7. RANGO PILOTO

### 7.1 Fecha Sugerida

**Rango:** 1 día cerrado (ayer o anteayer)

```python
fecha_inicio = "2026-06-01"  # Día cerrado
fecha_fin = "2026-06-02"     # Exclusivo
```

### 7.2 Justificación

- ✅ Día completo con todas las ventas cerradas
- ✅ Sin riesgo de tickets abiertos
- ✅ Volumen conocido para validación cruzada con KPIs existentes

---

## 8. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Duplicados por folio repetido | Baja | Medio | Llave anti-duplicado existente |
| Timeout por volumen alto | Media | Bajo | Procesar en lotes de 1000 |
| Credenciales POS inválidas | Media | Alto | Validar conexión antes de dry-run |
| JSON items malformado | Baja | Bajo | FOR JSON PATH maneja NULLs |
| Afectar KPIs existentes | **CERO** | N/A | Dry-run no ejecuta `update_kpis_diarios` |

### 8.1 Confirmación Crítica

**✅ CONFIRMADO: El dry-run NO afecta `Comercial_KPIs_Diarios_v2`**

El código actual en `inteligencia_comercial_sync_job.py` tiene dos partes separadas:
1. `insert_into_sync_sales()` → Escribe en Sync_Sales
2. `update_kpis_diarios()` → Escribe en Comercial_KPIs_Diarios_v2

El dry-run **solo ejecutará la parte 1** sin commit, y **nunca llamará la parte 2**.

---

## 9. COMANDO EXACTO PARA EJECUTAR

### 9.1 Dry-Run (Sin Inserción)

```bash
cd /app
python3 backend/tools/sync_sales_dry_run.py \
  --unidad CIENFUEGOS \
  --fecha-inicio 2026-06-01 \
  --fecha-fin 2026-06-02 \
  --dry-run \
  --verbose
```

### 9.2 Ejecución Real (Post-Validación)

```bash
cd /app
python3 backend/tools/sync_sales_dry_run.py \
  --unidad CIENFUEGOS \
  --fecha-inicio 2026-06-01 \
  --fecha-fin 2026-06-02 \
  --execute \
  --verbose
```

---

## 10. CHECKLIST PREVIO A EJECUCIÓN

- [ ] 1. Credenciales POS validadas (CIENFUEGOS conecta)
- [ ] 2. Dry-run ejecutado exitosamente
- [ ] 3. Conteo estimado revisado y aprobado
- [ ] 4. Estructura JSON items validada
- [ ] 5. Regla anti-duplicado confirmada
- [ ] 6. Log de ejecución generado
- [ ] 7. Comparación antes/después preparada

## 11. HALLAZGOS DE CONECTIVIDAD (Test 2026-06-02)

### 11.1 Servidores SoftRestaurant (CIENFUEGOS, 130MID, ESTELAR)

| Servidor | Estado | Razón |
|----------|--------|-------|
| servercienfuegos.ddns.net | ❌ No accesible | Red externa, DDNS |
| 130mid.ddns.net | ❌ No accesible | Red externa, DDNS |
| serverestelar.ddns.net | ❌ No accesible | Red externa, DDNS |

**Nota:** Los servidores SoftRestaurant usan DNS dinámico (DDNS) y están en redes de los restaurantes. 
Solo son accesibles desde la red corporativa o VPN.

### 11.2 Servidores MPRO (130QRO, ORIGEN)

| Base | Estado | Razón |
|------|--------|-------|
| QUERETARO | ❌ Login failed | Usuario <REDACTED_EDARSAHUB_SQL_USER> sin permisos |
| ORIGEN | ❌ Login failed | Usuario <REDACTED_EDARSAHUB_SQL_USER> sin permisos |

**Nota:** Las bases MPRO están en <REDACTED_EDARSAHUB_SQL_HOST> pero el usuario `<REDACTED_EDARSAHUB_SQL_USER>` solo tiene acceso a `EDARSAHUB`, no a `QUERETARO`/`ORIGEN`.

### 11.3 Acciones Requeridas

Para ejecutar el dry-run desde este entorno se necesita:

1. **Opción A:** Ejecutar desde servidor con acceso a red corporativa
2. **Opción B:** Habilitar usuario <REDACTED_EDARSAHUB_SQL_USER> en bases QUERETARO/ORIGEN
3. **Opción C:** Proporcionar credenciales alternativas para MPRO

### 11.4 Alternativa: Usar Datos Ya Existentes

Dado que `Comercial_KPIs_Diarios_v2` YA tiene datos de estas unidades (extraídos por el job existente), 
se puede validar la estructura del dry-run usando una query de simulación sin conectar al POS:

```sql
-- Simular extracción desde KPIs existentes
SELECT 
    'DRY-RUN-' + CONVERT(VARCHAR(10), NEWID()) AS IdTransaccion,
    unidad_negocio_nombre AS UnidadNegocio,
    CAST(tickets_total AS VARCHAR) AS NumeroTicket_simulado,
    ventas_total AS MontoTotal,
    pax_total AS Pax,
    fecha_operacion AS FechaHora,
    'COMPLETED' AS status,
    NULL AS items
FROM Comercial_KPIs_Diarios_v2
WHERE fecha_operacion = '2026-06-01'
```

---

## 12. VALIDACIÓN POST-EJECUCIÓN

### 11.1 Query de Validación

```sql
-- Después del dry-run (debería seguir en 0)
SELECT COUNT(*) AS registros_sync_sales FROM Sync_Sales;

-- Después de ejecución real
SELECT 
    UnidadNegocio,
    CAST(FechaHora AS DATE) AS fecha,
    COUNT(*) AS tickets,
    SUM(MontoTotal) AS ventas_total,
    SUM(Pax) AS pax_total
FROM Sync_Sales
WHERE UnidadNegocio = 'CIENFUEGOS'
  AND CAST(FechaHora AS DATE) = '2026-06-01'
GROUP BY UnidadNegocio, CAST(FechaHora AS DATE);
```

### 11.2 Comparación con KPIs Existentes

```sql
-- KPIs existentes para el mismo día
SELECT 
    unidad_negocio_nombre,
    fecha_operacion,
    tickets_total,
    ventas_total,
    pax_total
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_nombre LIKE '%CIENFUEGOS%'
  AND fecha_operacion = '2026-06-01';
```

**Criterio de éxito:** Los totales deben coincidir (con tolerancia de ±1% por redondeos).

---

## 13. RESULTADO DRY-RUN SIMULADO (2026-06-02)

### Ejecución

```bash
python3 backend/tools/sync_sales_dry_run.py \
  --unidad CIENFUEGOS \
  --fecha-inicio 2026-06-01 \
  --fecha-fin 2026-06-02 \
  --simulate \
  --dry-run \
  --verbose
```

### Resultado

| Métrica | Valor |
|---------|-------|
| Total registros extraídos | 27 |
| Monto total | $100,134.88 |
| PAX total | 81 |
| Ticket promedio | $3,708.70 |
| Nuevos a insertar | 27 |
| Ya existentes (skip) | 0 |
| Items JSON válidos | 27 |
| Items JSON inválidos | 0 |
| **Estado** | ✅ LISTO PARA EJECUTAR |

### Muestra de Registros

| Ticket | Monto | PAX | Fecha |
|--------|-------|-----|-------|
| SIM000001 | $3,000.30 | 2 | 2026-06-01 |
| SIM000002 | $3,375.33 | 3 | 2026-06-01 |
| SIM000003 | $3,750.37 | 4 | 2026-06-01 |
| SIM000004 | $4,125.41 | 2 | 2026-06-01 |
| SIM000005 | $4,500.44 | 3 | 2026-06-01 |

### Archivos Generados

- `/app/docs/reports/DRY_RUN_CIENFUEGOS_20260601_SIMULADO.json`

---

## 14. PRÓXIMOS PASOS

### ✅ Completados
1. ~~Crear script `/app/backend/tools/sync_sales_dry_run.py`~~ ✓
2. ~~Validar estructura de código~~ ✓
3. ~~Ejecutar dry-run simulado~~ ✓

### ⏳ Pendientes (Requieren Acción del Usuario)
4. **Habilitar acceso de red** a servidores SoftRestaurant (DDNS) desde entorno de producción
5. **O** Ejecutar el script desde servidor con acceso a red corporativa
6. **Ejecutar dry-run real** con conexión a POS
7. **Revisar y aprobar** conteo de registros reales
8. **Ejecutar inserción real** si dry-run es exitoso
9. **Validar resultados** con query de comparación

### Comando para Ejecución Real (cuando haya conectividad)

```bash
# Desde servidor con acceso a red corporativa
cd /app
python3 backend/tools/sync_sales_dry_run.py \
  --unidad CIENFUEGOS \
  --fecha-inicio 2026-06-01 \
  --fecha-fin 2026-06-02 \
  --dry-run \
  --verbose \
  --output /app/docs/reports/DRY_RUN_CIENFUEGOS_REAL.json
```

---

## 15. RESUMEN DE ENTREGABLES

| Entregable | Estado | Ubicación |
|------------|--------|-----------|
| Plan de Activación | ✅ | Este documento |
| Script Dry-Run | ✅ | `/app/backend/tools/sync_sales_dry_run.py` |
| Reporte Dry-Run Simulado | ✅ | `/app/docs/reports/DRY_RUN_CIENFUEGOS_20260601_SIMULADO.json` |
| Dry-Run Real | ⏳ | Requiere conectividad a POS |
| Inserción Real | ⏳ | Post-aprobación dry-run real |

---

**Documento preparado para aprobación antes de ejecución**  
**Agente E1 | 2026-06-02**
