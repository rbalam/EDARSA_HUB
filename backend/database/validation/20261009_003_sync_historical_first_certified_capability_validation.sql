SET NOCOUNT ON;

SELECT
    sc.Codigo,
    sc.CategoriaCodigo,
    sc.EntidadCodigo,
    sc.CampoFecha,
    sc.ClaveNegocio,
    sc.SoportaResume,
    sc.SoportaSafeStop,
    sc.VersionContrato,
    sc.MetadataJSON
FROM dbo.Sistema_Sync_Catalogo sc
WHERE sc.Codigo='comercial_ventas_cerradas';

SELECT
    st.CodigoSistema,
    cap.CodigoCapacidad,
    link.CodigoSync,
    link.Activo
FROM dbo.Sistema_Sync_Capacidades link
JOIN dbo.Sistema_Capacidades cap
  ON cap.SistemaCapacidadID=link.SistemaCapacidadID
JOIN dbo.Sistema_Tipos st
  ON st.SistemaTipoID=cap.SistemaTipoID
WHERE link.CodigoSync='comercial_ventas_cerradas'
AND st.CodigoSistema IN ('MPRO','SOFTRESTAURANT_PRO')
ORDER BY st.CodigoSistema;
