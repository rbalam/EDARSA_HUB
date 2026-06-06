# ARQ - Catálogo Maestro de Sistemas y Capacidades
## FASE 1: Diagnóstico - Matriz de Auditoría

**Fecha:** 2025-12-XX
**Autor:** Arquitecto Senior Backend/DBA
**Estado:** EN PROGRESO

---

## 1. RESUMEN EJECUTIVO

### 1.1 Problema Actual
Cada vez que se agrega un nuevo sistema (ej: SoftRestaurant Enterprise), se requieren modificaciones en múltiples puntos del código:
- Filtros frontend
- Explorador BD
- Listado de conexiones
- Carga de tablas
- Sync históricos
- Queries
- Normalizadores system_type

Esto genera:
- **Deuda técnica** acumulada
- **Bugs recurrentes** por hardcoding
- **Tiempo de desarrollo** elevado por cambio de sistema

### 1.2 Objetivo
Diseñar e implementar un **Catálogo Maestro de Sistemas + Motor de Capacidades** donde:
1. Un sistema nuevo se registra en EDARSAHUB SQL
2. Se le asignan capacidades
3. Aparece automáticamente en filtros/menús aplicables
4. No se modifica frontend por cada sistema
5. No se modifica backend por cada sistema (salvo adapter tecnológico nuevo)

---

## 2. ESTADO ACTUAL DE TABLAS EN EDARSAHUB

### 2.1 Tablas EXISTENTES (No duplicar)

| Tabla | Propósito | Ubicación |
|-------|-----------|-----------|
| `Sistema_Tipos` | Catálogo de tipos de sistema (MPRO, SOFTRESTAURANT) | EDARSAHUB |
| `Sistema_Empresas` | Catálogo maestro de empresas | EDARSAHUB |
| `Sistema_EmpresasServidores` | Relación empresa ↔ servidor con roles | EDARSAHUB |
| `Sistema_EmpresasAlias` | Aliases de nombres de empresas | EDARSAHUB |
| `Servidores_Conexiones` | Conexiones SQL/API a servidores | EDARSAHUB |

### 2.2 Campos EXISTENTES en Sistema_Tipos

```sql
-- Confirmado en empresa_resolver.py:718-724
SELECT SistemaTipoID, CodigoSistema, NombreSistema, Descripcion, Activo
FROM Sistema_Tipos
```

### 2.3 Tablas a CREAR (No existen)

| Tabla | Propósito |
|-------|-----------|
| `Sistema_Capacidades` | Capacidades por tipo de sistema |
| `Sistema_ModulosVisibilidad` | Visibilidad en módulos/menús |
| `Sistema_Consultas` | Queries por sistema/capacidad (opcional si se reutiliza catálogo existente) |

---

## 3. MATRIZ DE AUDITORÍA - HARDCODING DETECTADO

### 3.1 BACKEND - system_type y normalizadores

| Archivo | Función/Línea | Uso Actual | Riesgo | Reemplazo Propuesto |
|---------|---------------|------------|--------|---------------------|
| `core/system_type_utils.py` | `SYSTEM_TYPE_MAP` (L55-77) | Mapeo hardcodeado de variantes | MEDIO | Cargar desde `Sistema_Tipos.VariantesJSON` o tabla auxiliar |
| `core/system_type_utils.py` | `is_mpro_system()` | Comparación directa | BAJO | Mantener como helper, pero usar resolver central |
| `core/system_type_utils.py` | `is_softrestaurant_system()` | Comparación directa | BAJO | Mantener como helper, pero usar resolver central |
| `modules/comercial/service.py` L1096-1098 | `if system_type.upper() in ['MPRO', 'MANAGEMENTPRO']` | Lista hardcodeada | MEDIO | `system_supports(codigo, 'VENTAS_DIA')` |
| `modules/comercial/service.py` L928-937 | `UNIDADES_EDARSAHUB_MAP` | Mapeo hardcodeado de servidores | ALTO | Resolver desde `Sistema_EmpresasServidores` |
| `modules/comercial/routes.py` L725-1092 | `is_softrestaurant_system() / is_mpro_system()` | Bifurcación por sistema | MEDIO | `get_query_for_capability(sistema, 'VENTAS_PERIODO')` |
| `catalogo/catalogo_consultas.py` | `CATALOGO_CONSULTAS` con `"sistema": "SoftRestaurant"` | Hardcodeado | ALTO | Mover a tabla `Sistema_Consultas` o `Catalogo_SQL` existente |
| `init_queries.py` L277-281 | `"system_type": "MPRO"` | Hardcodeado | BAJO | Usar código de `Sistema_Tipos` |

### 3.2 BACKEND - visible_en_operaciones y filtros

| Archivo | Función/Línea | Uso Actual | Riesgo | Reemplazo Propuesto |
|---------|---------------|------------|--------|---------------------|
| `modules/comercial/repository.py` L140-141 | `visible_en_operaciones` en respuesta | OK - campo SQL | BAJO | Mantener |
| `modules/comercial/repository.py` L194 | `WHERE visible_en_operaciones = 1` | OK - filtro SQL | BAJO | Mantener |
| `server.py` L612-750 | Schemas con `visible_en_operaciones` | OK - estructura | BAJO | Mantener |
| `server.py` L9526-9621 | `listar_conexiones_explorables()` | Derivado `explorable` | MEDIO | Usar `Sistema_Capacidades` para determinar explorabilidad |

### 3.3 BACKEND - Sync Históricos

| Archivo | Función/Línea | Uso Actual | Riesgo | Reemplazo Propuesto |
|---------|---------------|------------|--------|---------------------|
| `modules/sync_historicos/service.py` | Consulta servidores candidatos | Usa `Servidores_Conexiones` + `query_ventas IS NOT NULL` | OK | Agregar capacidad `SYNC_VENTAS_HISTORICAS` |
| `modules/comercial/queries/mpro.py` | `query_ventas_periodo_mpro()` | Específico MPRO | OK | Registrar como capacidad `VENTAS_PERIODO` |
| `modules/comercial/queries/softrestaurant.py` | `query_ventas_periodo_sr()` | Específico SR | OK | Registrar como capacidad `VENTAS_PERIODO` |

### 3.4 FRONTEND - Hardcoding de sistemas

| Archivo | Línea | Uso Actual | Riesgo | Reemplazo Propuesto |
|---------|-------|------------|--------|---------------------|
| `pages/Servidores.js` L187-188 | `['MPRO', 'SOFTRESTAURANT']` en dropdown | ALTO | Consumir `GET /api/catalogos/sistemas/activos` |
| `pages/Servidores.js` L119, 283, 295, 472, 980, 1446 | `tipo: 'MPRO'` hardcodeado | ALTO | Usar valor dinámico del catálogo |
| `pages/Servidores.js` L1414 | `system_type === 'MPRO'` para mostrar botón | MEDIO | `system_supports(codigo, 'SUCURSALES_VISIBLES')` |
| `pages/Reportes.js` L37, 527, 531, 583, etc. | `system_type === 'SoftRestaurant'` / `'MPRO'` | ALTO | Consumir capacidades del sistema |
| `pages/Reportes.js` L1065-1070 | `calculateDates()` con lógica por sistema | MEDIO | Mover lógica a backend con capacidad `FECHA_AJUSTE_INVENTARIO` |
| `pages/Finanzas.js` L62, 177, 351 | Referencias a `MPRO` para CxP | MEDIO | Usar capacidad `CUENTAS_POR_PAGAR` |
| `pages/Compras.js` L3437-3454 | Lógica `MPRO` vs `SoftRestaurant` | ALTO | Capacidades por sistema |
| `pages/CatalogoConsultas.js` L70-71 | Comparación `=== 'MPRO'` | MEDIO | Normalizar con helper o resolver |
| `pages/ExploradorBD.js` L816 | `system_type: c.sistema_codigo` | OK | Ya usa campo dinámico |
| `services/exploradorService.js` | `fetchSistemasDisponibles()` | OK | Ya consume endpoint dinámico |

### 3.5 RESUMEN POR MÓDULO

| Módulo | Archivos Afectados | Hardcoding Crítico | Prioridad |
|--------|--------------------|--------------------|-----------|
| **Comercial** | service.py, routes.py, repository.py | UNIDADES_EDARSAHUB_MAP, bifurcaciones if/else | P1 |
| **Servidores** | Servidores.js | Lista de sistemas en dropdown | P1 |
| **Reportes** | Reportes.js | Lógica de fechas y almacenes por sistema | P1 |
| **Explorador BD** | ExploradorBD.js, server.py | Ya parcialmente dinámico | P2 |
| **Sync Históricos** | service.py, sync_ventas.py | Capacidades de sync | P2 |
| **Catálogo Consultas** | catalogo_consultas.py | Queries hardcodeadas por sistema | P2 |
| **Finanzas** | Finanzas.js, tesoreria.py | Filtros CxP MPRO | P3 |
| **Compras** | Compras.js | Bifurcación por sistema | P3 |

---

## 4. DIAGNÓSTICO DE system_type_utils.py

### 4.1 Estructura Actual
El archivo `core/system_type_utils.py` ya implementa:
- ✅ Enum `SystemType` con valores normalizados
- ✅ Mapeo `SYSTEM_TYPE_MAP` de variantes
- ✅ Helpers `is_mpro_system()`, `is_softrestaurant_system()`
- ✅ Labels para UI
- ✅ Cache key builder

### 4.2 Limitaciones
- ❌ Mapeo hardcodeado en código Python
- ❌ No consulta EDARSAHUB para nuevos sistemas
- ❌ No soporta capacidades (solo normalización)

### 4.3 Propuesta de Evolución
1. Mantener helpers existentes para compatibilidad
2. Agregar `SystemCapabilityResolver` que consulte SQL
3. Migrar gradualmente el mapeo estático a dinámico

---

## 5. PROPUESTA ARQUITECTÓNICA (FASES 2-7)

### FASE 2 - DDL SQL-FIRST

```sql
-- Sistema_Capacidades (NUEVA)
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_Capacidades')
CREATE TABLE Sistema_Capacidades (
    SistemaCapacidadID INT IDENTITY(1,1) PRIMARY KEY,
    SistemaTipoID INT NOT NULL FOREIGN KEY REFERENCES Sistema_Tipos(SistemaTipoID),
    CodigoCapacidad VARCHAR(50) NOT NULL,  -- EXPLORADOR_BD, SYNC_VENTAS_HISTORICAS, etc.
    Descripcion NVARCHAR(200),
    RequiereApiLocal BIT DEFAULT 0,
    RequiereSqlDirecto BIT DEFAULT 1,
    ConfiguracionJSON NVARCHAR(MAX),  -- Configuración específica
    Activo BIT DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_Sistema_Capacidad UNIQUE (SistemaTipoID, CodigoCapacidad)
);

-- Sistema_ModulosVisibilidad (NUEVA)
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_ModulosVisibilidad')
CREATE TABLE Sistema_ModulosVisibilidad (
    ModuloVisibilidadID INT IDENTITY(1,1) PRIMARY KEY,
    SistemaTipoID INT NOT NULL FOREIGN KEY REFERENCES Sistema_Tipos(SistemaTipoID),
    CodigoModulo VARCHAR(50) NOT NULL,  -- EXPLORADOR_BD, COMERCIAL, FINANZAS, COMPRAS, etc.
    Visible BIT DEFAULT 1,
    OrdenMenu INT DEFAULT 0,
    ConfiguracionJSON NVARCHAR(MAX),
    Activo BIT DEFAULT 1,
    CreatedAt DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_Sistema_Modulo UNIQUE (SistemaTipoID, CodigoModulo)
);
```

### FASE 3 - SEED INICIAL

```sql
-- Capacidades para SOFTRESTAURANT
INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto)
SELECT st.SistemaTipoID, 'EXPLORADOR_BD', 'Explorador de Base de Datos', 1
FROM Sistema_Tipos st WHERE st.CodigoSistema = 'SOFTRESTAURANT';

INSERT INTO Sistema_Capacidades (SistemaTipoID, CodigoCapacidad, Descripcion, RequiereSqlDirecto)
SELECT st.SistemaTipoID, 'SYNC_VENTAS_HISTORICAS', 'Sync de ventas históricas', 1
FROM Sistema_Tipos st WHERE st.CodigoSistema = 'SOFTRESTAURANT';

-- (Continuar para MPRO, SOFTRESTAURANT_ENTERPRISE, etc.)
```

### FASE 4 - RESOLVER CENTRAL

```python
# /app/backend/core/system_capability_resolver.py

class SystemCapabilityResolver:
    """
    Resolver central para capacidades de sistemas.
    FUENTE: EDARSAHUB SQL
    """
    
    def system_supports(self, codigo_sistema: str, capacidad: str) -> bool:
        """Verifica si un sistema soporta una capacidad"""
        pass
    
    def get_systems_for_capability(self, capacidad: str) -> List[str]:
        """Obtiene sistemas que soportan una capacidad"""
        pass
    
    def get_query_for_capability(self, codigo_sistema: str, capacidad: str) -> Optional[str]:
        """Obtiene la query SQL para una capacidad específica"""
        pass
    
    def get_visible_systems_for_module(self, modulo: str) -> List[Dict]:
        """Obtiene sistemas visibles para un módulo"""
        pass
```

### FASE 5 - ENDPOINTS

```
GET /api/catalogos/sistemas
GET /api/catalogos/sistemas/capacidades
GET /api/catalogos/sistemas/por-capacidad/{capacidad}
GET /api/catalogos/servidores/por-capacidad/{capacidad}
```

### FASE 6 - INTEGRACIÓN NO DESTRUCTIVA

1. Explorador BD (ya parcialmente dinámico)
2. Filtros de sistema/conexión
3. Sync_Historicos candidatos
4. Catálogo SQL

### FASE 7 - FRONTEND

1. Cambiar filtros para consumir endpoints dinámicos
2. Eliminar listas hardcodeadas SOLO después de validar

---

## 6. CAPACIDADES PROPUESTAS

| Código | Descripción | Sistemas Iniciales |
|--------|-------------|-------------------|
| `EXPLORADOR_BD` | Explorar tablas y columnas | SR, MPRO, SR_ENTERPRISE |
| `EXPLORADOR_TABLAS` | Listar tablas | SR, MPRO, SR_ENTERPRISE |
| `EXPLORADOR_COLUMNAS` | Listar columnas | SR, MPRO, SR_ENTERPRISE |
| `EXPLORADOR_PREVIEW` | Preview de datos | SR, MPRO, SR_ENTERPRISE |
| `SYNC_VENTAS_HISTORICAS` | Sync de ventas históricas | SR, MPRO |
| `SYNC_VENTAS_POR_HORA` | Sync por hora | SR, MPRO |
| `SYNC_VENTAS_DIA_SEMANA` | Sync por día de semana | SR, MPRO |
| `VENTAS_DIA` | KPIs de ventas del día | SR, MPRO |
| `VENTAS_PERIODO` | KPIs de ventas por período | SR, MPRO |
| `COMPRAS` | Módulo de compras | SR, MPRO |
| `INVENTARIOS` | Módulo de inventarios | SR, MPRO |
| `CORTES_Z` | Cortes de caja | SR, MPRO |
| `CATALOGO_SQL` | Catálogo de consultas | SR, MPRO |
| `SUCURSALES_VISIBLES` | Configuración de sucursales | MPRO |
| `PROPINAS_TPV` | Propinas por TPV | SR, MPRO |
| `CUENTAS_POR_PAGAR` | CxP en Finanzas | MPRO |

---

## 7. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Romper Explorador BD | Media | Alto | Mantener lógica legacy hasta validar resolver |
| Romper Sync Históricos | Baja | Alto | Capacidad opcional, no bloquear sync existente |
| Romper filtros Comercial | Media | Alto | Feature flag para resolver vs legacy |
| Romper filtros Frontend | Media | Medio | Endpoint dinámico + fallback a lista legacy |

---

## 8. PRÓXIMOS PASOS

### Requiere Autorización:
1. [ ] FASE 2: Crear tablas DDL `Sistema_Capacidades` y `Sistema_ModulosVisibilidad`
2. [ ] FASE 3: Ejecutar SEED inicial de capacidades
3. [ ] FASE 4: Implementar `SystemCapabilityResolver`
4. [ ] FASE 5: Crear endpoints de catálogo
5. [ ] FASE 6: Integrar en módulos existentes (no destructivo)
6. [ ] FASE 7: Migrar frontend a endpoints dinámicos

---

## 9. ARCHIVOS DE REFERENCIA CLAVE

- `/app/backend/core/system_type_utils.py` - Normalización actual
- `/app/backend/core/empresa_resolver.py` - Resolver de empresas (usa Sistema_Tipos)
- `/app/backend/modules/comercial/service.py` - Lógica comercial con bifurcaciones
- `/app/backend/modules/comercial/routes.py` - Endpoints con bifurcaciones
- `/app/backend/catalogo/catalogo_consultas.py` - Queries hardcodeadas
- `/app/frontend/src/pages/Servidores.js` - Dropdown de sistemas
- `/app/frontend/src/pages/Reportes.js` - Lógica por sistema
- `/app/frontend/src/services/exploradorService.js` - Ya dinámico

---

**ESTADO:** Diagnóstico completado. Esperando autorización para FASE 2.
