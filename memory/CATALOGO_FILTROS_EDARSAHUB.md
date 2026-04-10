# CATÁLOGO MAESTRO DE REGLAS DE FILTROS - EDARSA HUB

**Versión:** 1.1  
**Fecha de creación:** 2025-04-08  
**Última actualización:** 2025-04-09  
**Estado:** ACTIVO - Fuente de Verdad del Sistema

---

## A. INTRODUCCIÓN

Este catálogo establece las reglas obligatorias para el manejo de filtros en todo el sistema EDARSA HUB. Su propósito es:

1. **Estandarizar** el comportamiento de filtros en backend, frontend y queries SQL
2. **Prevenir errores** recurrentes en el filtrado de datos
3. **Documentar** los formatos válidos de entrada para cada parámetro
4. **Servir como referencia** obligatoria para cualquier desarrollo futuro

### Alcance

Este catálogo aplica a:
- Todos los endpoints de `/api/*`
- Todas las queries SQL hacia MPRO y SoftRestaurant
- Todos los componentes de frontend que consumen filtros
- Cualquier nuevo módulo que se agregue al sistema

### Uso Obligatorio

**TODO desarrollador DEBE consultar este catálogo antes de:**
- Crear nuevos endpoints con parámetros de filtro
- Modificar queries SQL existentes
- Agregar filtros a componentes de frontend
- Diagnosticar bugs relacionados con filtrado

---

## B. TABLA RESUMEN DE FILTROS

| Filtro | Tipo | Formato Principal | Sistemas Afectados | Prioridad |
|--------|------|-------------------|-------------------|-----------|
| `sucursal` | Identificador | Código O Nombre | MPRO | CRÍTICO |
| `server_id` | UUID/String | ID de MongoDB | Todos | CRÍTICO |
| `empresa` | Identificador | Código | MPRO | ALTO |
| `proveedor` | Identificador | Código O Nombre | MPRO, SR | ALTO |
| `periodo/fechas` | Rango temporal | YYYY-MM-DD | Todos | CRÍTICO |
| `almacen` | Identificador | Código O Nombre | MPRO, SR | ALTO |
| `folio` | Documento | Alfanumérico | Todos | MEDIO |

**Leyenda de Sistemas:**
- MPRO = ManagementPro
- SR = SoftRestaurant

---

## C. DEFINICIÓN DETALLADA POR FILTRO

---

### C.1 FILTRO: `sucursal`

#### Información General

| Atributo | Valor |
|----------|-------|
| **Nombre** | sucursal |
| **Descripción** | Identifica una ubicación física o unidad de negocio dentro de un servidor |
| **Origen del dato** | Frontend (selector) → Backend → SQL Server externo |
| **Sistemas donde aplica** | MPRO (tabla `Sucursal`), SoftRestaurant (virtual) |

#### Formatos Posibles de Entrada

| Formato | Ejemplo | Fuente Típica |
|---------|---------|---------------|
| **Código** | `"0021"`, `"001"`, `"QRO"` | Selector con ID |
| **Nombre completo** | `"130° QUERETARO"`, `"CIENFUEGOS PRINCIPAL"` | Selector con nombre |
| **Nombre parcial** | `"QUERETARO"`, `"QRO"`, `"Origen"` | Búsqueda libre |

#### Ejemplos Reales del Sistema

```
# Desde API /servers/{id}/sucursales (MPRO):
[
  {"id": "0021", "nombre": "130° QUERETARO"},
  {"id": "0001", "nombre": "ORIGEN"},
  {"id": "0022", "nombre": "LA ESTELAR QRO"}
]

# Parámetro enviado desde frontend:
?sucursal=130° QUERETARO    // Nombre completo
?sucursal=0021              // Código
?sucursal=QUERETARO         // Parcial (PELIGROSO)
```

#### ❌ PATRÓN INCORRECTO (Errores Comunes)

```sql
-- ERROR: Solo busca por descripción, ignora códigos
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'

-- ERROR: No encuentra "0021" porque busca en descripción
-- ERROR: "QRO" puede coincidir con múltiples sucursales
-- ERROR: Caracteres especiales (°) pueden causar problemas
```

**Consecuencias del patrón incorrecto:**
- Requisiciones no aparecen cuando se filtra por código
- Resultados duplicados si hay nombres similares
- Queries vacías sin error visible

#### ✅ PATRÓN CORRECTO DE IMPLEMENTACIÓN

```sql
-- CORRECTO: Busca por código exacto O descripción parcial
WHERE (
    S.Sc_Cve_Sucursal = '{sucursal}'  -- Coincidencia exacta por código
    OR S.Sc_Descripcion LIKE '%{sucursal}%'  -- Coincidencia parcial por nombre
)

-- ALTERNATIVA MÁS ROBUSTA (para nombres con caracteres especiales):
WHERE (
    S.Sc_Cve_Sucursal = '{sucursal}'
    OR UPPER(S.Sc_Descripcion) LIKE UPPER('%{sucursal}%')
)
```

#### Reglas Obligatorias

| # | Regla | Prioridad |
|---|-------|-----------|
| 1 | **SIEMPRE** buscar por código Y descripción | CRÍTICO |
| 2 | **NUNCA** asumir que el parámetro es solo nombre | CRÍTICO |
| 3 | Usar `UPPER()` para comparaciones case-insensitive | ALTO |
| 4 | Escapar caracteres especiales (°, ñ, acentos) | MEDIO |
| 5 | Validar que el parámetro no esté vacío antes de usar LIKE | ALTO |

#### Consideraciones de Performance

- **Índices recomendados:** `Sc_Cve_Sucursal` (PK), `Sc_Descripcion`
- **Evitar:** `LIKE '%valor%'` sin filtro adicional en tablas grandes
- **Preferir:** Código exacto cuando esté disponible

#### Impacto en Queries SQL

```sql
-- Query de ejemplo: Requisiciones por sucursal (MPRO)
SELECT RC.Rc_Folio, RC.Rc_Fecha
FROM Requisicion_Compra RC
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = RC.Sc_Cve_Sucursal
WHERE (
    S.Sc_Cve_Sucursal = '{sucursal}'
    OR S.Sc_Descripcion LIKE '%{sucursal}%'
)
AND RC.Es_Cve_Estado = 'PXA'
```

#### Impacto en Endpoints

| Endpoint | Uso de sucursal | Estado actual |
|----------|-----------------|---------------|
| `/compras/pedidos-vigentes/{server_id}` | Query param | ⚠️ Solo LIKE |
| `/compras/inventarios-fisicos/{server_id}` | Query param | ⚠️ Solo LIKE |
| `/servers/{server_id}/almacenes` | Query param | ✅ Correcto |

#### Módulos Afectados

- ✅ Comercial
- ⚠️ Compras (requiere corrección)
- ✅ Inventarios
- ✅ Finanzas
- ✅ RRHH

---

### C.2 FILTRO: `server_id`

#### Información General

| Atributo | Valor |
|----------|-------|
| **Nombre** | server_id |
| **Descripción** | Identificador único del servidor de base de datos en MongoDB |
| **Origen del dato** | Frontend (selector de servidores) |
| **Sistemas donde aplica** | Todos (MongoDB → SQL Server) |

#### Formatos Posibles de Entrada

| Formato | Ejemplo | Válido |
|---------|---------|--------|
| **UUID string** | `"srv_12345"`, `"abc123def"` | ✅ |
| **ObjectId** | `ObjectId("...")` | ❌ No en URL |
| **Nombre** | `"CIENFUEGOS"` | ❌ Nunca |

#### ✅ PATRÓN CORRECTO DE IMPLEMENTACIÓN

```python
# Backend - Validación
server = await db.servers.find_one({"id": server_id, "active": True})
if not server:
    raise HTTPException(status_code=404, detail="Servidor no encontrado")

# Verificar permisos
if not user_has_server_access(current_user, server_id):
    raise HTTPException(status_code=403, detail="Sin acceso a este servidor")
```

```javascript
// Frontend - Uso correcto
const response = await api.get(`/compras/dashboard/${selectedServer}`);

// NUNCA construir server_id manualmente
// SIEMPRE obtenerlo del selector de servidores
```

#### Reglas Obligatorias

| # | Regla | Prioridad |
|---|-------|-----------|
| 1 | Validar existencia en MongoDB antes de usar | CRÍTICO |
| 2 | Verificar `active: True` | CRÍTICO |
| 3 | Verificar permisos del usuario | CRÍTICO |
| 4 | Filtrar por `visible_en_operaciones` cuando aplique | ALTO |

#### Consideraciones de Performance

- El server_id se usa para obtener credenciales de conexión
- **NUNCA** exponer credenciales en logs o respuestas
- Usar `serversService.js` para obtener servidores en frontend

---

### C.3 FILTRO: `empresa`

#### Información General

| Atributo | Valor |
|----------|-------|
| **Nombre** | empresa |
| **Descripción** | Identifica la entidad legal o razón social |
| **Origen del dato** | Frontend (selector global) |
| **Sistemas donde aplica** | MPRO (campo `Em_Cve_Empresa`) |

#### Formatos Posibles de Entrada

| Formato | Ejemplo |
|---------|---------|
| **Código** | `"001"`, `"EMP01"` |
| **Nombre** | `"RESTAURANTES DEL BAJIO SA DE CV"` |

#### ✅ PATRÓN CORRECTO

```sql
-- Por código (preferido)
WHERE Em_Cve_Empresa = '{empresa}'

-- Por nombre (solo si no hay código)
WHERE Em_Descripcion LIKE '%{empresa}%'
```

#### Reglas Obligatorias

| # | Regla | Prioridad |
|---|-------|-----------|
| 1 | Empresa es filtro GLOBAL, afecta todas las queries | CRÍTICO |
| 2 | Si no se especifica, usar empresa por defecto del servidor | ALTO |

---

### C.4 FILTRO: `proveedor`

#### Información General

| Atributo | Valor |
|----------|-------|
| **Nombre** | proveedor / proveedor_codigo |
| **Descripción** | Identifica un proveedor de insumos/productos |
| **Origen del dato** | Frontend (tabla de análisis, selector) |
| **Sistemas donde aplica** | MPRO (`Pv_Cve_Proveedor`), SR (`idproveedor`) |

#### Formatos Posibles de Entrada

| Formato | Ejemplo MPRO | Ejemplo SR |
|---------|--------------|------------|
| **Código** | `"PROV001"` | `12345` (numérico) |
| **Nombre** | `"DISTRIBUIDORA XYZ"` | `"ABARROTES S.A."` |

#### ✅ PATRÓN CORRECTO

```sql
-- MPRO
WHERE Pv_Cve_Proveedor = '{proveedor_codigo}'

-- SoftRestaurant (código numérico)
WHERE c.idproveedor = {proveedor_codigo}
```

#### ❌ PATRÓN INCORRECTO

```sql
-- ERROR: Mezclar código con nombre sin validar
WHERE Pv_Descripcion = '{proveedor}'  -- Si es código, falla
```

#### Reglas Obligatorias

| # | Regla | Prioridad |
|---|-------|-----------|
| 1 | En MPRO, proveedor es STRING (código alfanumérico) | CRÍTICO |
| 2 | En SR, proveedor es INTEGER (ID numérico) | CRÍTICO |
| 3 | Validar tipo de dato según sistema antes de query | ALTO |

---

### C.5 FILTRO: `periodo / fechas`

#### Información General

| Atributo | Valor |
|----------|-------|
| **Nombre** | fecha_ini, fecha_fin, periodo |
| **Descripción** | Define el rango temporal de la consulta |
| **Origen del dato** | Frontend (date pickers, selectores de período) |
| **Sistemas donde aplica** | Todos |

#### Formatos Posibles de Entrada

| Formato | Ejemplo | Uso |
|---------|---------|-----|
| **ISO 8601** | `"2025-04-08"` | ✅ Preferido |
| **Con hora** | `"2025-04-08 23:59:59"` | Para fin de día |
| **Período nombrado** | `"dia"`, `"semana"`, `"mes"` | Calculado en backend |
| **Mes/Año** | `meses=01,02&anio=2025` | Multi-selección |

#### ✅ PATRÓN CORRECTO

```sql
-- Rango de fechas (MPRO)
WHERE Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'

-- SoftRestaurant (incluir hora)
WHERE c.fechaaplicacion BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'

-- Para fin de día exacto
WHERE Mv_Fecha >= '{fecha_ini}' AND Mv_Fecha < DATEADD(day, 1, '{fecha_fin}')
```

#### ❌ PATRÓN INCORRECTO

```sql
-- ERROR: No incluye hora final, pierde registros del último día
WHERE Mv_Fecha BETWEEN '{fecha_ini}' AND '{fecha_fin}'

-- ERROR: Formato incorrecto
WHERE Mv_Fecha = '08/04/2025'  -- Ambiguo: ¿DD/MM o MM/DD?
```

#### Reglas Obligatorias

| # | Regla | Prioridad |
|---|-------|-----------|
| 1 | **SIEMPRE** usar formato `YYYY-MM-DD` | CRÍTICO |
| 2 | Para `fecha_fin`, agregar `23:59:59` o usar `< fecha_fin + 1 día` | CRÍTICO |
| 3 | Validar que `fecha_ini <= fecha_fin` | ALTO |
| 4 | Limitar rango máximo (ej: 1 año) para evitar timeouts | MEDIO |

#### Consideraciones de Performance

- **Índices recomendados:** Campos de fecha deben estar indexados
- **Particionamiento:** Considerar partición por fecha en tablas grandes
- **Timeout:** Queries de más de 1 año pueden requerir paginación

#### ⚠️ REGLA CRÍTICA: Multiselección de Meses

**BUG HISTÓRICO CORREGIDO (2025-04-08):**

Cuando se selecciona **todo el año** o **múltiples meses** (ej: "01,02,03,04"), la lógica **INCORRECTA** era usar solo el mes más reciente (`max(lista_meses)`) para calcular fechas. Esto causaba que:
- Solo se consultaran datos del último mes seleccionado
- Los comparativos vs año anterior fueran incorrectos

**❌ PATRÓN INCORRECTO (NO USAR):**
```python
# ERROR: Solo usa el mes más reciente, ignora los demás
lista_meses = [1, 2, 3, 4]
mes = max(lista_meses)  # mes = 4
fecha_ini = f"{anio}-{mes:02d}-01"  # "2026-04-01" - INCORRECTO, debería ser "2026-01-01"
```

**✅ PATRÓN CORRECTO (OBLIGATORIO):**
```python
# CORRECTO: Usa el rango completo de meses
lista_meses = [1, 2, 3, 4]
mes_min = min(lista_meses)  # 1 (enero)
mes_max = max(lista_meses)  # 4 (abril)

# Fecha inicio: primer día del PRIMER mes
fecha_ini = f"{anio}-{mes_min:02d}-01"  # "2026-01-01"

# Fecha fin: día actual del ÚLTIMO mes (si es mes actual) o último día (si ya pasó)
if anio == hoy.year and mes_max == hoy.month:
    fecha_fin = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')  # Hasta ayer
else:
    ultimo_dia = calendar.monthrange(anio, mes_max)[1]
    fecha_fin = f"{anio}-{mes_max:02d}-{ultimo_dia:02d}"

# Comparativo año anterior: MISMO RANGO de meses y días
# Si es 01-ene a 08-abr 2026, comparar con 01-ene a 08-abr 2025
fecha_ini_año_ant = f"{anio-1}-{mes_min:02d}-01"
fecha_fin_año_ant = f"{anio-1}-{mes_max:02d}-{dia_actual:02d}"  # Mismo día del año anterior
```

**Ejemplo de cálculo correcto:**
| Selección | Período Actual | Año Anterior |
|-----------|----------------|--------------|
| Ene-Abr 2026 | 01-ene-2026 a 07-abr-2026 (97 días) | 01-ene-2025 a 07-abr-2025 (97 días) |
| Todo 2026 | 01-ene-2026 a 07-abr-2026 (97 días) | 01-ene-2025 a 07-abr-2025 (97 días) |
| Solo Abril | 01-abr-2026 a 07-abr-2026 (7 días) | 01-abr-2025 a 07-abr-2025 (7 días) |

**Endpoints corregidos:**
- ✅ `/comercial/tablero-ejecutivo` - Corregido 2025-04-08
- ✅ `/comercial/dashboard/{server_id}` - Corregido 2025-04-08

---

#### ⚠️ REGLA CRÍTICA: Función get_kpis_softrestaurant - Conversión de Fechas

**BUG HISTÓRICO CORREGIDO (2025-04-08):**

La función `get_kpis_softrestaurant()` recibe `fecha_ini` y `fecha_fin` como strings (ej: `"2026-01-01"` y `"2026-04-07"`), pero internamente las convierte a formato sin guiones (`fi` y `ff`). 

**Problema crítico:** Cuando detecta el último día con ventas en SQL Server, **sobrescribía** `ff` y `dias_transcurridos` usando el prefijo del **mes inicial**, no del **mes final**.

**❌ PATRÓN INCORRECTO (NO USAR):**
```python
# ERROR: Usa fi[:6] que es "202601" (enero), no "202604" (abril)
fi = fecha_ini.replace('-', '')  # "20260101"
ff = fecha_fin.replace('-', '')  # "20260407"

# Al detectar último día con ventas:
dia_con_datos = 7  # Día 7 de abril
ff = f"{fi[:6]}{str(dia_con_datos).zfill(2)}"  # "20260107" - ¡INCORRECTO!
# Resultado: Consulta solo datos de ENERO (mes 01), no de TODO el rango

dias_transcurridos = dia_con_datos  # 7 - ¡INCORRECTO! Debería ser ~97 días
```

**Consecuencias del bug:**
- CIENFUEGOS mostraba $784K en lugar de $15.49M
- Solo consultaba datos del primer mes (enero) en lugar de todo el rango (enero-abril)
- Los días transcurridos eran incorrectos (7 en lugar de 97)

**✅ PATRÓN CORRECTO (OBLIGATORIO):**
```python
fi = fecha_ini.replace('-', '')  # "20260101"
ff = fecha_fin.replace('-', '')  # "20260407"

# Extraer mes y año de fecha_fin para usarlos en recálculos
mes_final = int(fecha_fin[5:7])  # 4 (abril)
anio_final = int(fecha_fin[:4])  # 2026

# Al detectar último día con ventas:
# Parsear la fecha completa del último día (YYYY-MM-DD)
ultimo_dia_venta = "2026-04-07"  # Ejemplo de resultado de SQL
anio_ultimo = 2026
mes_ultimo = 4
dia_con_datos = 7

# CORRECTO: Usar el mes y año del último día con ventas
ff = f"{anio_ultimo}{str(mes_ultimo).zfill(2)}{str(dia_con_datos).zfill(2)}"  # "20260407" ✅

# Calcular días transcurridos desde fecha_ini hasta último día con ventas
from datetime import datetime
fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
fecha_ultimo_dt = datetime(anio_ultimo, mes_ultimo, dia_con_datos)
dias_transcurridos = (fecha_ultimo_dt - fecha_ini_dt).days + 1  # 97 días ✅
```

**Verificación de la corrección:**
| Unidad | Antes (bug) | Después (correcto) |
|--------|-------------|-------------------|
| CIENFUEGOS (Ene-Abr 2026) | $784,330 | $15,490,862 ✅ |
| Total Consolidado | $3.7M | $42.1M ✅ |

**Funciones afectadas:**
- ✅ `get_kpis_softrestaurant()` - Corregido 2025-04-08 (líneas ~9671-9740)

---

#### ⚠️ REGLA CRÍTICA: NO sobrescribir fecha_ini_año_ant en get_kpis_softrestaurant

**BUG HISTÓRICO CORREGIDO (2025-04-08):**

Cuando el Tablero Ejecutivo llama a `get_kpis_softrestaurant()` con un **rango de múltiples meses** (ej: Ene-Abr 2026), ya envía correctamente:
- `fecha_ini_año_ant = "2025-01-01"` (primer día del primer mes del rango, año anterior)
- `fecha_fin_año_ant = "2025-04-08"` (mismo día del último mes, año anterior)

**El bug:** Dentro de la función, al detectar el último día con ventas, se **sobrescribía** `fecha_ini_año_ant` usando solo el mes del último día con ventas (`mes_actual`), ignorando el rango completo.

**❌ PATRÓN INCORRECTO (NO USAR):**
```python
# ERROR: Sobrescribe fecha_ini_año_ant usando solo el mes actual (abril)
# Esto compara "01-abr-2025 a 08-abr-2025" en vez de "01-ene-2025 a 08-abr-2025"
anio_pasado = anio_actual - 1
fecha_ini_año_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-01"  # ❌ INCORRECTO
fecha_fin_año_ant = f"{anio_pasado}-{str(mes_actual).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
```

**Consecuencias del bug:**
- CIENFUEGOS (Ene-Abr 2026) comparaba vs solo abril 2025, no vs Ene-Abr 2025
- KPI "vs año" mostraba variaciones incorrectas
- Ventas año anterior truncadas a un solo mes

**✅ PATRÓN CORRECTO (OBLIGATORIO):**
```python
# CORRECTO: PRESERVAR fecha_ini_año_ant original (viene del Tablero con el rango correcto)
# Solo actualizar fecha_fin_año_ant con el día ajustado del mes final
anio_pasado = anio_actual - 1
max_dia_ano_ant = calendar.monthrange(anio_pasado, mes_ultimo)[1]
dia_ano_ant = min(dia_con_datos, max_dia_ano_ant)
# NO TOCAR fecha_ini_año_ant - ya viene correctamente calculada
fecha_fin_año_ant = f"{anio_pasado}-{str(mes_ultimo).zfill(2)}-{str(dia_ano_ant).zfill(2)}"
```

**Ejemplo de comparación correcta:**
| Selección Usuario | Período Actual | Año Anterior (CORRECTO) |
|-------------------|----------------|-------------------------|
| Ene-Abr 2026 | 01-ene-2026 a 08-abr-2026 | 01-ene-2025 a 08-abr-2025 ✅ |
| Todo 2026 | 01-ene-2026 a 08-abr-2026 | 01-ene-2025 a 08-abr-2025 ✅ |

**Verificación esperada:**
| Unidad | Antes (bug) | Después (correcto) |
|--------|-------------|-------------------|
| CIENFUEGOS (Ene-Abr 2026) | vs Año incorrecto | vs Año correcto ✅ |

**Funciones corregidas:**
- ✅ `get_kpis_softrestaurant()` - Corregido 2025-04-08 (línea ~9744)

---

#### ⚠️ REGLA VISUALIZACIÓN: KPIs "vs Mes" en Multiselección de Meses

**IMPLEMENTACIÓN (2025-04-08):**

Cuando se seleccionan **múltiples meses** (ej: "Todo el año" o "Ene, Feb, Mar"), los KPIs de comparación "vs Mes Anterior" **no tienen sentido matemático** (comparar un acumulado de 4 meses contra 1 solo mes es inválido).

**Comportamiento implementado:**

| Selección | KPIs "vs Mes" | KPIs "vs Año" | Etiqueta Proyección |
|-----------|---------------|---------------|---------------------|
| 1 solo mes | ✅ Visibles | ✅ Visibles | "Proyección Mes" |
| 2+ meses | ❌ Ocultos | ✅ Visibles | "Proyección Periodo" |

**Lógica en Frontend:**
```javascript
// TableroEjecutivo.js y Comercial.js
const esMultiMes = selectedMeses.length > 1;

// En los KPIs:
{!esMultiMes && (
  <div className="text-center">
    <span>vs Mes</span>
    <p>{formatPercent(data.var_vs_mes_ant)}</p>
  </div>
)}

// En la etiqueta de Proyección:
<p>{esMultiMes ? 'Proyección Periodo' : 'Proyección Mes'}</p>
```

**Archivos modificados:**
- ✅ `/app/frontend/src/pages/TableroEjecutivo.js` - Corregido 2025-04-08
- ✅ `/app/frontend/src/pages/Comercial.js` - Corregido 2025-04-08

**KPIs afectados:**
1. Ventas Consolidadas - "vs Mes" → Oculto en multiselección
2. PAX Total - "vs Mes" → Oculto en multiselección
3. Cheques - "vs Mes" → Oculto en multiselección
4. Rotación Mesas - "vs Mes" → Oculto en multiselección
5. Etiqueta "Proyección Mes" → "Proyección Periodo"

---

### C.6 FILTRO: `almacen`

#### Información General

| Atributo | Valor |
|----------|-------|
| **Nombre** | almacen / almacen_id / almacenes |
| **Descripción** | Identifica un almacén o bodega física |
| **Origen del dato** | Frontend (selector múltiple) |
| **Sistemas donde aplica** | MPRO (`Al_Cve_Almacen`), SR (`idalmacen` / `nombre`) |

#### Formatos Posibles de Entrada

| Formato | Ejemplo MPRO | Ejemplo SR |
|---------|--------------|------------|
| **Código** | `"ALM001"` | `5` (numérico) |
| **Nombre** | `"ALMACEN GENERAL"` | `"COCINA CALIENTE"` |
| **Lista** | `["ALM001", "ALM002"]` | `[5, 6, 7]` |

#### ✅ PATRÓN CORRECTO

```sql
-- MPRO - Por código
WHERE Al_Cve_Almacen = '{almacen}'

-- MPRO - Por nombre (cuando viene del selector)
WHERE Al_Descripcion LIKE '%{almacen}%'

-- MPRO - Múltiples almacenes
WHERE Al_Descripcion LIKE '%{alm1}%' OR Al_Descripcion LIKE '%{alm2}%'

-- SoftRestaurant - Por nombre (SR no tiene códigos consistentes)
WHERE A.nombre LIKE '%{almacen}%'
```

#### Reglas Obligatorias

| # | Regla | Prioridad |
|---|-------|-----------|
| 1 | En MPRO, preferir código cuando esté disponible | ALTO |
| 2 | En SR, usar nombre (no hay códigos estandarizados) | ALTO |
| 3 | Soportar selección múltiple con OR | MEDIO |

---

### C.7 FILTRO: `folio`

#### Información General

| Atributo | Valor |
|----------|-------|
| **Nombre** | folio / documento / referencia |
| **Descripción** | Identificador de un documento (factura, requisición, inventario) |
| **Origen del dato** | Frontend (selector, input manual) |
| **Sistemas donde aplica** | Todos |

#### Formatos Posibles de Entrada

| Tipo de Documento | Formato MPRO | Formato SR |
|-------------------|--------------|------------|
| **Requisición** | `"REQ-2025-001"` | N/A |
| **Factura** | `"FAC-12345"` | `12345` (numérico) |
| **Inv. Físico** | `"INVF-001"` | `"2025-04-08"` (fecha) |
| **Orden Compra** | `"OC-2025-001"` | `100` (numérico) |

#### ✅ PATRÓN CORRECTO

```sql
-- MPRO - Búsqueda exacta por folio
WHERE Rc_Folio = '{folio}'

-- MPRO - Si puede venir con o sin prefijo
WHERE Rc_Folio = '{folio}' OR Rc_Folio LIKE '%{folio}'

-- SoftRestaurant - ID numérico
WHERE idcompra = {folio}
```

#### ❌ PATRÓN INCORRECTO

```sql
-- ERROR: LIKE sin necesidad (afecta performance)
WHERE Rc_Folio LIKE '%{folio}%'  -- Si el folio es exacto, usar =
```

#### Reglas Obligatorias

| # | Regla | Prioridad |
|---|-------|-----------|
| 1 | Validar formato según tipo de documento | ALTO |
| 2 | Sanitizar input para prevenir SQL injection | CRÍTICO |
| 3 | En SR, convertir a entero cuando sea ID numérico | ALTO |

---

## D. REGLAS GLOBALES DEL SISTEMA

### D.1 Orden de Precedencia de Filtros

```
1. server_id (OBLIGATORIO - define la conexión)
2. empresa (GLOBAL - afecta todo)
3. sucursal (GLOBAL - filtra unidad de negocio)
4. periodo/fechas (CONTEXTUAL - define rango temporal)
5. almacen (LOCAL - específico del módulo)
6. proveedor/folio (LOCAL - específico de la consulta)
```

### D.2 Validaciones Obligatorias

| Validación | Dónde Aplicar | Acción si Falla |
|------------|---------------|-----------------|
| server_id existe y está activo | Backend | HTTP 404 |
| Usuario tiene acceso al servidor | Backend | HTTP 403 |
| Fechas en formato correcto | Backend | HTTP 400 |
| Parámetros no vacíos para LIKE | Backend | Omitir filtro o error |
| Caracteres especiales escapados | Backend | Sanitizar |

### D.3 Manejo de Valores Vacíos

| Parámetro | Si es vacío/null | Acción |
|-----------|------------------|--------|
| `sucursal` | `""` o `"default"` | No aplicar filtro de sucursal |
| `almacen` | `[]` o `null` | Incluir todos los almacenes |
| `fecha_ini` | `null` | Calcular desde inventario inicial o error |
| `fecha_fin` | `null` | Usar fecha actual |

---

## E. ERRORES COMUNES A EVITAR

### E.1 Error: Solo LIKE en sucursal
```sql
-- ❌ INCORRECTO
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'

-- ✅ CORRECTO
WHERE (S.Sc_Cve_Sucursal = '{sucursal}' OR S.Sc_Descripcion LIKE '%{sucursal}%')
```

### E.2 Error: Fecha sin hora final
```sql
-- ❌ INCORRECTO (pierde registros del último día después de 00:00:00)
WHERE fecha BETWEEN '2025-04-01' AND '2025-04-30'

-- ✅ CORRECTO
WHERE fecha BETWEEN '2025-04-01' AND '2025-04-30 23:59:59'
```

### E.3 Error: Tipo de dato incorrecto para proveedor
```python
# ❌ INCORRECTO (SR usa enteros)
query = f"WHERE idproveedor = '{proveedor}'"  # String con comillas

# ✅ CORRECTO
query = f"WHERE idproveedor = {int(proveedor)}"  # Entero sin comillas
```

### E.4 Error: LIKE sin validar valor vacío
```sql
-- ❌ INCORRECTO (si {sucursal} es vacío, retorna todo)
WHERE S.Sc_Descripcion LIKE '%{sucursal}%'

-- ✅ CORRECTO (validar antes)
-- En Python:
if sucursal and sucursal != 'default':
    query += f" AND S.Sc_Descripcion LIKE '%{sucursal}%'"
```

### E.5 Error: No escapar caracteres especiales
```python
# ❌ INCORRECTO
sucursal = "130° QUERETARO"  # El ° puede causar problemas

# ✅ CORRECTO
sucursal = sucursal.replace("'", "''")  # Escapar comillas simples
```

---

## F. RECOMENDACIONES DE IMPLEMENTACIÓN

### F.1 Crear Helper de Filtros (Backend)

```python
def build_sucursal_filter(sucursal: str, alias: str = "S") -> str:
    """
    Construye filtro de sucursal correcto para MPRO.
    Busca por código exacto O descripción parcial.
    """
    if not sucursal or sucursal == 'default':
        return ""
    
    sucursal_escaped = sucursal.replace("'", "''")
    return f"""
    AND (
        {alias}.Sc_Cve_Sucursal = '{sucursal_escaped}'
        OR {alias}.Sc_Descripcion LIKE '%{sucursal_escaped}%'
    )
    """
```

### F.2 Crear Helper de Fechas (Backend)

```python
def build_date_filter(fecha_ini: str, fecha_fin: str, campo: str) -> str:
    """
    Construye filtro de fechas incluyendo hora final.
    """
    if not fecha_ini or not fecha_fin:
        return ""
    
    return f"AND {campo} BETWEEN '{fecha_ini}' AND '{fecha_fin} 23:59:59'"
```

### F.3 Validación en Frontend

```javascript
// Antes de enviar al backend
const validateFilters = (filters) => {
  if (!filters.server_id) throw new Error('Servidor requerido');
  if (filters.fecha_ini && filters.fecha_fin) {
    if (new Date(filters.fecha_ini) > new Date(filters.fecha_fin)) {
      throw new Error('Fecha inicial no puede ser mayor a fecha final');
    }
  }
  return true;
};
```

---

## G. CÓMO USAR ESTE CATÁLOGO EN FUTUROS DESARROLLOS

### G.1 Antes de crear un nuevo endpoint

1. ✅ Identificar qué filtros necesita el endpoint
2. ✅ Consultar la sección C de este catálogo para cada filtro
3. ✅ Usar los patrones CORRECTOS documentados
4. ✅ Agregar validaciones según sección D
5. ✅ Evitar los errores de sección E

### G.2 Antes de modificar una query existente

1. ✅ Verificar si la query usa filtros
2. ✅ Comparar con los patrones CORRECTOS de este catálogo
3. ✅ Corregir patrones INCORRECTOS si los detecta
4. ✅ Documentar el cambio

### G.3 Al diagnosticar bugs de filtrado

1. ✅ Identificar qué filtro está fallando
2. ✅ Revisar el patrón actual vs el patrón CORRECTO
3. ✅ Verificar el formato de entrada del parámetro
4. ✅ Revisar la sección E de errores comunes

### G.4 Al agregar un nuevo filtro al sistema

1. ✅ Documentarlo en este catálogo (sección C)
2. ✅ Definir todos los formatos posibles de entrada
3. ✅ Crear ejemplos reales
4. ✅ Documentar patrón correcto e incorrecto
5. ✅ Actualizar tabla resumen (sección B)

---

## HISTORIAL DE CAMBIOS

| Fecha | Versión | Cambio | Autor |
|-------|---------|--------|-------|
| 2025-04-08 | 1.0 | Creación inicial del catálogo | E1 Agent |
| 2025-04-08 | 1.1 | Corrección aplicada en `/compras/pedidos-vigentes/` - Filtro sucursal MPRO | E1 Agent |
| 2025-04-08 | 1.2 | Agregada REGLA CRÍTICA: Multiselección de Meses en filtro periodo/fechas | E1 Agent |
| 2025-04-08 | 1.3 | Agregada REGLA CRÍTICA: Función get_kpis_softrestaurant - Conversión de Fechas | E1 Agent |
| 2025-04-08 | 1.4 | REGLA VISUALIZACIÓN: KPIs "vs Mes" deshabilitados en multiselección de meses | E1 Agent |
| 2025-04-08 | 1.5 | REGLA CRÍTICA: NO sobrescribir fecha_ini_año_ant en get_kpis_softrestaurant | E1 Agent |
| 2025-04-09 | 1.6 | Verificación de fechas recibidas en get_kpis_softrestaurant (log debug) | E1 Agent |
| 2025-04-09 | 1.7 | REGLA UX: Auto-actualización de filtros en Tablero Ejecutivo | E1 Agent |
| 2025-04-09 | 1.8 | FIX: Multiselección de meses en Dashboard Comercial (MPRO + SoftRestaurant) | E1 Agent |
| 2025-04-09 | 1.9 | REGLA CRÍTICA: Captura de inventario solo con productos de requisiciones seleccionadas | E1 Agent |
| 2025-04-09 | 2.0 | REGLA UX: Modal de captura arrastrable + botón Limpiar + persistencia | E1 Agent |
| 2025-04-09 | 2.1 | REGLA UX: Scroll horizontal en modal de Pantalla Completa (I.7) | E1 Agent |
| 2025-04-09 | 2.2 | REGLA UX: Auto-scroll con Tab en Captura Manual de Inventario (I.8) | E1 Agent |
| 2025-04-09 | 2.3 | REGLA UX: Scroll horizontal en tabla Detalle de Auditoría (vista normal) (I.9) | E1 Agent |
| 2025-04-09 | 2.4 | REGLA UX: Modo Pantalla Completa en Explorador BD (ocultar sidebar) (I.10) | E1 Agent |
| 2025-04-09 | 2.5 | REGLA UX: Scroll horizontal y altura expandida en Pantalla Completa de Explorador BD (I.11) | E1 Agent |
| 2025-04-10 | 2.6 | REGLA UX: Indicadores de estado en filtros de Auditoría (loading, vacío, sucursal) (I.12) | E1 Agent |
| 2025-04-10 | 2.7 | FIX CRÍTICO: Formato de fecha SQL para APIs locales (101 en lugar de 103) (I.13) | E1 Agent |

---

## REGLAS ESPECÍFICAS POR SISTEMA

### MPRO - Reglas de Sucursal

**Endpoints corregidos:**
- ✅ `/compras/pedidos-vigentes/{server_id}` (línea 5394) - CORREGIDO 2025-04-08

**Patrón obligatorio para MPRO:**
```sql
WHERE (S.Sc_Cve_Sucursal = '{sucursal}' OR S.Sc_Descripcion LIKE '%{sucursal}%')
```

**Sucursales de referencia (Querétaro y Origen):**
| Código | Nombre Completo | Búsquedas válidas |
|--------|-----------------|-------------------|
| `0021` | `130° QUERETARO` | "0021", "QUERETARO", "QRO", "130°" |
| `0001` | `ORIGEN` | "0001", "ORIGEN", "Origen" |

---

## G. REGLAS DE UX - FILTROS AUTOMÁTICOS

### G.1 Auto-actualización en Tablero Ejecutivo

**IMPLEMENTACIÓN (2025-04-09):**

Cuando el usuario cambia los filtros de **Mes(es)** o **Año(s)** en el Tablero Ejecutivo, el dashboard se actualiza **automáticamente** sin necesidad de hacer clic en el botón "Actualizar".

**Comportamiento:**

| Acción | ANTES | DESPUÉS |
|--------|-------|---------|
| Cambiar mes(es) | Requería clic en "Actualizar" | ✅ Se actualiza automáticamente |
| Cambiar año(s) | Requería clic en "Actualizar" | ✅ Se actualiza automáticamente |

**Implementación técnica (TableroEjecutivo.js):**

```javascript
// Auto-actualizar cuando cambian los filtros de mes o año
useEffect(() => {
  // Solo ejecutar si ya se cargó inicialmente (data existe o hubo un error previo)
  // Esto evita doble carga al montar el componente
  const token = localStorage.getItem('token');
  if (token && (data || loading === false)) {
    cargarDatos();
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [selectedMeses, selectedAnios]);
```

**Consideraciones:**
- Se evita doble carga al montar el componente verificando si ya existe `data`
- El `eslint-disable` es necesario porque `cargarDatos` se define dentro del componente

**Archivos afectados:**
- ✅ `/app/frontend/src/pages/TableroEjecutivo.js`

---

## H. FIXES DE MULTISELECCIÓN DE MESES (2025-04-09)

### H.1 Dashboard Comercial - Cálculo de fechas multiselección

**PROBLEMA:**
Al seleccionar múltiples meses (Ene-Abr 2026) en el Dashboard Comercial, las fechas se calculaban incorrectamente:
- **Período actual**: `20260101 a 20260107` (solo 7 días de enero!)
- **Año anterior**: `20250101 a 20250130` (solo enero)

**CAUSA:**
El código usaba `int(fecha_ini[5:7])` para obtener el mes, pero esto tomaba el mes de `fecha_ini` (enero) en lugar del mes máximo del rango (abril).

**SOLUCIÓN:**
Usar `mes_max` (el mes máximo del rango seleccionado) en lugar de extraer el mes de `fecha_ini`.

**Código corregido (server.py):**

```python
# ❌ INCORRECTO - Solo tomaba el mes de fecha_ini (enero)
mes_actual = int(fecha_ini[5:7])
anio_actual = int(fecha_ini[:4])
fecha_fin = f"{anio_actual}-{str(mes_actual).zfill(2)}-{str(dia_con_datos).zfill(2)}"

# ✅ CORRECTO - Usa mes_max para multiselección
mes_actual = mes_max  # CORRECCIÓN: Usar mes_max para multiselección
anio_actual = year
fecha_fin = f"{year}-{str(mes_max).zfill(2)}-{str(dia_con_datos).zfill(2)}"
```

**Lugares corregidos en server.py:**
1. SoftRestaurant Dashboard (líneas ~7908-7914)
2. MPRO Dashboard sin filtro de sucursal (líneas ~8150-8155)
3. MPRO Dashboard con filtro de sucursal (líneas ~8249-8270)

### H.2 Condición es_mes_actual para multiselección

**PROBLEMA:**
La condición `es_mes_actual` requería `len(lista_meses) == 1`, lo que excluía multiselección de meses.

**SOLUCIÓN:**
Remover la restricción de `len(lista_meses) == 1`:

```python
# ❌ INCORRECTO - Solo funcionaba con 1 mes
es_mes_actual = (year == hoy.year and mes_max == hoy.month and len(lista_meses) == 1)

# ✅ CORRECTO - Funciona con multiselección
es_mes_actual = (year == hoy.year and mes_max == hoy.month)
```

---

## I. REGLAS CRÍTICAS - MÓDULO COMPRAS

### I.1 Captura de Inventario Físico - Filtro por Requisiciones

**⚠️ REGLA CRÍTICA - NO MODIFICAR NUNCA ⚠️**

**IMPLEMENTACIÓN (2025-04-09):**

En el modal de "Captura Manual de Inventario Físico", **SOLO SE DEBEN MOSTRAR** los productos que están en las **requisiciones seleccionadas**.

**❌ COMPORTAMIENTO INCORRECTO (PROHIBIDO):**
- Mostrar TODOS los productos del catálogo (ej: 1764 productos)
- Mezclar productos de inventarios iniciales con requisiciones
- Ignorar las requisiciones seleccionadas

**✅ COMPORTAMIENTO CORRECTO (OBLIGATORIO):**
1. Si hay **requisiciones seleccionadas** (`folioPedido.length > 0`):
   - Mostrar **SOLO** productos de esas requisiciones
   - **IGNORAR** inventarios iniciales
   
2. Si **NO hay requisiciones** pero hay **inventarios iniciales**:
   - Mostrar productos de los inventarios iniciales

3. Si **NO hay nada seleccionado**:
   - Mostrar alert pidiendo selección

**Código CORRECTO (Compras.js - función iniciarCapturaManual):**

```javascript
// REGLA CRÍTICA: Solo mostrar productos de las REQUISICIONES SELECCIONADAS
// Si hay requisiciones seleccionadas, ignorar inventarios iniciales
if (folioPedido.length > 0) {
  const response = await axios.post(`${API_URL}/api/compras/productos-para-captura`, {
    server_id: selectedServer,
    folios_inv_inicial: [],  // IMPORTANTE: Array vacío - ignorar inventarios
    folios_requisiciones: folioPedido
  }, { headers: { Authorization: `Bearer ${token}` } });
  // ...
}
```

**Prioridad de filtros:**
| Prioridad | Condición | Acción |
|-----------|-----------|--------|
| 1 (Alta) | `folioPedido.length > 0` | Solo productos de requisiciones |
| 2 (Media) | `selectedInvIniciales.length > 0` | Solo productos de inv. iniciales |
| 3 (Baja) | Nada seleccionado | Alert de error |

**Archivo afectado:**
- ✅ `/app/frontend/src/pages/Compras.js` - Función `iniciarCapturaManual`

**⚠️ ADVERTENCIA:**
Esta regla ha sido modificada incorrectamente 3 veces anteriormente.
**NO MODIFICAR** sin aprobación explícita del usuario.

---

### I.2 Modal de Captura - Arrastrable y Persistente

**IMPLEMENTACIÓN (2025-04-09):**

El modal de "Captura Manual de Inventario Físico" debe ser **arrastrable** para poder ver el fondo, y debe **conservar el inventario capturado** hasta que se limpie explícitamente.

**Características implementadas:**

| Característica | Descripción |
|----------------|-------------|
| **Arrastrable** | Arrastrar desde la barra de título (bg-blue-50) |
| **Persistencia** | Inventario guardado en localStorage |
| **Botón Limpiar** | Resetea todos los valores a 0 |
| **Fondo semi-transparente** | `bg-black/30` permite ver el contenido detrás |

**Código de implementación (Compras.js):**

```javascript
// Estados para modal arrastrable
const [modalPosition, setModalPosition] = useState({ x: 0, y: 0 });
const [isDragging, setIsDragging] = useState(false);
const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

// Handlers para arrastrar
const handleMouseDown = (e) => {
  if (e.target.closest('.modal-header-drag')) {
    setIsDragging(true);
    setDragOffset({
      x: e.clientX - modalPosition.x,
      y: e.clientY - modalPosition.y
    });
  }
};

// Función para limpiar inventario
const limpiarInventarioCaptura = () => {
  setInventarioManualCaptura(prev => prev.map(item => ({
    ...item,
    cantidadInsumos: 0,
    cantidadPresentaciones: 0,
    totalInsumos: 0
  })));
  localStorage.removeItem('inventarioManualCaptura_backup');
};

// Guardar en localStorage cuando cambia
useEffect(() => {
  if (inventarioManualCaptura.length > 0 && 
      inventarioManualCaptura.some(i => i.totalInsumos > 0)) {
    localStorage.setItem('inventarioManualCaptura_backup', 
      JSON.stringify(inventarioManualCaptura));
  }
}, [inventarioManualCaptura]);
```

**Estructura del modal:**
```jsx
<div 
  className="bg-white rounded-lg shadow-xl..."
  style={{
    transform: `translate(${modalPosition.x}px, ${modalPosition.y}px)`,
    cursor: isDragging ? 'grabbing' : 'default'
  }}
>
  <div 
    className="modal-header-drag ... cursor-grab"
    onMouseDown={handleMouseDown}
  >
    {/* Contenido del header */}
  </div>
</div>
```

**Archivo afectado:**
- ✅ `/app/frontend/src/pages/Compras.js`

---

## I. FUNCIONALIDAD: VISTA PANTALLA COMPLETA EN REPORTES

### I.1 Descripción General

Todos los reportes con tablas de datos extensas deben incluir un botón de **"Pantalla Completa"** para mejorar la experiencia de análisis de datos.

### I.2 Especificación Técnica

| Atributo | Valor |
|----------|-------|
| **Propósito** | Visualizar tablas de datos al 95% de la pantalla |
| **Trigger** | Botón con icono `Maximize2` en el header de la tabla |
| **Cerrar** | Botón "Minimizar" con icono `Minimize2` |
| **Componente UI** | Dialog de shadcn/ui |

### I.3 Implementación Estándar

```jsx
// === Estado requerido ===
const [showFullscreen, setShowFullscreen] = useState(false);

// === Imports de iconos ===
import { Maximize2, Minimize2 } from 'lucide-react';

// === Botón en header de Card ===
<Button
  variant="outline"
  size="sm"
  onClick={() => setShowFullscreen(true)}
  className="h-7 px-2"
  title="Ver en pantalla completa"
>
  <Maximize2 className="h-4 w-4" />
</Button>

// === Modal de pantalla completa ===
<Dialog open={showFullscreen} onOpenChange={setShowFullscreen}>
  <DialogContent className="max-w-[95vw] w-[95vw] max-h-[95vh] h-[95vh] p-0 overflow-hidden">
    <DialogHeader className="px-4 py-3 border-b bg-zinc-100 flex flex-row items-center justify-between">
      <DialogTitle>Título del Reporte ({data?.length || 0} registros)</DialogTitle>
      <div className="flex items-center gap-4">
        {/* Controles del reporte (filtros, toggles) */}
        <Button variant="ghost" size="sm" onClick={() => setShowFullscreen(false)}>
          <Minimize2 className="h-4 w-4 mr-1" />
          Minimizar
        </Button>
      </div>
    </DialogHeader>
    <div className="flex-1 overflow-auto" style={{ height: 'calc(95vh - 70px)' }}>
      {/* Tabla completa aquí */}
    </div>
  </DialogContent>
</Dialog>
```

### I.4 Módulos con Pantalla Completa Implementada

| Módulo | Componente | Estado | Fecha |
|--------|------------|--------|-------|
| Compras | `showFullscreenAuditoria` | ✅ Implementado | 2025-04-09 |
| Comercial | Pendiente | 🔲 Por implementar | - |
| Nóminas | Pendiente | 🔲 Por implementar | - |
| RRHH | Pendiente | 🔲 Por implementar | - |

### I.5 Características del Modal Fullscreen

1. **Dimensiones:** 95vw × 95vh (casi toda la pantalla)
2. **Header fijo:** Contiene título, controles y botón minimizar
3. **Tabla con scroll:** Header sticky, cuerpo scrolleable
4. **Controles replicados:** Los mismos filtros/toggles que en la vista normal
5. **Cierre:** Click en "Minimizar" o fuera del modal

### I.6 Archivos Modificados para Compras.js

| Cambio | Descripción |
|--------|-------------|
| Estado | `const [showFullscreenAuditoria, setShowFullscreenAuditoria] = useState(false)` |
| Iconos | `Maximize2, Minimize2` agregados a imports de lucide-react |
| Botón | Agregado en `CardHeader` del "Detalle de Auditoría" |
| Modal | `<Dialog>` con tabla completa replicada |

**Archivos afectados:**
- ✅ `/app/frontend/src/pages/Compras.js`

---

### I.7 Scroll Horizontal en Modal de Pantalla Completa

**IMPLEMENTACIÓN (2025-04-09):**

Cuando una tabla tiene muchas columnas (ej: Auditoría de Inventarios con ~19 columnas), el modal de Pantalla Completa debe permitir **scroll horizontal** para visualizar todas las columnas.

**Problema original:**
- Al abrir el modal de pantalla completa, la tabla se recortaba horizontalmente
- La columna "Recomendar" (última columna) no era visible
- No había barra de desplazamiento horizontal

**Solución implementada:**
Se agregó un wrapper `<div>` con `overflow-x-auto` alrededor de la tabla:

```jsx
// Estructura CORRECTA con scroll horizontal
<div className="flex-1 overflow-auto p-0" style={{ height: 'calc(95vh - 70px)' }}>
  <div className="overflow-x-auto min-w-full">  {/* ← WRAPPER PARA SCROLL HORIZONTAL */}
    <table className="w-max min-w-full text-sm">
      {/* thead, tbody... */}
    </table>
  </div>  {/* ← Cierre del wrapper */}
</div>
```

**Clases CSS aplicadas:**

| Elemento | Clase | Propósito |
|----------|-------|-----------|
| Contenedor externo | `overflow-auto` | Scroll vertical |
| Wrapper interno | `overflow-x-auto min-w-full` | Scroll horizontal |
| Tabla | `w-max min-w-full` | Ancho automático según contenido |

**Comportamiento:**
- **Scroll vertical:** Permite navegar por todas las filas
- **Scroll horizontal:** Permite ver todas las columnas de la tabla
- **Header sticky:** El encabezado de la tabla permanece visible al hacer scroll vertical

**⚠️ ERROR COMÚN A EVITAR:**
```jsx
// ❌ INCORRECTO - Falta un </div> de cierre
<div className="flex-1 overflow-auto">
  <div className="overflow-x-auto">
    <table>...</table>
  </div>
</DialogContent>  // ← Error: falta cerrar el div externo

// ✅ CORRECTO - Todos los divs cerrados
<div className="flex-1 overflow-auto">
  <div className="overflow-x-auto">
    <table>...</table>
  </div>
</div>  // ← Cierre correcto
</DialogContent>
```

**Archivo afectado:**
- ✅ `/app/frontend/src/pages/Compras.js` (líneas ~2844-2960)

---

### I.8 Auto-Scroll en Captura Manual de Inventario (Navegación con Tab)

**IMPLEMENTACIÓN (2025-04-09):**

En el modal de "Captura Manual de Inventario Físico", al navegar entre los campos de captura usando la tecla **Tab**, la tabla debe hacer scroll automático para mantener visible el campo activo y los siguientes.

**Comportamiento implementado:**

| Situación | Acción automática |
|-----------|-------------------|
| Cursor llega al borde **inferior** | Scroll automático hacia abajo (~100px) |
| Cursor llega al borde **superior** | Scroll automático hacia arriba (~100px) |

**Código de implementación (Compras.js):**

```jsx
// Función para manejar el auto-scroll cuando se navega con Tab
const handleInputFocus = (e) => {
  const input = e.target;
  const tableContainer = input.closest('.overflow-y-auto');
  
  if (tableContainer) {
    const inputRect = input.getBoundingClientRect();
    const containerRect = tableContainer.getBoundingClientRect();
    
    // Si el input está cerca del borde inferior, hacer scroll hacia abajo
    if (inputRect.bottom > containerRect.bottom - 50) {
      tableContainer.scrollTop += 100;
    }
    // Si el input está cerca del borde superior, hacer scroll hacia arriba
    else if (inputRect.top < containerRect.top + 50) {
      tableContainer.scrollTop -= 100;
    }
  }
};

// Aplicar en los inputs de la tabla
<input
  type="number"
  value={item.cantidadInsumos || ''}
  onChange={(e) => handleCantidadChange(idx, 'cantidadInsumos', e.target.value)}
  onFocus={handleInputFocus}  // ← Handler de auto-scroll
  className="..."
/>
```

**Experiencia de usuario:**
1. Usuario hace clic en el primer campo de captura
2. Ingresa cantidad y presiona **Tab**
3. El cursor se mueve al siguiente campo
4. Si el siguiente campo está cerca del borde, la tabla hace scroll automáticamente
5. El campo activo siempre permanece visible

**Parámetros de configuración:**

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| Umbral de detección | 50px | Distancia al borde para activar scroll |
| Cantidad de scroll | 100px | Píxeles de desplazamiento por cada activación |

**Archivo afectado:**
- ✅ `/app/frontend/src/pages/Compras.js` - Modal de Captura Manual

---

### I.9 Scroll Horizontal en Tabla "Detalle de Auditoría" (Vista Normal)

**IMPLEMENTACIÓN (2025-04-09):**

La tabla de "Detalle de Auditoría" en la vista normal (Card dentro del módulo Compras) tiene ~19 columnas. En pantallas con resolución menor, las últimas columnas (Días Inv, Días Obj, Pedido, Ajuste, Recomendar) se recortaban sin posibilidad de verlas.

**Solución implementada:**
Se agregó scroll horizontal al contenedor de la tabla:

```jsx
// ANTES (sin scroll horizontal)
<CardContent className="p-0">
  <div className="max-h-[400px] overflow-auto">
    <table className="w-full text-xs">

// DESPUÉS (con scroll horizontal)
<CardContent className="p-0">
  <div className="max-h-[400px] overflow-auto overflow-x-auto">
    <table className="w-full min-w-max text-xs">
```

**Clases CSS modificadas:**

| Elemento | Antes | Después | Propósito |
|----------|-------|---------|-----------|
| Div contenedor | `overflow-auto` | `overflow-auto overflow-x-auto` | Habilita scroll horizontal |
| Tabla | `w-full` | `w-full min-w-max` | Fuerza ancho mínimo según contenido |

**Comportamiento:**
- **Scroll vertical:** Se mantiene igual (max-height 400px)
- **Scroll horizontal:** Nueva barra de desplazamiento cuando las columnas exceden el ancho visible
- **Header sticky:** Se mantiene fijo al hacer scroll vertical

**Archivo afectado:**
- ✅ `/app/frontend/src/pages/Compras.js` (líneas 2473-2474)

---

### I.10 Modo Pantalla Completa en Explorador BD (Ocultar Sidebar)

**IMPLEMENTACIÓN (2025-04-09):**

El módulo "Explorador de Base de Datos" permite activar un **modo pantalla completa** que oculta el sidebar para maximizar el espacio de visualización de tablas y resultados.

**Problema original:**
- El sidebar ocupaba ~256px del lado izquierdo
- En pantallas pequeñas o con muchas columnas, el espacio era insuficiente
- No había forma de ocultar temporalmente el menú

**Solución implementada:**
Se agregó un botón "Pantalla Completa" / "Minimizar" que activa un modo fullscreen usando `position: fixed`:

```jsx
// Estado para modo pantalla completa
const [fullscreenMode, setFullscreenMode] = useState(false);

// Contenedor principal con clases condicionales
<div 
  className={fullscreenMode 
    ? "fixed inset-0 z-[100] bg-white overflow-auto p-6" 
    : "space-y-4"
  }
>
  {/* Botón toggle */}
  <Button onClick={() => setFullscreenMode(!fullscreenMode)}>
    {fullscreenMode ? <Minimize2 /> : <Maximize2 />}
    {fullscreenMode ? "Minimizar" : "Pantalla Completa"}
  </Button>
  {/* Contenido... */}
</div>
```

**Clases CSS clave:**

| Clase | Propósito |
|-------|-----------|
| `fixed inset-0` | Cubre toda la pantalla |
| `z-[100]` | Superpone el sidebar (z-40) |
| `bg-white` | Fondo blanco sólido |
| `overflow-auto` | Permite scroll si el contenido excede |
| `p-6` | Padding interno |

**Comportamiento:**
- **Modo Normal:** El módulo respeta el layout con sidebar
- **Modo Pantalla Completa:** El contenido ocupa 100% de la pantalla, el sidebar queda oculto detrás
- **Toggle:** El botón permite alternar entre ambos modos

**Archivo afectado:**
- ✅ `/app/frontend/src/pages/ExploradorBD.js`

**Archivos NO modificados:**
- ❌ `Layout.js` - El sidebar global NO fue alterado
- ❌ `serversService.js` - NO fue modificado
- ❌ `server.py` - NO fue modificado

---

### I.11 Scroll Horizontal y Altura Expandida en Pantalla Completa de Explorador BD

**IMPLEMENTACIÓN (2025-04-09):**

En el modo Pantalla Completa del Explorador BD, las tablas de **Columnas** y **Preview de datos** ahora tienen:
1. **Scroll horizontal** garantizado con `min-w-max`
2. **Altura expandida** condicional según el modo (normal vs fullscreen)

**Problema original:**
- En modo Pantalla Completa, las tablas mantenían alturas fijas pequeñas (`max-h-[250px]` y `max-h-[300px]`)
- No se aprovechaba el espacio adicional disponible al ocultar el sidebar
- Tablas con muchas columnas podían recortarse horizontalmente

**Solución implementada:**

```jsx
// ANTES (altura fija)
<div className="overflow-x-auto max-h-[250px]">
  <table className="w-full text-xs">

// DESPUÉS (altura condicional por fullscreenMode)
<div className={`overflow-x-auto overflow-y-auto ${fullscreenMode ? 'max-h-[60vh]' : 'max-h-[250px]'}`}>
  <table className="w-full min-w-max text-xs">
```

**Alturas configuradas:**

| Tabla | Modo Normal | Modo Pantalla Completa |
|-------|-------------|------------------------|
| Columnas | `max-h-[250px]` | `max-h-[60vh]` |
| Preview de datos | `max-h-[300px]` | `max-h-[70vh]` |

**Clases CSS aplicadas:**

| Clase | Propósito |
|-------|-----------|
| `overflow-x-auto` | Scroll horizontal cuando el contenido excede |
| `overflow-y-auto` | Scroll vertical dentro del contenedor |
| `min-w-max` | Fuerza ancho mínimo según contenido de columnas |
| `max-h-[60vh]` / `max-h-[70vh]` | Altura máxima como porcentaje del viewport |

**Archivo afectado:**
- ✅ `/app/frontend/src/pages/ExploradorBD.js` (líneas 1292 y 1354)

---

### I.12 Indicadores de Estado en Filtros de Auditoría de Inventarios

**IMPLEMENTACIÓN (2025-04-10):**

Los dropdowns de filtros en la sección "Auditoría Operativa de Inventarios" ahora muestran indicadores visuales de estado para ayudar al usuario a entender qué está pasando.

**Problema original:**
- Cuando no había requisiciones o inventarios, el dropdown aparecía vacío sin explicación
- El usuario no sabía si los datos estaban cargando o si simplemente no había datos
- No había feedback visual de qué sucursal estaba seleccionada

**Solución implementada:**

1. **Estados de carga** (`loadingPedidos`, `loadingInventarios`)
2. **Mensajes contextuales** cuando no hay datos
3. **Indicador de sucursal** activa en el mensaje vacío
4. **Logs de consola** para diagnóstico (F12 → Console)

**Nuevos estados agregados:**
```jsx
const [loadingPedidos, setLoadingPedidos] = useState(false);
const [loadingInventarios, setLoadingInventarios] = useState(false);
```

**Mensajes mostrados en los dropdowns:**

| Estado | Mensaje en Requisiciones | Mensaje en Inventarios |
|--------|-------------------------|------------------------|
| Cargando | "Cargando..." + spinner | "Cargando..." + spinner |
| Sin datos | "Sin requisiciones" | "Sin inventarios" |
| Con datos | "Seleccionar" | "Seleccionar inventario(s)" |
| Seleccionado | "N seleccionada(s)" | "N seleccionado(s)" |

**Diagnóstico en consola:**
```javascript
// Al cargar requisiciones
console.log(`[Auditoría] Requisiciones cargadas para sucursal "${parentSucursal}":`, response.data.length);

// Al cargar inventarios
console.log(`[Auditoría] Inventarios cargados para sucursal "${parentSucursal}":`, response.data.length);
```

**Mensaje cuando dropdown está vacío:**
```jsx
<div className="py-4 px-3 text-center text-zinc-500">
  <p className="text-xs font-medium">No hay requisiciones pendientes</p>
  <p className="text-xs mt-1">Sucursal: {parentSucursal || 'No seleccionada'}</p>
</div>
```

**Archivo afectado:**
- ✅ `/app/frontend/src/pages/Compras.js`

**Archivos NO modificados:**
- ❌ `server.py` - NO fue modificado
- ❌ `serversService.js` - NO fue modificado

---

### I.13 Fix Crítico: Formato de Fecha SQL para APIs Locales MPRO

**IMPLEMENTACIÓN (2025-04-10):**

**Problema identificado:**
La función `obtener_ventas_dia_api_local()` usaba formato de fecha `103` (dd/mm/yyyy - europeo) pero los servidores SQL Server de MPRO esperan formato `101` (mm/dd/yyyy - USA).

**Síntoma:**
- El módulo "Servidores" → "Probar Conexión" funcionaba correctamente mostrando ventas del día
- El Tablero Ejecutivo en modo "Ventas del Día" mostraba $0 para QRO y ORIGEN
- Los logs mostraban "API Local ERROR - HTTP 500"

**Causa raíz:**
El endpoint `/api/test-api-connection` usaba formato `101` (que funcionaba), pero la función `obtener_ventas_dia_api_local()` usaba formato `103` (que fallaba).

**Solución aplicada:**

```sql
-- ANTES (formato europeo - NO funcionaba)
WHERE CONVERT(date, co_fecha, 103) = CONVERT(date, GETDATE(), 103)

-- DESPUÉS (formato USA - SÍ funciona)
WHERE CONVERT(date, co_fecha, 101) = CONVERT(date, GETDATE(), 101)
```

**Referencia de formatos SQL Server CONVERT:**

| Código | Formato | Ejemplo |
|--------|---------|---------|
| 101 | mm/dd/yyyy (USA) | 04/10/2026 |
| 103 | dd/mm/yyyy (Europeo) | 10/04/2026 |

**REGLA CRÍTICA:**
Siempre usar formato `101` para consultas de fecha en servidores MPRO de EDARSA.

**Archivo modificado:**
- ✅ `/app/backend/server.py` (línea 152)

---

## APROBACIONES

- **Creado por:** E1 Agent
- **Revisado por:** Usuario EDARSA
- **Estado:** Pendiente de aprobación formal

---

**FIN DEL CATÁLOGO**
