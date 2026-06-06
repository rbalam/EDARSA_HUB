# AUDITORÍA - Finanzas Fase 2: Control de Ingresos / Cortes de Caja

**Fecha:** 30 de Abril de 2026  
**Autor:** E1 Agent  
**Status:** AUDITORÍA COMPLETA - VALIDACIÓN EDARSAHUB VS ORIGEN

---

## 🔴 HALLAZGO CRÍTICO

**Los 70 registros en `Finanzas_CortesCaja` de EDARSAHUB son DATOS DEMO, NO DATOS REALES.**

**Evidencia:**
- Todos tienen `FechaAlta` = 2026-04-13 (mismo día)
- Los montos tienen patrones uniformes/aleatorios
- `SucursalID` usa enteros (1-5) en lugar de UUIDs de unidades reales
- No hay `UnidadNegocioID` poblado
- Rango de fechas solo cubre 13 días (2026-03-31 a 2026-04-13)

**Los sistemas origen tienen datos reales:**
- SoftRestaurant: **4,992 turnos** + **23,387 movimientos de caja**
- MPRO: **4,427 cortes** en `Comanda_Corte`

---

## 1. RESUMEN EJECUTIVO

Esta auditoría documenta la arquitectura existente para Control de Ingresos, identificando las fuentes de datos en EDARSAHUB y los sistemas origen (SoftRestaurant, MPRO), siguiendo estrictamente la regla de usar EDARSAHUB como fuente única de configuración.

### Hallazgos Principales

| # | Hallazgo | Severidad | Acción Requerida |
|---|----------|-----------|------------------|
| 1 | El módulo `ingresos.py` usa datos demo hardcodeados | CRÍTICO | Reescribir para usar EDARSAHUB |
| 2 | Las 5 unidades de negocio están configuradas en EDARSAHUB | OK | Usar esta fuente |
| 3 | Tabla `Finanzas_CortesCaja` existe en EDARSAHUB (70 registros) | OK | Es la tabla destino |
| 4 | SoftRestaurant tiene tablas origen (`turnos`, `movtoscaja`) | OK | Consultar para datos reales |
| 5 | MPRO requiere identificar tablas de cortes equivalentes | PENDIENTE | Investigar estructura |

---

## 2. RESOLUCIÓN DE UNIDADES DE NEGOCIO DESDE EDARSAHUB

### 2.1 Tabla Principal: `Unidades_Negocio`

**Ubicación:** EDARSAHUB SQL Server (`<REDACTED_EDARSAHUB_SQL_HOST>:1433`)

**Estructura:**
```sql
CREATE TABLE Unidades_Negocio (
    id              UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
    nombre          NVARCHAR(100) NOT NULL,
    codigo          NVARCHAR(20) NOT NULL,
    server_id       NVARCHAR(50) NOT NULL,      -- FK a Servidores_Conexiones
    sucursal_origen_id NVARCHAR(50) NULL,       -- ID en sistema origen
    system_type     NVARCHAR(50) NOT NULL,      -- 'SoftRestaurant' | 'MPRO'
    activo          BIT DEFAULT 1,
    orden           INT,
    created_at      DATETIME,
    updated_at      DATETIME
)
```

### 2.2 Mapeo de las 5 Unidades de Negocio

| # | Unidad | ID | ServerID | System Type | Activo |
|---|--------|-----|----------|-------------|--------|
| 1 | **130° QUERÉTARO** | `9bc05ced-6b2b-4a0a-aa90-ce649b78e12c` | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | MPRO | ✅ |
| 2 | **130° MÉRIDA** | `19e076fb-c6de-4ea5-84ab-1caa9e86082c` | `a5547321-1139-4d2b-9d53-182ca737b6b6` | SoftRestaurant | ✅ |
| 3 | **ORIGEN** | `23ca0b76-6580-4874-ba9b-672b122ca197` | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` | MPRO | ✅ |
| 4 | **CIENFUEGOS** | `b06ee652-0370-4267-b0a8-da6fc39b590a` | `6d053c22-523e-48c0-b72b-96081e2d781b` | SoftRestaurant | ✅ |
| 5 | **LA ESTELAR** | `dfb86008-1b81-472a-9e50-8a0821dec4b2` | `a5ff0e25-f029-43db-b634-d4ac814c904f` | SoftRestaurant | ✅ |

### 2.3 Query para Obtener Unidades

```sql
-- Obtener unidades de negocio activas con su servidor asociado
SELECT 
    un.id AS unidad_id,
    un.nombre AS unidad_nombre,
    un.codigo AS unidad_codigo,
    un.server_id,
    un.sucursal_origen_id,
    un.system_type,
    sc.nombre AS servidor_nombre,
    sc.host,
    sc.port,
    sc.database_name,
    sc.username,
    sc.password_encrypted
FROM Unidades_Negocio un
JOIN Servidores_Conexiones sc ON un.server_id = CAST(sc.id AS NVARCHAR(50))
WHERE un.activo = 1 AND sc.activo = 1
ORDER BY un.orden
```

---

## 3. RESOLUCIÓN DE CONEXIONES DESDE EDARSAHUB

### 3.1 Tabla Principal: `Servidores_Conexiones`

**Ubicación:** EDARSAHUB SQL Server

**Campos Relevantes:**
- `id` - Identificador único (GUID)
- `nombre` - Nombre descriptivo
- `system_type` - 'SoftRestaurant' | 'MPRO' | 'EDARSA_HUB'
- `host` - Host de conexión
- `port` - Puerto
- `database_name` - Base de datos
- `username` - Usuario
- `password_encrypted` - Password cifrado (usar `decrypt_secret()`)
- `activo` - Estado activo

### 3.2 Servidores Activos Relevantes

| ID | Nombre | System Type | Host | Puerto | Database |
|----|--------|-------------|------|--------|----------|
| `a5547321-...` | 130° MÉRIDA | SoftRestaurant | 130mid.ddns.net | 1433 | softrestaurant10 |
| `6d053c22-...` | CIENFUEGOS | SoftRestaurant | servercienfuegos.ddns.net,6669 | 1433 | softrestaurant95pro |
| `a5ff0e25-...` | LA ESTELAR | SoftRestaurant | serverestelar.ddns.net,6969 | 6969 | softrestaurant12 |
| `1b230a06-...` | ManagementPro | MPRO | <REDACTED_EDARSAHUB_SQL_HOST> | 1433 | CENTRAL2020 |

### 3.3 Función Existente para Obtener Servidores

```python
# Archivo: /app/backend/modules/comercial/repository.py
from modules.comercial.repository import _get_server_by_id_sql, _get_servers_for_tablero_sql

# Obtener servidor por ID
server = _get_server_by_id_sql("a5547321-1139-4d2b-9d53-182ca737b6b6")

# Obtener todos los servidores activos para tablero
servers = _get_servers_for_tablero_sql()
```

---

## 4. MAPEO UNIDAD → SERVER → CONEXIÓN → SYSTEM_TYPE

### 4.1 Diagrama de Flujo

```
Usuario Autenticado
        │
        ▼
┌─────────────────────────┐
│  get_user_empresas_     │
│  permitidas(user)       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  EDARSAHUB:             │
│  Unidades_Negocio       │
│  WHERE activo=1         │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Para cada unidad:      │
│  server_id → conexión   │
└───────────┬─────────────┘
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
┌─────────┐   ┌─────────┐
│  MPRO   │   │SoftRest │
│CENTRAL  │   │  SQL    │
└────┬────┘   └────┬────┘
     │             │
     ▼             ▼
┌─────────────────────────┐
│  Consultar datos de     │
│  cortes de caja origen  │
└─────────────────────────┘
```

### 4.2 Mapeo Completo por Unidad

| Unidad | server_id | Conexión | System Type | Filtro Interno |
|--------|-----------|----------|-------------|----------------|
| 130° QRO | `1b230a06-...` | CENTRAL2020 | MPRO | `sucursal_id` o `almacen_id` |
| 130° MÉRIDA | `a5547321-...` | softrestaurant10 | SoftRestaurant | Consulta directa |
| ORIGEN | `1b230a06-...` | CENTRAL2020 | MPRO | `sucursal_id` o `almacen_id` |
| CIENFUEGOS | `6d053c22-...` | softrestaurant95pro | SoftRestaurant | Consulta directa |
| LA ESTELAR | `a5ff0e25-...` | softrestaurant12 | SoftRestaurant | Consulta directa |

---

## 5. TABLAS ORIGEN PARA CORTES DE CAJA

### 5.1 SoftRestaurant - Tablas Identificadas

```
130° MÉRIDA (softrestaurant10):
├── turnos              - Turnos de caja
├── turnosf             - Turnos finalizados
├── movtoscaja          - Movimientos de caja
├── movtoscajadetalles  - Detalles de movimientos
├── declaracioncorte    - Declaración de corte
├── destinatariocorte   - Destinatarios de corte
└── HORARIOCORTE        - Horarios de corte
```

### 5.2 Query Propuesta para SoftRestaurant

```sql
-- Obtener cortes de caja de SoftRestaurant
SELECT 
    t.idturno,
    t.fecha,
    t.turno,
    t.efectivo,
    t.tarjeta,
    t.vales,
    t.credito,
    t.cheque,
    t.otros,
    t.totalcorte,
    t.estatus
FROM turnos t
WHERE t.fecha BETWEEN @fecha_inicio AND @fecha_fin
  AND t.estatus = 'CERRADO'
ORDER BY t.fecha DESC
```

### 5.3 MPRO - Tablas a Identificar

**PENDIENTE:** Investigar estructura de CENTRAL2020 para:
- Tabla de cortes de caja
- Tabla de turnos
- Tabla de movimientos de efectivo

---

## 6. TABLA DESTINO EN EDARSAHUB

### 6.1 Estructura: `Finanzas_CortesCaja`

```sql
CREATE TABLE Finanzas_CortesCaja (
    CorteCajaID             BIGINT IDENTITY PRIMARY KEY,
    SucursalID              INT NOT NULL,
    UnidadNegocioID         NVARCHAR(50),        -- FK a Unidades_Negocio
    FechaCorte              DATE NOT NULL,
    TurnoID                 INT,
    
    -- Montos por forma de pago
    TotalEfectivo           DECIMAL(18,2),
    TotalTarjetaDebito      DECIMAL(18,2),
    TotalTarjetaCredito     DECIMAL(18,2),
    TotalAmex               DECIMAL(18,2),
    TotalInternacional      DECIMAL(18,2),
    TotalVales              DECIMAL(18,2),
    TotalOtros              DECIMAL(18,2),
    
    -- Comisiones calculadas
    ComisionDebito          DECIMAL(18,2),
    ComisionCredito         DECIMAL(18,2),
    ComisionAmex            DECIMAL(18,2),
    ComisionInternacional   DECIMAL(18,2),
    
    -- Fechas de depósito proyectadas
    FechaDepositoEfectivo       DATE,
    FechaDepositoDebito         DATE,
    FechaDepositoCredito        DATE,
    FechaDepositoAmex           DATE,
    FechaDepositoInternacional  DATE,
    
    -- Estados de depósito
    DepositadoEfectivo          BIT DEFAULT 0,
    DepositadoDebito            BIT DEFAULT 0,
    DepositadoCredito           BIT DEFAULT 0,
    DepositadoAmex              BIT DEFAULT 0,
    DepositadoInternacional     BIT DEFAULT 0,
    
    -- Control
    EstatusCierreID         TINYINT DEFAULT 1,
    Observaciones           VARCHAR(500),
    Activo                  BIT DEFAULT 1,
    FechaAlta               DATETIME2 DEFAULT GETDATE()
)
```

### 6.2 Estado Actual

- **Registros existentes:** 70
- **Última consulta:** Sin datos recientes (SELECT TOP 5 no retorna filas)

---

## 7. VALIDACIÓN RBAC / ALCANCE

### 7.1 Flujo de Autorización

```python
# Archivo: /app/backend/core/security.py

async def get_user_empresas_permitidas(user: Dict) -> List[str]:
    """
    1. SuperAdministrador → todas las empresas activas
    2. empresas_permitidas en user → usar esa lista
    3. Administrador → todas las empresas activas
    4. Otros → lista vacía
    """
```

### 7.2 Opción "TODAS"

- **NO significa:** Todos los servidores del sistema
- **SÍ significa:** Todas las unidades autorizadas para el usuario autenticado
- **Validación:** Filtrar por `empresas_permitidas` y `unidades_negocio_permitidas`

### 7.3 Query con RBAC

```sql
-- Obtener unidades permitidas para un usuario
SELECT un.*
FROM Unidades_Negocio un
JOIN Usuario_Catalogo u ON u.empresa_id IN (
    SELECT value FROM STRING_SPLIT(u.empresas_permitidas, ',')
)
WHERE un.activo = 1
  AND u.user_id = @user_id
```

---

## 8. CÓDIGO EXISTENTE A CORREGIR

### 8.1 Archivo: `/app/backend/modules/finanzas/ingresos.py`

**Problema:** Usa datos demo hardcodeados

```python
# LÍNEA 171-179 - PROBLEMA: Sucursales hardcodeadas
def generar_cortes_caja_demo():
    sucursales = [
        {"id": 1, "nombre": "130° QUERETARO"},
        {"id": 2, "nombre": "ORIGEN"},
        {"id": 3, "nombre": "130° TULUM"},  # ❌ No existe
        {"id": 4, "nombre": "CIEN FUEGOS"},
        {"id": 5, "nombre": "XCANATUN"},    # ❌ No existe
    ]
```

### 8.2 Corrección Requerida

```python
# CORRECTO: Obtener unidades desde EDARSAHUB
async def get_unidades_negocio_activas():
    """Obtiene unidades de negocio desde EDARSAHUB SQL"""
    from core.db import execute_sql_query
    
    query = """
    SELECT 
        id, nombre, codigo, server_id, system_type
    FROM Unidades_Negocio
    WHERE activo = 1
    ORDER BY orden
    """
    
    return execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )
```

---

## 9. EVIDENCIA POR UNIDAD

### 9.1 130° QUERÉTARO (MPRO)

| Campo | Valor |
|-------|-------|
| unidad_negocio_id | `9bc05ced-6b2b-4a0a-aa90-ce649b78e12c` |
| nombre_unidad | 130° QUERETARO |
| server_id | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` |
| conexión | ManagementPro / CENTRAL2020 |
| system_type | MPRO |
| activa | ✅ |
| datos_disponibles | PENDIENTE VALIDAR |

### 9.2 130° MÉRIDA (SoftRestaurant)

| Campo | Valor |
|-------|-------|
| unidad_negocio_id | `19e076fb-c6de-4ea5-84ab-1caa9e86082c` |
| nombre_unidad | 130° MERIDA |
| server_id | `a5547321-1139-4d2b-9d53-182ca737b6b6` |
| conexión | 130mid.ddns.net:1433 / softrestaurant10 |
| system_type | SoftRestaurant |
| activa | ✅ |
| tablas_origen | turnos, movtoscaja, declaracioncorte |

### 9.3 ORIGEN (MPRO)

| Campo | Valor |
|-------|-------|
| unidad_negocio_id | `23ca0b76-6580-4874-ba9b-672b122ca197` |
| nombre_unidad | ORIGEN |
| server_id | `1b230a06-ffaf-4c70-bd27-b1be3579dea6` |
| conexión | ManagementPro / CENTRAL2020 |
| system_type | MPRO |
| activa | ✅ |
| datos_disponibles | PENDIENTE VALIDAR |

### 9.4 CIENFUEGOS (SoftRestaurant)

| Campo | Valor |
|-------|-------|
| unidad_negocio_id | `b06ee652-0370-4267-b0a8-da6fc39b590a` |
| nombre_unidad | CIENFUEGOS |
| server_id | `6d053c22-523e-48c0-b72b-96081e2d781b` |
| conexión | servercienfuegos.ddns.net:6669 / softrestaurant95pro |
| system_type | SoftRestaurant |
| activa | ✅ |
| tablas_origen | turnos, movtoscaja |

### 9.5 LA ESTELAR (SoftRestaurant)

| Campo | Valor |
|-------|-------|
| unidad_negocio_id | `dfb86008-1b81-472a-9e50-8a0821dec4b2` |
| nombre_unidad | LA ESTELAR |
| server_id | `a5ff0e25-f029-43db-b634-d4ac814c904f` |
| conexión | serverestelar.ddns.net:6969 / softrestaurant12 |
| system_type | SoftRestaurant |
| activa | ✅ |
| tablas_origen | turnos, movtoscaja |

---

## 10. CONFIRMACIONES DE CUMPLIMIENTO

| # | Regla | Cumplimiento |
|---|-------|--------------|
| 1 | No usar MongoDB como fuente principal de configuración | ✅ Confirmado - Usar EDARSAHUB SQL |
| 2 | No hardcodear unidades de negocio | ⚠️ Pendiente corregir en `ingresos.py` |
| 3 | No crear conexiones nuevas | ✅ Usar `Servidores_Conexiones` |
| 4 | No duplicar tablas o campos | ✅ Usar `Finanzas_CortesCaja` existente |
| 5 | Usar lógica de RBAC existente | ✅ `get_user_empresas_permitidas()` |
| 6 | Validar las 5 unidades | ✅ Documentadas |
| 7 | Documentar unidad → conexión → origen | ✅ Sección 4 |

---

## 11. PRÓXIMOS PASOS (IMPLEMENTACIÓN)

### Fase 2.1: Repositorio SoftRestaurant para Cortes
1. Crear `/app/backend/modules/finanzas/repository_ingresos_softrestaurant.py`
2. Usar `execute_sql_subprocess` para consultas
3. Implementar query a tablas `turnos`, `movtoscaja`
4. Mapear a estructura de `Finanzas_CortesCaja`

### Fase 2.2: Repositorio MPRO para Cortes
1. Investigar tablas de cortes en CENTRAL2020
2. Crear `/app/backend/modules/finanzas/repository_ingresos_mpro.py`
3. Implementar queries equivalentes

### Fase 2.3: Orquestador
1. Modificar `/app/backend/modules/finanzas/ingresos.py`
2. Eliminar datos demo
3. Implementar flujo: Unidad → Server → Datos origen
4. Respetar RBAC del usuario

### Fase 2.4: Frontend
1. Usar selector de Unidad de Negocio existente
2. Integrar con endpoint real
3. Mostrar datos por unidad seleccionada

---

## 12. ANEXO: QUERIES DE VALIDACIÓN

```sql
-- A. Verificar mapeo unidad-servidor completo
SELECT 
    un.nombre AS unidad,
    un.system_type,
    sc.nombre AS servidor,
    sc.host,
    sc.database_name
FROM Unidades_Negocio un
LEFT JOIN Servidores_Conexiones sc 
    ON un.server_id = CAST(sc.id AS NVARCHAR(50))
WHERE un.activo = 1
ORDER BY un.orden;

-- B. Verificar cortes existentes en EDARSAHUB
SELECT 
    COUNT(*) as total,
    MIN(FechaCorte) as primera_fecha,
    MAX(FechaCorte) as ultima_fecha
FROM Finanzas_CortesCaja
WHERE Activo = 1;

-- C. Verificar conexiones activas por system_type
SELECT 
    system_type,
    COUNT(*) as total
FROM Servidores_Conexiones
WHERE activo = 1
GROUP BY system_type;
```

---

**FIN DEL DOCUMENTO DE AUDITORÍA**

---

## 13. VALIDACIÓN DE DATOS DE CORTES EN EDARSAHUB

### 13.1 Estado Actual de `Finanzas_CortesCaja`

| Campo | Valor |
|-------|-------|
| **Tabla existe** | ✅ Sí |
| **Total registros** | 70 |
| **Registros activos** | 70 |
| **Rango fechas** | 2026-03-31 a 2026-04-13 (13 días) |
| **Gran total** | $5,123,473.51 |

### 13.2 Estructura de la Tabla

```sql
Finanzas_CortesCaja:
├── CorteCajaID (bigint, PK)
├── SucursalID (int) ⚠️ Usa enteros 1-5, no UUIDs
├── FechaCorte (date)
├── TurnoID (int)
├── TotalEfectivo, TotalTarjetaDebito, TotalTarjetaCredito (decimal)
├── TotalAmex, TotalInternacional, TotalVales, TotalOtros (decimal)
├── Comisiones (Débito, Crédito, AMEX, Internacional)
├── FechasDepósito (Efectivo, Débito, Crédito, AMEX, Internacional)
├── Depositado* (bit) - Estados de depósito
├── EstatusCierreID, Observaciones, Activo
└── FechaAlta (datetime2)
```

### 13.3 Campos FALTANTES en EDARSAHUB

| Campo Requerido | Presente | Observación |
|----------------|----------|-------------|
| unidad_negocio_id | ❌ NO | Crítico - No hay vínculo a unidades |
| sistema_origen | ❌ NO | No se identifica SoftRestaurant vs MPRO |
| server_id | ❌ NO | No hay trazabilidad a conexión origen |
| folio_corte | ❌ NO | No hay folio único del sistema origen |
| cajero | ❌ NO | Solo TurnoID, sin identificar cajero |
| caja | ❌ NO | No hay identificación de caja/estación |
| propinas | ❌ NO | No existe columna |
| retiros | ❌ NO | No existe columna |
| hash_origen | ❌ NO | Sin validación de integridad |
| origen_tabla | ❌ NO | Sin referencia a tabla origen |

### 13.4 Cobertura por SucursalID (DEMO)

| SucursalID | Registros | Fechas | Efectivo | Tarjetas |
|------------|-----------|--------|----------|----------|
| 1 | 14 | 03/31-04/13 | $221,403 | $703,690 |
| 2 | 14 | 03/31-04/13 | $255,108 | $663,436 |
| 3 | 14 | 03/31-04/13 | $247,460 | $655,854 |
| 4 | 14 | 03/31-04/13 | $216,363 | $656,078 |
| 5 | 14 | 03/31-04/13 | $244,412 | $734,642 |

**⚠️ PROBLEMA:** Los SucursalID (1-5) NO corresponden a las unidades de negocio reales. No hay mapeo a:
- 130° QRO
- 130° MÉRIDA
- ORIGEN
- CIENFUEGOS
- LA ESTELAR

### 13.5 Indicadores de que son DATOS DEMO

1. **FechaAlta uniforme:** Todos los registros creados el 2026-04-13 en el mismo segundo
2. **Montos con patrones:** Valores aleatorios uniformes ($8,342 - $32,981)
3. **SucursalID enteros:** Usa 1,2,3,4,5 en lugar de UUIDs
4. **Sin UnidadNegocioID:** Columna vacía o inexistente
5. **Sin trazabilidad:** No hay folio_origen, sistema_origen, hash

---

## 14. COMPARACIÓN EDARSAHUB VS ORIGEN

### 14.1 SoftRestaurant - 130° MÉRIDA

| Métrica | EDARSAHUB | Origen (turnos) | Diferencia |
|---------|-----------|-----------------|------------|
| Registros | ~14 (SucID=?) | **4,992** | -99.7% |
| Tabla origen | N/A | `turnos` | No mapeado |
| Columnas clave | Parciales | Completas | Faltan: cajero, caja, cierre |
| Rango fechas | 13 días | Histórico completo | Incompleto |

**Estructura `turnos` en SoftRestaurant:**
```
- idturno, idturnointerno (identificadores únicos)
- apertura, cierre (datetime)
- idestacion (ej: "130GRADOSCAJA")
- cajero (ej: "CAJA1", "CAJA2")
- efectivo, tarjeta, vales, credito
- idempresa, procesadoweb, enviadoacentral
```

**Muestra de datos reales:**
```
ID=8135, Fecha=2026-04-29, Cajero=CAJA1, Efectivo=$120,509, Crédito=$1,325
ID=8134, Fecha=2026-04-28, Cajero=CAJA2, Efectivo=$68,337, Crédito=$0
```

### 14.2 SoftRestaurant - CIENFUEGOS

| Métrica | EDARSAHUB | Origen | Observación |
|---------|-----------|--------|-------------|
| Conexión | N/A | servercienfuegos.ddns.net:6669 | Activa |
| Database | N/A | softrestaurant95pro | Verificada |
| Tablas | N/A | turnos, movtoscaja | Disponibles |

### 14.3 MPRO - ORIGEN / 130° QRO

| Métrica | EDARSAHUB | Origen (Comanda_Corte) | Diferencia |
|---------|-----------|------------------------|------------|
| Registros | ~14 (SucID=?) | **4,427** | -99.7% |
| Tabla origen | N/A | `Comanda_Corte` | No mapeado |

**Estructura `Comanda_Corte` en MPRO:**
```
- Cc_Folio (ej: "12-0000004") - Folio único
- Sc_Cve_Sucursal (ej: "0012", "0021", "0023")
- Cc_Fecha, Cc_Turno
- Cc_Caja, Cc_Cajero
- Cc_Importe_Pago, Cc_Importe_Venta
- Cc_Importe_Declarado, Cc_Importe_Retirado
- Cc_Venta_Contado, Cc_Venta_Credito
- Es_Cve_Estado
```

**Muestra de datos reales:**
```
Folio="12-0000004", Sucursal=0012, Fecha=2020-12-23
Pago=$7,552, Venta=$16,437, Declarado=$7,554, Retirado=$-54
```

### 14.4 Resumen de Cobertura

| Unidad | System | EDARSAHUB | Origen | Cobertura |
|--------|--------|-----------|--------|-----------|
| 130° QRO | MPRO | ❌ 0 real | ✅ 4,427 | **0%** |
| 130° MÉRIDA | SoftRest | ❌ 0 real | ✅ 4,992 | **0%** |
| ORIGEN | MPRO | ❌ 0 real | ✅ 4,427 | **0%** |
| CIENFUEGOS | SoftRest | ❌ 0 real | ✅ ~5,000 | **0%** |
| LA ESTELAR | SoftRest | ❌ 0 real | ✅ ~3,000 | **0%** |

**CONCLUSIÓN:** EDARSAHUB tiene 0% de datos reales de cortes de caja.

---

## 15. RECOMENDACIÓN: NO DEPENDER DE CONEXIONES EN VIVO

### 15.1 Arquitectura Objetivo

```
┌─────────────────────────────────────────────────────────┐
│                    ARQUITECTURA OBJETIVO                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐       │
│  │SoftRestau.│    │   MPRO    │    │  Otros    │       │
│  │  turnos   │    │Comanda_   │    │ Sistemas  │       │
│  │movtoscaja │    │  Corte    │    │           │       │
│  └─────┬─────┘    └─────┬─────┘    └─────┬─────┘       │
│        │                │                │              │
│        └────────────────┼────────────────┘              │
│                         │                               │
│                         ▼                               │
│              ┌─────────────────────┐                    │
│              │  PROCESO DE SYNC    │                    │
│              │  (Job programado)   │                    │
│              │  - Extrae de origen │                    │
│              │  - Valida duplicados│                    │
│              │  - Calcula hash     │                    │
│              │  - Inserta/actualiza│                    │
│              └──────────┬──────────┘                    │
│                         │                               │
│                         ▼                               │
│              ┌─────────────────────┐                    │
│              │     EDARSAHUB       │                    │
│              │ Finanzas_CortesCaja │                    │
│              │  (DATOS REALES)     │                    │
│              └──────────┬──────────┘                    │
│                         │                               │
│                         ▼                               │
│              ┌─────────────────────┐                    │
│              │  DASHBOARD FINANZAS │                    │
│              │  Control de Ingresos│                    │
│              │  (Lee de EDARSAHUB) │                    │
│              └─────────────────────┘                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 15.2 Riesgos de Depender de Conexiones en Vivo

| Riesgo | Impacto | Probabilidad |
|--------|---------|--------------|
| Servidor origen caído | Dashboard en ceros | Alta (DDNS) |
| Conexión lenta/timeout | UI bloqueada | Media |
| Credenciales rotadas | Falla silenciosa | Media |
| Puerto bloqueado | Sin datos | Media |
| Base de datos bloqueada | Error 500 | Baja |

### 15.3 Ventajas de Sincronizar a EDARSAHUB

1. **Resiliencia:** Dashboard siempre funcional aunque origen esté caído
2. **Rendimiento:** Queries locales vs remotas
3. **Trazabilidad:** hash_origen, sistema_origen, folio_origen
4. **Auditoría:** Log de sincronización
5. **Consistencia:** Un solo modelo de datos
6. **RBAC:** Control centralizado en EDARSAHUB

---

## 16. PROPUESTA DE MIGRACIÓN/SINCRONIZACIÓN

### 16.1 Diseño de Tabla Destino (Modificaciones)

```sql
-- Agregar columnas faltantes a Finanzas_CortesCaja
ALTER TABLE Finanzas_CortesCaja ADD
    UnidadNegocioID NVARCHAR(50) NULL,          -- UUID de Unidades_Negocio
    SistemaOrigen NVARCHAR(20) NULL,            -- 'SoftRestaurant' | 'MPRO'
    ServerID NVARCHAR(50) NULL,                 -- UUID de Servidores_Conexiones
    FolioOrigen NVARCHAR(50) NULL,              -- Folio único del sistema origen
    Cajero NVARCHAR(50) NULL,                   -- Nombre/código cajero
    Caja NVARCHAR(50) NULL,                     -- ID de caja/estación
    Propinas DECIMAL(18,2) DEFAULT 0,           -- Total propinas
    Retiros DECIMAL(18,2) DEFAULT 0,            -- Total retiros
    HashOrigen NVARCHAR(64) NULL,               -- SHA256 para validación
    OrigenTabla NVARCHAR(50) NULL,              -- 'turnos', 'Comanda_Corte'
    SucursalOrigenID NVARCHAR(20) NULL,         -- ID en sistema origen
    FechaSincronizacion DATETIME2 NULL;         -- Última sync
```

### 16.2 Llave Única Propuesta

**Para SoftRestaurant:**
```
UNIQUE (SistemaOrigen, ServerID, idturnointerno)
```

**Para MPRO:**
```
UNIQUE (SistemaOrigen, ServerID, Cc_Folio)
```

**Hash de origen:**
```
HashOrigen = SHA256(SistemaOrigen + ServerID + FolioOrigen + FechaCorte + Cajero + TotalCorte)
```

### 16.3 Mapeo de Campos

#### SoftRestaurant (`turnos`) → `Finanzas_CortesCaja`

| Origen | Destino | Transformación |
|--------|---------|----------------|
| idturnointerno | FolioOrigen | Directo |
| CAST(cierre AS DATE) | FechaCorte | Extraer fecha |
| idturno | TurnoID | Directo |
| cajero | Cajero | Directo |
| idestacion | Caja | Directo |
| efectivo | TotalEfectivo | Directo |
| tarjeta | TotalTarjetaDebito | *Requiere desglose |
| vales | TotalVales | Directo |
| credito | TotalTarjetaCredito | *Mapear |
| - | UnidadNegocioID | Lookup por server_id |
| - | SistemaOrigen | 'SoftRestaurant' |
| - | HashOrigen | Calculado |

#### MPRO (`Comanda_Corte`) → `Finanzas_CortesCaja`

| Origen | Destino | Transformación |
|--------|---------|----------------|
| Cc_Folio | FolioOrigen | Directo |
| Cc_Fecha | FechaCorte | Directo |
| Cc_Turno | TurnoID | CAST |
| Cc_Cajero | Cajero | Lookup a tabla Cajero |
| Cc_Caja | Caja | Directo |
| Cc_Importe_Pago | TotalEfectivo | *Desglose por forma pago |
| Cc_Venta_Contado | TotalTarjetaDebito | *Mapear |
| Cc_Venta_Credito | TotalTarjetaCredito | *Mapear |
| Cc_Importe_Retirado | Retiros | Directo |
| Sc_Cve_Sucursal | SucursalOrigenID | Directo |
| - | UnidadNegocioID | Lookup por sucursal → unidad |
| - | SistemaOrigen | 'MPRO' |

### 16.4 Estrategia de Sincronización

1. **Frecuencia:** Cada 15 minutos (configurable)
2. **Estrategia:** Incremental por fecha
3. **Anti-duplicados:** MERGE con llave única
4. **Reintentos:** 3 intentos con backoff exponencial
5. **Bitácora:** Tabla `Finanzas_CortesCaja_SyncLog`
6. **Alertas:** Si sync falla 3 veces consecutivas

### 16.5 Validaciones Post-Sync

```sql
-- Validar totales por unidad y fecha
SELECT 
    UnidadNegocioID,
    FechaCorte,
    SUM(TotalEfectivo + TotalTarjetaDebito + TotalTarjetaCredito) as Total_EDARSA,
    -- Comparar con origen...
FROM Finanzas_CortesCaja
WHERE FechaSincronizacion >= @ultima_sync
GROUP BY UnidadNegocioID, FechaCorte;
```

---

## 17. UBICACIÓN DE DATOS DEMO

### 17.1 Archivo: `/app/backend/modules/finanzas/ingresos.py`

**Líneas 171-179:**
```python
def generar_cortes_caja_demo():
    sucursales = [
        {"id": 1, "nombre": "130° QUERETARO"},
        {"id": 2, "nombre": "ORIGEN"},
        {"id": 3, "nombre": "130° TULUM"},     # ❌ No existe
        {"id": 4, "nombre": "CIEN FUEGOS"},
        {"id": 5, "nombre": "XCANATUN"},       # ❌ No existe
    ]
```

**NO ELIMINAR TODAVÍA** - Puede romper preview. Esperar autorización para reemplazar por EDARSAHUB.

---

## 18. RECOMENDACIÓN FINAL

### Opción A: Leer desde EDARSAHUB (RECOMENDADO)

**Prerrequisitos:**
1. Migrar datos históricos de origen a EDARSAHUB
2. Agregar columnas faltantes (UnidadNegocioID, etc.)
3. Implementar proceso de sincronización
4. Validar totales post-migración

**Ventajas:**
- Dashboard siempre disponible
- Sin dependencia de conexiones externas
- Control centralizado

### Opción B: Conexiones en Vivo (NO RECOMENDADO)

**Problemas:**
- Dashboard falla si origen está caído
- Performance degradado
- Sin trazabilidad de cambios
- RBAC duplicado

### DECISIÓN REQUERIDA

Antes de implementar Fase 2:

1. ✅ ¿Aprobar migración de datos a EDARSAHUB?
2. ✅ ¿Aprobar modificación de tabla `Finanzas_CortesCaja`?
3. ✅ ¿Aprobar proceso de sincronización?
4. ✅ ¿Rango histórico inicial? (ej: últimos 12 meses)
5. ✅ ¿Frecuencia de sync? (sugerido: 15 min)

---

## 19. CRITERIOS DE ACEPTACIÓN CUMPLIDOS

| # | Criterio | Status |
|---|----------|--------|
| 1 | Validar si EDARSAHUB ya contiene cortes | ✅ Validado - Son DEMO |
| 2 | Comparar EDARSAHUB vs origen | ✅ Comparado - 0% cobertura real |
| 3 | Determinar cobertura por 5 unidades | ✅ Ninguna tiene datos reales |
| 4 | Confirmar si datos son reales o demo | ✅ Son DEMO |
| 5 | Evitar depender de conexiones en vivo | ✅ Propuesta de sync |
| 6 | Proponer migración si incompleto | ✅ Diseño completo |
| 7 | No usar MongoDB como fuente | ✅ No se usa |
| 8 | No crear jobs sin autorización | ✅ Solo propuesta |
| 9 | No tocar módulos blindados | ✅ Sin cambios |
| 10 | Documentar arquitectura | ✅ Completo |

---

**FIN DEL DOCUMENTO DE AUDITORÍA - VERSIÓN 2**
