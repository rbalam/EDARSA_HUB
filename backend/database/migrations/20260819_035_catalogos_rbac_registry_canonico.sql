SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.Sistema_CatalogosConfig', N'U') IS NULL
        THROW 51350, 'Sistema_CatalogosConfig no existe.', 1;

    IF COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'CatalogoConfigID') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'CodigoCatalogo') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'NombreCatalogo') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'TipoConfiguracion') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'ConfigJSON') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'Activo') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'CreatedBy') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'UpdatedAt') IS NULL
       OR COL_LENGTH(N'dbo.Sistema_CatalogosConfig', N'UpdatedBy') IS NULL
        THROW 51351, 'Contrato inesperado de Sistema_CatalogosConfig.', 1;

    DECLARE @Target TABLE (
        CodigoCatalogo NVARCHAR(120) NOT NULL PRIMARY KEY,
        NombreCatalogo NVARCHAR(200) NOT NULL,
        ConfigJSON NVARCHAR(MAX) NOT NULL
    );

    INSERT INTO @Target (
        CodigoCatalogo,
        NombreCatalogo,
        ConfigJSON
    )
    VALUES
        (N'ActivoFijo_EstatusActivo', N'Estatus de Activo', N'{"dominios":["activos"],"tabla":"ActivoFijo_EstatusActivo"}'),
        (N'ActivoFijo_EstatusOT', N'Estatus de OT', N'{"dominios":["activos"],"tabla":"ActivoFijo_EstatusOT"}'),
        (N'ActivoFijo_TipoActivo', N'Tipos de Activo', N'{"dominios":["activos"],"tabla":"ActivoFijo_TipoActivo"}'),
        (N'ActivoFijo_TipoBaja', N'Tipos de Baja', N'{"dominios":["activos"],"tabla":"ActivoFijo_TipoBaja"}'),
        (N'ActivoFijo_TipoMedidor', N'Tipos de Medidor', N'{"dominios":["activos"],"tabla":"ActivoFijo_TipoMedidor"}'),
        (N'ActivoFijo_TipoOT', N'Tipos de OT', N'{"dominios":["activos"],"tabla":"ActivoFijo_TipoOT"}'),
        (N'ActivoFijo_TipoUbicacion', N'Tipos de Ubicación', N'{"dominios":["activos"],"tabla":"ActivoFijo_TipoUbicacion"}'),
        (N'Compras_ConciliacionSATEstatus', N'Estatus Conciliación SAT', N'{"dominios":["compras"],"tabla":"Compras_ConciliacionSATEstatus"}'),
        (N'Compras_DocumentosFiscalesEstatus', N'Estatus Docs. Fiscales', N'{"dominios":["compras"],"tabla":"Compras_DocumentosFiscalesEstatus"}'),
        (N'Compras_Estatus', N'Estatus de Compras', N'{"dominios":["compras"],"tabla":"Compras_Estatus"}'),
        (N'Compras_OrdenesEstatus', N'Estatus de Órdenes', N'{"dominios":["compras"],"tabla":"Compras_OrdenesEstatus"}'),
        (N'Compras_PedidosEstatus', N'Estatus de Pedidos', N'{"dominios":["compras"],"tabla":"Compras_PedidosEstatus"}'),
        (N'Compras_RecepcionesEstatus', N'Estatus de Recepciones', N'{"dominios":["compras"],"tabla":"Compras_RecepcionesEstatus"}'),
        (N'Finanzas_Cat_CuentasBancarias', N'Cuentas Bancarias', N'{"dominios":["finanzas"],"tabla":"Finanzas_Cat_CuentasBancarias"}'),
        (N'Finanzas_ConfiguracionTPV_Sucursal', N'Config. TPV por Sucursal', N'{"dominios":["finanzas"],"tabla":"Finanzas_ConfiguracionTPV_Sucursal"}'),
        (N'Finanzas_EstatusCierre', N'Estatus de Cierre', N'{"dominios":["finanzas"],"tabla":"Finanzas_EstatusCierre"}'),
        (N'Finanzas_EstatusPago', N'Estatus de Pago', N'{"dominios":["finanzas"],"tabla":"Finanzas_EstatusPago"}'),
        (N'Global_Cat_Bancos', N'Bancos', N'{"dominios":["generales","finanzas"],"tabla":"Global_Cat_Bancos"}'),
        (N'Global_Cat_FormaPagoSAT', N'Formas de Pago SAT', N'{"dominios":["finanzas"],"tabla":"Global_Cat_FormaPagoSAT"}'),
        (N'Inventario_TipoMovimiento', N'Tipos de Movimiento', N'{"dominios":["inventarios"],"tabla":"Inventario_TipoMovimiento"}'),
        (N'Producto_Familias', N'Familias', N'{"dominios":["inventarios"],"tabla":"Producto_Familias"}'),
        (N'Producto_Lineas', N'Líneas', N'{"dominios":["inventarios"],"tabla":"Producto_Lineas"}'),
        (N'Producto_Marcas', N'Marcas', N'{"dominios":["inventarios"],"tabla":"Producto_Marcas"}'),
        (N'Producto_SubFamilias', N'Subfamilias', N'{"dominios":["inventarios"],"tabla":"Producto_SubFamilias"}'),
        (N'Proveedor_EstatusProveedor', N'Estatus de Proveedor', N'{"dominios":["compras"],"tabla":"Proveedor_EstatusProveedor"}'),
        (N'Proveedor_Monedas', N'Monedas', N'{"dominios":["generales"],"tabla":"Proveedor_Monedas"}'),
        (N'Proveedor_TipoContacto', N'Tipos de Contacto', N'{"dominios":["compras"],"tabla":"Proveedor_TipoContacto"}'),
        (N'Proveedor_TipoDocumento', N'Tipos de Documento', N'{"dominios":["compras"],"tabla":"Proveedor_TipoDocumento"}'),
        (N'Proveedor_TipoProveedor', N'Tipos de Proveedor', N'{"dominios":["compras"],"tabla":"Proveedor_TipoProveedor"}'),
        (N'RH_Cat_Areas', N'Áreas', N'{"dominios":["rh"],"tabla":"RH_Cat_Areas"}'),
        (N'RH_Cat_Beneficios', N'Beneficios', N'{"dominios":["rh"],"tabla":"RH_Cat_Beneficios"}'),
        (N'RH_Cat_ConceptosNomina', N'Conceptos de Nómina', N'{"dominios":["nomina"],"tabla":"RH_Cat_ConceptosNomina"}'),
        (N'RH_Cat_Departamentos', N'Departamentos', N'{"dominios":["generales"],"tabla":"RH_Cat_Departamentos"}'),
        (N'RH_Cat_EstatusPeriodoNomina', N'Estatus de Período', N'{"dominios":["nomina"],"tabla":"RH_Cat_EstatusPeriodoNomina"}'),
        (N'RH_Cat_Jornadas', N'Jornadas', N'{"dominios":["rh"],"tabla":"RH_Cat_Jornadas"}'),
        (N'RH_Cat_MotivosBaja', N'Motivos de Baja', N'{"dominios":["rh"],"tabla":"RH_Cat_MotivosBaja"}'),
        (N'RH_Cat_Puestos', N'Puestos', N'{"dominios":["generales"],"tabla":"RH_Cat_Puestos"}'),
        (N'RH_Cat_RegimenContratacion', N'Régimen de Contratación', N'{"dominios":["rh"],"tabla":"RH_Cat_RegimenContratacion"}'),
        (N'RH_Cat_Sucursales', N'Sucursales', N'{"dominios":["generales"],"tabla":"RH_Cat_Sucursales"}'),
        (N'RH_Cat_TiposAusencia', N'Tipos de Ausencia', N'{"dominios":["rh"],"tabla":"RH_Cat_TiposAusencia"}'),
        (N'RH_Cat_TiposConceptoNomina', N'Tipos de Concepto', N'{"dominios":["nomina"],"tabla":"RH_Cat_TiposConceptoNomina"}'),
        (N'RH_Cat_TiposContrato', N'Tipos de Contrato', N'{"dominios":["rh"],"tabla":"RH_Cat_TiposContrato"}'),
        (N'RH_Cat_TiposPeriodoNomina', N'Tipos de Período', N'{"dominios":["nomina"],"tabla":"RH_Cat_TiposPeriodoNomina"}'),
        (N'RH_Cat_Turnos', N'Turnos', N'{"dominios":["rh"],"tabla":"RH_Cat_Turnos"}'),
        (N'RH_Homologacion_Equivalencias', N'Equivalencias', N'{"dominios":["homologacion"],"tabla":"RH_Homologacion_Equivalencias"}'),
        (N'Sistema_Catalogo', N'Sistemas', N'{"dominios":["configuracion"],"tabla":"Sistema_Catalogo"}'),
        (N'Usuario_Modulos', N'Módulos', N'{"dominios":["seguridad"],"tabla":"Usuario_Modulos"}'),
        (N'Usuario_Roles', N'Roles', N'{"dominios":["seguridad"],"tabla":"Usuario_Roles"}'),
        (N'Usuario_TiposAutorizacion', N'Tipos de Autorización', N'{"dominios":["seguridad"],"tabla":"Usuario_TiposAutorizacion"}'),
        (N'Venta_CotizacionesEstatus', N'Estatus de Cotizaciones', N'{"dominios":["ventas"],"tabla":"Venta_CotizacionesEstatus"}'),
        (N'Venta_Estatus', N'Estatus de Venta', N'{"dominios":["ventas"],"tabla":"Venta_Estatus"}'),
        (N'Venta_PedidosEstatus', N'Estatus de Pedidos', N'{"dominios":["ventas"],"tabla":"Venta_PedidosEstatus"}');

    IF (SELECT COUNT(*) FROM @Target) <> 52
        THROW 51352, 'El universo físico objetivo debe contener exactamente 52 catálogos.', 1;

    IF EXISTS (
        SELECT 1
        FROM @Target t
        WHERE OBJECT_ID(N'dbo.' + QUOTENAME(t.CodigoCatalogo), N'U') IS NULL
    )
        THROW 51353, 'Existe un catálogo objetivo sin tabla física dbo.', 1;

    IF EXISTS (
        SELECT c.CodigoCatalogo
        FROM dbo.Sistema_CatalogosConfig c
        JOIN @Target t
          ON UPPER(LTRIM(RTRIM(c.CodigoCatalogo)))
           = UPPER(LTRIM(RTRIM(t.CodigoCatalogo)))
        GROUP BY c.CodigoCatalogo
        HAVING COUNT(*) > 1
    )
        THROW 51354, 'Existe CodigoCatalogo físico ambiguo/duplicado en Sistema_CatalogosConfig.', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Sistema_CatalogosConfig c
        JOIN @Target t
          ON UPPER(LTRIM(RTRIM(c.CodigoCatalogo)))
           = UPPER(LTRIM(RTRIM(t.CodigoCatalogo)))
        WHERE UPPER(LTRIM(RTRIM(c.TipoConfiguracion))) <> N'CATALOGO_FISICO'
    )
        THROW 51355, 'Existe configuración incompatible para un catálogo físico objetivo.', 1;

    /*
      Slice 035 solo crea registros físicos inexistentes.
      No sobrescribe registros existentes compatibles.
      Esto hace el rollback determinista: CreatedBy identifica exactamente
      las filas creadas por esta migración.
    */
    INSERT INTO dbo.Sistema_CatalogosConfig (
        CodigoCatalogo,
        NombreCatalogo,
        Descripcion,
        TipoConfiguracion,
        EmpresaID,
        UnidadNegocioID,
        SucursalID,
        ConfigJSON,
        Activo,
        LegacyMongoID,
        LegacyCollection,
        MigratedAt,
        CreatedAt,
        CreatedBy,
        UpdatedAt,
        UpdatedBy
    )
    SELECT
        t.CodigoCatalogo,
        t.NombreCatalogo,
        N'Catálogo físico canónico EDARSAHUB',
        N'CATALOGO_FISICO',
        NULL,
        NULL,
        NULL,
        t.ConfigJSON,
        1,
        NULL,
        NULL,
        NULL,
        SYSUTCDATETIME(),
        N'MIGRATION_20260819_035',
        NULL,
        NULL
    FROM @Target t
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_CatalogosConfig c WITH (UPDLOCK, HOLDLOCK)
        WHERE UPPER(LTRIM(RTRIM(c.CodigoCatalogo)))
            = UPPER(LTRIM(RTRIM(t.CodigoCatalogo)))
    );

    IF (
        SELECT COUNT(DISTINCT UPPER(LTRIM(RTRIM(c.CodigoCatalogo))))
        FROM dbo.Sistema_CatalogosConfig c
        JOIN @Target t
          ON UPPER(LTRIM(RTRIM(c.CodigoCatalogo)))
           = UPPER(LTRIM(RTRIM(t.CodigoCatalogo)))
        WHERE c.Activo = 1
          AND UPPER(LTRIM(RTRIM(c.TipoConfiguracion))) = N'CATALOGO_FISICO'
    ) <> 52
        THROW 51356, 'No se alcanzó cobertura física activa 52/52.', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
