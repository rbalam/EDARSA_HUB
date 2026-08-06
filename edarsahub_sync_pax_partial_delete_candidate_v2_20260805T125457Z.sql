/*
EDARSAHUB - CANDIDATO DE LIMPIEZA
NO EJECUTADO.

Elimina exclusivamente las tres filas parciales auditadas
de dbo.Sync_PAX_Detalle.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
    THROW 51000, 'BASE_DATOS_INESPERADA', 1;

BEGIN TRANSACTION;

DECLARE @FilasObjetivoAntes bigint;
DECLARE @FilasObjetivoDespues bigint;
DECLARE @FilasEliminadas int;

SELECT @FilasObjetivoAntes = COUNT_BIG(*)
FROM dbo.Sync_PAX_Detalle
WHERE
        [PAXRegistroID] = N'379ef2b96dda3f4234b9290ac44c1ad9a65c1d0486251ce12c'
        OR [PAXRegistroID] = N'55708f66125c132d622b946c2fbff726301594ca2f6a4a6d24'
        OR [PAXRegistroID] = N'c0460e55b20fd4430c5b3268fb07c587d44151b32e3c2e917b';

IF @FilasObjetivoAntes <> 3
BEGIN
    ROLLBACK TRANSACTION;
    THROW 51001, 'FILAS_OBJETIVO_ESPERADAS_3', 1;
END;

DELETE FROM dbo.Sync_PAX_Detalle
WHERE
        [PAXRegistroID] = N'379ef2b96dda3f4234b9290ac44c1ad9a65c1d0486251ce12c'
        OR [PAXRegistroID] = N'55708f66125c132d622b946c2fbff726301594ca2f6a4a6d24'
        OR [PAXRegistroID] = N'c0460e55b20fd4430c5b3268fb07c587d44151b32e3c2e917b';

SET @FilasEliminadas = @@ROWCOUNT;

IF @FilasEliminadas <> 3
BEGIN
    ROLLBACK TRANSACTION;
    THROW 51002, 'FILAS_ELIMINADAS_ESPERADAS_3', 1;
END;

SELECT @FilasObjetivoDespues = COUNT_BIG(*)
FROM dbo.Sync_PAX_Detalle
WHERE
        [PAXRegistroID] = N'379ef2b96dda3f4234b9290ac44c1ad9a65c1d0486251ce12c'
        OR [PAXRegistroID] = N'55708f66125c132d622b946c2fbff726301594ca2f6a4a6d24'
        OR [PAXRegistroID] = N'c0460e55b20fd4430c5b3268fb07c587d44151b32e3c2e917b';

IF @FilasObjetivoDespues <> 0
BEGIN
    ROLLBACK TRANSACTION;
    THROW 51003, 'FILAS_OBJETIVO_RESTANTES', 1;
END;

/*
Este candidato permanece en ROLLBACK.
El script autorizado posterior deberá sustituir únicamente
este ROLLBACK final por COMMIT.
*/
ROLLBACK TRANSACTION;

SELECT
    N'VALIDACION_DELETE_CANDIDATO_PASS' AS Resultado,
    @FilasObjetivoAntes AS FilasObjetivoAntes,
    @FilasEliminadas AS FilasEliminadas,
    @FilasObjetivoDespues AS FilasObjetivoDespues;
