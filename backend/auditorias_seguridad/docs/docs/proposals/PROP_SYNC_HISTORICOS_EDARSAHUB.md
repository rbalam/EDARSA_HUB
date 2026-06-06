# PROPUESTA: Sincronización de Históricos a EDARSAHUB
## FASE SYNC - Centralización de Datos Operativos

**Fecha:** 2026-05-15  
**Autor:** E1 Agent  
**Estado:** PROPUESTA - Pendiente Autorización  
**Prioridad sugerida:** P1

---

## 1. RESUMEN EJECUTIVO

### Situación Actual
- Los inventarios, almacenes y ventas se consultan **EN VIVO** contra servidores SoftRestaurant/MPRO
- No existe repositorio central de históricos
- Si un servidor está offline, no hay acceso a sus datos
- Los análisis cruzados entre sucursales requieren múltiples conexiones simultáneas

### Propuesta
Crear un **Data Lake centralizado en EDARSAHUB** que sincronice periódicamente:
- Inventarios físicos
- Catálogo de almacenes
- Ventas históricas
- Movimientos de inventario

### Beneficios Esperados
| Beneficio | Impacto |
|-----------|---------|
| Disponibilidad 24/7 | Consultas incluso con servidores offline |
| Rendimiento | Queries locales vs conexiones remotas |
| Análisis cruzados | Dashboard unificado multi-sucursal |
| Históricos | Retención de datos más allá del servidor origen |
| Auditoría | Trazabilidad centralizada |

---

## 2. ALCANCE PROPUESTO

### 2.1 Datos a Sincronizar

| Entidad | Sistema Origen | Prioridad | Volumen Estimado |
|---------|----------------|-----------|------------------|
| **Inventarios Físicos** | SR + MPRO | P0 | ~500 folios/mes/sucursal |
| **Almacenes** | SR + MPRO | P0 | ~50-100 por servidor |
| **Ventas Diarias** | SR + MPRO | P1 | ~1000-5000 registros/día/sucursal |
| **Movimientos Inventario** | SR + MPRO | P1 | ~200-500/día/sucursal |
| **Productos/Insumos** | SR + MPRO | P2 | ~2000-5000 por servidor |
| **Cortes de Caja** | SR | P2 | ~3-5/día/sucursal |

### 2.2 Datos NO Sincronizados (Consulta LIVE)
- Datos en tiempo real (ventas del día actual)
- Configuraciones de sistema
- Datos sensibles de usuarios

---

## 3. ARQUITECTURA PROPUESTA

### 3.1 Modelo de Tablas en EDARSAHUB

```
EDARSAHUB (SQL Server)
│
├── Sync_Inventarios_Fisicos
│   ├── SyncID (PK, IDENTITY)
│   ├── EmpresaID (FK → Sistema_Empresas)
│   ├── ServidorID (FK → Servidores_Conexiones)
│   ├── SucursalCodigo
│   ├── SucursalNombre
│   ├── AlmacenCodigo
│   ├── AlmacenNombre
│   ├── Folio
│   ├── FechaInventario
│   ├── Comentario
│   ├── TotalProductos
│   ├── SistemaOrigen (SR/MPRO)
│   ├── FechaSyncUTC
│   └── HashDatos (para detectar cambios)
│
├── Sync_Inventarios_Detalle
│   ├── DetalleID (PK, IDENTITY)
│   ├── SyncID (FK → Sync_Inventarios_Fisicos)
│   ├── ProductoCodigo
│   ├── ProductoNombre
│   ├── Existencia
│   ├── Costo
│   ├── CostoTotal
│   ├── Unidad
│   └── FechaSyncUTC
│
├── Sync_Almacenes
│   ├── AlmacenSyncID (PK, IDENTITY)
│   ├── EmpresaID
│   ├── ServidorID
│   ├── AlmacenCodigo
│   ├── AlmacenNombre
│   ├── SucursalCodigo
│   ├── SucursalNombre
│   ├── Tipo (1=Consumo, 2=Presentaciones)
│   ├── Activo
│   ├── SistemaOrigen
│   ├── FechaSyncUTC
│   └── UNIQUE(ServidorID, AlmacenCodigo)
│
├── Sync_Ventas_Diarias
│   ├── VentaSyncID (PK, IDENTITY)
│   ├── EmpresaID
│   ├── ServidorID
│   ├── FechaOperativa
│   ├── SucursalCodigo
│   ├── TotalVentaBruta
│   ├── TotalDescuentos
│   ├── TotalCortesias
│   ├── TotalCancelaciones
│   ├── TotalVentaNeta
│   ├── TotalPropinas
│   ├── NumeroTickets
│   ├── TicketPromedio
│   ├── SistemaOrigen
│   ├── FechaSyncUTC
│   └── UNIQUE(ServidorID, FechaOperativa)
│
├── Sync_Ventas_PorHora
│   ├── VentaHoraID (PK, IDENTITY)
│   ├── EmpresaID
│   ├── ServidorID
│   ├── FechaOperativa
│   ├── Hora (0-23)
│   ├── TotalVenta
│   ├── NumeroTickets
│   ├── SistemaOrigen
│   └── FechaSyncUTC
│
├── Sync_Movimientos_Inventario
│   ├── MovimientoSyncID (PK, IDENTITY)
│   ├── EmpresaID
│   ├── ServidorID
│   ├── FechaMovimiento
│   ├── TipoMovimiento
│   ├── AlmacenOrigen
│   ├── AlmacenDestino
│   ├── ProductoCodigo
│   ├── Cantidad
│   ├── Costo
│   ├── Usuario
│   ├── Referencia
│   ├── SistemaOrigen
│   └── FechaSyncUTC
│
└── Sync_Control_Ejecuciones
    ├── EjecucionID (PK, IDENTITY)
    ├── ServidorID
    ├── TipoSync (INVENTARIOS/VENTAS/ALMACENES/MOVIMIENTOS)
    ├── FechaInicioUTC
    ├── FechaFinUTC
    ├── Estado (RUNNING/SUCCESS/ERROR/PARTIAL)
    ├── RegistrosSincronizados
    ├── RegistrosError
    ├── UltimaFechaSincronizada
    ├── ErrorMensaje
    └── DuracionSegundos
```

### 3.2 Índices Propuestos

```sql
-- Búsquedas frecuentes
CREATE INDEX IX_Sync_Inventarios_Empresa_Fecha ON Sync_Inventarios_Fisicos(EmpresaID, FechaInventario);
CREATE INDEX IX_Sync_Inventarios_Servidor_Folio ON Sync_Inventarios_Fisicos(ServidorID, Folio);
CREATE INDEX IX_Sync_Ventas_Empresa_Fecha ON Sync_Ventas_Diarias(EmpresaID, FechaOperativa);
CREATE INDEX IX_Sync_Ventas_Servidor_Fecha ON Sync_Ventas_Diarias(ServidorID, FechaOperativa);
CREATE INDEX IX_Sync_Almacenes_Servidor ON Sync_Almacenes(ServidorID, Activo);
```

---

## 4. ESTRATEGIA DE SINCRONIZACIÓN

### 4.1 Tipos de Sincronización

| Tipo | Frecuencia | Datos | Estrategia |
|------|------------|-------|------------|
| **Full Sync** | Semanal (domingo 3am) | Todo | Truncate + Insert |
| **Incremental** | Cada 4 horas | Últimas 48h | Upsert por hash |
| **On-Demand** | Manual | Rango específico | Insert con validación |
| **Real-time** | Futuro | Eventos críticos | Webhook/trigger |

### 4.2 Flujo de Sincronización Incremental

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCHEDULER (cada 4 horas)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Obtener lista de servidores activos desde Sistema_Empresas   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Por cada servidor:                                           │
│     a. Verificar última sync exitosa                             │
│     b. Calcular rango de fechas a sincronizar                    │
│     c. Ejecutar queries contra servidor LIVE                     │
│     d. Calcular hash de cada registro                            │
│     e. Comparar con registros existentes en EDARSAHUB            │
│     f. INSERT nuevos / UPDATE modificados                        │
│     g. Registrar en Sync_Control_Ejecuciones                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Generar reporte de sincronización                            │
│     - Registros nuevos                                           │
│     - Registros actualizados                                     │
│     - Errores encontrados                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Manejo de Errores

| Escenario | Acción |
|-----------|--------|
| Servidor offline | Saltar, reintentar en próximo ciclo |
| Timeout de conexión | Reintentar 3 veces con backoff |
| Datos corruptos | Registrar error, continuar con siguiente |
| Conflicto de datos | Priorizar dato más reciente (FechaSyncUTC) |

---

## 5. MÓDULO BACKEND PROPUESTO

### 5.1 Estructura de Archivos

```
/app/backend/modules/sync_historicos/
├── __init__.py
├── models.py              # Modelos Pydantic para sync
├── repository.py          # Acceso a tablas Sync_*
├── sync_inventarios.py    # Lógica sync inventarios
├── sync_ventas.py         # Lógica sync ventas
├── sync_almacenes.py      # Lógica sync almacenes
├── sync_movimientos.py    # Lógica sync movimientos
├── scheduler.py           # Jobs de sincronización
├── service.py             # Orquestación general
└── README.md
```

### 5.2 API Endpoints Propuestos

```
POST /api/sync/inventarios/{server_id}
  - Sincroniza inventarios de un servidor
  - Parámetros: fecha_desde, fecha_hasta

POST /api/sync/ventas/{server_id}
  - Sincroniza ventas de un servidor
  - Parámetros: fecha_desde, fecha_hasta

POST /api/sync/almacenes/{server_id}
  - Sincroniza catálogo de almacenes

GET /api/sync/status/{server_id}
  - Estado de última sincronización

GET /api/sync/historico/inventarios
  - Consulta inventarios desde EDARSAHUB (no LIVE)
  - Filtros: empresa, servidor, fecha, almacen

GET /api/sync/historico/ventas
  - Consulta ventas históricas desde EDARSAHUB
  - Filtros: empresa, servidor, rango fechas

POST /api/sync/full
  - Ejecuta sincronización completa (admin only)
```

---

## 6. FASES DE IMPLEMENTACIÓN

### FASE SYNC-1: Infraestructura (2 días)
- [ ] DDL de tablas Sync_* en EDARSAHUB
- [ ] Índices y constraints
- [ ] Módulo base `/modules/sync_historicos/`
- [ ] Models y repository básico

### FASE SYNC-2: Sincronización de Almacenes (1 día)
- [ ] Implementar `sync_almacenes.py`
- [ ] Endpoint POST `/api/sync/almacenes/{server_id}`
- [ ] Pruebas con 2-3 servidores
- [ ] Documentación

### FASE SYNC-3: Sincronización de Inventarios (2 días)
- [ ] Implementar `sync_inventarios.py`
- [ ] Manejo de inventarios_detalle
- [ ] Cálculo de hash para detección de cambios
- [ ] Endpoint POST `/api/sync/inventarios/{server_id}`
- [ ] Pruebas

### FASE SYNC-4: Sincronización de Ventas (2 días)
- [ ] Implementar `sync_ventas.py`
- [ ] Ventas diarias + ventas por hora
- [ ] Endpoint POST `/api/sync/ventas/{server_id}`
- [ ] Pruebas

### FASE SYNC-5: Scheduler Automático (1 día)
- [ ] Integrar con scheduler existente
- [ ] Jobs cada 4 horas
- [ ] Monitoreo y alertas
- [ ] Reintentos automáticos

### FASE SYNC-6: Endpoints de Consulta (1 día)
- [ ] GET `/api/sync/historico/inventarios`
- [ ] GET `/api/sync/historico/ventas`
- [ ] Integración opcional con frontend

### FASE SYNC-7: Dashboard de Sincronización (Opcional)
- [ ] Vista de estado de sync por servidor
- [ ] Logs de errores
- [ ] Ejecución manual

---

## 7. ESTIMACIONES

### Volumen de Datos (por servidor/mes)
| Entidad | Registros | Tamaño estimado |
|---------|-----------|-----------------|
| Inventarios header | ~500 | ~50 KB |
| Inventarios detalle | ~50,000 | ~5 MB |
| Almacenes | ~100 | ~10 KB |
| Ventas diarias | ~30 | ~5 KB |
| Ventas por hora | ~720 | ~100 KB |

### Con 20 servidores activos
- **Almacenamiento mensual:** ~100-150 MB
- **Almacenamiento anual:** ~1.5-2 GB
- **Tiempo de sync completo:** ~30-60 minutos

---

## 8. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Servidores offline durante sync | Media | Bajo | Reintentos + sync parcial |
| Volumen excesivo de datos | Baja | Medio | Paginación + límites |
| Inconsistencia de datos | Baja | Alto | Hash + validación + logs |
| Impacto en servidores LIVE | Media | Medio | Queries optimizadas + horarios nocturnos |
| Duplicados | Baja | Medio | UNIQUE constraints + upsert |

---

## 9. DEPENDENCIAS

### Requiere completado:
- ✅ FASE 3: Repository SQL-First (para patrón de conexión)
- ✅ Sistema_Empresas como fuente autoritativa
- ✅ Servidores_Conexiones activos

### No requiere:
- ❌ Cambios en frontend
- ❌ Cambios en endpoints legacy
- ❌ MongoDB

---

## 10. DECISIONES PENDIENTES

1. **¿Frecuencia de sincronización?**
   - Opción A: Cada 4 horas (recomendado)
   - Opción B: Cada hora
   - Opción C: Solo manual

2. **¿Retención de datos?**
   - Opción A: 12 meses rolling
   - Opción B: Indefinido
   - Opción C: Configurable por empresa

3. **¿Sincronizar movimientos de inventario?**
   - P1: Solo inventarios físicos
   - P2: Incluir movimientos

4. **¿Notificaciones de errores?**
   - Email
   - Log interno
   - Ambos

---

## 11. CONCLUSIÓN

La sincronización de históricos a EDARSAHUB permitirá:

1. **Independencia operativa** - Consultas sin depender de servidores LIVE
2. **Análisis centralizados** - Dashboards multi-sucursal
3. **Resiliencia** - Datos disponibles 24/7
4. **Escalabilidad** - Base para BI/Analytics futuro

**Esfuerzo estimado total:** 8-10 días de desarrollo

---

## 12. PRÓXIMOS PASOS

Pendiente autorización para:

1. [ ] Aprobar alcance de FASE SYNC-1 a SYNC-4
2. [ ] Definir frecuencia de sincronización
3. [ ] Definir política de retención
4. [ ] Ejecutar DDL de tablas en EDARSAHUB

---

*Propuesta generada por E1 Agent*  
*Fecha: 2026-05-15*  
*Documento: `/app/docs/proposals/PROP_SYNC_HISTORICOS_EDARSAHUB.md`*
