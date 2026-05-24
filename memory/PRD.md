# EDARSA HUB - Product Requirements Document

## Problema Original
Sistema ERP integrado para EDARSA con CRM Comercial Enterprise, conectado a múltiples fuentes de datos SQL Server (MPRO, SoftRestaurant, EDARSAHUB).

## Máximas del Proyecto
1. **EDARSAHUB SQL Server es el cerebro absoluto** - CERO dependencias de MongoDB
2. **Política de Autorización Controlada** - No asumir reglas; esperar autorización explícita
3. **No Testing Agent** - Pruebas exclusivas vía cURL, bash, python -c

## Arquitectura Técnica
- **Frontend**: React (`/app/frontend/src/`)
- **Backend**: FastAPI (`/app/backend/`)
- **Base de Datos Principal**: EDARSAHUB SQL Server (54.39.104.176)
- **Legacy (ELIMINADO)**: MongoDB → Reemplazado por StubDatabase

## Credenciales de Prueba
- Admin: `admin@edarsa.com` / `admin123`

---

## Estado Actual (24 Mayo 2026)

### ✅ Completado

#### Migración MongoDB → SQL Server (COMPLETA)
- [x] Auth/Login migrado a SQL (login < 1s)
- [x] RBAC migrado a SQL Server (Usuario_Roles)
- [x] **Tablas Sesiones/SesionesHistorico creadas**
- [x] Scheduler usa StubDatabase para operaciones no críticas
- [x] **Tablas Scheduler_* creadas para tracking de jobs**
- [x] `sql_repository.py` creado con funciones SQL

#### CRM Comercial Enterprise (Fase 4)
- [x] Backend endpoints creados (`/api/crm/*`)
- [x] Datos: 18 cuentas, 2 cotizaciones
- [x] Rutas frontend y submenús agregados

#### Tablajería Fase 4: Captura Directa (24 Mayo 2026) ✅ NUEVO
- [x] **Endpoint `/api/tablajeria/ordenes/captura-directa` funcional**
- [x] **Creación de órdenes sin plantilla predefinida**
- [x] **Flujo completo verificado**: Crear → Iniciar → Registrar Resultados → Cerrar
- [x] **Corrección de columnas SQL**: Alineación `PorcentajeEsperado` vs `PorcentajeRendimientoEsperado`
- [x] **UUID especial para captura directa**: `00000000-0000-0000-0000-000000000001`
- [x] **UI Frontend**: Página `/tablajeria/captura-directa` con formulario completo

#### RBAC Tablajería (24 Mayo 2026) ✅ NUEVO
- [x] **11 módulos creados** en `Usuario_Modulos`:
  - tablajeria, tablajeria.dashboard, tablajeria.ordenes
  - tablajeria.captura_directa, tablajeria.plantillas, tablajeria.rendimientos
  - tablajeria.mermas, tablajeria.costeo, tablajeria.polizas
  - tablajeria.sync, tablajeria.config
- [x] **199 permisos asignados** a 8 roles (SUPERADMIN, ADMIN, GERENCIA, GERENTE_OPS, SUPERVISOR, OPERADOR, AUDITOR, VISOR)
- [x] **Script RBAC**: `/app/backend/scripts/create_tablajeria_rbac.py`

#### Tablajería Fase 6: Inventarios, Costeo, Contabilidad (24 Mayo 2026) ✅ INTEGRADO
- [x] **Credenciales hardcodeadas removidas** - Ahora usa variables de entorno `EDARSAHUB_*`
- [x] **6 tablas SQL creadas**:
  - `Tablajeria_MovimientosInventario`
  - `Tablajeria_CosteoProduccion`
  - `Tablajeria_CosteoDetalle`
  - `Tablajeria_PolizasContables`
  - `Tablajeria_PolizasDetalle`
  - `Tablajeria_ConfigContable`
- [x] **Servicio fase6_service.py operativo** con funcionalidades:
  - Afectación de inventarios (SALIDA_INSUMO, ENTRADA_DERIVADO, SALIDA_MERMA)
  - Costeo de producción (reglas PROPORCIONAL, FIJO, RESIDUAL)
  - Generación de pólizas contables
  - Proceso completo de cierre
- [x] **Integración automática con cierre de órdenes**:
  - Al cerrar orden con `ejecutar_fase6=true` y `costo_unitario_insumo`:
    1. Afecta inventarios automáticamente
    2. Calcula costeo con regla proporcional
    3. Genera póliza contable
- [x] **Endpoints API**:
  - `PUT /api/tablajeria/ordenes/{id}/cerrar` (con parámetros Fase 6)
  - `POST /api/tablajeria/ordenes/{id}/fase6/procesar-cierre`
  - `POST /api/tablajeria/ordenes/{id}/fase6/afectar-inventario`
  - `POST /api/tablajeria/ordenes/{id}/fase6/calcular-costeo`
  - `POST /api/tablajeria/ordenes/{id}/fase6/generar-poliza`
  - `GET/PUT /api/tablajeria/fase6/config-contable/{empresa_id}`

#### Correcciones de Columnas SQL (24 Mayo 2026)
- [x] `EsInventariable` → Usar `GeneraMovimiento` + inferencia por `TipoDerivado`
- [x] `FechaAfectacionInventario` → `MovimientoInventarioGenerado`
- [x] Limpieza de cache `__pycache__` para reflejar cambios

#### Migración P0 Workflows/SLA (24 Mayo 2026)
- [x] **OrquestadorService migrado a SQL** (11 → 0 refs MongoDB)
- [x] **SLA Service migrado a SQL** (17 → 0 refs MongoDB)
- [x] **Tablas creadas en EDARSAHUB**

#### Migración Referencias MongoDB Restantes
- [x] **Referencias MongoDB reducidas**: 80 → 21 en producción (-74%)

---

### 🔄 En Progreso

#### Jobs del Scheduler
- [x] 9 jobs funcionando (sync_comercial, notificaciones, etc.)
- [x] `inventarios_detector` y `pedidos_detector` con protección `_is_stub_db()`

---

### ⏳ Pendiente

#### P1 - Alta Prioridad
1. **Dashboard Rendimientos Tablajería** - Gráficos de rendimiento histórico por plantilla/insumo

#### P2 - Media Prioridad
1. **Flujos avanzados pipeline CRM** - Automatizaciones de etapas
2. **Reportes de Tablajería** - Exportación de costeo y mermas

#### CRM Fase 3 - Integraciones Externas ✅ YA EXISTENTE
- [x] Tablas: `CRM_Integracion_Conectores`, `CRM_Staging_*`, `CRM_Integracion_SyncLog`
- [x] VTiger Client implementado
- [x] 17+ endpoints de integración en `integration_routes.py`

---

## Archivos Clave - Tablajería

### Backend
- `/app/backend/modules/tablajeria/ordenes_service.py` - Servicio principal de órdenes
- `/app/backend/modules/tablajeria/fase6_service.py` - Inventario, Costeo, Contabilidad
- `/app/backend/modules/tablajeria/routes.py` - Endpoints API
- `/app/backend/modules/tablajeria/schemas.py` - Modelos Pydantic

### Tablas SQL Server
- `Operaciones_Tablaje_Ordenes` - Órdenes de tablaje
- `Operaciones_Tablaje_OrdenesDetalle` - Detalles (derivados)
- `Operaciones_Tablaje_Plantillas` - Plantillas de transformación
- `Operaciones_Tablaje_PlantillasDetalle` - Detalles de plantillas
- `Tablajeria_MovimientosInventario` - Afectación de inventarios
- `Tablajeria_CosteoProduccion` - Costeo de producción
- `Tablajeria_CosteoDetalle` - Detalle de costeo por producto
- `Tablajeria_PolizasContables` - Pólizas generadas
- `Tablajeria_PolizasDetalle` - Asientos contables
- `Tablajeria_ConfigContable` - Configuración por empresa

---

## API Endpoints Tablajería

### Órdenes
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/tablajeria/ordenes` | Listar órdenes |
| GET | `/api/tablajeria/ordenes/{id}` | Obtener orden con detalles |
| POST | `/api/tablajeria/ordenes` | Crear orden desde plantilla |
| POST | `/api/tablajeria/ordenes/captura-directa` | Crear orden sin plantilla |
| PUT | `/api/tablajeria/ordenes/{id}/iniciar` | Iniciar ejecución |
| PUT | `/api/tablajeria/ordenes/{id}/resultados` | Registrar resultados |
| PUT | `/api/tablajeria/ordenes/{id}/cerrar` | Cerrar (con Fase 6 opcional) |
| PUT | `/api/tablajeria/ordenes/{id}/cancelar` | Cancelar orden |
| PUT | `/api/tablajeria/ordenes/{id}/autorizar` | Autorizar desviaciones |

### Fase 6 (Inventario, Costeo, Contabilidad)
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/tablajeria/ordenes/{id}/fase6/procesar-cierre` | Proceso completo |
| POST | `/api/tablajeria/ordenes/{id}/fase6/afectar-inventario` | Solo inventario |
| POST | `/api/tablajeria/ordenes/{id}/fase6/calcular-costeo` | Solo costeo |
| POST | `/api/tablajeria/ordenes/{id}/fase6/generar-poliza` | Solo póliza |
| GET | `/api/tablajeria/fase6/config-contable/{empresa_id}` | Config contable |
| PUT | `/api/tablajeria/fase6/config-contable/{empresa_id}` | Guardar config |

---

## Payload Captura Directa (Ejemplo)

```json
{
  "empresa_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "fecha_operacion_mexico": "2026-05-24",
  "insumo_base_codigo": "INS-SALMON-001",
  "insumo_base_nombre": "Salmón fresco",
  "cantidad_base_planeada": 5.0,
  "detalles": [
    {
      "producto_derivado_nombre": "Filete de salmón",
      "tipo_derivado": "PRINCIPAL",
      "cantidad_esperada": 3.5,
      "porcentaje_esperado": 70.0
    },
    {
      "producto_derivado_nombre": "Recortes",
      "tipo_derivado": "MERMA",
      "cantidad_esperada": 1.0,
      "porcentaje_esperado": 20.0
    }
  ]
}
```

## Payload Cerrar con Fase 6 (Ejemplo)

```json
{
  "observaciones": "Cierre con costeo",
  "ejecutar_fase6": true,
  "costo_unitario_insumo": 180.00,
  "costo_mano_obra": 30.00,
  "costo_indirectos": 20.00,
  "costo_energia": 10.00,
  "otros_costos": 5.00
}
```

---

## Notas Técnicas

### Diferencias de Columnas SQL
| Tabla | Columna Plantilla | Columna Orden |
|-------|-------------------|---------------|
| PlantillasDetalle | `PorcentajeRendimientoEsperado` | - |
| OrdenesDetalle | - | `PorcentajeEsperado` |
| PlantillasDetalle | `EsInventariable` | - |
| OrdenesDetalle | - | `GeneraMovimiento` |

### Reglas de Costeo
1. **PROPORCIONAL**: Costo distribuido según cantidad producida
2. **FIJO**: Costo según % predefinido en plantilla
3. **RESIDUAL**: (Futuro) Costo asignado al producto residual

### Tolerancia de Desviación
- Default: 5%
- Si desviación > tolerancia: Estado `PENDIENTE_AUTORIZACION`
- Si desviación <= tolerancia: Estado `CERRADA` + Fase 6 ejecutada
