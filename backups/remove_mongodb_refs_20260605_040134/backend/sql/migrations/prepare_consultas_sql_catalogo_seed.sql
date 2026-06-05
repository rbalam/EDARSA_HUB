-- ============================================================================
-- FASE 2: Seed Consultas SQL Catálogo desde catalogo_consultas.py
-- Fecha: 2026-05-15
-- Autor: E1 Agent
-- Estado: PREPARATORIO - NO EJECUTAR SIN AUTORIZACIÓN
-- ============================================================================
-- 
-- NOTAS:
-- 1. Este script es IDEMPOTENTE (usa MERGE para evitar duplicados)
-- 2. Las consultas se marcan como:
--    - EsSistema = 1 (predefinidas, no editables)
--    - ConfigOrigen = 'LEGACY_PYTHON' (migradas desde código)
--    - SoloLectura = 1 (solo SELECT)
-- 3. Se cargan parámetros en ConsultasSQL_Parametros
-- 4. Se crea versión inicial en ConsultasSQL_Versiones
--
-- DEPENDENCIAS:
-- - Tabla Sistema_Tipos debe existir con:
--   ID=1 SOFTRESTAURANT
--   ID=2 MPRO
-- ============================================================================

SET NOCOUNT ON;
PRINT '=== INICIANDO CARGA DE CONSULTAS CATÁLOGO ===';
PRINT 'Fecha: ' + CONVERT(VARCHAR, GETDATE(), 120);

-- ============================================================================
-- SOFTRESTAURANT - VENTAS
-- ============================================================================

-- 1. SR_VENTAS_DIA
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_DIA')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_VENTAS_DIA',
        'Ventas del Día',
        'Total de ventas, cheques y comensales del día seleccionado',
        'Ventas',
        'CONSULTA',
        1, -- SoftRestaurant
        'SELECT 
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta_Total,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX,
    ISNULL(AVG(cheques.total), 0) as Cheque_Promedio,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as PAX_Promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(date, turnos.apertura) = ''{fecha}''
  AND cheques.cancelado = 0',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_VENTAS_DIA';
END
ELSE
    PRINT 'EXISTS: SR_VENTAS_DIA';

-- Parámetro para SR_VENTAS_DIA
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Parametros p 
               JOIN ConsultasSQL_Catalogo c ON c.ConsultaID = p.ConsultaID 
               WHERE c.CodigoConsulta = 'SR_VENTAS_DIA' AND p.NombreParametro = 'fecha')
BEGIN
    INSERT INTO ConsultasSQL_Parametros (ConsultaID, NombreParametro, NombreMostrar, TipoDato, Requerido, OrdenMostrar, ComponenteUI)
    SELECT ConsultaID, 'fecha', 'Fecha', 'DATE', 1, 1, 'DATE_PICKER'
    FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_DIA';
END;

-- 2. SR_VENTAS_PERIODO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_PERIODO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_VENTAS_PERIODO',
        'Ventas por Período',
        'Total de ventas entre dos fechas',
        'Ventas',
        'CONSULTA',
        1,
        'SELECT 
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta_Total,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX,
    ISNULL(AVG(cheques.total), 0) as Cheque_Promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= ''{fecha_ini} 00:00:00''
  AND turnos.apertura <= ''{fecha_fin} 23:59:59''
  AND cheques.cancelado = 0',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_VENTAS_PERIODO';
END
ELSE
    PRINT 'EXISTS: SR_VENTAS_PERIODO';

-- Parámetros para SR_VENTAS_PERIODO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Parametros p 
               JOIN ConsultasSQL_Catalogo c ON c.ConsultaID = p.ConsultaID 
               WHERE c.CodigoConsulta = 'SR_VENTAS_PERIODO' AND p.NombreParametro = 'fecha_ini')
BEGIN
    INSERT INTO ConsultasSQL_Parametros (ConsultaID, NombreParametro, NombreMostrar, TipoDato, Requerido, OrdenMostrar, ComponenteUI)
    SELECT ConsultaID, 'fecha_ini', 'Fecha Inicio', 'DATE', 1, 1, 'DATE_PICKER'
    FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_PERIODO';
    
    INSERT INTO ConsultasSQL_Parametros (ConsultaID, NombreParametro, NombreMostrar, TipoDato, Requerido, OrdenMostrar, ComponenteUI)
    SELECT ConsultaID, 'fecha_fin', 'Fecha Fin', 'DATE', 1, 2, 'DATE_PICKER'
    FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_PERIODO';
END;

-- 3. SR_VENTAS_POR_DIA
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_POR_DIA')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_VENTAS_POR_DIA',
        'Ventas Desglosadas por Día',
        'Ventas día a día en un período',
        'Ventas',
        'CONSULTA',
        1,
        'SELECT 
    CONVERT(date, turnos.apertura) as Fecha,
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= ''{fecha_ini} 00:00:00''
  AND turnos.apertura <= ''{fecha_fin} 23:59:59''
  AND cheques.cancelado = 0
GROUP BY CONVERT(date, turnos.apertura)
ORDER BY CONVERT(date, turnos.apertura)',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_VENTAS_POR_DIA';
END;

-- 4. SR_VENTAS_POR_HORA
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_POR_HORA')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_VENTAS_POR_HORA',
        'Ventas por Hora',
        'Distribución de ventas por hora del día',
        'Ventas',
        'CONSULTA',
        1,
        'SELECT 
    DATEPART(HOUR, cheques.fecha) as Hora,
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= ''{fecha_ini} 00:00:00''
  AND turnos.apertura <= ''{fecha_fin} 23:59:59''
  AND cheques.cancelado = 0
GROUP BY DATEPART(HOUR, cheques.fecha)
ORDER BY DATEPART(HOUR, cheques.fecha)',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_VENTAS_POR_HORA';
END;

-- 5. SR_VENTAS_POR_MESERO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_POR_MESERO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_VENTAS_POR_MESERO',
        'Ventas por Mesero',
        'Ranking de ventas por mesero/vendedor',
        'Ventas',
        'CONSULTA',
        1,
        'SELECT 
    ISNULL(m.nombre, ''Sin asignar'') as Mesero,
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX,
    ISNULL(AVG(cheques.total), 0) as Cheque_Promedio
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= ''{fecha_ini} 00:00:00''
  AND turnos.apertura <= ''{fecha_fin} 23:59:59''
  AND cheques.cancelado = 0
GROUP BY m.nombre
ORDER BY SUM(cheques.total) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_VENTAS_POR_MESERO';
END;

-- 6. SR_VENTAS_POR_PRODUCTO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_VENTAS_POR_PRODUCTO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_VENTAS_POR_PRODUCTO',
        'Ventas por Producto',
        'Top productos más vendidos',
        'Ventas',
        'CONSULTA',
        1,
        'SELECT TOP 50
    p.idproducto as Codigo,
    p.descripcion as Producto,
    SUM(cd.cantidad) as Cantidad,
    SUM(cd.cantidad * cd.precio) as Venta
FROM cheqdet cd
INNER JOIN cheques ON cheques.folio = cd.foliodet
INNER JOIN productos p ON p.idproducto = cd.idproducto
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= ''{fecha_ini} 00:00:00''
  AND turnos.apertura <= ''{fecha_fin} 23:59:59''
  AND cheques.cancelado = 0
GROUP BY p.idproducto, p.descripcion
ORDER BY SUM(cd.cantidad * cd.precio) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_VENTAS_POR_PRODUCTO';
END;

-- 7. SR_CORTESIAS
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_CORTESIAS')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_CORTESIAS',
        'Cortesías y Descuentos',
        'Detalle de cortesías aplicadas',
        'Ventas',
        'CONSULTA',
        1,
        'SELECT 
    CONVERT(date, turnos.apertura) as Fecha,
    cheques.folio as Folio,
    ISNULL(m.nombre, ''N/A'') as Mesero,
    cheques.subtotal as Subtotal,
    cheques.descuento as Descuento,
    cheques.total as Total,
    cheques.razondescuento as Razon
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= ''{fecha_ini} 00:00:00''
  AND turnos.apertura <= ''{fecha_fin} 23:59:59''
  AND cheques.descuento > 0
ORDER BY turnos.apertura DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_CORTESIAS';
END;

-- 8. SR_CANCELACIONES
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_CANCELACIONES')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_CANCELACIONES',
        'Cancelaciones',
        'Cheques cancelados en el período',
        'Ventas',
        'CONSULTA',
        1,
        'SELECT 
    CONVERT(date, turnos.apertura) as Fecha,
    cheques.folio as Folio,
    ISNULL(m.nombre, ''N/A'') as Mesero,
    cheques.total as Monto,
    cheques.razoncancelado as Razon
FROM cheques
LEFT JOIN meseros m ON m.idmesero = cheques.idmesero
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.apertura >= ''{fecha_ini} 00:00:00''
  AND turnos.apertura <= ''{fecha_fin} 23:59:59''
  AND cheques.cancelado = 1
ORDER BY turnos.apertura DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_CANCELACIONES';
END;

-- ============================================================================
-- SOFTRESTAURANT - COMPRAS
-- ============================================================================

-- 9. SR_COMPRAS_PERIODO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_COMPRAS_PERIODO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_COMPRAS_PERIODO',
        'Compras por Período',
        'Total de compras entre dos fechas',
        'Compras',
        'CONSULTA',
        1,
        'SELECT 
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
WHERE c.fechaaplicacion >= ''{fecha_ini}''
  AND c.fechaaplicacion <= ''{fecha_fin} 23:59:59''
  AND c.cancelado = 0',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_COMPRAS_PERIODO';
END;

-- 10. SR_COMPRAS_POR_PROVEEDOR
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_COMPRAS_POR_PROVEEDOR')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_COMPRAS_POR_PROVEEDOR',
        'Compras por Proveedor',
        'Desglose de compras por proveedor',
        'Compras',
        'CONSULTA',
        1,
        'SELECT 
    ISNULL(p.nombre, ''Sin proveedor'') as Proveedor,
    COUNT(DISTINCT c.idcompra) as Facturas,
    ISNULL(SUM(c.total), 0) as Compra_Total
FROM compras c
LEFT JOIN proveedores p ON p.idproveedor = c.idproveedor
WHERE c.fechaaplicacion >= ''{fecha_ini}''
  AND c.fechaaplicacion <= ''{fecha_fin} 23:59:59''
  AND c.cancelado = 0
GROUP BY p.nombre
ORDER BY SUM(c.total) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_COMPRAS_POR_PROVEEDOR';
END;

-- 11. SR_COMPRAS_POR_PRODUCTO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_COMPRAS_POR_PRODUCTO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_COMPRAS_POR_PRODUCTO',
        'Compras por Producto',
        'Detalle de productos comprados',
        'Compras',
        'CONSULTA',
        1,
        'SELECT TOP 50
    i.idinsumo as Codigo,
    i.descripcion as Producto,
    SUM(cm.cantidad) as Cantidad,
    AVG(cm.costo) as Costo_Promedio,
    SUM(cm.cantidad * cm.costo) as Compra_Total
FROM comprasmovtos cm
INNER JOIN compras c ON c.idcompra = cm.idcompra
INNER JOIN insumos i ON i.idinsumo = cm.idinsumo
WHERE c.fechaaplicacion >= ''{fecha_ini}''
  AND c.fechaaplicacion <= ''{fecha_fin} 23:59:59''
  AND c.cancelado = 0
GROUP BY i.idinsumo, i.descripcion
ORDER BY SUM(cm.cantidad * cm.costo) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_COMPRAS_POR_PRODUCTO';
END;

-- ============================================================================
-- SOFTRESTAURANT - INVENTARIOS
-- ============================================================================

-- 12. SR_INVENTARIO_ACTUAL
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_INVENTARIO_ACTUAL')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_INVENTARIO_ACTUAL',
        'Inventario Actual',
        'Existencias actuales por almacén',
        'Inventarios',
        'CONSULTA',
        1,
        'SELECT 
    i.idinsumo as Codigo,
    i.descripcion as Producto,
    ISNULL(e.existencia, 0) as Existencia,
    i.unidadcompra as Unidad,
    ISNULL(i.costo, 0) as Costo,
    ISNULL(e.existencia * i.costo, 0) as Valor
FROM insumos i
LEFT JOIN existenciasalmacen e ON e.idinsumo = i.idinsumo
LEFT JOIN almacen a ON a.idalmacen = e.idalmacen
WHERE a.nombre LIKE ''%{almacen}%''
  AND ISNULL(e.existencia, 0) > 0
ORDER BY i.descripcion',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_INVENTARIO_ACTUAL';
END;

-- Parámetro especial: almacen (STRING con riesgo)
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Parametros p 
               JOIN ConsultasSQL_Catalogo c ON c.ConsultaID = p.ConsultaID 
               WHERE c.CodigoConsulta = 'SR_INVENTARIO_ACTUAL' AND p.NombreParametro = 'almacen')
BEGIN
    INSERT INTO ConsultasSQL_Parametros (ConsultaID, NombreParametro, NombreMostrar, TipoDato, Requerido, OrdenMostrar, ComponenteUI, RegexValidacion)
    SELECT ConsultaID, 'almacen', 'Almacén', 'STRING', 1, 1, 'INPUT', '^[a-zA-Z0-9\s\-áéíóúÁÉÍÓÚñÑ]+$'
    FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_INVENTARIO_ACTUAL';
END;

-- ============================================================================
-- SOFTRESTAURANT - PAGOS
-- ============================================================================

-- 13. SR_FORMAS_PAGO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_FORMAS_PAGO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_FORMAS_PAGO',
        'Formas de Pago',
        'Desglose por forma de pago',
        'Pagos',
        'CONSULTA',
        1,
        'SELECT 
    ISNULL(fp.descripcion, ''Efectivo'') as Forma_Pago,
    COUNT(*) as Operaciones,
    ISNULL(SUM(cp.importe), 0) as Monto
FROM chequespagos cp
INNER JOIN cheques c ON c.folio = cp.folio
INNER JOIN turnos t ON t.idturno = c.idturno
LEFT JOIN formaspago fp ON fp.idformapago = cp.idformapago
WHERE t.apertura >= ''{fecha_ini} 00:00:00''
  AND t.apertura <= ''{fecha_fin} 23:59:59''
  AND c.cancelado = 0
GROUP BY fp.descripcion
ORDER BY SUM(cp.importe) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_FORMAS_PAGO';
END;

-- 14. SR_PROPINAS
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'SR_PROPINAS')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'SR_PROPINAS',
        'Propinas',
        'Total de propinas por mesero',
        'Pagos',
        'CONSULTA',
        1,
        'SELECT 
    ISNULL(m.nombre, ''Sin asignar'') as Mesero,
    COUNT(DISTINCT c.folio) as Cheques,
    ISNULL(SUM(c.propina), 0) as Propinas,
    ISNULL(SUM(c.total), 0) as Ventas
FROM cheques c
LEFT JOIN meseros m ON m.idmesero = c.idmesero
INNER JOIN turnos t ON t.idturno = c.idturno
WHERE t.apertura >= ''{fecha_ini} 00:00:00''
  AND t.apertura <= ''{fecha_fin} 23:59:59''
  AND c.cancelado = 0
  AND c.propina > 0
GROUP BY m.nombre
ORDER BY SUM(c.propina) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: SR_PROPINAS';
END;

-- ============================================================================
-- MPRO - VENTAS
-- ============================================================================

-- 15. MPRO_VENTAS_PERIODO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'MPRO_VENTAS_PERIODO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'MPRO_VENTAS_PERIODO',
        'Ventas por Período',
        'Total de ventas MPRO entre dos fechas',
        'Ventas',
        'CONSULTA',
        2, -- MPRO
        'SELECT 
    COUNT(DISTINCT Vn_Folio) as Tickets,
    ISNULL(SUM(Vn_Importe), 0) as Venta_Total
FROM Venta
WHERE Vn_Fecha >= ''{fecha_ini}'' 
  AND Vn_Fecha <= ''{fecha_fin} 23:59:59''
  AND ISNULL(Es_Cve_Estado, '''') <> ''CA''',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: MPRO_VENTAS_PERIODO';
END;

-- 16. MPRO_VENTAS_POR_DIA
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'MPRO_VENTAS_POR_DIA')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'MPRO_VENTAS_POR_DIA',
        'Ventas por Día',
        'Ventas MPRO desglosadas por día',
        'Ventas',
        'CONSULTA',
        2,
        'SELECT 
    CONVERT(date, Vn_Fecha) as Fecha,
    COUNT(DISTINCT Vn_Folio) as Tickets,
    ISNULL(SUM(Vn_Importe), 0) as Venta
FROM Venta
WHERE Vn_Fecha >= ''{fecha_ini}'' 
  AND Vn_Fecha <= ''{fecha_fin} 23:59:59''
  AND ISNULL(Es_Cve_Estado, '''') <> ''CA''
GROUP BY CONVERT(date, Vn_Fecha)
ORDER BY CONVERT(date, Vn_Fecha)',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: MPRO_VENTAS_POR_DIA';
END;

-- 17. MPRO_VENTAS_POR_SUCURSAL
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'MPRO_VENTAS_POR_SUCURSAL')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'MPRO_VENTAS_POR_SUCURSAL',
        'Ventas por Sucursal',
        'Ventas MPRO por sucursal/almacén',
        'Ventas',
        'CONSULTA',
        2,
        'SELECT 
    ISNULL(A.Al_Descripcion, ''Sin sucursal'') as Sucursal,
    COUNT(DISTINCT V.Vn_Folio) as Tickets,
    ISNULL(SUM(V.Vn_Importe), 0) as Venta
FROM Venta V
LEFT JOIN Almacen A ON A.Al_Cve_Almacen = V.Al_Cve_Almacen
WHERE V.Vn_Fecha >= ''{fecha_ini}'' 
  AND V.Vn_Fecha <= ''{fecha_fin} 23:59:59''
  AND ISNULL(V.Es_Cve_Estado, '''') <> ''CA''
GROUP BY A.Al_Descripcion
ORDER BY SUM(V.Vn_Importe) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: MPRO_VENTAS_POR_SUCURSAL';
END;

-- 18. MPRO_VENTAS_POR_PRODUCTO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'MPRO_VENTAS_POR_PRODUCTO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'MPRO_VENTAS_POR_PRODUCTO',
        'Ventas por Producto',
        'Top productos MPRO más vendidos',
        'Ventas',
        'CONSULTA',
        2,
        'SELECT TOP 50
    P.Pd_Cve_Producto as Codigo,
    P.Pd_Descripcion as Producto,
    SUM(V.Vn_Cantidad_1) as Cantidad,
    SUM(V.Vn_Importe) as Venta
FROM Venta V
INNER JOIN Producto P ON P.Pd_Cve_Producto = V.Pd_Cve_Producto
WHERE V.Vn_Fecha >= ''{fecha_ini}'' 
  AND V.Vn_Fecha <= ''{fecha_fin} 23:59:59''
  AND ISNULL(V.Es_Cve_Estado, '''') <> ''CA''
GROUP BY P.Pd_Cve_Producto, P.Pd_Descripcion
ORDER BY SUM(V.Vn_Importe) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: MPRO_VENTAS_POR_PRODUCTO';
END;

-- ============================================================================
-- MPRO - COMPRAS
-- ============================================================================

-- 19. MPRO_COMPRAS_PERIODO
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'MPRO_COMPRAS_PERIODO')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'MPRO_COMPRAS_PERIODO',
        'Compras por Período',
        'Total de compras MPRO',
        'Compras',
        'CONSULTA',
        2,
        'SELECT 
    COUNT(DISTINCT RC.Rc_Folio) as Facturas,
    ISNULL(SUM(RCD.Rd_Cantidad * RCD.Rd_Costo), 0) as Compra_Total
FROM REQUISICION_COMPRA RC
INNER JOIN REQUISICION_COMPRA_DETALLE RCD ON RCD.Rc_Folio = RC.Rc_Folio
WHERE RC.Rc_FechaCaptura >= ''{fecha_ini}'' 
  AND RC.Rc_FechaCaptura <= ''{fecha_fin} 23:59:59''',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: MPRO_COMPRAS_PERIODO';
END;

-- 20. MPRO_COMPRAS_POR_PROVEEDOR
IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Catalogo WHERE CodigoConsulta = 'MPRO_COMPRAS_POR_PROVEEDOR')
BEGIN
    INSERT INTO ConsultasSQL_Catalogo (
        CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
        SistemaTipoID, ConsultaSQL, EsSistema, EsPersonalizada, EsSincronizable,
        PermiteEjecucionManual, SoloLectura, ConfigOrigen, UsuarioCreacionID
    ) VALUES (
        'MPRO_COMPRAS_POR_PROVEEDOR',
        'Compras por Proveedor',
        'Compras MPRO por proveedor',
        'Compras',
        'CONSULTA',
        2,
        'SELECT 
    ISNULL(P.Pv_Descripcion, ''Sin proveedor'') as Proveedor,
    COUNT(DISTINCT RC.Rc_Folio) as Facturas,
    ISNULL(SUM(RCD.Rd_Cantidad * RCD.Rd_Costo), 0) as Compra_Total
FROM REQUISICION_COMPRA RC
INNER JOIN REQUISICION_COMPRA_DETALLE RCD ON RCD.Rc_Folio = RC.Rc_Folio
LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = RC.Pv_Cve_Proveedor
WHERE RC.Rc_FechaCaptura >= ''{fecha_ini}'' 
  AND RC.Rc_FechaCaptura <= ''{fecha_fin} 23:59:59''
GROUP BY P.Pv_Descripcion
ORDER BY SUM(RCD.Rd_Cantidad * RCD.Rd_Costo) DESC',
        1, 0, 0, 1, 1, 'LEGACY_PYTHON', 'SISTEMA'
    );
    PRINT 'INSERTED: MPRO_COMPRAS_POR_PROVEEDOR';
END;

-- ============================================================================
-- AGREGAR PARÁMETROS fecha_ini/fecha_fin A TODAS LAS CONSULTAS QUE LOS USAN
-- ============================================================================

-- Insertar parámetros para consultas con fecha_ini/fecha_fin (idempotente)
DECLARE @ConsultaID INT;
DECLARE consultas_cursor CURSOR FOR
    SELECT ConsultaID FROM ConsultasSQL_Catalogo 
    WHERE CodigoConsulta NOT IN ('SR_VENTAS_DIA', 'SR_INVENTARIO_ACTUAL');

OPEN consultas_cursor;
FETCH NEXT FROM consultas_cursor INTO @ConsultaID;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- fecha_ini
    IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Parametros WHERE ConsultaID = @ConsultaID AND NombreParametro = 'fecha_ini')
    BEGIN
        INSERT INTO ConsultasSQL_Parametros (ConsultaID, NombreParametro, NombreMostrar, TipoDato, Requerido, OrdenMostrar, ComponenteUI)
        VALUES (@ConsultaID, 'fecha_ini', 'Fecha Inicio', 'DATE', 1, 1, 'DATE_PICKER');
    END;
    
    -- fecha_fin
    IF NOT EXISTS (SELECT 1 FROM ConsultasSQL_Parametros WHERE ConsultaID = @ConsultaID AND NombreParametro = 'fecha_fin')
    BEGIN
        INSERT INTO ConsultasSQL_Parametros (ConsultaID, NombreParametro, NombreMostrar, TipoDato, Requerido, OrdenMostrar, ComponenteUI)
        VALUES (@ConsultaID, 'fecha_fin', 'Fecha Fin', 'DATE', 1, 2, 'DATE_PICKER');
    END;
    
    FETCH NEXT FROM consultas_cursor INTO @ConsultaID;
END;

CLOSE consultas_cursor;
DEALLOCATE consultas_cursor;

PRINT '';
PRINT '=== CARGA COMPLETADA ===';

-- Resumen final
SELECT 
    'Consultas cargadas' as Metrica,
    COUNT(*) as Valor
FROM ConsultasSQL_Catalogo
UNION ALL
SELECT 
    'Parámetros cargados',
    COUNT(*)
FROM ConsultasSQL_Parametros;

PRINT '';
PRINT 'Script completado: ' + CONVERT(VARCHAR, GETDATE(), 120);
GO
