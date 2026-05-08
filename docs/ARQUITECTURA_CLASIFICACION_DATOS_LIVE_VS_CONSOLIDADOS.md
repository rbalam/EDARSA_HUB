# EDARSA HUB - Arquitectura de Clasificación de Datos
## LIVE OPERATIVO vs ANALÍTICO/CONSOLIDADO

**Versión**: 1.0  
**Fecha**: Abril 2026  
**Autor**: Arquitectura Senior  
**Estado**: VIGENTE  

---

## 1. DEFINICIONES FORMALES

### 1.1 TIPO A: LIVE OPERATIVO ("LIVE FIRST, PERSIST SECOND")

**Definición**: Módulos que requieren información en tiempo real de los sistemas origen (SoftRestaurant, MPRO) para tomar decisiones operativas críticas.

**Principio**: 
```
CONSULTA LIVE → DECISIÓN → PERSISTENCIA POSTERIOR
```

**Características**:
- La decisión del usuario depende de datos actuales (segundos/minutos)
- Un dato obsoleto puede causar errores operativos graves
- El cache/réplica NUNCA puede ser fuente de verdad
- Si no hay conexión, MOSTRAR ERROR (no datos de cache)
- La persistencia a EDARSA HUB es para auditoría, no para lectura operativa

**Fuentes Válidas**:
- SQL Server externo (SoftRestaurant, MPRO) - Conexión directa
- API local de punto de venta (cuando esté disponible)

**Fuentes INVÁLIDAS para decisiones operativas**:
- MongoDB cache
- Réplica diferida
- Datos consolidados de días anteriores

---

### 1.2 TIPO B: ANALÍTICO/EJECUTIVO ("EDARSA HUB FIRST")

**Definición**: Módulos que muestran información histórica, consolidada o que sirve para análisis, donde la latencia de minutos/horas es aceptable.

**Principio**:
```
EDARSA HUB (YA CONSOLIDADO) → PRESENTACIÓN → SINCRONIZACIÓN EN BACKGROUND
```

**Características**:
- Los datos ya fueron sincronizados previamente (scheduler, trigger, manual)
- La decisión del usuario NO es crítica al segundo
- Se acepta que los datos tengan latencia de minutos a horas
- El cache SÍ puede ser fuente de verdad
- Si EDARSA HUB no responde, mostrar "Servicio no disponible"

**Fuentes Válidas**:
- SQL Server EDARSA HUB (tablas propias)
- Almacenamiento estructurado interno de EDARSA HUB (la tecnología específica se decide según el caso)

**Importante**: EDARSA HUB es el cerebro del sistema. La tecnología de persistencia específica (SQL Server propio, almacenamiento estructurado, etc.) se decide según el caso de uso, pero la regla arquitectónica siempre habla de EDARSA HUB como fuente, no de una tecnología específica como MongoDB.

**Procesos de Sincronización Separados**:
- SYNC-S: Sincronización corta (cada 10-15 min) para datos recientes
- SYNC-N: Consolidación nocturna (03:00) para períodos cerrados
- POST-CIERRE: Sincronización por evento (después de corte Z o cierre)
- Reconciliación mensual: Validación de integridad

---

### 1.3 TIPO MIXTO

**Definición**: Módulos que combinan datos LIVE para ciertas operaciones y datos consolidados para otras.

**Ejemplo**: Módulo de Inventarios
- **LIVE**: Ver existencias actuales para decidir pedido → SQL externo
- **CONSOLIDADO**: Ver historial de movimientos del mes → EDARSA HUB

---

## 2. INVENTARIO DE MÓDULOS Y CLASIFICACIÓN

### 2.1 MÓDULOS TIPO A - LIVE OPERATIVO

| Módulo | Archivo Backend | Fuente Actual | Estado | Notas |
|--------|----------------|---------------|--------|-------|
| **Compras - Pedidos Vigentes** | `modules/compras/service.py` | SQL externo | ✅ CORRECTO | Usa `repo.query_pedidos_vigentes_mpro()` |
| **Compras - Inventarios Físicos** | `modules/compras/service.py` | SQL externo | ✅ CORRECTO | Consulta viva a SoftRestaurant/MPRO |
| **Compras - Facturas Proveedor** | `modules/compras/service.py` | SQL externo | ✅ CORRECTO | Lee directamente de SQL origen |
| **Explorador BD** | `routes/` | SQL externo | ✅ CORRECTO | Por definición es consulta directa |
| **Servidores - Test Conexión** | `server.py` | SQL externo | ✅ CORRECTO | Prueba conectividad real |
| **Comercial - Ventas del Día** | `modules/comercial/service.py` | SQL externo + API local | ✅ CORRECTO | Usa `tempcheques` y API local MPRO |

### 2.2 MÓDULOS TIPO B - ANALÍTICO/EJECUTIVO (EDARSA HUB FIRST)

| Módulo | Archivo Backend | Fuente Actual | Estado | Notas |
|--------|----------------|---------------|--------|-------|
| **Tablero Ejecutivo** | `modules/comercial/` | SQL externo + cache | ⚠️ REVISAR | Usa `cache_service.py` con circuit breaker |
| **Comercial - Históricos** | `modules/comercial/service.py` | SQL externo + cache | ⚠️ REVISAR | Debería priorizar EDARSA HUB para históricos |
| **Finanzas - Cortes Caja** | `modules/finanzas/repository_real.py` | SQL EDARSA HUB | ✅ CORRECTO | Lee de tablas propias `Finanzas_*` |
| **Finanzas - Cuentas x Pagar** | `modules/finanzas/repository_real.py` | SQL EDARSA HUB | ✅ CORRECTO | Lee de `Finanzas_CuentasPorPagar` |
| **RH - Colaboradores** | `modules/rh/service.py` | SQL EDARSA HUB | ✅ CORRECTO | Lee de `RH_Colaboradores_*` |
| **RH - Incidencias** | `modules/rh/service.py` | SQL EDARSA HUB | ✅ CORRECTO | Lee de `RH_Incidencias_Nomina` |
| **RH - Flujo Nómina** | `modules/rh/service.py` | SQL EDARSA HUB | ✅ CORRECTO | Lee de tablas propias |
| **Catálogos** | `modules/catalogos/service.py` | SQL EDARSA HUB | ✅ CORRECTO | Lee de tablas propias |
| **Manuales Operativos** | `modules/manuales_operativos/` | MongoDB | ✅ CORRECTO | Documentos internos |
| **Configuración - Asignaciones** | `modules/configuracion/` | MongoDB | ✅ CORRECTO | Configuración interna |
| **Usuarios/Roles** | `modules/auth/` | MongoDB | ✅ CORRECTO | Datos internos del sistema |

### 2.3 MÓDULOS TIPO MIXTO

| Módulo | Operación LIVE | Operación Consolidada | Estado |
|--------|---------------|----------------------|--------|
| **Inventarios** | Ver stock actual | Ver historial movimientos | ✅ CORRECTO |
| **Fase2 Operativo** | Tareas activas | Auditorías históricas | ⚠️ REVISAR |
| **Auditorías Programadas** | Ejecución actual | Historial | ⚠️ REVISAR |

---

## 3. DESVIACIONES IDENTIFICADAS

### 3.1 CRÍTICA: Tablero Ejecutivo con Circuit Breaker

**Archivo**: `/app/backend/modules/comercial/cache_service.py`

**Problema Identificado**:
El Tablero Ejecutivo usa un `cache_service.py` que implementa un "circuit breaker" de 10 minutos. Si hubo un error de conexión SQL (ej: error de fecha que ya se corrigió), el sistema bloquea reintentos durante 10 minutos y muestra estado "OFFLINE" falsamente.

**Impacto**:
- El Tablero muestra "Offline" cuando el servidor YA ESTÁ disponible
- Los usuarios creen que hay un problema de infraestructura cuando no lo hay
- Falsos positivos de desconexión

**Código Actual**:
```python
# cache_service.py
CACHE_TTL = {
    "dashboard": 180,       # 3 minutos
    ...
}
```

**Recomendación**:
1. El Tablero Ejecutivo es **TIPO B** (Analítico) - usar datos de EDARSA HUB consolidados
2. Si se mantiene consulta a SQL externo, NO bloquear reintentos por error previo
3. Separar claramente: histórico (EDARSA HUB) vs tiempo real (opcional)

**Prioridad**: 🔴 ALTA

---

### 3.2 MEDIA: Comercial Históricos vs Live

**Archivo**: `/app/backend/modules/comercial/service.py`

**Problema Identificado**:
Las funciones `get_kpis_softrestaurant` y `get_kpis_mpro` consultan SQL externo para datos históricos del mes anterior y año anterior. Esto causa:
- Múltiples conexiones a servidores externos para datos que NO cambian
- Timeouts cuando el servidor externo está lento
- Carga innecesaria en infraestructura

**Impacto**:
- Latencia alta en Tablero Ejecutivo
- Dependencia de conexión externa para datos del año pasado

**Código Actual**:
```python
# Año anterior (mismos días) - Consulta SQL externo
query_año = f"""
SELECT ... FROM cheques ... WHERE ...
"""
r_año = execute_sql_query(server['host'], ...)
```

**Recomendación**:
1. Migrar datos históricos (mes anterior, año anterior) a EDARSA HUB
2. Consolidar KPIs en proceso nocturno
3. Solo consultar SQL externo para período actual

**Prioridad**: 🟡 MEDIA

---

### 3.3 BAJA: Endpoints secundarios de Comercial sin homologar

**Archivo**: `/app/backend/modules/comercial/routes.py`

**Problema Identificado**:
Algunos endpoints secundarios no usan el patrón `SourceQueryResult` para distinguir entre "consulta exitosa con cero" vs "error de conexión".

**Impacto**:
- Posibles ceros falsos cuando hay error de red

**Prioridad**: 🟢 BAJA

---

### 3.4 REVISAR: Fase2 Operativo - Mezcla de fuentes

**Archivo**: `/app/backend/modules/fase2_operativo/services/`

**Observación**:
El módulo Fase2 Operativo tiene múltiples servicios que mezclan consultas. Requiere auditoría para clasificar cada operación.

**Servicios a revisar**:
- `auditoria_service.py`
- `operativo_service.py`
- `automatizacion_compras_service.py`

**Prioridad**: 🟡 MEDIA

---

## 4. MÓDULOS QUE CUMPLEN CORRECTAMENTE

### 4.1 Finanzas (TIPO B - EDARSA HUB FIRST) ✅

El módulo de Finanzas consulta exclusivamente tablas propias en SQL Server EDARSA HUB:
- `Finanzas_CortesCaja`
- `Finanzas_CuentasPorPagar`
- `Finanzas_ConfiguracionTPV_Sucursal`

**Código correcto**:
```python
# repository_real.py
query = f"""
    SELECT ... FROM Finanzas_CortesCaja c
    LEFT JOIN RH_Cat_Sucursales s ON ...
    WHERE {where}
"""
return await self._execute_query(query)  # Ejecuta en EDARSA HUB
```

### 4.2 Recursos Humanos (TIPO B - EDARSA HUB FIRST) ✅

Todo el módulo RH usa exclusivamente EDARSA HUB:
- Colaboradores, Incidencias, Asistencia, Flujo Nómina, Reclutamiento
- Catálogos internos (Puestos, Sucursales, Tipos Incidencias)

### 4.3 Compras (TIPO A - LIVE OPERATIVO) ✅

El módulo de Compras correctamente consulta SQL externo para:
- Inventarios físicos actuales
- Pedidos vigentes
- Facturas recientes

---

## 5. REGLAS PARA NUEVOS DESARROLLOS

### 5.1 Checklist antes de crear un nuevo endpoint

1. **¿Los datos son para decisión operativa inmediata?**
   - SÍ → TIPO A (LIVE)
   - NO → TIPO B (EDARSA HUB)

2. **¿Un dato obsoleto (1 hora) causa problemas graves?**
   - SÍ → TIPO A
   - NO → TIPO B

3. **¿El dato cambia frecuentemente (minutos)?**
   - SÍ → TIPO A
   - NO → TIPO B

4. **¿Es un reporte/histórico/análisis?**
   - SÍ → TIPO B
   - NO → Evaluar caso por caso

### 5.2 Patrón de código para TIPO A

```python
async def obtener_stock_actual(server_id: str, producto_id: str):
    """TIPO A: Siempre consulta SQL externo en vivo."""
    server = await get_server(server_id)
    
    try:
        result = execute_sql_query(
            server['host'], server['port'], server['database'],
            server['username'], server['password'],
            f"SELECT stock FROM productos WHERE id = '{producto_id}'"
        )
        return {"status": "SUCCESS", "data": result}
    except Exception as e:
        # NUNCA retornar cache como verdad operativa
        return {"status": "ERROR", "message": str(e), "data": None}
```

### 5.3 Patrón de código para TIPO B

```python
async def obtener_ventas_mes_anterior(sucursal_id: str):
    """TIPO B: Consulta datos ya consolidados en EDARSA HUB."""
    # EDARSA HUB tiene los datos ya sincronizados
    result = await db.kpis_consolidados.find_one({
        "sucursal_id": sucursal_id,
        "periodo": "mes_anterior"
    })
    
    if not result:
        return {"status": "NO_DATA", "message": "Datos no disponibles"}
    
    return {"status": "SUCCESS", "data": result}
```

---

## 6. PLAN DE CORRECCIÓN PROPUESTO

### Fase 1: Documentación (COMPLETADA ✅)
- [x] Crear este documento de arquitectura
- [x] Actualizar NORMAS_TECNICAS.md
- [x] Inventario de módulos

### Fase 2: Corrección Tablero Ejecutivo (PRIORIDAD ALTA)
- [ ] Separar LIVE-C (ventas_dia, hoy sin corte) de HUB (históricos)
- [ ] Modificar circuit breaker para no bloquear reintentos en datos LIVE
- [ ] Implementar SYNC-S para días cerrados del mes actual

### Fase 3: Consolidación en EDARSA HUB (PRIORIDAD MEDIA)
- [ ] Diseñar esquema en EDARSA HUB para KPIs consolidados
- [ ] Implementar schedulers: SYNC-S (15 min), SYNC-N (03:00)
- [ ] Migrar históricos con política UPSERT + ventana deslizante
- [ ] Establecer reconciliación mensual

### Fase 4: Homologación SourceQueryResult (PRIORIDAD BAJA)
- [ ] Aplicar patrón en endpoints secundarios de Comercial
- [ ] Documentar respuestas estándar

---

## 7. GLOSARIO

| Término | Definición |
|---------|------------|
| **EDARSA HUB** | Sistema central de inteligencia empresarial. Cerebro del sistema. La tecnología de persistencia se decide según el caso. |
| **SQL Externo** | Servidores de punto de venta (SoftRestaurant, MPRO) que NO pertenecen a EDARSA HUB. |
| **LIVE-C** | Consulta en tiempo real crítica (latencia < 1 min). |
| **SYNC-S** | Sincronización corta (cada 10-15 min). |
| **SYNC-N** | Sincronización nocturna (consolidación diaria). |
| **UPSERT** | Insertar si no existe, actualizar si existe (evita duplicados). |
| **Ventana Deslizante** | Período de relectura que captura correcciones tardías. |
| **Reconciliación** | Proceso de validar integridad entre SQL externo y EDARSA HUB. |

---

## HISTORIAL DE CAMBIOS

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-04-22 | 2.0 | Corrección: EDARSA HUB como cerebro, no tecnología específica |
| 2026-04-22 | 1.0 | Documento inicial con inventario y clasificación de módulos |
