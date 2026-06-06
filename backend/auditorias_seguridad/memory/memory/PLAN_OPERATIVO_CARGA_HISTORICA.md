# PLAN OPERATIVO: EJECUCIÓN CARGA HISTÓRICA 24 MESES

**Fecha:** 2026-04-23  
**Versión:** 1.1 (Corregido)  
**Estado:** PENDIENTE DE EJECUCIÓN  
**Prerrequisito:** Conectividad efectiva a las fuentes según configuración del menú de Servidores

---

## 1. AMBIENTE OBJETIVO DE EJECUCIÓN

### 1.1 Definición Arquitectónica

EDARSA HUB **no asume un único mecanismo de conectividad** para todas las unidades.
Cada servidor origen tiene su propio tipo de conexión configurado en el **menú de Servidores**:

| Tipo de Conexión | Descripción |
|------------------|-------------|
| **SQL** | Conexión directa a base de datos SQL Server |
| **API** | Conexión vía API REST del sistema origen |

### 1.2 Ambiente de Ejecución Correcto

**Ambiente con conectividad operativa efectiva a las fuentes configuradas en el menú de Servidores de EDARSA HUB**, validando para cada servidor:
- Tipo de conexión (SQL o API)
- Credenciales/configuración válidas
- Disponibilidad del origen al momento de la carga

### 1.3 Opciones de Ambiente

| Opción | Descripción | Consideración |
|--------|-------------|---------------|
| **A - Producción EDARSA** | Servidor de producción con acceso a orígenes | ⭐ RECOMENDADO |
| **B - Preview** | Si tiene conectividad configurada a orígenes | Alternativa |
| **C - Local** | Máquina con acceso a los orígenes configurados | Para pruebas |

---

## 2. PRERREQUISITOS DE CONECTIVIDAD

### 2.1 Principio Arquitectónico

> EDARSA HUB no debe asumir un único mecanismo de conectividad para todas las unidades.
> Cada servidor puede tener un tipo de acceso distinto.
> El plan operativo debe validar servidor por servidor qué tipo de conexión usa y si está disponible.

### 2.2 Checklist de Conectividad por Servidor

**Para CADA servidor en el menú de Servidores, validar:**

| # | Validación | Criterio |
|---|------------|----------|
| 1 | Servidor habilitado en menú de Servidores | `status` = activo |
| 2 | Tipo de conexión identificado | SQL o API |
| 3 | Credenciales/configuración válidas | host, port, user, pass (SQL) o endpoint, token (API) |
| 4 | Prueba de conectividad exitosa | Query de prueba responde |
| 5 | Origen responde correctamente | Datos coherentes |
| 6 | Timeout configurado | Manejo de error validado |

### 2.3 Script de Verificación Pre-Carga

```python
# Ejecutar ANTES de la carga
# Valida conectividad de cada servidor según su tipo

async def verificar_conectividad_servidores():
    """
    Verifica conectividad de cada servidor según su configuración
    en el menú de Servidores de EDARSA HUB.
    """
    from pymongo import MongoClient
    import os
    
    client = MongoClient(os.environ.get('MONGO_URL'))
    db = client[os.environ.get('DB_NAME', 'edarsa_hub')]
    
    servidores = list(db.servers.find({
        "system_type": {"$in": ["SoftRestaurant", "MPRO"]}
    }))
    
    resultados = []
    
    for srv in servidores:
        resultado = {
            "nombre": srv.get('name'),
            "system_type": srv.get('system_type'),
            "tipo_conexion": "SQL" if srv.get('host') else "API",
            "status_config": srv.get('status'),
            "conectividad": None,
            "error": None
        }
        
        # Determinar tipo de conexión
        if srv.get('host'):
            # Conexión SQL
            resultado["tipo_conexion"] = "SQL"
            resultado["config"] = f"{srv.get('host')}:{srv.get('port')}"
            
            # Probar conexión SQL
            try:
                from core.db import execute_sql_query
                test_result = execute_sql_query(
                    srv['host'], srv['port'], srv['database'],
                    srv['username'], srv['password'],
                    "SELECT 1 as test"
                )
                resultado["conectividad"] = "OK" if test_result else "SIN_DATOS"
            except Exception as e:
                resultado["conectividad"] = "ERROR"
                resultado["error"] = str(e)[:100]
        
        elif srv.get('api_endpoint'):
            # Conexión API
            resultado["tipo_conexion"] = "API"
            resultado["config"] = srv.get('api_endpoint')
            
            # Probar conexión API
            try:
                import httpx
                response = httpx.get(srv['api_endpoint'], timeout=10)
                resultado["conectividad"] = "OK" if response.status_code == 200 else f"HTTP_{response.status_code}"
            except Exception as e:
                resultado["conectividad"] = "ERROR"
                resultado["error"] = str(e)[:100]
        
        else:
            resultado["tipo_conexion"] = "NO_CONFIGURADO"
            resultado["conectividad"] = "N/A"
        
        resultados.append(resultado)
        print(f"[{resultado['tipo_conexion']}] {resultado['nombre']}: {resultado['conectividad']}")
    
    return resultados
```

### 2.4 Checklist Pre-Ejecución General

| # | Verificación | Responsable | Estado |
|---|--------------|-------------|--------|
| 1 | MongoDB accesible | Operaciones | ⬜ |
| 2 | Script de verificación ejecutado | Operaciones | ⬜ |
| 3 | Todos los servidores objetivo con conectividad OK | Operaciones | ⬜ |
| 4 | Backup de kpis_comercial realizado | DBA | ⬜ |
| 5 | Ventana operativa autorizada | Gerencia | ⬜ |

### 2.5 Matriz de Servidores y Conectividad

| Servidor | Tipo Sistema | Tipo Conexión | Config | Estado Conectividad |
|----------|--------------|---------------|--------|---------------------|
| CIENFUEGOS | SoftRestaurant | SQL | host:port | ⬜ Pendiente |
| LA ESTELAR | SoftRestaurant | SQL | host:port | ⬜ Pendiente |
| 130° MERIDA | SoftRestaurant | SQL | host:port | ⬜ Pendiente |
| ManagmentPro | MPRO | SQL | host:port | ⬜ Pendiente |
| MPRO TABLAJERIA | MPRO | SQL | host:port | ⬜ Pendiente |
| CIENFUEGOS TABLAJERIA | SoftRestaurant | SQL | host:port | ⬜ Pendiente |
| HR2020 ESCRITURA | MPRO | SQL | host:port | ⬜ Pendiente |
| PRUEBAS SOFTRESTAURANT | SoftRestaurant | SQL | host:port | ⬜ Pendiente |

**Nota**: Esta matriz debe completarse ejecutando el script de verificación antes de la carga.

---

## 3. VENTANA OPERATIVA SUGERIDA

### 3.1 Horario Recomendado

| Aspecto | Valor | Justificación |
|---------|-------|---------------|
| **Día** | Sábado o Domingo | Menor carga operativa |
| **Hora inicio** | 02:00 - 04:00 AM | Fuera de horario SYNC-S/SYNC-N |
| **Duración estimada** | 60-120 minutos | Depende de conectividad de cada servidor |
| **Hora fin máxima** | 06:00 AM | Antes de actividad diurna |

### 3.2 Estimación de Tiempos

```
Por servidor (con conectividad efectiva):
  - 25 meses × ~30 días = ~750 consultas
  - Tiempo promedio por consulta: 2-5 segundos (SQL) / 1-3 segundos (API)
  - Tiempo por servidor: 25-60 minutos (con reintentos)

Total estimado:
  - 8 servidores × 45 min promedio = 6 horas (secuencial)
  - Con paralelización: 2-3 horas
  - Solo servidores con conectividad OK serán procesados

Recomendación: Ejecutar solo servidores con conectividad validada
```

### 3.3 Plan de Contingencia de Tiempo

| Situación | Acción |
|-----------|--------|
| Servidor sin conectividad | Saltar, registrar, continuar con siguientes |
| Carga toma más de 3 horas | Pausar y retomar siguiente ventana |
| Pérdida de conectividad mid-carga | Detener ese servidor, continuar con otros |

---

## 4. ORDEN DE SERVIDORES/SUCURSALES

### 4.1 Regla Operativa

> **Antes de ejecutar Fase 2.3, validar por cada servidor:**
> 1. Nombre del servidor
> 2. Tipo de conexión (SQL o API)
> 3. Método de acceso efectivo
> 4. Estado de conectividad (OK / ERROR)
> 5. Si entra o no en la ventana de carga

### 4.2 Orden de Ejecución (Prioridad)

| Orden | Servidor | Tipo Sistema | Tipo Conexión | Prioridad | Entra en Carga |
|-------|----------|--------------|---------------|-----------|----------------|
| 1 | CIENFUEGOS | SoftRestaurant | SQL | 🔴 ALTA | ⬜ Si conectividad OK |
| 2 | LA ESTELAR | SoftRestaurant | SQL | 🔴 ALTA | ⬜ Si conectividad OK |
| 3 | 130° MERIDA | SoftRestaurant | SQL | 🟡 MEDIA | ⬜ Si conectividad OK |
| 4 | ManagmentPro | MPRO | SQL | 🟡 MEDIA | ⬜ Si conectividad OK |
| 5 | MPRO TABLAJERIA | MPRO | SQL | 🟡 MEDIA | ⬜ Si conectividad OK |
| 6 | CIENFUEGOS TABLAJERIA | SoftRestaurant | SQL | 🟢 BAJA | ⬜ Si conectividad OK |
| 7 | HR2020 ESCRITURA | MPRO | SQL | 🟢 BAJA | ⬜ Si conectividad OK |
| 8 | PRUEBAS SOFTRESTAURANT | SoftRestaurant | SQL | ⚪ OPCIONAL | ⬜ Si hay tiempo |

### 4.3 Lógica de Procesamiento por Servidor

```
Para cada servidor:
  1. Obtener configuración del menú de Servidores
  2. Identificar tipo de conexión (SQL o API)
  3. Verificar conectividad según tipo:
     - SQL: Ejecutar query de prueba
     - API: Hacer request de prueba
  4. Si conectividad OK:
     a. Procesar meses de más antiguo a más reciente
     b. Por cada mes:
        - Consultar ventas según tipo de conexión
        - UPSERT cada día con kpis
        - Registrar en bitácora
     c. Al terminar mes: log de progreso
  5. Si conectividad FAIL:
     a. Registrar error con tipo de conexión y causa
     b. Continuar con siguiente servidor
     c. Marcar para validación posterior
```

---

## 5. CRITERIO DE ROLLBACK

### 5.1 Condiciones de Activación de Rollback

| Condición | Acción | Comando |
|-----------|--------|---------|
| Duplicados > 0 detectados | ROLLBACK INMEDIATO | Ver 5.2 |
| Error de integridad en MongoDB | ROLLBACK INMEDIATO | Ver 5.2 |
| Datos corruptos en kpis existentes | ROLLBACK INMEDIATO | Ver 5.2 |
| Más de 50% errores en un servidor | ROLLBACK PARCIAL (ese servidor) | Ver 5.3 |
| Usuario solicita cancelación | ROLLBACK TOTAL | Ver 5.2 |

### 5.2 Comando de Rollback Total

```javascript
// Ejecutar en MongoDB shell o compass
// ANTES: Verificar cuántos registros se eliminarán
db.kpis_comercial.countDocuments({created_by: 'carga_historica_fase23'})

// ROLLBACK: Eliminar todos los registros de la carga
db.kpis_comercial.deleteMany({created_by: 'carga_historica_fase23'})

// VERIFICAR: Confirmar que solo quedan los originales
db.kpis_comercial.countDocuments({})
// Debe ser 38 (registros pre-existentes)
```

### 5.3 Rollback Parcial (Por Servidor)

```javascript
// Eliminar solo registros de un servidor específico
db.kpis_comercial.deleteMany({
  created_by: 'carga_historica_fase23',
  server_id: '<UUID_DEL_SERVIDOR>'
})
```

### 5.4 Backup Pre-Ejecución (OBLIGATORIO)

```bash
# Crear backup antes de iniciar
mongodump --uri="$MONGO_URL" --db=edarsa_hub --collection=kpis_comercial --out=/backup/pre_carga_historica_$(date +%Y%m%d_%H%M%S)

# Restaurar si es necesario
mongorestore --uri="$MONGO_URL" --db=edarsa_hub --collection=kpis_comercial /backup/pre_carga_historica_YYYYMMDD_HHMMSS/edarsa_hub/kpis_comercial.bson
```

---

## 6. VALIDACIONES POST-CARGA REALES

### 6.1 Validaciones Automáticas (Script)

```python
# Ejecutar después de la carga
async def validar_post_carga():
    validaciones = {}
    
    # 1. DUPLICADOS (CRÍTICO)
    pipeline = [
        {"$group": {
            "_id": {"server_id": "$server_id", "empresa_id": "$empresa_id", 
                    "sucursal_id": "$sucursal_id", "fecha": "$fecha"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    duplicados = await db.kpis_comercial.aggregate(pipeline).to_list(100)
    validaciones["duplicados"] = len(duplicados)
    validaciones["duplicados_ok"] = len(duplicados) == 0
    
    # 2. CONTEO TOTAL
    total = await db.kpis_comercial.count_documents({})
    total_nuevos = await db.kpis_comercial.count_documents({
        "created_by": "carga_historica_fase23"
    })
    validaciones["total_documentos"] = total
    validaciones["documentos_nuevos"] = total_nuevos
    
    # 3. RANGO DE FECHAS
    min_doc = await db.kpis_comercial.find_one(sort=[("fecha", 1)])
    max_doc = await db.kpis_comercial.find_one(sort=[("fecha", -1)])
    validaciones["fecha_min"] = min_doc.get("fecha")
    validaciones["fecha_max"] = max_doc.get("fecha")
    validaciones["rango_24_meses"] = # calcular si cubre 24 meses
    
    # 4. POR SERVIDOR
    pipeline_servers = [
        {"$match": {"created_by": "carga_historica_fase23"}},
        {"$group": {"_id": "$server_id", "count": {"$sum": 1}}}
    ]
    por_servidor = await db.kpis_comercial.aggregate(pipeline_servers).to_list(20)
    validaciones["por_servidor"] = por_servidor
    
    # 5. INTEGRIDAD DE DATOS PREVIOS
    # Verificar que los 38 registros originales siguen intactos
    originales = await db.kpis_comercial.count_documents({
        "created_by": {"$ne": "carga_historica_fase23"}
    })
    validaciones["registros_originales"] = originales
    validaciones["originales_intactos"] = originales >= 38
    
    return validaciones
```

### 6.2 Validaciones Manuales (Checklist)

| # | Validación | Criterio de Éxito | Resultado |
|---|------------|-------------------|-----------|
| 1 | Duplicados = 0 | Exactamente 0 | ⬜ |
| 2 | Registros originales intactos | >= 38 documentos sin `carga_historica_fase23` | ⬜ |
| 3 | Rango de fechas | Desde ~2024-04-01 hasta ~2026-04-16 | ⬜ |
| 4 | Cobertura de servidores | 8 servidores con datos | ⬜ |
| 5 | Estado de período | Todos históricos en CERRADO | ⬜ |
| 6 | UPSERT idempotente | Re-ejecutar script no duplica | ⬜ |
| 7 | Queries de tablero funcionan | `/api/comercial/tablero-ejecutivo` responde | ⬜ |
| 8 | Datos coherentes | Ventas, PAX, Cheques en rangos esperados | ⬜ |

### 6.3 Validación de Muestra (Spot Check)

```javascript
// Seleccionar 5 registros aleatorios de la carga y verificar:
db.kpis_comercial.aggregate([
  {$match: {created_by: 'carga_historica_fase23'}},
  {$sample: {size: 5}}
]).forEach(doc => {
  print(`Fecha: ${doc.fecha}, Servidor: ${doc.server_id}`);
  print(`  Ventas: ${doc.kpis.ventas}, PAX: ${doc.kpis.pax}, Cheques: ${doc.kpis.cheques}`);
  print(`  Estado: ${doc.estado_periodo}`);
});
```

---

## 7. DICTAMEN ESPERADO TRAS EJECUCIÓN

### 7.1 Escenario A: Éxito Total

```
## ✅ FASE 2.3 EJECUCIÓN COMPLETADA

- Documentos insertados: [N]
- Duplicados: 0
- Errores: 0
- Rango: 2024-04-01 a 2026-04-16
- Servidores: 8/8 procesados
- Registros originales: Intactos

DICTAMEN: FASE 2.3 COMPLETADA EXITOSAMENTE
```

### 7.2 Escenario B: Éxito Parcial

```
## 🟡 FASE 2.3 EJECUCIÓN PARCIAL

- Documentos insertados: [N]
- Duplicados: 0
- Errores: [M] (servidores sin conectividad)
- Servidores procesados: [X]/8
- Servidores pendientes: [lista]

DICTAMEN: FASE 2.3 COMPLETADA CON OBSERVACIONES
- Requiere reintento para servidores fallidos
- Datos parciales disponibles para análisis
```

### 7.3 Escenario C: Fallo / Rollback

```
## ❌ FASE 2.3 EJECUCIÓN FALLIDA - ROLLBACK APLICADO

- Motivo: [duplicados/error crítico/corrupción]
- Rollback ejecutado: Sí
- Documentos eliminados: [N]
- Estado actual: Igual que pre-ejecución (38 docs)

DICTAMEN: FASE 2.3 NO APROBADA
- Requiere análisis de causa raíz
- No proceder con operaciones dependientes
```

---

## 8. RESUMEN DE DECISIONES PENDIENTES

| # | Decisión | Opciones | Responsable |
|---|----------|----------|-------------|
| 1 | Ambiente de ejecución | Producción con conectividad efectiva a orígenes | Usuario |
| 2 | Fecha y hora de ventana | Sábado/Domingo 02:00-06:00 | Usuario |
| 3 | ¿Ejecutar antes o en paralelo con Bloque 5? | Antes (recomendado) / Paralelo | Usuario |
| 4 | Responsable de ejecución | E1 Agent / Operaciones EDARSA | Usuario |

---

## 9. ACLARACIÓN ARQUITECTÓNICA

> **EDARSA HUB no asume un único mecanismo de conectividad para todas las unidades.**
> 
> - Cada servidor puede tener un tipo de acceso distinto (SQL o API)
> - El tipo de conexión se define en el **menú de Servidores**
> - El plan operativo debe validar servidor por servidor:
>   - Qué tipo de conexión usa
>   - Si está disponible al momento de la carga
>   - Si las credenciales/configuración son válidas
> 
> **NO se asume conectividad general tipo VPN para todos los orígenes.**
> **Cada origen tiene su propio mecanismo de acceso configurado.**

---

**Este documento queda como guía operativa para la ejecución real.**
**No proceder sin confirmación de prerrequisitos y ventana autorizada.**
**Validar conectividad de cada servidor según su tipo de conexión antes de iniciar.**

---

Firma: E1 Agent  
Fecha: 2026-04-23  
Versión: 1.1 (Corregido para alinear con arquitectura de conectividad de EDARSA HUB)
