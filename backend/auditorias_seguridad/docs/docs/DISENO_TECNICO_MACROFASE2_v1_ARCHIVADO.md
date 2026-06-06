# EDARSA HUB - Diseño Técnico MACROFASE 2
## Consolidación en EDARSA HUB: KPIs e Históricos

**Versión**: 1.0  
**Fecha**: 2026-04-22  
**Estado**: PROPUESTA TÉCNICA  

---

## 1. OBJETIVO

Implementar la infraestructura de consolidación de datos históricos en EDARSA HUB para:
1. Reducir carga en servidores SQL externos
2. Mejorar tiempos de respuesta del Tablero Ejecutivo
3. Establecer política formal de UPSERT, ventana deslizante y reconciliación

---

## 2. ESQUEMA EN EDARSA HUB

### 2.1 Tabla/Colección: `kpis_comercial_diarios`

**Propósito**: Almacenar KPIs de ventas por día/sucursal

```javascript
{
  // Clave única compuesta
  "server_id": "uuid",
  "fecha": "2026-04-21",
  "sucursal_id": "codigo_sucursal",
  
  // KPIs principales
  "kpis": {
    "ventas": 125000.00,
    "pax": 450,
    "cheques": 120,
    "ticket_promedio": 277.78,
    "cheque_promedio": 1041.67,
    "propina": 5000.00,
    "descuentos": 2500.00,
    "cortesias": 1000.00
  },
  
  // Detalle por hora (para análisis de patrones)
  "ventas_por_hora": [
    {"hora": 9, "ventas": 5000, "cheques": 10},
    {"hora": 10, "ventas": 8000, "cheques": 15},
    // ... 24 horas
  ],
  
  // Metadata de auditoría
  "created_at": ISODate("2026-04-22T03:15:00Z"),
  "updated_at": ISODate("2026-04-22T03:15:00Z"),
  "source": "SoftRestaurant",
  "source_query_time_ms": 1500,
  
  // Control de estado
  "estado_periodo": "CERRADO",  // ABIERTO | CERRADO | RECONCILIADO
  "reconciled_at": null,
  "reconciliation_diff": null,
  
  // Versionado para cambios retroactivos
  "version": 1
}
```

**Índices**:
```javascript
// Índice único para UPSERT
{ "server_id": 1, "fecha": 1, "sucursal_id": 1 } // unique: true

// Índices de consulta
{ "fecha": -1 }  // Ordenar por fecha descendente
{ "server_id": 1, "fecha": -1 }  // Consultas por servidor
{ "estado_periodo": 1, "fecha": -1 }  // Filtrar por estado
```

### 2.2 Tabla/Colección: `kpis_comercial_historico`

**Propósito**: Almacenar versiones anteriores de KPIs modificados retroactivamente

```javascript
{
  "original_id": "referencia_al_documento_principal",
  "server_id": "uuid",
  "fecha": "2026-04-21",
  "sucursal_id": "codigo_sucursal",
  
  // Snapshot completo del documento anterior
  "kpis_snapshot": { /* copia del documento original */ },
  
  // Metadata de cambio
  "replaced_at": ISODate("2026-04-22T10:30:00Z"),
  "replaced_by": "scheduler_reconciliacion",
  "reason": "Reconciliación mensual",
  "diff": {
    "ventas": { "old": 125000.00, "new": 126500.00 },
    "cheques": { "old": 120, "new": 122 }
  }
}
```

### 2.3 Tabla/Colección: `kpis_compras_diarios`

**Propósito**: Almacenar KPIs de compras por día/servidor

```javascript
{
  // Clave única
  "server_id": "uuid",
  "fecha": "2026-04-21",
  
  // KPIs de compras
  "kpis": {
    "total_compras": 50000.00,
    "total_movimientos": 120,
    "proveedores_activos": 15,
    "pedidos_generados": 5,
    "pedidos_autorizados": 4
  },
  
  // Top proveedores del día
  "top_proveedores": [
    {"proveedor": "PROVEEDOR X", "monto": 15000.00},
    {"proveedor": "PROVEEDOR Y", "monto": 10000.00}
  ],
  
  // Metadata
  "created_at": ISODate("2026-04-22T03:20:00Z"),
  "updated_at": ISODate("2026-04-22T03:20:00Z"),
  "source": "SoftRestaurant",
  "estado_periodo": "CERRADO"
}
```

---

## 3. SCHEDULERS DE SINCRONIZACIÓN

### 3.1 SYNC-S: Sincronización Corta (cada 15 minutos)

**Archivo**: `/app/backend/schedulers/sync_short_comercial.py`

```python
"""
SYNC-S: Sincronización corta de KPIs comerciales.
Frecuencia: Cada 15 minutos
Ventana: Últimas 48 horas
"""

async def sync_short_kpis_comercial():
    """
    Sincroniza KPIs de las últimas 48 horas.
    
    Proceso:
    1. Para cada servidor activo
    2. Consultar KPIs de los últimos 2 días (ventana deslizante)
    3. UPSERT en kpis_comercial_diarios
    4. Marcar días > 48h como candidatos a período CERRADO
    """
    servers = await get_active_servers()
    
    fecha_fin = datetime.now().date()
    fecha_ini = fecha_fin - timedelta(days=2)  # 48 horas
    
    for server in servers:
        try:
            # Consultar SQL externo
            kpis_list = await query_kpis_rango(server, fecha_ini, fecha_fin)
            
            for kpi_dia in kpis_list:
                # UPSERT obligatorio
                await upsert_kpi_diario(
                    server_id=server['id'],
                    fecha=kpi_dia['fecha'],
                    sucursal_id=kpi_dia['sucursal_id'],
                    kpis=kpi_dia['kpis'],
                    source=server['system_type']
                )
            
            logging.info(f"SYNC-S: {server['name']} - {len(kpis_list)} días actualizados")
            
        except Exception as e:
            logging.error(f"SYNC-S error {server['name']}: {e}")
```

**Ejecución**:
```python
# En startup del servidor
scheduler.add_job(
    sync_short_kpis_comercial,
    'interval',
    minutes=15,
    id='sync_short_comercial',
    replace_existing=True
)
```

### 3.2 SYNC-N: Sincronización Nocturna (03:00)

**Archivo**: `/app/backend/schedulers/sync_nightly_comercial.py`

```python
"""
SYNC-N: Consolidación nocturna de KPIs.
Frecuencia: Diario 03:00
Ventana: Últimos 7 días (captura ajustes tardíos)
"""

async def sync_nightly_kpis_comercial():
    """
    Consolidación nocturna completa.
    
    Proceso:
    1. Para cada servidor activo
    2. Consultar KPIs de los últimos 7 días
    3. UPSERT con detección de cambios
    4. Marcar días anteriores como CERRADO
    5. Generar log de cambios detectados
    """
    servers = await get_active_servers()
    
    fecha_fin = (datetime.now() - timedelta(days=1)).date()  # Ayer
    fecha_ini = fecha_fin - timedelta(days=6)  # 7 días atrás
    
    cambios_detectados = []
    
    for server in servers:
        try:
            kpis_list = await query_kpis_rango(server, fecha_ini, fecha_fin)
            
            for kpi_dia in kpis_list:
                # Verificar si hubo cambios vs lo guardado
                existing = await get_kpi_diario(server['id'], kpi_dia['fecha'], kpi_dia['sucursal_id'])
                
                if existing and has_differences(existing, kpi_dia):
                    # Guardar versión anterior en histórico
                    await save_to_historico(existing, "SYNC-N ajuste tardío")
                    cambios_detectados.append({
                        "server": server['name'],
                        "fecha": kpi_dia['fecha'],
                        "diff": calculate_diff(existing, kpi_dia)
                    })
                
                # UPSERT
                await upsert_kpi_diario(
                    server_id=server['id'],
                    fecha=kpi_dia['fecha'],
                    sucursal_id=kpi_dia['sucursal_id'],
                    kpis=kpi_dia['kpis'],
                    estado_periodo="CERRADO" if kpi_dia['fecha'] < fecha_fin else "ABIERTO"
                )
            
            logging.info(f"SYNC-N: {server['name']} - {len(kpis_list)} días consolidados")
            
        except Exception as e:
            logging.error(f"SYNC-N error {server['name']}: {e}")
    
    # Notificar cambios detectados
    if cambios_detectados:
        await notify_changes(cambios_detectados)
```

**Ejecución**:
```python
scheduler.add_job(
    sync_nightly_kpis_comercial,
    'cron',
    hour=3,
    minute=0,
    id='sync_nightly_comercial',
    replace_existing=True
)
```

### 3.3 Reconciliación Mensual (Día 5)

**Archivo**: `/app/backend/schedulers/reconciliation_monthly.py`

```python
"""
Reconciliación mensual de KPIs.
Frecuencia: Día 5 de cada mes
Ventana: Mes anterior completo
"""

async def reconciliation_monthly():
    """
    Reconciliación mensual completa.
    
    Proceso:
    1. Determinar mes anterior
    2. Para cada servidor:
       a. Leer TODOS los registros del mes desde SQL externo
       b. Comparar vs EDARSA HUB
       c. Aplicar diferencias con marca de reconciliación
       d. Generar reporte de discrepancias
    3. Marcar mes como RECONCILIADO
    """
    # Calcular mes anterior
    hoy = datetime.now()
    primer_dia_mes_actual = hoy.replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
    
    fecha_ini = primer_dia_mes_anterior.strftime('%Y-%m-%d')
    fecha_fin = ultimo_dia_mes_anterior.strftime('%Y-%m-%d')
    
    logging.info(f"RECONCILIACIÓN MENSUAL: {fecha_ini} a {fecha_fin}")
    
    discrepancias = []
    servers = await get_active_servers()
    
    for server in servers:
        try:
            # Leer todo el mes desde SQL externo
            kpis_sql = await query_kpis_mes_completo(server, fecha_ini, fecha_fin)
            
            for kpi in kpis_sql:
                # Comparar vs EDARSA HUB
                kpi_hub = await get_kpi_diario(server['id'], kpi['fecha'], kpi['sucursal_id'])
                
                if kpi_hub and has_differences(kpi_hub, kpi):
                    diff = calculate_diff(kpi_hub, kpi)
                    discrepancias.append({
                        "server": server['name'],
                        "fecha": kpi['fecha'],
                        "sucursal": kpi['sucursal_id'],
                        "diff": diff
                    })
                    
                    # Guardar versión anterior
                    await save_to_historico(kpi_hub, "Reconciliación mensual")
                
                # UPSERT con marca de reconciliación
                await upsert_kpi_diario(
                    server_id=server['id'],
                    fecha=kpi['fecha'],
                    sucursal_id=kpi['sucursal_id'],
                    kpis=kpi['kpis'],
                    estado_periodo="RECONCILIADO",
                    reconciled_at=datetime.now(timezone.utc).isoformat()
                )
            
        except Exception as e:
            logging.error(f"Reconciliación error {server['name']}: {e}")
    
    # Generar reporte
    await generate_reconciliation_report(fecha_ini, fecha_fin, discrepancias)
```

---

## 4. FUNCIONES UPSERT

### 4.1 UPSERT Obligatorio con Detección de Cambios

```python
async def upsert_kpi_diario(
    server_id: str,
    fecha: str,
    sucursal_id: str,
    kpis: Dict,
    source: str = None,
    estado_periodo: str = "ABIERTO",
    reconciled_at: str = None
) -> bool:
    """
    UPSERT obligatorio para KPIs diarios.
    
    Reglas:
    1. Clave única: server_id + fecha + sucursal_id
    2. Si existe: actualizar solo si hay cambios
    3. Si no existe: insertar
    4. Siempre actualizar updated_at
    """
    db = get_db()
    
    filter_query = {
        "server_id": server_id,
        "fecha": fecha,
        "sucursal_id": sucursal_id
    }
    
    update_doc = {
        "$set": {
            "kpis": kpis,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "estado_periodo": estado_periodo,
        },
        "$setOnInsert": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": 1
        }
    }
    
    if source:
        update_doc["$set"]["source"] = source
    
    if reconciled_at:
        update_doc["$set"]["reconciled_at"] = reconciled_at
    
    result = await db.kpis_comercial_diarios.update_one(
        filter_query,
        update_doc,
        upsert=True
    )
    
    return result.upserted_id is not None or result.modified_count > 0
```

---

## 5. VENTANA DESLIZANTE DE RELECTURA

| Scheduler | Ventana | Justificación |
|-----------|---------|---------------|
| **SYNC-S** | 48 horas | Captura correcciones del día anterior, ajustes de cierre Z tardío |
| **SYNC-N** | 7 días | Captura ajustes contables de la semana, notas de crédito |
| **Reconciliación** | Mes completo | Validación de integridad total del período |

### Implementación de Ventana

```python
def get_sync_window(sync_type: str) -> tuple:
    """Calcula la ventana de fechas según el tipo de sync."""
    hoy = datetime.now().date()
    
    if sync_type == "SYNC-S":
        return (hoy - timedelta(days=2), hoy)
    
    elif sync_type == "SYNC-N":
        return (hoy - timedelta(days=7), hoy - timedelta(days=1))
    
    elif sync_type == "RECONCILIATION":
        # Mes anterior completo
        primer_dia_mes = hoy.replace(day=1)
        ultimo_dia_mes_ant = primer_dia_mes - timedelta(days=1)
        primer_dia_mes_ant = ultimo_dia_mes_ant.replace(day=1)
        return (primer_dia_mes_ant, ultimo_dia_mes_ant)
    
    raise ValueError(f"Tipo de sync desconocido: {sync_type}")
```

---

## 6. PERÍODOS ABIERTOS vs CERRADOS

| Estado | Definición | Comportamiento |
|--------|------------|----------------|
| **ABIERTO** | El día/mes puede tener cambios (no hay corte Z completo) | SYNC-S activo, datos se refrescan constantemente |
| **CERRADO** | Ya hubo corte Z o fin de día oficial | Dato estable, solo SYNC-N lo toca |
| **RECONCILIADO** | Período validado en reconciliación mensual | Inmutable salvo corrección manual autorizada |

### Transiciones de Estado

```
ABIERTO → CERRADO: Automático cuando el día termina (en SYNC-N)
CERRADO → RECONCILIADO: En reconciliación mensual (día 5)
RECONCILIADO → RECONCILIADO: Solo con corrección manual + auditoría
```

---

## 7. MANEJO DE CAMBIOS RETROACTIVOS

### 7.1 Detección de Cambios

```python
def has_differences(existing: Dict, new: Dict, tolerance: float = 0.01) -> bool:
    """
    Detecta si hay diferencias significativas entre KPIs.
    Tolerancia: 1% para evitar falsos positivos por redondeo.
    """
    kpis_old = existing.get('kpis', {})
    kpis_new = new.get('kpis', {})
    
    for key in ['ventas', 'pax', 'cheques']:
        old_val = kpis_old.get(key, 0) or 0
        new_val = kpis_new.get(key, 0) or 0
        
        if old_val == 0 and new_val == 0:
            continue
        
        diff_pct = abs(new_val - old_val) / max(old_val, new_val, 1)
        if diff_pct > tolerance:
            return True
    
    return False
```

### 7.2 Versionado en Histórico

```python
async def save_to_historico(document: Dict, reason: str):
    """
    Guarda versión anterior de un documento antes de actualizarlo.
    """
    db = get_db()
    
    historico_doc = {
        "original_id": document.get('_id'),
        "server_id": document.get('server_id'),
        "fecha": document.get('fecha'),
        "sucursal_id": document.get('sucursal_id'),
        "kpis_snapshot": document.get('kpis'),
        "replaced_at": datetime.now(timezone.utc).isoformat(),
        "replaced_by": "scheduler",
        "reason": reason,
        "version": document.get('version', 1)
    }
    
    await db.kpis_comercial_historico.insert_one(historico_doc)
```

---

## 8. MIGRACIÓN DE ENDPOINTS

### 8.1 Tablero Ejecutivo - Datos Históricos

**Antes** (LIVE a SQL externo):
```python
# Consulta SQL para año anterior
r_año = execute_sql_query(server, query_año_anterior)
```

**Después** (EDARSA HUB FIRST):
```python
async def get_kpis_año_anterior(server_id: str, fecha_referencia: str) -> Dict:
    """
    Lee KPIs del año anterior desde EDARSA HUB.
    Fallback a SQL solo si no hay datos consolidados.
    """
    db = get_db()
    
    # Calcular rango del año anterior (mismos días)
    fecha_ref = datetime.strptime(fecha_referencia, '%Y-%m-%d')
    fecha_ini_año_ant = (fecha_ref - timedelta(days=365)).strftime('%Y-%m-%d')
    fecha_fin_año_ant = fecha_referencia.replace(str(fecha_ref.year), str(fecha_ref.year - 1))
    
    # Buscar en EDARSA HUB
    kpis = await db.kpis_comercial_diarios.find({
        "server_id": server_id,
        "fecha": {"$gte": fecha_ini_año_ant, "$lte": fecha_fin_año_ant}
    }).to_list(100)
    
    if kpis:
        return aggregate_kpis(kpis)
    
    # Fallback: consultar SQL (marcar para futura consolidación)
    logging.warning(f"FALLBACK SQL: KPIs año anterior no consolidados para {server_id}")
    return await query_sql_año_anterior(server_id, fecha_ini_año_ant, fecha_fin_año_ant)
```

---

## 9. CRONOGRAMA DE IMPLEMENTACIÓN

| Semana | Tarea | Entregable |
|--------|-------|------------|
| 1 | Crear esquema en EDARSA HUB | Colecciones + índices |
| 1 | Implementar función UPSERT | `upsert_kpi_diario()` |
| 2 | Implementar SYNC-S | Scheduler cada 15 min |
| 2 | Implementar SYNC-N | Scheduler nocturno |
| 3 | Carga inicial histórica | Últimos 24 meses |
| 3 | Implementar reconciliación | Scheduler día 5 |
| 4 | Migrar endpoints | Tablero año anterior → EDARSA HUB |
| 4 | Pruebas de integración | Validar no regresión |

---

## HISTORIAL DE CAMBIOS

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-04-22 | 1.0 | Documento inicial - Diseño técnico MACROFASE 2 |
