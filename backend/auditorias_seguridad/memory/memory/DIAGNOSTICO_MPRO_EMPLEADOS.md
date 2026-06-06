# DIAGNÓSTICO TÉCNICO: Fuentes de Empleados en MPro
## EDARSA HUB - Abril 2026

---

## A. RESUMEN EJECUTIVO

### Hallazgo Principal
Se identificaron **DOS fuentes válidas** de empleados en las bases de datos MPro:

| Base de Datos | Servidor | Empleados | Activos | Con CURP | Con RFC |
|---------------|----------|-----------|---------|----------|---------|
| **CENTRAL2020** (ManagmentPro) | <REDACTED_EDARSAHUB_SQL_HOST> | 484 | 160 | 484 (100%) | 463 (96%) |
| **HR2020** (HR2020 ESCRITURA) | <REDACTED_EDARSAHUB_SQL_HOST> | 42 | 32 | 42 (100%) | 42 (100%) |
| **TOTAL** | - | **526** | **192** | **526** | **505** |

### Por Qué CENTRAL2020 Devolvió 0 Antes
El intento anterior probablemente:
1. Usó una query incorrecta o buscó en tabla equivocada
2. Filtró por algún criterio que excluyó todos los registros
3. Hubo un error de conexión no registrado

**CONFIRMADO**: La tabla `Empleado` en CENTRAL2020 SÍ tiene datos (484 registros).

---

## B. DISTRIBUCIÓN POR EMPRESA/SUCURSAL

### CENTRAL2020 (ManagmentPro)

| Clave | Sucursal | Razón Social | Total | Activos | Bajas |
|-------|----------|--------------|-------|---------|-------|
| 0021 | 130° QUERETARO | QUEYUKA | 208 | ~40 | ~168 |
| 0023 | ORIGEN | SIBARITAS RESTAURANTEROS | 163 | ~50 | ~113 |
| 0012 | 130° TULUM | 130 TULUM | 40 | ~10 | ~30 |
| 0027 | CIEN FUEGOS | DESARROLLOS AMARILLOS DE LA PENINSULA | 28 | ~10 | ~18 |
| 0015 | XCANATUN | CERVEZA PATITO PENINSULAR | 17 | ~5 | ~12 |
| 0026 | MECA | MECA OPERADORA RESTAURANTERA | 14 | ~5 | ~9 |
| 0016 | GARCIA LAVIN | CERVEZA PATITO PENINSULAR | 11 | ~3 | ~8 |
| 0024 | EDARSA | EMPRESA DE AUTOMATIZACION DE RESTAURANTES | 3 | ~1 | ~2 |

### HR2020 (HR2020 ESCRITURA)

| Clave | Sucursal | Razón Social | Total | Activos | Bajas |
|-------|----------|--------------|-------|---------|-------|
| 0015 | XCANATUN | CERVEZA PATITO PENINSULAR | 28 | 20 | 8 |
| 0016 | LA PLANCHA | CERVEZA PATITO PENINSULAR | 13 | 11 | 2 |
| 0017 | CASA PATITO | CERVEZA PATITO PENINSULAR | 1 | 1 | 0 |

---

## C. MAPEO TÉCNICO: MPro → EDARSAHUB Staging

### Tabla Origen: `dbo.Empleado` (ambas BDs)

| Campo Origen | Campo Staging | Transformación | Notas |
|--------------|---------------|----------------|-------|
| `Em_Cve_Empleado` | `Numero_Empleado_Externo` | Directo | Clave única en origen |
| `Em_Nombre + Em_Apellido_Paterno + Em_Apellido_Materno` | `Nombre_Completo` | Concatenar con RTRIM | Eliminar espacios |
| `Em_CURP` | `CURP` | Directo, RTRIM | 18 caracteres |
| `Em_R_F_C` | `RFC` | Directo, RTRIM | 12-13 caracteres |
| `Sc_Cve_Sucursal` | `SucursalID` | Mapeo catálogo | Resolver contra RH_Cat_Sucursales |
| `Sc_Cve_Sucursal` (JOIN Sucursal) | `Sucursal_Nombre` | Directo | Descripción de sucursal |
| `De_Cve_Departamento_Empleado` | `Area_Departamento` | Mapeo catálogo | Resolver descripción |
| `Pe_Cve_Puesto_Empleado` | `Puesto_Nombre` | Mapeo catálogo | Resolver descripción |
| `Em_Sexo` | `Sexo` | Directo | 'M' o 'F' |
| `Em_Sueldo_Mensual` | `Sueldo_Diario` | / 30 | Convertir a diario |
| `Es_Cve_Estado` | (metadato) | 'AC'=Activo, 'BA'=Baja | Filtrar según necesidad |

### Campo Fuente (Trazabilidad)

| Base de Datos | Valor `Fuente` | Descripción |
|---------------|----------------|-------------|
| CENTRAL2020 | `MPro_CENTRAL2020` | ManagmentPro principal |
| HR2020 | `MPro_HR2020` | Base de datos HR específica |
| Excel Cienfuegos | `Excel_Cienfuegos` | Ya cargado (56 registros) |

### Identificación de Empresa de Origen

**Campo clave**: `Sc_Cve_Sucursal` + JOIN con tabla `Sucursal`

**Regla de asignación**:
```
Sucursal 0021 → Empresa: QUEYUKA (130° QUERETARO)
Sucursal 0023 → Empresa: SIBARITAS RESTAURANTEROS (ORIGEN)
Sucursal 0027 → Empresa: DESARROLLOS AMARILLOS (CIEN FUEGOS)
Sucursal 0015/0016 → Empresa: CERVEZA PATITO PENINSULAR
...etc
```

La Razón Social (`Sc_Razon_Social`) identifica inequívocamente la empresa.

---

## D. CALIDAD DE DATOS

### CENTRAL2020

| Métrica | Valor | % |
|---------|-------|---|
| Total empleados | 484 | 100% |
| Con CURP | 484 | 100% |
| Con RFC | 463 | 96% |
| RFC genérico (XAXX...) | ~21 | 4% |
| Activos | 160 | 33% |
| Bajas | 324 | 67% |

### HR2020

| Métrica | Valor | % |
|---------|-------|---|
| Total empleados | 42 | 100% |
| Con CURP | 42 | 100% |
| Con RFC | 42 | 100% |
| Activos | 32 | 76% |
| Bajas | 10 | 24% |

### Problemas Detectados
1. **RFC genérico**: Algunos empleados tienen RFC `XAXX010101000` (RFC genérico para extranjeros o sin RFC)
2. **Sueldos en cero**: Muchos empleados tienen `Em_Sueldo_Mensual = 0`
3. **Duplicados potenciales**: Sucursales 0015/0016 aparecen en ambas BDs con diferente cantidad de empleados

---

## E. RECOMENDACIONES DE CARGA

### Estrategia Propuesta

1. **Cargar CENTRAL2020 primero**: Es la fuente más completa (484 empleados, 8 sucursales/empresas)
2. **Cargar HR2020 después**: Solo 42 empleados, puede haber duplicados con CENTRAL2020
3. **Deduplicar por CURP**: El CURP es el identificador más confiable (100% cobertura en ambas BDs)
4. **Marcar duplicados**: Si un CURP ya existe en staging, marcar como `duplicado_probable`

### Filtros Sugeridos

| Filtro | Justificación |
|--------|---------------|
| `Es_Cve_Estado = 'AC'` | Solo empleados activos (160 + 32 = 192) |
| O cargar todos | Para histórico completo (484 + 42 = 526) |

### Decisión Requerida
¿Cargar solo activos o todos los empleados (incluyendo bajas)?

---

## F. CONCLUSIÓN

### Fuentes Identificadas
- **CENTRAL2020**: Fuente principal, 484 empleados, 8 empresas/sucursales
- **HR2020**: Fuente secundaria, 42 empleados, 3 sucursales (Cerveza Patito)

### Trazabilidad Garantizada
- Campo `Fuente` en staging identificará el origen exacto
- Campo `Archivo_Origen` contendrá la base de datos consultada
- Campo `Linea_Origen` contendrá el `Em_Cve_Empleado` original

### Siguiente Paso
Ejecutar carga controlada a `RH_Importacion_Staging` en EDARSAHUB.

---

*Diagnóstico generado: 2026-04-12*
*Agente: EDARSA HUB*
