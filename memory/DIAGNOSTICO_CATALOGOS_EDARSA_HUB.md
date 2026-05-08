# Diagnóstico de Catálogos - EDARSA HUB

## Resumen Ejecutivo

**Fecha:** Diciembre 2025
**Base de datos:** EDARSAHUB (SQL Server)
**Total tablas:** 164
**Tablas de catálogos identificadas:** 47

---

## 1. Inventario de Catálogos Existentes

### 1.1 Catálogos de RH (19 tablas)

| Tabla | Registros | Estado | Clasificación | Acción Recomendada |
|-------|-----------|--------|---------------|-------------------|
| RH_Cat_Sucursales | 8 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_Departamentos | 11 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_Puestos | 37 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_TiposContrato | 3 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_MotivosBaja | 3 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_TiposAusencia | 5 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_ConceptosNomina | 10 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_TiposConceptoNomina | 4 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_TiposPeriodoNomina | 4 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_EstatusPeriodoNomina | 6 | 🟢 CON DATOS | **REUTILIZABLE** | Usar directamente |
| RH_Cat_Areas | 0 | ⚪ VACÍA | **AMPLIABLE** | Habilitar si se requiere |
| RH_Cat_Beneficios | 0 | ⚪ VACÍA | **AMPLIABLE** | Habilitar si se requiere |
| RH_Cat_Jornadas | 0 | ⚪ VACÍA | **AMPLIABLE** | Poblar con datos |
| RH_Cat_RegimenContratacion | 0 | ⚪ VACÍA | **AMPLIABLE** | Poblar con datos |
| RH_Cat_SucursalesFiscal | 0 | ⚪ VACÍA | **AMPLIABLE** | Requiere datos fiscales |
| RH_Cat_Turnos | 0 | ⚪ VACÍA | **AMPLIABLE** | Habilitar si se requiere |

### 1.2 Catálogos de Compras (7 tablas)

| Tabla | Registros | Estado | Clasificación |
|-------|-----------|--------|---------------|
| Compras_Estatus | 8 | 🟢 CON DATOS | **REUTILIZABLE** |
| Compras_OrdenesEstatus | 8 | 🟢 CON DATOS | **REUTILIZABLE** |
| Compras_PedidosEstatus | 8 | 🟢 CON DATOS | **REUTILIZABLE** |
| Compras_RecepcionesEstatus | 6 | 🟢 CON DATOS | **REUTILIZABLE** |
| Compras_DocumentosFiscalesEstatus | 7 | 🟢 CON DATOS | **REUTILIZABLE** |
| Compras_ConciliacionSATEstatus | 11 | 🟢 CON DATOS | **REUTILIZABLE** |

### 1.3 Catálogos de Proveedor (6 tablas)

| Tabla | Registros | Estado | Clasificación |
|-------|-----------|--------|---------------|
| Proveedor_TipoProveedor | 7 | 🟢 CON DATOS | **REUTILIZABLE** |
| Proveedor_TipoContacto | 5 | 🟢 CON DATOS | **REUTILIZABLE** |
| Proveedor_TipoDocumento | 8 | 🟢 CON DATOS | **REUTILIZABLE** |
| Proveedor_EstatusProveedor | 4 | 🟢 CON DATOS | **REUTILIZABLE** |
| Proveedor_EstatusSAT | 4 | 🟢 CON DATOS | **REUTILIZABLE** |
| Proveedor_EstatusSincronizacion | 3 | 🟢 CON DATOS | **REUTILIZABLE** |
| Proveedor_Catalogo | 0 | ⚪ VACÍA | **AMPLIABLE** |
| Proveedor_Categorias | 0 | ⚪ VACÍA | **AMPLIABLE** |

### 1.4 Catálogos de Inventario (1 tabla)

| Tabla | Registros | Estado | Clasificación |
|-------|-----------|--------|---------------|
| Inventario_TipoMovimiento | 6 | 🟢 CON DATOS | **REUTILIZABLE** |

### 1.5 Catálogos de Venta (3 tablas)

| Tabla | Registros | Estado | Clasificación |
|-------|-----------|--------|---------------|
| Venta_Estatus | 6 | 🟢 CON DATOS | **REUTILIZABLE** |
| Venta_PedidosEstatus | 6 | 🟢 CON DATOS | **REUTILIZABLE** |
| Venta_CotizacionesEstatus | 6 | 🟢 CON DATOS | **REUTILIZABLE** |

### 1.6 Catálogos de Activo Fijo (7 tablas)

| Tabla | Registros | Estado | Clasificación |
|-------|-----------|--------|---------------|
| ActivoFijo_TipoActivo | 9 | 🟢 CON DATOS | **REUTILIZABLE** |
| ActivoFijo_TipoBaja | 7 | 🟢 CON DATOS | **REUTILIZABLE** |
| ActivoFijo_TipoMedidor | 3 | 🟢 CON DATOS | **REUTILIZABLE** |
| ActivoFijo_TipoOT | 3 | 🟢 CON DATOS | **REUTILIZABLE** |
| ActivoFijo_TipoUbicacion | 9 | 🟢 CON DATOS | **REUTILIZABLE** |
| ActivoFijo_EstatusActivo | 6 | 🟢 CON DATOS | **REUTILIZABLE** |
| ActivoFijo_EstatusOT | 5 | 🟢 CON DATOS | **REUTILIZABLE** |

### 1.7 Catálogos de Usuario/Seguridad (2 tablas)

| Tabla | Registros | Estado | Clasificación |
|-------|-----------|--------|---------------|
| Usuario_Roles | 5 | 🟢 CON DATOS | **REUTILIZABLE** |
| Usuario_TiposAutorizacion | 7 | 🟢 CON DATOS | **REUTILIZABLE** |
| Usuario_Modulos | 8 | 🟢 CON DATOS | **REUTILIZABLE** |
| Usuario_Catalogo | 0 | ⚪ VACÍA | **AMPLIABLE** |

---

## 2. Estructura Base Detectada

### Patrones de Columnas Estándar Encontrados

Los catálogos existentes siguen estos patrones:

**Patrón A - Catálogos simples (3 columnas):**
```
- [Entidad]ID (int/smallint, PK)
- Descripcion (varchar)
- Activo (bit)
```

**Patrón B - Catálogos con código (5+ columnas):**
```
- [Entidad]ID (int, PK, IDENTITY)
- Codigo[Entidad] (varchar, UNIQUE)
- Nombre/Descripcion (varchar)
- Activo (bit)
- FechaAlta (datetime2)
- FechaModificacion (datetime2, NULL)
```

**Patrón C - Catálogos completos (7+ columnas):**
```
- [Entidad]ID (int, PK, IDENTITY)
- Codigo[Entidad] (varchar, UNIQUE)
- Nombre[Entidad] (varchar)
- Descripcion (varchar, NULL)
- [Campos específicos del dominio...]
- Activo (bit)
- FechaAlta (datetime2)
- FechaModificacion (datetime2, NULL)
```

---

## 3. Datos Existentes (Muestra)

### RH_Cat_Sucursales
| ID | Nombre | Ciudad | Activa |
|----|--------|--------|--------|
| 1 | 130° QUERETARO | México | ✓ |
| 2 | 130° TULUM | México | ✓ |
| 3 | CIEN FUEGOS | México | ✓ |
| 4 | EDARSA | México | ✓ |
| 5 | GARCIA LAVIN | México | ✓ |
| 6 | MECA | México | ✓ |
| 7 | ORIGEN | México | ✓ |
| 8 | XCANATUN | México | ✓ |

### RH_Cat_Departamentos
| ID | Código | Nombre |
|----|--------|--------|
| 1 | ADMINISTRACION | ADMINISTRACION |
| 2 | AUDITORIA | AUDITORIA |
| 3 | CAJAS | CAJAS |
| 4 | CAPITAL HUMANO | CAPITAL HUMANO |
| 5 | COCINA | COCINA |
| 6 | CONTABILIDAD | CONTABILIDAD |
| 7 | MARKETING | MARKETING |
| 8 | OPERACIONES | OPERACIONES |
| 9 | PISO | PISO |
| 10 | TECNOLOGIAS DE LA INFORMACION | TECNOLOGIAS... |
| 11 | TESORERIA | TESORERIA |

### Usuario_Roles
| ID | Código | Nombre | Sistema |
|----|--------|--------|---------|
| 1 | ADMIN | Administrador | ✓ |
| 2 | GERENCIA | Gerencia | ✓ |
| 3 | COMPRAS | Compras | ✓ |
| 4 | VENTAS | Ventas | ✓ |
| 5 | TESORERIA | Tesoreria | ✓ |

---

## 4. Catálogos Faltantes (Para Crear)

### 4.1 Catálogos Globales
| Catálogo | Existe | Acción |
|----------|--------|--------|
| Empresas | ❌ NO | CREAR: `Global_Cat_Empresas` |
| Bancos | ❌ NO | CREAR: `Global_Cat_Bancos` |
| Monedas | 🟡 PARCIAL | `Proveedor_Monedas` existe (3 regs) - REUSAR |
| Formas de pago SAT | ❌ NO | CREAR: `Global_Cat_FormaPagoSAT` |
| Métodos de pago SAT | ❌ NO | CREAR: `Global_Cat_MetodoPagoSAT` |
| Usos CFDI | ❌ NO | CREAR: `Global_Cat_UsoCFDI` |
| Regímenes fiscales | ❌ NO | CREAR: `Global_Cat_RegimenFiscal` |
| Unidades de medida | ❌ NO | CREAR: `Global_Cat_UnidadesMedida` |
| Centros de costo | ❌ NO | CREAR: `Global_Cat_CentrosCosto` |

### 4.2 Catálogos de Finanzas
| Catálogo | Existe | Acción |
|----------|--------|--------|
| Cuentas bancarias | ❌ NO | CREAR |
| Tipos de póliza | ❌ NO | CREAR |
| Conceptos contables | ❌ NO | CREAR |

### 4.3 Tabla de Homologación
| Tabla | Registros | Acción |
|-------|-----------|--------|
| RH_Homologacion_Equivalencias | 56 | **REUTILIZABLE** - Ya existe |

---

## 5. Clasificación Final para Módulo de Catálogos

### REUTILIZABLES (34 catálogos con datos)
Estos catálogos se integran directamente al módulo sin modificaciones:
- Todo el grupo RH_Cat_* con datos
- Todo el grupo Compras_*Estatus
- Todo el grupo Proveedor_Tipo*, Proveedor_Estatus*
- Inventario_TipoMovimiento
- Todo el grupo Venta_*Estatus
- Todo el grupo ActivoFijo_Tipo*, ActivoFijo_Estatus*
- Usuario_Roles, Usuario_TiposAutorizacion, Usuario_Modulos

### AMPLIABLES (13 catálogos vacíos pero con estructura)
Estos catálogos existen pero están vacíos, se habilitan gradualmente:
- RH_Cat_Areas, RH_Cat_Beneficios, RH_Cat_Jornadas
- RH_Cat_RegimenContratacion, RH_Cat_SucursalesFiscal, RH_Cat_Turnos
- Proveedor_Catalogo, Proveedor_Categorias
- Cliente_Catalogo, Producto_Catalogo
- Usuario_Catalogo

### A CREAR (9 catálogos nuevos)
Tablas que NO existen y son necesarias:
- Global_Cat_Empresas
- Global_Cat_Bancos
- Global_Cat_FormaPagoSAT
- Global_Cat_MetodoPagoSAT
- Global_Cat_UsoCFDI
- Global_Cat_RegimenFiscal
- Global_Cat_UnidadesMedida
- Global_Cat_CentrosCosto
- Finanzas_Cat_CuentasBancarias

---

## 6. Recomendaciones de Implementación

### Fase 1: Integración de Catálogos Existentes
1. ✅ Crear módulo `/backend/modules/catalogos/`
2. ✅ Crear endpoints genéricos para CRUD
3. ✅ Integrar catálogos RH existentes
4. ✅ Integrar catálogos Compras/Proveedor existentes

### Fase 2: Catálogos Globales Nuevos
1. Crear tablas Global_Cat_*
2. Poblar con datos del SAT (Formas de pago, Usos CFDI, etc.)
3. Integrar al módulo

### Fase 3: Accesos Contextuales
1. Agregar accesos desde módulo RH → Catálogos RH
2. Agregar accesos desde módulo Compras → Catálogos Compras
3. Agregar accesos desde módulo Finanzas → Catálogos Finanzas

---

## 7. Confirmación Requerida

**ANTES DE PROCEDER, confirme:**

1. ¿Los catálogos existentes con datos (RH_Cat_*, Compras_*, etc.) pueden modificarse desde el nuevo módulo?
   - Opción A: Solo lectura (protección total)
   - Opción B: CRUD completo (recomendado)

2. ¿Crear los catálogos globales nuevos (Global_Cat_Empresas, Global_Cat_Bancos, etc.)?
   - Estos NO existen actualmente en la BD

3. ¿La tabla Usuario_Modulos se puede actualizar para agregar el módulo "Catálogos" al menú de la BD?

---

**Documento generado automáticamente - Diciembre 2025**
