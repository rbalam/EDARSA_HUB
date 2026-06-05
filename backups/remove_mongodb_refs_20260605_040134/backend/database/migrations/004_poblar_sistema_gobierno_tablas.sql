/* ============================================================
   MIGRACIÓN: Poblar Gobierno de Tablas
   Script: 004_poblar_sistema_gobierno_tablas.sql
   Modo: migrate
   
   Inserta/actualiza registros de gobierno para tablas EDARSAHUB.
   ============================================================ */

MERGE dbo.Sistema_Gobierno_Tablas AS tgt
USING (
    SELECT 'Global_Cat_Empresas' AS nombre_tabla, 'Global' AS modulo, 'CANONICA' AS categoria, 'ACTIVA' AS estado, 'EDARSAHUB SQL' AS fuente_verdad
    UNION ALL SELECT 'Global_Cat_Bancos', 'Global', 'CANONICA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'Global_Cat_UnidadesMedida', 'Global', 'CANONICA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'Global_Cat_CentrosCosto', 'Global', 'CANONICA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'Finanzas_Cat_CuentasBancarias', 'Finanzas', 'CANONICA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'propinas_tpv_control', 'Finanzas/PropinasTPV', 'CANONICA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'propinas_tpv_config', 'Finanzas/PropinasTPV', 'CANONICA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'propinas_tpv_historial', 'Finanzas/PropinasTPV', 'CANONICA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'RH_Colaboradores_Expediente', 'RH', 'CANONICA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'RH_Importacion_Staging', 'RH', 'STAGING', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'RH_Importacion_Bitacora', 'RH', 'LOG', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'Sync_Sales', 'Comercial', 'SINCRONIZADA', 'ACTIVA', 'SoftRestaurant/MPRO sincronizado'
    UNION ALL SELECT 'Sync_PAX_Detalle', 'Comercial', 'SINCRONIZADA', 'ACTIVA', 'SoftRestaurant/MPRO sincronizado'
    UNION ALL SELECT 'Sync_Productos', 'Comercial', 'SINCRONIZADA', 'ACTIVA', 'SoftRestaurant/MPRO sincronizado'
    UNION ALL SELECT 'Sync_Productos_Familias', 'Comercial', 'SINCRONIZADA', 'ACTIVA', 'SoftRestaurant/MPRO sincronizado'
    UNION ALL SELECT 'Sync_Productos_SubFamilias', 'Comercial', 'SINCRONIZADA', 'ACTIVA', 'SoftRestaurant/MPRO sincronizado'
    UNION ALL SELECT 'Comercial_KPIs_Diarios_v2', 'Comercial', 'DERIVADA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'Comercial_Ventas_Dia_Abiertas_v2', 'Comercial', 'DERIVADA', 'ACTIVA', 'EDARSAHUB SQL'
    UNION ALL SELECT 'Fact_Ventas_Consolidadas', 'Comercial', 'LEGADO_REVISION', 'NO_USAR_NUEVO', 'Pendiente validar'
    UNION ALL SELECT 'Products', 'Comercial', 'LEGADO_REVISION', 'NO_USAR_NUEVO', 'Pendiente validar'
    UNION ALL SELECT 'Config_Horarios', 'Comercial', 'LEGADO_REVISION', 'NO_USAR_NUEVO', 'Pendiente validar'
) AS src
ON tgt.nombre_tabla = src.nombre_tabla AND tgt.esquema = 'dbo'
WHEN MATCHED THEN
    UPDATE SET
        modulo = src.modulo,
        categoria = src.categoria,
        estado = src.estado,
        fuente_verdad = src.fuente_verdad,
        fecha_ultima_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN
    INSERT (nombre_tabla, modulo, categoria, estado, fuente_verdad)
    VALUES (src.nombre_tabla, src.modulo, src.categoria, src.estado, src.fuente_verdad);
GO
