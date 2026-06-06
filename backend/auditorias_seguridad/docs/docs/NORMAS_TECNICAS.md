# EDARSA HUB - Normas Técnicas y Reglas Arquitectónicas

## Documento Maestro de Estándares
**Versión**: 2.0
**Fecha**: Abril 2026
**Estado**: VIGENTE

---

## 0. REGLA ARQUITECTÓNICA FUNDAMENTAL: CLASIFICACIÓN DE FUENTES DE DATOS

### NORMA OBLIGATORIA
**Todo módulo del sistema debe clasificarse según el origen de sus datos:**

| Clasificación | Descripción | Fuente de Verdad |
|--------------|-------------|------------------|
| **TIPO A: LIVE OPERATIVO** | Datos que requieren tiempo real para tomar decisiones operativas | SQL Server externo en VIVO |
| **TIPO B: ANALÍTICO/EJECUTIVO** | Datos históricos, consolidados o reportes | EDARSA HUB (sistema central, tecnología según caso) |
| **MIXTO** | Combinación según caso de uso | Ambos, según contexto |

### PRINCIPIOS FUNDAMENTALES

#### TIPO A: "LIVE FIRST, PERSIST SECOND"
Para módulos operativos donde las decisiones dependen de información en tiempo real:
```
1. CONSULTAR SQL SERVER EXTERNO EN VIVO (SoftRestaurant, MPRO)
2. Si la consulta tiene éxito → usar esos datos
3. Si hay error de conexión → MOSTRAR ERROR, NO CACHE COMO VERDAD
4. Persistir a EDARSA HUB en background para auditoría/histórico
```
**NUNCA** usar cache o réplica como fuente de verdad operativa.

#### TIPO B: "EDARSA HUB FIRST"
Para módulos analíticos, ejecutivos o consolidados:
```
1. CONSULTAR EDARSA HUB (el cerebro del sistema)
2. Los datos ya fueron sincronizados/consolidados previamente
3. Si hay falla → mostrar "Servicio no disponible"
4. Sincronización es proceso separado:
   - SYNC-S: Cada 10-15 min (datos recientes)
   - SYNC-N: Nocturno (consolidación diaria)
   - POST-CIERRE: Por evento (después de corte Z)
```
**EDARSA HUB es el cerebro del sistema**. La tecnología de persistencia (SQL Server propio, almacenamiento estructurado, etc.) se decide según el caso, pero la regla arquitectónica habla de EDARSA HUB, no de una tecnología específica.

### DOCUMENTO DETALLADO
Ver `/app/docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md` para:
- Inventario completo de módulos
- Desviaciones identificadas
- Plan de corrección

---

## 1. MANEJO DE FECHAS EN QUERIES SQL

### REGLA OBLIGATORIA
Todas las queries SQL que involucren fechas DEBEN usar formatos independientes de la configuración regional del servidor.

### PROBLEMA
Los servidores SQL externos (SoftRestaurant, MPRO) pueden tener diferentes configuraciones de `DATEFORMAT` y `LANGUAGE`, lo que causa errores como:
- "Error al convertir una cadena de caracteres en fecha y/u hora"
- Datos interpretados incorrectamente (día/mes invertidos)

### SOLUCIÓN ESTÁNDAR

#### 1.1 Formato de Fecha Seguro (ISO 8601)
```sql
-- INCORRECTO (depende de configuración regional)
WHERE fecha = '21/04/2026'
WHERE fecha = '04-21-2026'
WHERE CONVERT(date, fecha, 101) = '2026-04-21'

-- CORRECTO (formato ISO, universal)
WHERE fecha = '2026-04-21'
WHERE fecha >= '20260401' AND fecha < '20260501'
WHERE CONVERT(varchar, fecha, 112) = '20260421'
```

#### 1.2 Conversión Segura en SQL Server
```sql
-- Usar estilo 112 (YYYYMMDD) - SIEMPRE funciona
CONVERT(varchar, campo_fecha, 112)

-- Comparaciones seguras
WHERE CONVERT(varchar, co_fecha, 112) >= '20260401'
  AND CONVERT(varchar, co_fecha, 112) <= '20260430'

-- Para GETDATE() usar el mismo formato
WHERE CONVERT(varchar, co_fecha, 112) = CONVERT(varchar, GETDATE(), 112)
```

#### 1.3 Parámetros desde Python/Backend
```python
# INCORRECTO
fecha_str = fecha.strftime('%d/%m/%Y')  # Depende de locale
fecha_str = fecha.strftime('%m-%d-%Y')  # Ambiguo

# CORRECTO
fecha_str = fecha.strftime('%Y%m%d')    # Formato 112: YYYYMMDD
fecha_iso = fecha.strftime('%Y-%m-%d')  # ISO 8601
```

### IMPLEMENTACIÓN EN EDARSA HUB

#### Archivo: `/app/backend/core/date_utils.py`
Utilidades centralizadas para formateo de fechas en queries SQL.

#### Patrón de Query
```python
from core.date_utils import sql_date_format, sql_date_range

# En lugar de f-strings con fechas directas
query = f"""
    SELECT * FROM ventas 
    WHERE {sql_date_range('co_fecha', fecha_inicio, fecha_fin)}
"""
```

---

## 2. CONEXIONES A SERVIDORES SQL EXTERNOS

### REGLA
- NUNCA consultar SQL directamente desde UI o endpoints de lectura normal
- Usar catálogos locales (MongoDB) como cache/espejo
- Sincronización controlada y bajo demanda

### PATRÓN
```
UI → API → MongoDB (lectura)
Admin → API Sync → SQL Externo → MongoDB (escritura)
```

---

## 3. MANEJO DE ObjectId EN MONGODB

### REGLA
- SIEMPRE excluir `_id` en proyecciones cuando se retorna JSON
- Usar modelos Pydantic para serialización segura

```python
# INCORRECTO
doc = await db.collection.find_one({"id": x})
return doc  # Falla si tiene _id

# CORRECTO
doc = await db.collection.find_one({"id": x}, {"_id": 0})
return doc
```

---

## 4. VARIABLES DE ENTORNO

### REGLA
- Todas las URLs, puertos, tokens y credenciales vienen de `.env`
- NO usar valores por defecto - si falta config, debe fallar rápido
- NO agregar comentarios en archivos `.env`

---

## 5. THEME Y DISEÑO UI

### REGLA ESTRICTA
- Mantener theme oscuro: `bg-slate-950`, `bg-slate-900` para tarjetas
- Bordes: `border-slate-700`, `border-slate-800`
- Botones principales: `bg-emerald-600`
- NO rediseñar pantallas sin aprobación explícita

---

## HISTORIAL DE CAMBIOS

| Fecha | Version | Cambio |
|-------|---------|--------|
| 2026-04-22 | 1.0 | Documento inicial con reglas de fechas SQL |
| 2026-04-22 | 2.0 | Agregada Seccion 0: Clasificacion de Fuentes de Datos (LIVE vs EDARSA HUB FIRST) |

