# DIAGNÓSTICO FASE 6: INVENTARIOS, COSTEO Y EVENTOS CONTABLES
## MÓDULO TABLAJERÍA - EDARSAHUB

**Fecha de Elaboración:** 2025-12-XX  
**Elaborado por:** Agente de Desarrollo  
**Estado:** DIAGNÓSTICO ENTREGADO - PENDIENTE AUTORIZACIÓN PARA IMPLEMENTAR

---

## 1. RESUMEN EJECUTIVO

### 1.1 Situación Actual
El módulo de Tablajería Fase 5 opera como **flujo administrativo-operativo** sin afectar inventarios, costos ni contabilidad. Esto es temporal y NO aceptable como comportamiento final.

### 1.2 Hallazgos Críticos
| Elemento | Estado Actual | Estado Requerido |
|----------|---------------|------------------|
| Movimientos de Inventario | NO SE GENERAN | OBLIGATORIO al cerrar orden |
| Prorrateo de Costos | TABLA VACÍA | OBLIGATORIO al cerrar orden |
| Eventos Contables | TABLA VACÍA | OBLIGATORIO al cerrar orden |
| Tipos de Movimiento Tablaje | NO EXISTEN | Crear 3 tipos nuevos |

### 1.3 Evidencia de Órdenes sin Afectación
```
Folio: TBJ-20260523-0001 | Estatus: CERRADA | AfectaInv: SÍ | MovGen: NO
Folio: TBJ-20260523-0002 | Estatus: CERRADA | AfectaInv: SÍ | MovGen: NO
```
Las órdenes tienen `AfectaInventario = 1` pero `MovimientoInventarioGenerado = 0`.

---

## 2. MAPA DE TABLAS ACTUALES DE INVENTARIO

### 2.1 Estructura Existente (REUTILIZAR, NO DUPLICAR)

#### Inventario_TipoMovimiento (Catálogo de tipos)
```sql
TipoMovimientoID  tinyint       NOT NULL  -- PK
Codigo            varchar(30)   NOT NULL  -- Ej: 'ENTRADA_COMPRA'
Descripcion       varchar(100)  NOT NULL
Naturaleza        char(1)       NOT NULL  -- 'E' = Entrada, 'S' = Salida
AfectaCostoPromedio bit         NOT NULL  -- 1 = Afecta costo promedio
Activo            bit           NOT NULL
```

**Tipos existentes:**
| ID | Código | Naturaleza | Afecta Costo |
|----|--------|------------|--------------|
| 1 | ENTRADA_COMPRA | ENTRADA | Sí |
| 2 | SALIDA_DEV_PROV | SALIDA | Sí |
| 3 | AJUSTE_ENTRADA | ENTRADA | Sí |
| 4 | AJUSTE_SALIDA | SALIDA | Sí |
| 5 | TRASPASO_ENTRADA | ENTRADA | No |
| 6 | TRASPASO_SALIDA | SALIDA | No |

**TIPOS A CREAR:**
| ID | Código | Naturaleza | Afecta Costo |
|----|--------|------------|--------------|
| 10 | TABLAJE_SALIDA_INSUMO | SALIDA | Sí |
| 11 | TABLAJE_ENTRADA_DERIVADO | ENTRADA | Sí |
| 12 | TABLAJE_MERMA | SALIDA | No |

#### Inventario_Movimientos (Header de movimiento)
```sql
MovimientoID        bigint       NOT NULL  -- PK Identity
TipoMovimientoID    tinyint      NOT NULL  -- FK a TipoMovimiento
EmpresaID           int          NULL
SucursalID          int          NOT NULL
AlmacenID           int          NOT NULL
FechaMovimiento     datetime2    NOT NULL
ReferenciaTipo      varchar(30)  NOT NULL  -- 'ORDEN_TABLAJE'
ReferenciaID        bigint       NULL      -- OrdenID (cast a bigint)
FolioReferencia     varchar(50)  NULL      -- FolioOrden
Observaciones       varchar(1000) NULL
UsuarioID           int          NULL
Activo              bit          NOT NULL
CreatedAt           datetime2    NOT NULL
```

#### Inventario_MovimientosDetalle (Líneas del movimiento)
```sql
MovimientoDetalleID   bigint     NOT NULL  -- PK Identity
MovimientoID          bigint     NOT NULL  -- FK a Movimientos
ProductoID            int        NOT NULL  -- FK a Producto_Catalogo
PresentacionProductoID bigint    NULL
Cantidad              decimal    NOT NULL
CostoUnitario         decimal    NOT NULL
Importe               decimal    NULL      -- Cantidad * CostoUnitario
Lote                  varchar(50) NULL
FechaCaducidad        date       NULL
ReferenciaDetalleTipo varchar(30) NULL     -- 'ORDEN_TABLAJE_DETALLE'
ReferenciaDetalleID   bigint     NULL      -- OrdenDetalleID
CreatedAt             datetime2  NOT NULL
```

#### Inventario_Existencias (Stock por almacén/producto)
```sql
ExistenciaID          bigint     NOT NULL  -- PK Identity
EmpresaID             int        NULL
SucursalID            int        NOT NULL
AlmacenID             int        NOT NULL
ProductoID            int        NOT NULL
ExistenciaActual      decimal    NOT NULL
CostoPromedio         decimal    NOT NULL
UltimaFechaMovimiento datetime2  NULL
UltimoMovimientoDetalleID bigint NULL
```

#### Inventario_Almacenes (Catálogo de almacenes)
```sql
AlmacenID         int           NOT NULL  -- PK Identity
EmpresaID         int           NULL
SucursalID        int           NOT NULL
CodigoAlmacen     varchar(20)   NOT NULL
NombreAlmacen     varchar(120)  NOT NULL
TipoAlmacen       varchar(20)   NOT NULL  -- 'GENERAL', 'PRODUCCION', etc.
PermiteCompras    bit           NOT NULL
PermiteVentas     bit           NOT NULL
Activo            bit           NOT NULL
```

---

## 3. MAPA DE TABLAS ACTUALES DE COSTOS

### 3.1 Operaciones_Tablaje_Costos (YA EXISTE - VACÍA)
```sql
CostoID               uniqueidentifier NOT NULL  -- PK
OrdenID               uniqueidentifier NOT NULL  -- FK a Órdenes
OrdenDetalleID        uniqueidentifier NULL      -- FK a OrdenesDetalle
EmpresaID             uniqueidentifier NOT NULL
FechaOperacionMexico  date             NOT NULL
ProductoID            int              NULL
ProductoCodigo        nvarchar(50)     NULL
ProductoNombre        nvarchar(200)    NULL
ReglaCosteo           nvarchar(50)     NOT NULL  -- 'PROPORCIONAL', 'POR_PESO', etc.
CostoInsumoBase       decimal          NULL      -- Costo total del insumo consumido
PorcentajeAsignado    decimal          NULL      -- % asignado al derivado
CostoAsignado         decimal          NOT NULL  -- Costo prorrateado al derivado
CantidadProducida     decimal          NULL
CostoUnitario         decimal          NULL      -- CostoAsignado / CantidadProducida
MonedaID              int              NOT NULL
EsCostoFinal          bit              NOT NULL
FechaCalculoUTC       datetime2        NOT NULL
UsuarioCalculoID      uniqueidentifier NULL
```

**Uso propuesto:**
- Al cerrar orden, insertar un registro por cada derivado producido
- Guardar el costo total del insumo base
- Calcular porcentaje asignado según regla de costeo
- Calcular costo unitario = CostoAsignado / CantidadProducida

---

## 4. MAPA DE TABLAS ACTUALES DE CONTABILIDAD

### 4.1 Operaciones_Tablaje_EventosContables (YA EXISTE - VACÍA)
```sql
EventoContableID      uniqueidentifier NOT NULL  -- PK
EmpresaID             uniqueidentifier NOT NULL
UnidadNegocioID       uniqueidentifier NULL
FechaOperacionMexico  date             NOT NULL
OrdenID               uniqueidentifier NOT NULL
OrdenFolio            nvarchar(50)     NULL
TipoEvento            nvarchar(100)    NOT NULL  -- 'TABLAJE_SALIDA_INSUMO', etc.
ProductoID            int              NULL
ProductoCodigo        nvarchar(50)     NULL
ProductoNombre        nvarchar(200)    NULL
Cantidad              decimal          NULL
Importe               decimal          NOT NULL
MonedaID              int              NOT NULL
CuentaCargoSugerida   nvarchar(50)     NULL      -- Cuenta contable sugerida
CuentaAbonoSugerida   nvarchar(50)     NULL
CentroCostoID         int              NULL
CentroCostoCodigo     nvarchar(50)     NULL
EstatusContable       nvarchar(50)     NOT NULL  -- 'PENDIENTE', 'PROCESADO', 'ERROR'
PolizaID              nvarchar(100)    NULL      -- Ref a póliza generada
NumeroPoliza          nvarchar(50)     NULL
FechaContabilizacion  date             NULL
Descripcion           nvarchar(500)    NULL
FechaCreacionUTC      datetime2        NOT NULL
FechaProcesoUTC       datetime2        NULL
UsuarioProcesoID      uniqueidentifier NULL
MensajeError          nvarchar(500)    NULL
```

**Tipos de Evento a Generar:**
1. `TABLAJE_SALIDA_INSUMO_BASE` - Consumo de materia prima
2. `TABLAJE_ENTRADA_DERIVADOS` - Producción de productos terminados
3. `TABLAJE_REGISTRO_MERMA` - Pérdida por merma
4. `TABLAJE_VARIACION_COSTO` - Diferencia vs costo estándar
5. `TABLAJE_VARIACION_RENDIMIENTO` - Diferencia vs rendimiento esperado
6. `TABLAJE_REVERSA_CANCELACION` - Solo si se cancela orden cerrada

---

## 5. TABLAS DE COMPRAS (FUENTE DE COSTO DE INSUMOS)

### 5.1 Flujo Existente
```
Compras_Ordenes → Compras_Recepciones → Inventario_Movimientos → Inventario_Existencias
```

La recepción de compra genera:
- `Inventario_Movimientos` con `TipoMovimientoID = 1` (ENTRADA_COMPRA)
- Actualiza `Inventario_Existencias.ExistenciaActual` y `CostoPromedio`

### 5.2 Cómo Obtener Costo del Insumo Base
**Opción 1:** Usar `Inventario_Existencias.CostoPromedio` del producto/almacén
**Opción 2:** Usar costo de última compra desde `Compras_RecepcionesDetalle`
**Opción 3:** Usar costo configurado en `Producto_Catalogo.PrecioCostoBase`

**RECOMENDACIÓN:** Usar `Inventario_Existencias.CostoPromedio` como primera opción, fallback a `Producto_Catalogo.PrecioCostoBase`.

---

## 6. TABLAS NUEVAS REQUERIDAS

### 6.1 NO SE REQUIEREN TABLAS NUEVAS
Todas las estructuras necesarias ya existen en EDARSAHUB:
- `Inventario_TipoMovimiento` → Solo INSERT de 3 tipos nuevos
- `Inventario_Movimientos` → Usar con ReferenciaTipo = 'ORDEN_TABLAJE'
- `Inventario_MovimientosDetalle` → Usar para cada producto
- `Inventario_Existencias` → Actualizar existencias y costos
- `Operaciones_Tablaje_Costos` → Poblar con prorrateo
- `Operaciones_Tablaje_EventosContables` → Poblar eventos

---

## 7. PROPUESTA DE FLUJO DE CIERRE CON AFECTACIÓN REAL

### 7.1 Validaciones Previas al Cierre (Fase Actual)
✅ Ya implementado:
- Validar que la orden esté EN_EJECUCION
- Validar que tenga `CantidadBaseReal` capturada
- Calcular rendimiento y desviación
- Determinar si requiere autorización

### 7.2 Nuevas Validaciones (A IMPLEMENTAR)
```python
def validar_cierre_con_inventario(orden_id):
    # 1. Verificar que exista almacén origen configurado
    if not orden.AlmacenOrigenID:
        raise ValueError("Orden sin almacén origen configurado")
    
    # 2. Verificar existencia suficiente del insumo base
    existencia = get_existencia(orden.AlmacenOrigenID, orden.InsumoBaseID)
    if existencia.ExistenciaActual < orden.CantidadBaseReal:
        raise ValueError(f"Existencia insuficiente: {existencia.ExistenciaActual} < {orden.CantidadBaseReal}")
    
    # 3. Verificar que todos los derivados tengan cantidad real
    for detalle in orden.detalles:
        if detalle.TipoDerivado != 'MERMA' and not detalle.CantidadReal:
            raise ValueError(f"Derivado {detalle.ProductoDerivadoNombre} sin cantidad real")
    
    # 4. Verificar consistencia de salidas vs entradas
    total_salida = orden.CantidadBaseReal
    total_entrada = sum(d.CantidadReal for d in detalles if d.TipoDerivado != 'MERMA')
    total_merma = sum(d.CantidadReal for d in detalles if d.TipoDerivado == 'MERMA')
    
    diferencia = total_salida - total_entrada - total_merma
    if abs(diferencia) > tolerancia:
        raise ValueError(f"Diferencia no cuadra: Salida={total_salida}, Entrada={total_entrada}, Merma={total_merma}")
```

### 7.3 Generación de Movimientos de Inventario
```python
def generar_movimientos_inventario(orden_id, usuario_id):
    """
    Genera movimientos de inventario al cerrar orden.
    Ejecutar en TRANSACCIÓN única.
    """
    
    # 1. MOVIMIENTO DE SALIDA - Insumo Base
    mov_salida = INSERT Inventario_Movimientos (
        TipoMovimientoID = 10,  -- TABLAJE_SALIDA_INSUMO
        AlmacenID = orden.AlmacenOrigenID,
        ReferenciaTipo = 'ORDEN_TABLAJE',
        ReferenciaID = orden.OrdenID,
        FolioReferencia = orden.FolioOrden
    )
    
    INSERT Inventario_MovimientosDetalle (
        MovimientoID = mov_salida.MovimientoID,
        ProductoID = orden.InsumoBaseID,
        Cantidad = orden.CantidadBaseReal,
        CostoUnitario = existencia.CostoPromedio,
        Importe = CantidadBaseReal * CostoPromedio,
        Lote = orden.LoteInsumo
    )
    
    # 2. ACTUALIZAR EXISTENCIA DEL INSUMO BASE (RESTAR)
    UPDATE Inventario_Existencias SET
        ExistenciaActual = ExistenciaActual - orden.CantidadBaseReal,
        UltimaFechaMovimiento = GETDATE()
    WHERE AlmacenID = orden.AlmacenOrigenID AND ProductoID = orden.InsumoBaseID
    
    # 3. MOVIMIENTOS DE ENTRADA - Derivados
    FOR detalle IN orden.detalles WHERE TipoDerivado != 'MERMA':
        
        mov_entrada = INSERT Inventario_Movimientos (
            TipoMovimientoID = 11,  -- TABLAJE_ENTRADA_DERIVADO
            AlmacenID = detalle.AlmacenDestinoID or orden.AlmacenDestinoID,
            ReferenciaTipo = 'ORDEN_TABLAJE',
            ReferenciaID = orden.OrdenID,
            FolioReferencia = orden.FolioOrden
        )
        
        INSERT Inventario_MovimientosDetalle (
            MovimientoID = mov_entrada.MovimientoID,
            ProductoID = detalle.ProductoDerivadoID,
            Cantidad = detalle.CantidadReal,
            CostoUnitario = detalle.CostoUnitario,  -- Del prorrateo
            Importe = detalle.CostoTotal,
            ReferenciaDetalleTipo = 'ORDEN_TABLAJE_DETALLE',
            ReferenciaDetalleID = detalle.OrdenDetalleID
        )
        
        # 4. ACTUALIZAR O CREAR EXISTENCIA DEL DERIVADO (SUMAR)
        MERGE Inventario_Existencias AS target
        USING (SELECT almacen, producto, cantidad, costo) AS source
        ON target.AlmacenID = source.almacen AND target.ProductoID = source.producto
        WHEN MATCHED THEN
            UPDATE SET 
                ExistenciaActual = ExistenciaActual + source.cantidad,
                CostoPromedio = recalcular_costo_promedio()
        WHEN NOT MATCHED THEN
            INSERT (AlmacenID, ProductoID, ExistenciaActual, CostoPromedio)
            VALUES (source.almacen, source.producto, source.cantidad, source.costo)
    
    # 5. MOVIMIENTO DE MERMA (si aplica)
    IF orden.MermaRealKg > 0:
        mov_merma = INSERT Inventario_Movimientos (
            TipoMovimientoID = 12,  -- TABLAJE_MERMA
            AlmacenID = orden.AlmacenOrigenID,
            ReferenciaTipo = 'ORDEN_TABLAJE',
            ReferenciaID = orden.OrdenID
        )
        # La merma no genera detalle de producto específico,
        # pero sí se registra el costo absorbido
    
    # 6. MARCAR ORDEN COMO MOVIMIENTO GENERADO
    UPDATE Operaciones_Tablaje_Ordenes SET
        MovimientoInventarioGenerado = 1
    WHERE OrdenID = orden_id
```

---

## 8. PROPUESTA DE PRORRATEO DE COSTOS

### 8.1 Reglas de Costeo Configurables
La plantilla define `ReglaCosteo` que puede ser:
- `PROPORCIONAL`: Por porcentaje definido en plantilla
- `POR_PESO`: Por peso real resultante
- `POR_CANTIDAD`: Por cantidad real
- `MIXTA`: Combinación (producto principal fijo, resto proporcional)

### 8.2 Algoritmo de Prorrateo
```python
def calcular_prorrateo_costos(orden_id):
    """
    Distribuye el costo del insumo base entre los derivados.
    """
    # 1. Obtener costo total del insumo base consumido
    existencia = get_existencia(orden.AlmacenOrigenID, orden.InsumoBaseID)
    costo_insumo_base = orden.CantidadBaseReal * existencia.CostoPromedio
    
    # 2. Guardar costo en la orden
    UPDATE orden SET CostoInsumoBase = costo_insumo_base
    
    # 3. Obtener derivados con cantidad real (excluyendo merma)
    derivados = [d for d in orden.detalles if d.TipoDerivado != 'MERMA' and d.CantidadReal > 0]
    
    # 4. Calcular prorrateo según regla
    if orden.ReglaCosteo == 'PROPORCIONAL':
        # Usar PorcentajeCostoAsignado de la plantilla
        for derivado in derivados:
            porcentaje = derivado.PorcentajeCostoAsignado or (100 / len(derivados))
            costo_asignado = costo_insumo_base * (porcentaje / 100)
            costo_unitario = costo_asignado / derivado.CantidadReal
    
    elif orden.ReglaCosteo == 'POR_PESO':
        # Usar PesoRealKg proporcional
        total_peso = sum(d.PesoRealKg or d.CantidadReal for d in derivados)
        for derivado in derivados:
            peso = derivado.PesoRealKg or derivado.CantidadReal
            porcentaje = (peso / total_peso) * 100
            costo_asignado = costo_insumo_base * (peso / total_peso)
            costo_unitario = costo_asignado / derivado.CantidadReal
    
    elif orden.ReglaCosteo == 'POR_CANTIDAD':
        # Proporcional a cantidad real
        total_cantidad = sum(d.CantidadReal for d in derivados)
        for derivado in derivados:
            porcentaje = (derivado.CantidadReal / total_cantidad) * 100
            costo_asignado = costo_insumo_base * (derivado.CantidadReal / total_cantidad)
            costo_unitario = costo_asignado / derivado.CantidadReal
    
    # 5. Asignar costo de merma (resto no asignado o explícito)
    costo_merma = costo_insumo_base - sum(d.CostoAsignado for d in derivados)
    
    # 6. Registrar en Operaciones_Tablaje_Costos
    for derivado in derivados:
        INSERT INTO Operaciones_Tablaje_Costos (
            CostoID, OrdenID, OrdenDetalleID, EmpresaID,
            FechaOperacionMexico, ProductoID, ProductoCodigo, ProductoNombre,
            ReglaCosteo, CostoInsumoBase, PorcentajeAsignado,
            CostoAsignado, CantidadProducida, CostoUnitario,
            EsCostoFinal, FechaCalculoUTC, UsuarioCalculoID
        ) VALUES (...)
    
    # 7. Actualizar detalles de la orden con costos
    for derivado in derivados:
        UPDATE Operaciones_Tablaje_OrdenesDetalle SET
            CostoUnitario = derivado.costo_unitario,
            CostoTotal = derivado.costo_asignado,
            PorcentajeCostoAsignado = derivado.porcentaje
        WHERE OrdenDetalleID = derivado.id
```

---

## 9. PROPUESTA DE EVENTOS CONTABLES

### 9.1 Tipos de Evento
| TipoEvento | Descripción | Cuenta Cargo | Cuenta Abono |
|------------|-------------|--------------|--------------|
| TABLAJE_SALIDA_INSUMO_BASE | Consumo materia prima | Producción en Proceso | Almacén MP |
| TABLAJE_ENTRADA_DERIVADOS | Alta producto terminado | Almacén PT | Producción en Proceso |
| TABLAJE_REGISTRO_MERMA | Merma del proceso | Gastos de Producción | Almacén MP |
| TABLAJE_VARIACION_COSTO | Diferencia vs estándar | Variación Costo | Varios |
| TABLAJE_VARIACION_RENDIMIENTO | Diferencia vs esperado | Variación Rendimiento | Varios |

### 9.2 Generación de Eventos
```python
def generar_eventos_contables(orden_id):
    """
    Genera eventos contables pendientes de procesar.
    NO genera pólizas directamente, solo prepara los eventos.
    """
    
    # 1. Evento: Salida de Insumo Base
    INSERT INTO Operaciones_Tablaje_EventosContables (
        EventoContableID, EmpresaID, FechaOperacionMexico,
        OrdenID, OrdenFolio, TipoEvento,
        ProductoID, ProductoCodigo, ProductoNombre,
        Cantidad, Importe,
        CuentaCargoSugerida = '5100-PROD-PROCESO',
        CuentaAbonoSugerida = '1150-ALMACEN-MP',
        EstatusContable = 'PENDIENTE'
    )
    
    # 2. Evento: Entrada de Derivados (uno por derivado)
    FOR derivado IN orden.derivados:
        INSERT INTO Operaciones_Tablaje_EventosContables (
            TipoEvento = 'TABLAJE_ENTRADA_DERIVADOS',
            ProductoID = derivado.ProductoID,
            Cantidad = derivado.CantidadReal,
            Importe = derivado.CostoTotal,
            CuentaCargoSugerida = '1160-ALMACEN-PT',
            CuentaAbonoSugerida = '5100-PROD-PROCESO',
            EstatusContable = 'PENDIENTE'
        )
    
    # 3. Evento: Merma (si aplica)
    IF orden.MermaRealKg > 0 AND costo_merma > 0:
        INSERT INTO Operaciones_Tablaje_EventosContables (
            TipoEvento = 'TABLAJE_REGISTRO_MERMA',
            Cantidad = orden.MermaRealKg,
            Importe = costo_merma,
            CuentaCargoSugerida = '5200-GASTOS-PROD',
            CuentaAbonoSugerida = '1150-ALMACEN-MP',
            EstatusContable = 'PENDIENTE'
        )
    
    # 4. Evento: Variación de Costo (si hay diferencia)
    # 5. Evento: Variación de Rendimiento (si hay diferencia fuera de tolerancia)
```

---

## 10. RIESGOS IDENTIFICADOS

### 10.1 Riesgos de Implementación
| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| R1 | ProductoID de derivados no existe en Producto_Catalogo | Alta | Alto | Validar antes de cierre o crear productos faltantes |
| R2 | AlmacenID no configurado en órdenes existentes | Alta | Alto | Requerir configuración en plantilla/orden |
| R3 | Existencia insuficiente al momento del cierre | Media | Alto | Validación previa con bloqueo |
| R4 | Costo promedio = 0 (producto sin movimientos previos) | Media | Medio | Usar PrecioCostoBase o marcar advertencia |
| R5 | Transacción muy larga bloquea tablas | Baja | Alto | Usar ROWLOCK, transacciones cortas |

### 10.2 Riesgos de Negocio
| # | Riesgo | Mitigación |
|---|--------|------------|
| R6 | Afectar inventario sin autorización de Auditoría | Fase de pruebas con datos simulados primero |
| R7 | Generar pólizas incorrectas | Los eventos contables quedan como PENDIENTE, no generan pólizas automáticamente |
| R8 | Romper tablero ejecutivo o comercial | Tablaje usa tablas propias aisladas |

---

## 11. TABLAS A REUTILIZAR (NO CREAR)

| Tabla | Uso |
|-------|-----|
| `Inventario_TipoMovimiento` | Agregar 3 tipos nuevos |
| `Inventario_Movimientos` | Header de movimientos de tablaje |
| `Inventario_MovimientosDetalle` | Líneas de movimiento |
| `Inventario_Existencias` | Actualizar stock y costo promedio |
| `Inventario_Almacenes` | Validar almacenes válidos |
| `Producto_Catalogo` | Obtener ProductoID y costo base |
| `Operaciones_Tablaje_Costos` | Guardar prorrateo de costos |
| `Operaciones_Tablaje_EventosContables` | Guardar eventos contables |
| `Operaciones_Tablaje_Mermas` | Ya se usa (mantener) |
| `Operaciones_Tablaje_Rendimientos` | Ya se usa (mantener) |
| `Operaciones_Tablaje_Auditoria` | Registrar cambios críticos |

---

## 12. TABLAS NUEVAS (NINGUNA REQUERIDA)

**NO se requiere crear tablas nuevas.** Toda la estructura necesaria ya existe en EDARSAHUB.

---

## 13. ENDPOINTS A CREAR/MODIFICAR

### 13.1 Endpoints a Modificar
| Endpoint | Archivo | Cambio |
|----------|---------|--------|
| `PUT /api/tablajeria/ordenes/{id}/cerrar` | `routes.py` | Agregar lógica de inventario, costos y eventos |
| `PUT /api/tablajeria/ordenes/{id}/cancelar` | `routes.py` | Si orden ya afectó inventario, generar reversa |

### 13.2 Endpoints Nuevos (Opcionales)
| Endpoint | Descripción |
|----------|-------------|
| `GET /api/tablajeria/ordenes/{id}/costos` | Ver detalle de prorrateo de costos |
| `GET /api/tablajeria/ordenes/{id}/eventos-contables` | Ver eventos contables generados |
| `POST /api/tablajeria/ordenes/{id}/validar-cierre` | Validar si la orden puede cerrarse (dry-run) |
| `POST /api/tablajeria/ordenes/{id}/revertir` | Revertir cierre (con autorización) |

---

## 14. PRUEBAS REQUERIDAS

### 14.1 Pruebas Unitarias (Backend)
1. Validación de existencia suficiente
2. Cálculo de prorrateo de costos por cada regla
3. Generación correcta de movimientos de inventario
4. Actualización de existencias y costo promedio
5. Generación de eventos contables
6. Reversa de cancelación

### 14.2 Pruebas de Integración
1. Cierre completo de orden con todos los pasos
2. Cierre con merma
3. Cierre con autorización requerida
4. Cancelación de orden cerrada (reversa)
5. Concurrencia: dos usuarios cerrando órdenes simultáneamente

### 14.3 Pruebas de Regresión
1. Tablero Ejecutivo no se ve afectado
2. Módulo Comercial no se ve afectado
3. Módulo Compras no se ve afectado
4. Inventarios Físicos (Auditoría) reflejan movimientos correctamente

---

## 15. CONFIRMACIÓN DE IMPLEMENTACIÓN SEGURA

### 15.1 Módulos que NO se rompen
| Módulo | Confirmación |
|--------|--------------|
| Inventarios | OK - Tablajería usa tablas estándar de inventario con sus propios tipos de movimiento |
| Compras | OK - No se modifican tablas de Compras, solo se leen costos |
| Finanzas | OK - Solo se generan eventos PENDIENTES, no pólizas automáticas |
| Contabilidad | OK - Eventos contables quedan pendientes de autorización |
| Tablero Ejecutivo | OK - No usa tablas de Tablajería |
| Comercial | OK - No hay intersección |

### 15.2 Condiciones para Implementación Segura
1. ✅ Usar tipos de movimiento nuevos (10, 11, 12) sin modificar existentes
2. ✅ No modificar lógica de ENTRADA_COMPRA ni otros movimientos
3. ✅ Eventos contables en estado PENDIENTE (no generan pólizas)
4. ✅ Transacciones atómicas con rollback en caso de error
5. ✅ Auditoría completa de cada operación

---

## 16. PLAN DE IMPLEMENTACIÓN PROPUESTO

### Fase 6A: Preparación de Catálogos (DDL)
1. INSERT tipos de movimiento nuevos (10, 11, 12)
2. Validar que ProductoID de insumos/derivados existan en Producto_Catalogo
3. Validar que AlmacenID existan en Inventario_Almacenes

### Fase 6B: Lógica de Cierre con Inventario
1. Implementar validaciones previas al cierre
2. Implementar generación de movimientos de inventario
3. Implementar actualización de existencias

### Fase 6C: Prorrateo de Costos
1. Implementar cálculo de costo del insumo base
2. Implementar algoritmos de prorrateo por regla
3. Implementar registro en Operaciones_Tablaje_Costos

### Fase 6D: Eventos Contables
1. Implementar generación de eventos por tipo
2. Implementar estado PENDIENTE para revisión
3. (Futuro) Endpoint para marcar eventos como PROCESADOS

### Fase 6E: Reversa y Cancelación
1. Implementar lógica de reversa para órdenes cerradas
2. Generar movimientos de reversa con signo contrario
3. Generar eventos contables de reversa

---

## 17. AUTORIZACIÓN REQUERIDA

**ANTES DE IMPLEMENTAR CUALQUIER CAMBIO:**

1. ✅ Autorización para agregar tipos de movimiento a `Inventario_TipoMovimiento`
2. ✅ Autorización para generar movimientos en `Inventario_Movimientos` e `Inventario_MovimientosDetalle`
3. ✅ Autorización para actualizar `Inventario_Existencias`
4. ✅ Autorización para poblar `Operaciones_Tablaje_Costos`
5. ✅ Autorización para poblar `Operaciones_Tablaje_EventosContables`
6. ✅ Confirmación de reglas de costeo a implementar
7. ✅ Confirmación de cuentas contables sugeridas

---

**FIN DEL DIAGNÓSTICO FASE 6**

**ESTADO:** DIAGNÓSTICO COMPLETO - ESPERANDO AUTORIZACIÓN PARA IMPLEMENTAR
