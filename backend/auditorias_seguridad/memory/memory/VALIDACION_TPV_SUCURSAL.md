# Validación Funcional: Finanzas_ConfiguracionTPV_Sucursal

## Fecha: Abril 2026

## 1. Estado de la Tabla

### Tabla Creada: ✅
- **Nombre**: `Finanzas_ConfiguracionTPV_Sucursal`
- **Registros**: 8 (uno por sucursal activa)

### Estructura Confirmada:
```
ConfiguracionTPVID    int           NOT NULL (PK, IDENTITY)
SucursalID            int           NOT NULL
ProveedorTPV          varchar(50)   NOT NULL DEFAULT 'NetPay'
ComisionDebito        decimal(5,3)  NOT NULL DEFAULT 1.20
ComisionCredito       decimal(5,3)  NOT NULL DEFAULT 1.50
ComisionAmex          decimal(5,3)  NOT NULL DEFAULT 2.40
ComisionInternacional decimal(5,3)  NOT NULL DEFAULT 2.00
AplicaIVAComision     bit           NOT NULL DEFAULT 1
PorcentajeIVA         decimal(5,2)  NOT NULL DEFAULT 16.00
DiasDepositoDebito    int           NOT NULL DEFAULT 1
DiasDepositoCredito   int           NOT NULL DEFAULT 1
DiasDepositoAmex      int           NOT NULL DEFAULT 2
DiasDepositoInternacional int       NOT NULL DEFAULT 2
DiasDepositoEfectivo  int           NOT NULL DEFAULT 1
EfectivoFinDeSemanaLunes bit        NOT NULL DEFAULT 1
CuentaBancariaID      int           NULL
NumeroAfiliacion      varchar(50)   NULL
TerminalID            varchar(50)   NULL
Activo                bit           NOT NULL DEFAULT 1
FechaAlta             datetime2     NOT NULL DEFAULT GETDATE()
FechaModificacion     datetime2     NULL
```

## 2. Datos Iniciales Confirmados

| Sucursal | TPV | Débito | Crédito | AMEX | Intl | D.Déb | D.Cré | D.AMX | D.Intl |
|----------|-----|--------|---------|------|------|-------|-------|-------|--------|
| 1 - 130° QUERETARO | NetPay | 1.2% | 1.5% | 2.4% | 2.0% | 1 | 1 | 2 | 2 |
| 2 - 130° TULUM | NetPay | 1.2% | 1.5% | 2.4% | 2.0% | 1 | 1 | 2 | 2 |
| 3 - CIEN FUEGOS | NetPay | 1.2% | 1.5% | 2.4% | 2.0% | 1 | 1 | 2 | 2 |
| 4 - EDARSA | NetPay | 1.2% | 1.5% | 2.4% | 2.0% | 1 | 1 | 2 | 2 |
| 5 - GARCIA LAVIN | NetPay | 1.2% | 1.5% | 2.4% | 2.0% | 1 | 1 | 2 | 2 |
| 6 - MECA | NetPay | 1.2% | 1.5% | 2.4% | 2.0% | 1 | 1 | 2 | 2 |
| 7 - ORIGEN | NetPay | 1.2% | 1.5% | 2.4% | 2.0% | 1 | 1 | 2 | 2 |
| 8 - XCANATUN | NetPay | 1.2% | 1.5% | 2.4% | 2.0% | 1 | 1 | 2 | 2 |

## 3. Endpoints Validados

### GET /api/catalogos/tabla/Finanzas_ConfiguracionTPV_Sucursal
- **Estado**: ✅ Funcional (cuando la conexión SQL es estable)
- **Retorna**: Lista de configuraciones con estructura completa

### GET /api/catalogos/tabla/Finanzas_ConfiguracionTPV_Sucursal/{id}
- **Estado**: ✅ Implementado
- **Nota**: El ID es `ConfiguracionTPVID`, no `SucursalID`

### PUT /api/catalogos/tabla/Finanzas_ConfiguracionTPV_Sucursal/{id}
- **Estado**: ✅ Implementado
- **Campos editables**: Todos excepto ConfiguracionTPVID, FechaAlta

## 4. Validación de UI

### Módulo de Catálogos
- **Menú Catálogos**: ✅ Accesible desde sidebar
- **Dominio Finanzas**: ✅ Visible con 6 catálogos
- **Catálogo "Config. TPV por Sucursal"**: ✅ Listado en dominio Finanzas

### Campos visibles en UI (primeros 6):
1. ConfiguracionTPVID
2. SucursalID
3. ProveedorTPV
4. ComisionDebito
5. ComisionCredito
6. ComisionAmex

### Acciones disponibles:
- ✅ Ver registros
- ✅ Editar (botón de edición)
- ✅ Activar/Desactivar
- ✅ Buscar
- ✅ Filtrar solo activos
- ✅ Crear nuevo

## 5. Problemas Detectados

### Problema de Conexión SQL Server
- **Descripción**: El servidor SQL Server remoto (<REDACTED_EDARSAHUB_SQL_HOST>) presenta timeouts intermitentes
- **Error**: "Adaptive Server connection timed out" / "DBPROCESS is dead or not enabled"
- **Impacto**: La conexión es inestable, causando que algunos queries no retornen datos
- **Mitigación**: La lógica de reintentos está implementada, pero el servidor remoto necesita estabilización

### Recomendación
- Verificar la estabilidad de la conexión de red con el servidor SQL remoto
- Considerar aumentar timeouts si el problema persiste
- Los endpoints funcionan correctamente cuando la conexión es estable

## 6. Validación de Edición (Pendiente por Conexión)

La funcionalidad de edición está implementada pero no pudo ser completamente validada debido a los problemas de conexión con SQL Server.

### Código de Edición Implementado:
```python
# En repository.py
async def actualizar_registro_catalogo(db, tabla, id_valor, datos, usuario):
    # Construye UPDATE dinámico con los campos editables
    # Agrega FechaModificacion = GETDATE()
    # Ejecuta el UPDATE
```

### Prueba Pendiente:
- Editar comisiones de una sucursal específica
- Verificar persistencia recargando datos
- Confirmar que FechaModificacion se actualiza

## 7. Conclusión

### Estado General: PARCIALMENTE VALIDADO

| Aspecto | Estado |
|---------|--------|
| Tabla creada | ✅ |
| Estructura correcta | ✅ |
| Datos semilla | ✅ |
| Endpoint GET lista | ✅ |
| Endpoint GET individual | ✅ |
| Endpoint PUT edición | ✅ (implementado, pendiente prueba) |
| UI Catálogos | ✅ |
| Conexión SQL estable | ⚠️ Problemas intermitentes |

### Siguiente Paso
Una vez estabilizada la conexión SQL, ejecutar prueba de edición completa:
1. Leer valores actuales de Sucursal 1
2. Modificar comisiones AMEX e Internacional
3. Guardar cambios
4. Verificar persistencia
5. Confirmar en UI
