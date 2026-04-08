# CATÁLOGO MAESTRO DE REGLAS DE FILTROS - EDARSA HUB

**Versión:** 1.0  
**Fecha de creación:** 2025-04-08  
**Última actualización:** 2025-04-08  
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

## APROBACIONES

- **Creado por:** E1 Agent
- **Revisado por:** Usuario EDARSA
- **Estado:** Pendiente de aprobación formal

---

**FIN DEL CATÁLOGO**
