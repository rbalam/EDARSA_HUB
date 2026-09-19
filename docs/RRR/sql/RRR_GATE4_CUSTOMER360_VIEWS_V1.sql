/* RRR GATE 4 CUSTOMER360 VIEWS V1 - DESIGN ONLY - NO EJECUTAR */

CREATE VIEW dbo.vw_RRR_ClienteActividadComercial AS
SELECT
    v.ClienteID,
    COUNT_BIG(*) AS VentasCount,
    MIN(v.FechaVenta) AS FechaPrimeraVenta,
    MAX(v.FechaVenta) AS FechaUltimaVenta,
    SUM(v.Total) AS VentasTotal
FROM dbo.Venta_Encabezado v
GROUP BY v.ClienteID;

CREATE VIEW dbo.vw_RRR_ClienteScoreActual AS
SELECT ClienteID, ScoreID, ModeloVersion, Score, CalculadoAtUtc, FechaOperacionCorte
FROM (
    SELECT s.*, ROW_NUMBER() OVER (PARTITION BY s.ClienteID ORDER BY s.CalculadoAtUtc DESC, s.ScoreID DESC) AS rn
    FROM dbo.RRR_ScoreHistorial s
) x
WHERE rn = 1;

CREATE VIEW dbo.vw_RRR_ClienteRankingActual AS
SELECT ClienteID, RankingID, ScoreID, ModeloVersion, RankCode, CalculadoAtUtc, VigenteDesde, VigenteHasta
FROM (
    SELECT r.*, ROW_NUMBER() OVER (PARTITION BY r.ClienteID ORDER BY r.CalculadoAtUtc DESC, r.RankingID DESC) AS rn
    FROM dbo.RRR_RankingHistorial r
) x
WHERE rn = 1;

CREATE VIEW dbo.vw_RRR_Customer360 AS
SELECT
    c.ClienteID,
    c.CodigoCliente,
    c.RazonSocial,
    c.NombreComercial,
    c.EmailPrincipal,
    c.TelefonoPrincipal,
    c.SectorID,
    c.TamanoClienteID,
    c.RiesgoCuentaID,
    c.EsProspecto,
    c.EsPartner,
    c.EsCuentaEstrategica,
    c.FechaUltimaInteraccion,
    a.FechaPrimeraVenta,
    a.FechaUltimaVenta,
    COALESCE(a.VentasCount,0) AS VentasCount,
    COALESCE(a.VentasTotal,0) AS VentasTotal,
    s.Score AS ScoreRRR,
    s.ModeloVersion AS ScoreModeloVersion,
    s.CalculadoAtUtc AS ScoreCalculadoAtUtc,
    r.RankCode,
    r.ModeloVersion AS RankModeloVersion,
    r.CalculadoAtUtc AS RankCalculadoAtUtc
FROM dbo.Cliente_Catalogo c
LEFT JOIN dbo.vw_RRR_ClienteActividadComercial a ON a.ClienteID=c.ClienteID
LEFT JOIN dbo.vw_RRR_ClienteScoreActual s ON s.ClienteID=c.ClienteID
LEFT JOIN dbo.vw_RRR_ClienteRankingActual r ON r.ClienteID=c.ClienteID;
