# CxP Slice 1 Authorization Engine Checkpoint

**Purpose:** durable, implementation-ready evidence package for Slice 1 only.
This is an audit/implementation-plan checkpoint; it does not apply SQL, change
runtime objects, or authorize implementation.

## A. Audited checkout and evidence provenance

- Branch: `Edarsahub_Desarrollo`
- HEAD: `4af9af9fc841d6d343f9c2ad6325b27475e66df6`
- Worktree: shared and dirty with unrelated files. No existing change or
  artifact collided with this checkpoint path.
- Runtime evidence was reproduced on 2026-08-19 through the canonical
  read-only runner and factory, before the current session lost its process
  configuration. Its validated identity was:
  `DB_NAME()=EDARSAHUB`, `SUSER_SNAME()=HRLectura`, and
  `USER_NAME()=HRLectura`.
- The complete definitions, hashes, metadata, dependencies, and plan below
  were recovered from the persisted local agent event history for that
  read-only reproduction. No SP was executed and no SQL write occurred.

## B. Runtime objects and pre-Slice 1 hashes

Canonical hash convention for Slice 1: `VARCHAR(MAX)` / ASCII / UTF-8 compatible byte stream representation, evaluated via `HASHBYTES('SHA2_256', CONVERT(VARCHAR(MAX), OBJECT_DEFINITION(...)))` in SQL Server and `hashlib.sha256(definition.encode('utf-8'))` in Python.

| Object | Canonical SHA-256 of runtime definition (VARCHAR representation) |
| --- | --- |
| `dbo.sp_Usuario_CrearAutorizacion` | `36686195682c3e0bef6f6aca9733d27e6622a6cf94c78ed6ff881626b595104e` |
| `dbo.sp_Usuario_ResolverAutorizacion` | `55dc7c243af010a4004e396f14b21f2946599648948bff53f244587b888f2b22` |

These are the required precondition hashes before implementation and the
required postcondition hashes after rollback. If either runtime hash differs
when Slice 1 starts, abort with `SP_RUNTIME_CHANGED_SIN_REAUDITORIA`.

## C. Exact pre-Slice 1 definitions for rollback

The following are the exact runtime definitions captured during the
read-only audit. The rollback artifact must restore these two definitions and
then verify the hashes in section B.

```sql
CREATE PROCEDURE dbo.sp_Usuario_CrearAutorizacion
    @FolioAutorizacion VARCHAR(30),
    @TipoAutorizacionCodigo VARCHAR(30),
    @EntidadNombre VARCHAR(100),
    @EntidadID VARCHAR(100) = NULL,
    @FolioReferencia VARCHAR(50) = NULL,
    @UsuarioSolicitanteID INT = NULL,
    @Monto DECIMAL(18,2) = NULL,
    @MonedaID SMALLINT = NULL,
    @Justificacion VARCHAR(2000),
    @AutorizacionID BIGINT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @TipoAutorizacionID SMALLINT;
    DECLARE @ModuloID INT;
    DECLARE @AccionID SMALLINT;
    DECLARE @NivelFinalRequerido SMALLINT = NULL;

    IF @UsuarioSolicitanteID IS NULL
        SELECT @UsuarioSolicitanteID = TRY_CONVERT(INT, SESSION_CONTEXT(N'UsuarioID'));

    IF @UsuarioSolicitanteID IS NULL
        SET @UsuarioSolicitanteID = 1;

    SELECT
        @TipoAutorizacionID = TipoAutorizacionID,
        @ModuloID = ModuloID,
        @AccionID = AccionID
    FROM dbo.Usuario_TiposAutorizacion
    WHERE CodigoTipoAutorizacion = @TipoAutorizacionCodigo
      AND Activo = 1;

    IF @TipoAutorizacionID IS NULL
    BEGIN
        RAISERROR('Tipo de autorizacion no existe o esta inactivo.',16,1);
        RETURN;
    END

    SELECT @NivelFinalRequerido = MAX(NivelAutorizacion)
    FROM dbo.Usuario_MatrizAutorizacion
    WHERE TipoAutorizacionID = @TipoAutorizacionID
      AND Activo = 1
      AND (
            @Monto IS NULL
            OR (
                (MontoMinimo IS NULL OR @Monto >= MontoMinimo)
                AND (MontoMaximo IS NULL OR @Monto <= MontoMaximo)
               )
          );

    INSERT INTO dbo.Usuario_Autorizaciones
    (
        FolioAutorizacion,
        TipoAutorizacionID,
        ModuloID,
        AccionID,
        EntidadNombre,
        EntidadID,
        FolioReferencia,
        UsuarioSolicitanteID,
        FechaSolicitud,
        Monto,
        MonedaID,
        Justificacion,
        EstatusAutorizacion,
        NivelActual,
        NivelFinalRequerido,
        Activo,
        CreatedAt,
        CreatedBy
    )
    VALUES
    (
        @FolioAutorizacion,
        @TipoAutorizacionID,
        @ModuloID,
        @AccionID,
        @EntidadNombre,
        @EntidadID,
        @FolioReferencia,
        @UsuarioSolicitanteID,
        SYSDATETIME(),
        @Monto,
        @MonedaID,
        @Justificacion,
        'PENDIENTE',
        1,
        @NivelFinalRequerido,
        1,
        SYSDATETIME(),
        CONVERT(VARCHAR(100), @UsuarioSolicitanteID)
    );

    SET @AutorizacionID = SCOPE_IDENTITY();

    INSERT INTO dbo.Usuario_AutorizacionesDetalle
    (
        AutorizacionID,
        NivelAutorizacion,
        UsuarioAutorizadorID,
        RolID,
        FechaAsignacion,
        Resultado,
        Activo
    )
    SELECT
        @AutorizacionID,
        MA.NivelAutorizacion,
        ISNULL(MA.UsuarioID, URA.UsuarioID) AS UsuarioAutorizadorID,
        MA.RolID,
        SYSDATETIME(),
        'PENDIENTE',
        1
    FROM dbo.Usuario_MatrizAutorizacion MA
    OUTER APPLY
    (
        SELECT TOP 1 URX.UsuarioID
        FROM dbo.Usuario_RolesAsignacion URX
        WHERE URX.RolID = MA.RolID
          AND URX.Activo = 1
        ORDER BY URX.EsPrincipal DESC, URX.UsuarioRolAsignacionID
    ) URA
    WHERE MA.TipoAutorizacionID = @TipoAutorizacionID
      AND MA.Activo = 1
      AND (
            @Monto IS NULL
            OR (
                (MA.MontoMinimo IS NULL OR @Monto >= MA.MontoMinimo)
                AND (MA.MontoMaximo IS NULL OR @Monto <= MA.MontoMaximo)
               )
          );

    EXEC dbo.sp_Usuario_LogActividad
        @UsuarioID = @UsuarioSolicitanteID,
        @ModuloCodigo = NULL,
        @AccionCodigo = 'AUTORIZAR',
        @EntidadNombre = @EntidadNombre,
        @EntidadID = @EntidadID,
        @FolioReferencia = @FolioReferencia,
        @ResumenActividad = 'Solicitud de autorizacion creada',
        @DetalleActividad = @Justificacion,
        @Resultado = 'OK',
        @Criticidad = 'ALTA';
END
```

```sql
CREATE PROCEDURE dbo.sp_Usuario_ResolverAutorizacion
    @AutorizacionID BIGINT,
    @UsuarioAutorizadorID INT = NULL,
    @Resultado VARCHAR(20),
    @Comentarios VARCHAR(2000) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @NivelPendiente SMALLINT;
    DECLARE @NivelFinalRequerido SMALLINT;
    DECLARE @EntidadNombre VARCHAR(100);
    DECLARE @EntidadID VARCHAR(100);
    DECLARE @FolioReferencia VARCHAR(50);

    IF @UsuarioAutorizadorID IS NULL
        SELECT @UsuarioAutorizadorID = TRY_CONVERT(INT, SESSION_CONTEXT(N'UsuarioID'));

    IF @UsuarioAutorizadorID IS NULL
        SET @UsuarioAutorizadorID = 1;

    SELECT
        @NivelFinalRequerido = NivelFinalRequerido,
        @EntidadNombre = EntidadNombre,
        @EntidadID = EntidadID,
        @FolioReferencia = FolioReferencia
    FROM dbo.Usuario_Autorizaciones
    WHERE AutorizacionID = @AutorizacionID;

    SELECT TOP 1
        @NivelPendiente = NivelAutorizacion
    FROM dbo.Usuario_AutorizacionesDetalle
    WHERE AutorizacionID = @AutorizacionID
      AND UsuarioAutorizadorID = @UsuarioAutorizadorID
      AND Resultado = 'PENDIENTE'
      AND Activo = 1
    ORDER BY NivelAutorizacion;

    IF @NivelPendiente IS NULL
    BEGIN
        RAISERROR('No hay autorizacion pendiente para este usuario.',16,1);
        RETURN;
    END

    UPDATE dbo.Usuario_AutorizacionesDetalle
    SET
        FechaResolucion = SYSDATETIME(),
        Resultado = @Resultado,
        Comentarios = @Comentarios,
        IPResolucion = CONVERT(VARCHAR(64), SESSION_CONTEXT(N'IPOrigen'))
    WHERE AutorizacionID = @AutorizacionID
      AND UsuarioAutorizadorID = @UsuarioAutorizadorID
      AND NivelAutorizacion = @NivelPendiente
      AND Resultado = 'PENDIENTE';

    IF @Resultado = 'RECHAZADA'
    BEGIN
        UPDATE dbo.Usuario_Autorizaciones
        SET
            EstatusAutorizacion = 'RECHAZADA',
            FechaResolucionFinal = SYSDATETIME(),
            UsuarioResolucionFinalID = @UsuarioAutorizadorID,
            ComentariosResolucionFinal = @Comentarios
        WHERE AutorizacionID = @AutorizacionID;
    END
    ELSE
    BEGIN
        IF NOT EXISTS
        (
            SELECT 1
            FROM dbo.Usuario_AutorizacionesDetalle
            WHERE AutorizacionID = @AutorizacionID
              AND Resultado = 'PENDIENTE'
              AND Activo = 1
        )
        BEGIN
            UPDATE dbo.Usuario_Autorizaciones
            SET
                EstatusAutorizacion = 'AUTORIZADA',
                FechaResolucionFinal = SYSDATETIME(),
                UsuarioResolucionFinalID = @UsuarioAutorizadorID,
                ComentariosResolucionFinal = @Comentarios,
                NivelActual = ISNULL(@NivelFinalRequerido, NivelActual)
            WHERE AutorizacionID = @AutorizacionID;
        END
        ELSE
        BEGIN
            UPDATE dbo.Usuario_Autorizaciones
            SET
                EstatusAutorizacion = 'EN_PROCESO',
                NivelActual = ISNULL(@NivelPendiente,1) + 1
            WHERE AutorizacionID = @AutorizacionID;
        END
    END

    EXEC dbo.sp_Usuario_LogActividad
        @UsuarioID = @UsuarioAutorizadorID,
        @ModuloCodigo = NULL,
        @AccionCodigo = 'AUTORIZAR',
        @EntidadNombre = @EntidadNombre,
        @EntidadID = @EntidadID,
        @FolioReferencia = @FolioReferencia,
        @ResumenActividad = 'Resolucion de autorizacion',
        @DetalleActividad = @Comentarios,
        @Resultado = 'OK',
        @Criticidad = 'ALTA';
END
```

## D. Current behavior, consumers, and writers

### Contract

| Procedure | Inputs and outputs | Result sets / return |
| --- | --- | --- |
| Create | Preserves all ten parameters; `@AutorizacionID bigint OUTPUT` is the only output parameter. | No result set; no explicit integer return. |
| Resolve | Preserves four parameters; no output parameter. | No result set; no explicit integer return. |

The current create procedure raises for an inactive/missing type; resolve
raises when the designated user has no pending detail. Other SQL failures are
unhandled. `sp_Usuario_LogActividad` emits no result set.

### Fallback and `OMITIDA`

- Both SPs resolve the explicit user from `SESSION_CONTEXT(N'UsuarioID')` when
  their optional user argument is null, then fall back to **`UsuarioID = 1`**.
- Resolve treats `RECHAZADA` specially and routes every other value, including
  `OMITIDA` and arbitrary strings, through the positive path.
- Slice 1 decision: accept only `AUTORIZADA` and `RECHAZADA`; reject
  `OMITIDA` as an input with no mutation until a canonical semantic is
  separately defined.

### Consumers and direct writers

- Versioned repository consumers of either SP: **none** (`PRODUCTIVE=0`,
  `TEST=0`, `MIGRACION=0`, `VALIDACION=0`, `LEGACY=0`,
  `DOCUMENTACION=0`).
- Runtime direct writers of `dbo.Usuario_Autorizaciones`:
  `dbo.sp_Usuario_CrearAutorizacion`,
  `dbo.TR_Venta_Cotizaciones_Autorizacion_U`, and
  `dbo.TR_Venta_Pedidos_Autorizacion_U`.
- Runtime direct writers of `dbo.Usuario_AutorizacionesDetalle`:
  those same two triggers, `dbo.sp_Usuario_CrearAutorizacion`, and
  `dbo.sp_Usuario_ResolverAutorizacion`.
- The triggers do not call the two Slice 1 SPs and are out of scope. Therefore
  `SINGLE_WRITE_PATH=NO`; this Slice must not claim otherwise.

## E. Atomicity and concurrency evidence

| Procedure | Current atomicity | Current concurrency gap |
| --- | --- | --- |
| Create | Header insert, detail insert, and activity log execute without `XACT_ABORT`, `TRY/CATCH`, or an explicit transaction. A failure can leave a header without details or committed data without activity log. | Only the unique folio index exists. There is no transaction, `UPDLOCK`, `HOLDLOCK`, `SERIALIZABLE`, `ROWLOCK`, or rowversion. |
| Resolve | Detail update, parent update, and activity log execute without `XACT_ABORT`, `TRY/CATCH`, or an explicit transaction. A failure can leave the detail and parent inconsistent. | It selects a pending detail and later updates it with `Resultado='PENDIENTE'`, but does not lock, check `@@ROWCOUNT`, or serialize the global next-level decision. |

`DOUBLE_RESOLUTION_CURRENTLY_POSSIBLE=YES` and
`DOUBLE_LEVEL_ADVANCE_CURRENTLY_POSSIBLE=YES`. The runtime tables do not have
rowversion. Existing relevant keys include the primary keys and the unique
`UQ_Usuario_Autorizaciones_FolioAutorizacion`; no existing index removes the
two resolution races.

## F. Final Slice 1 scope and exact implementation plan

Only replace the definitions of:

1. `dbo.sp_Usuario_CrearAutorizacion`
2. `dbo.sp_Usuario_ResolverAutorizacion`

Preserve both signatures, valid output shape, valid transition semantics, and
the canonical authorization path:

`Usuario -> Rol -> TES_PAGOS/AUTORIZAR permission -> Usuario_RolesContexto ->
Empresa/Unidad -> Usuario_MatrizAutorizacion -> level/monto/prioridad/
mancomunacion`.

The slice hardens the existing procedures; it does not define or seed the
matrix, RBAC permission, contextual configuration, or a new authorization
engine.

### Create procedure

1. Resolve the explicit or session-context requester; if absent, nonexistent,
   or inactive, `THROW` before mutation. Remove the `UsuarioID=1` fallback.
2. Validate active type, applicable matrix rows, and active resolved
   authorizer before inserting.
3. Use `SET XACT_ABORT ON`, `TRY/CATCH`, and one explicit transaction for the
   header, all details, and activity log. Roll back on every failure and
   rethrow.
4. Preserve `@AutorizacionID OUTPUT`, emit no result set, and verify coherent
   header/detail postconditions before commit.

### Resolve procedure

1. Resolve the explicit or session-context authorizer; fail closed if absent,
   nonexistent, or inactive. Remove the `UsuarioID=1` fallback.
2. Validate `@Resultado IN ('AUTORIZADA', 'RECHAZADA')`; reject `OMITIDA` and
   arbitrary values before mutation.
3. Use `SET XACT_ABORT ON`, `TRY/CATCH`, and one explicit transaction for
   detail, parent status, and activity log.
4. Lock the parent and applicable pending details with `UPDLOCK,HOLDLOCK`;
   serialize selection of the globally next pending level; issue a conditional
   detail update and require `@@ROWCOUNT = 1`.
5. Update the parent only after that successful detail change and preserve the
   terminal/nonterminal status contract. Roll back and throw for every
   inconsistency.

## G. Proposed artifacts, rollback, and tests

The current real sequence ends at `20260818_031`; none of the following names
exists, so all are collision-free:

```text
MIGRATION_FILE_PROPOSED=backend/database/migrations/20260819_032_usuario_autorizaciones_atomicas.sql
ROLLBACK_FILE_PROPOSED=backend/database/rollback/20260819_032_usuario_autorizaciones_atomicas_rollback.sql
VALIDATION_FILE_PROPOSED=backend/database/validation/20260819_032_usuario_autorizaciones_atomicas_validation.sql
TEST_FILE_PROPOSED=backend/tests/test_usuario_autorizaciones_atomicas_contract.py
```

The migration must be idempotent and use `CREATE OR ALTER PROCEDURE` only for
the two approved objects. The rollback must restore the definitions in section
C, then read the runtime definitions and require the exact section-B hashes.
Neither artifact may alter tables, data, roles, permissions, or triggers.

The validation SQL is read-only and must verify: both procedures exist; their
expected definitions and preconditions; absence of the fallback
`UsuarioID=1`; closed result validation; `OMITIDA` rejection; presence of
`XACT_ABORT`, `TRY/CATCH`, transaction, lock, and conditional-update guards;
and absence of unexpected schema objects.

The focused contract test covers:

- Create: valid requester; missing/inactive requester; missing matrix;
  missing/inactive authorizer; multiple candidates; intermediate write failure;
  valid-output compatibility.
- Resolve: `AUTORIZADA`; `RECHAZADA`; `OMITIDA`; arbitrary result; invalid
  authorizer; missing authorization/detail; already-resolved detail;
  final authorization; double resolution; double level advance; intermediate
  failure with rollback.

## H. Explicit exclusions and later slices

Do **not** create or modify tables, columns, indexes, roles, permissions,
authorization types, queues, endpoints, frontend components, workers,
triggers, or alternate data sources. In particular, Slice 1 does not create
or change `Usuario_Autorizaciones`, `Usuario_AutorizacionesDetalle`,
`Usuario_MatrizAutorizacion`, `Usuario_RolesAsignacion`,
`Usuario_RolesContexto`, or `dbo.Unidades_Negocio`.

Pending later slices are: canonical `AUT_TES_PAGOS` matrix and
`TES_PAGOS/AUTORIZAR` permissions; company/unit contextual configuration;
CxP integration and economic guardrail; queue consumer; frontend flow; and
separate treatment of runtime trigger writers.

## I. Execution gate

```text
HRLECTURA_IDENTITY_OK=YES
SP_RUNTIME_EVIDENCE_REPRODUCED=YES
TRANSACTION_GAPS_CONFIRMED=YES
CONCURRENCY_GAPS_CONFIRMED=YES
VALIDATION_PLAN_READY=YES
SLICE_1_IMPLEMENTATION_PLAN_READY=YES
IMPLEMENTATION_AUTHORIZED=NO
BLOCKERS=NONE
NEXT=WAIT_FOR_SLICE_1_IMPLEMENTATION_AUTHORIZATION
```

## J. Implementation continuity (2026-08-19)

```text
CURRENT_SUBSTEP=RECOVERED_AFTER_INTERRUPTION
COMPLETED_FILES=backend/database/migrations/20260819_032_usuario_autorizaciones_atomicas.sql
PARTIAL_FILES=backend/database/validation/20260819_032_usuario_autorizaciones_atomicas_validation.sql,backend/tests/test_usuario_autorizaciones_atomicas_contract.py
NEXT_UNFINISHED_ACTION=Complete the existing validation and contract test, then create backend/database/rollback/20260819_032_usuario_autorizaciones_atomicas_rollback.sql.
IMPLEMENTATION_AUTHORIZED=YES
```

## K. Runtime precondition and differential audit resolution (2026-08-19)

The differential audit confirmed there is NO runtime drift in the stored procedures:
- `SP_CREATE_DRIFT=NO`
- `SP_RESOLVE_DRIFT=NO`

The initial hash discrepancy was diagnosed and resolved as a representation difference:
- T-SQL `HASHBYTES('SHA2_256', CONVERT(VARBINARY(MAX), @nvarchar))` evaluated UTF-16LE 2-byte characters (`2C459497CB5D1B33A4FB6DF20EADB32EFF913AEB31BB52E1897B36215AC25CC8` and `09D2ABEFE525E0E603B6041DB2F0E7F143672210914DAB5DDEE1ADEB0E5FD208`).
- Canonical convention is established as `VARCHAR(MAX)` representation (`36686195682c3e0bef6f6aca9733d27e6622a6cf94c78ed6ff881626b595104e` and `55dc7c243af010a4004e396f14b21f2946599648948bff53f244587b888f2b22`).
- The rollback script `backend/database/rollback/20260819_032_usuario_autorizaciones_atomicas_rollback.sql` has undergone surgical rebase with the 100% exact runtime definitions and canonicalized hash verification.

```text
CURRENT_SUBSTEP=SLICE_1_COMPLETE
SP_CREATE_DRIFT=NO
SP_RESOLVE_DRIFT=NO
ROLLBACK_DEFINITION_EXACT_MATCH=YES
HASH_CONVENTION_CANONICAL=YES
SQL_WRITE_EXECUTED=YES
MIGRATION_EXECUTED=YES
VALIDATION_EXECUTED=YES
TESTS=PASSED
ROLLBACK_EXECUTED=NO
SLICE_1_COMPLETE=YES
NEXT=WAIT_FOR_SLICE_2_AUTHORIZATION
```

## L. Execution and Validation Summary (2026-08-19)

- Migration `backend/database/migrations/20260819_032_usuario_autorizaciones_atomicas.sql` executed with canonical runner (`edarsahub_sql_runner.py`).
- Validation `backend/database/validation/20260819_032_usuario_autorizaciones_atomicas_validation.sql` executed and PASSED.
- Pre- and Post-migration hashes (canonical VARCHAR SHA-256):
  - `HASH_BEFORE_CREATE=36686195682c3e0bef6f6aca9733d27e6622a6cf94c78ed6ff881626b595104e`
  - `HASH_AFTER_CREATE=6a2cf1ef26c5cba335476e62ff4e678438b3d4c1b942938b2340cb38c5edfda4`
  - `HASH_BEFORE_RESOLVE=55dc7c243af010a4004e396f14b21f2946599648948bff53f244587b888f2b22`
  - `HASH_AFTER_RESOLVE=847d46efd9b94953ed070391aeee13c26da8a6a2aaa84e42bd23e7c595f73277`
- Stored procedure contract hardened:
  - Fallback `UsuarioID = 1` removed from both `sp_Usuario_CrearAutorizacion` and `sp_Usuario_ResolverAutorizacion`.
  - Fail-closed validation for active user, matrix, authorizers, and valid result (`AUTORIZADA`/`RECHAZADA`).
  - `OMITIDA` blocked without mutation.
  - Full transactional atomicity (`SET XACT_ABORT ON`, `TRY/CATCH`, `BEGIN TRANSACTION`, `COMMIT`/`ROLLBACK`).
  - Concurrency concurrency guards added (`WITH (UPDLOCK, HOLDLOCK)`, `MIN(NivelAutorizacion)`, `@@ROWCOUNT = 1`).
- Focused tests passed: `pytest backend/tests/test_usuario_autorizaciones_atomicas_contract.py` (3 passed).
- Regression tests passed: `pytest backend/tests/test_cxp_decision_dashboard_contract.py` (7 passed).
- No new tables, columns, roles, or permissions created. No schema modifications outside the two designated stored procedures.
