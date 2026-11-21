"""
EDARSA HUB - Cuentas por Pagar (Facturas Pendientes)
=====================================================
Módulo para gestionar facturas pendientes de pago agrupadas por proveedor.
PROTEGIDO CON RBAC (Fase 3.1)

V1.0: lectura SQL-first no-live desde dbo.Finanzas_CxP_Sync
- Decisiones de pago en dbo.Finanzas_CxP_DecisionesPago
- Sin demo, MongoDB ni conexiones live en endpoints

Datos a mostrar:
1. Número de documento / Folio
2. Proveedor
3. Sucursal
4. Fecha de documento
5. Fecha de vencimiento
6. Días vencido
7. Monto original
8. Monto pagado
9. Saldo pendiente
10. Estatus de pago
"""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional
from urllib.parse import unquote
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from core.security import get_current_user
from core.sql_first.db import fetch_all_dict, execute_sql
from modules.finanzas.access import (
    FINANZAS_ADMINISTRAR,
    FINANZAS_EDITAR,
    FINANZAS_VER,
    require_any_finanzas_permission,
    resolve_finanzas_unit_filter,
)

router = APIRouter(prefix="/finanzas/cuentas-por-pagar", tags=["Cuentas por Pagar"])


# ============================================================================
# COMPATIBILIDAD SERVER.PY
# ============================================================================

def set_finanzas_repository(_repo):
    """Hook legacy: CxP V1.0 no usa repos runtime en endpoints."""
    return None

def set_mpro_repository(_repo):
    """Hook legacy: la lectura funcional viene de dbo.Finanzas_CxP_Sync."""
    return None

def set_softrestaurant_repository(_repo):
    """Hook legacy: la lectura funcional viene de dbo.Finanzas_CxP_Sync."""
    return None

# ============================================================================
# LECTURA NO-LIVE (CANÓNICA) · dbo.Finanzas_CxP_Sync
# La pantalla de CxP lee EXCLUSIVAMENTE de esta tabla, poblada por el job
# core/scheduler/jobs/cxp_sync_job.py (registrado en el scheduler).
# ============================================================================
def _cxp_decisiones_schema_ready() -> bool:
    rows = fetch_all_dict(
        """
        SELECT CASE WHEN
            OBJECT_ID('dbo.Finanzas_CxP_DecisionesPago', 'U') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'HashOrigen') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'DecisionPago') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'ImporteAPagar') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'UnidadNegocioID') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_DecisionesPago', 'EstadoAutorizacion') IS NOT NULL
        THEN 1 ELSE 0 END AS listo
        """
    )
    return bool(rows and rows[0].get("listo"))


def _cxp_queue_schema_ready() -> bool:
    rows = fetch_all_dict(
        """
        SELECT CASE WHEN
            OBJECT_ID('dbo.Finanzas_CxP_PagosOrigenQueue', 'U') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_PagosOrigenQueue', 'DecisionPagoID') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_PagosOrigenQueue', 'HashOrigen') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_PagosOrigenQueue', 'ImporteAPagar') IS NOT NULL
            AND COL_LENGTH('dbo.Finanzas_CxP_PagosOrigenQueue', 'EstadoEnvio') IS NOT NULL
        THEN 1 ELSE 0 END AS listo
        """
    )
    return bool(rows and rows[0].get("listo"))


def _cxp_decision_projection():
    if not _cxp_decisiones_schema_ready():
        return (
            ", CAST(0 AS bit) AS DecisionPagoCanonica, "
            "CAST(0 AS decimal(18,2)) AS ImporteAPagarCanonico, "
            "CAST(NULL AS bigint) AS DecisionPagoIDCanonica, "
            "CAST(NULL AS datetime2) AS FechaDecisionPago, "
            "CAST('SIN_DECISION' AS nvarchar(30)) AS EstadoAutorizacionPago",
            "",
        )

    return (
        ", ISNULL(d.DecisionPago, 0) AS DecisionPagoCanonica, "
        "ISNULL(d.ImporteAPagar, 0) AS ImporteAPagarCanonico, "
        "d.DecisionPagoID AS DecisionPagoIDCanonica, "
        "d.FechaDecision AS FechaDecisionPago, "
        "ISNULL(d.EstadoAutorizacion, 'SIN_DECISION') AS EstadoAutorizacionPago",
        "LEFT JOIN dbo.Finanzas_CxP_DecisionesPago d "
        "  ON d.HashOrigen = c.HashOrigen AND ISNULL(d.Activo, 1) = 1",
    )


def _cxp_require_decisiones_schema():
    if _cxp_decisiones_schema_ready():
        return
    raise HTTPException(
        status_code=409,
        detail=(
            "Falta la tabla canonica dbo.Finanzas_CxP_DecisionesPago. "
            "Revise y aplique la migracion "
            "backend/database/migrations/20260722_001_finanzas_cxp_decisiones_pago.sql; "
            "no se registro la decision."
        ),
    )


def _cxp_require_queue_schema():
    if _cxp_queue_schema_ready():
        return
    raise HTTPException(
        status_code=409,
        detail=(
            "Falta la cola canonica dbo.Finanzas_CxP_PagosOrigenQueue. "
            "Revise y aplique la migracion "
            "backend/database/migrations/20260722_001_finanzas_cxp_decisiones_pago.sql; "
            "no se programo carga a origen."
        ),
    )


def _parse_cxp_factura_ref(factura_id: str):
    decoded = unquote(str(factura_id or "")).strip()
    payload = decoded[4:] if decoded.upper().startswith("CXP_") else decoded
    payload = payload.strip()

    if payload.isdigit():
        return "sync_id", int(payload), decoded

    lower = payload.lower()
    if len(lower) == 64 and all(ch in "0123456789abcdef" for ch in lower):
        return "hash", lower, decoded

    raise HTTPException(
        status_code=400,
        detail="Factura CxP no canonica. Use el identificador CXP_<id_sync> o CXP_<hash_origen>.",
    )


def _validar_fecha_corte(fecha_corte: Optional[str]) -> Optional[str]:
    if not fecha_corte:
        return None
    try:
        date.fromisoformat(str(fecha_corte))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="fecha_corte debe tener formato YYYY-MM-DD.") from exc
    return str(fecha_corte)


def _cxp_rows_canonico(
    unidad_negocio_pk=None,
    tipo=None,
    solo_vencidas=False,
    proveedor_id=None,
    fecha_corte=None,
    unidades_permitidas=None,
    cxp_sync_id=None,
    cxp_sync_ids=None,
    hash_origen=None,
    hash_origenes=None,
):
    where = ["c.Activo=1", "c.Saldo>0", "ISNULL(c.EsDemo,0)=0"]
    params = []

    ref_conditions = []
    if cxp_sync_id is not None:
        ref_conditions.append("c.CxpSyncID=%s")
        params.append(int(cxp_sync_id))
    if cxp_sync_ids:
        ids = [int(v) for v in cxp_sync_ids if v is not None]
        if ids:
            placeholders = ",".join(["%s"] * len(ids))
            ref_conditions.append(f"c.CxpSyncID IN ({placeholders})")
            params.extend(ids)
    if hash_origen:
        ref_conditions.append("c.HashOrigen=%s")
        params.append(str(hash_origen))
    if hash_origenes:
        hashes = [str(v) for v in hash_origenes if v]
        if hashes:
            placeholders = ",".join(["%s"] * len(hashes))
            ref_conditions.append(f"c.HashOrigen IN ({placeholders})")
            params.extend(hashes)
    if ref_conditions:
        where.append("(" + " OR ".join(ref_conditions) + ")")

    if unidad_negocio_pk and str(unidad_negocio_pk).lower() not in ("todas", "all", ""):
        where.append("CONVERT(varchar(36), u.id) = %s")
        params.append(str(unidad_negocio_pk))
    elif unidades_permitidas is not None:
        allowed = [str(u) for u in unidades_permitidas if u]
        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            where.append(f"CONVERT(varchar(36), u.id) IN ({placeholders})")
            params.extend(allowed)
        else:
            where.append("1=0")
    if tipo:
        where.append("c.TipoProveedor=%s")
        params.append(tipo)
    if proveedor_id:
        where.append("c.ProveedorID=%s")
        params.append(str(proveedor_id))
    fecha_corte_validada = _validar_fecha_corte(fecha_corte)
    if fecha_corte_validada:
        where.append("c.FechaEntrada <= %s")
        params.append(fecha_corte_validada)
    if solo_vencidas:
        where.append("c.DiasVencido>0")

    decision_select, decision_join = _cxp_decision_projection()
    sql = (
        "SELECT c.*, CONVERT(varchar(36), u.id) AS UnidadNegocioIDCanonica, "
        "u.codigo AS UnidadNegocioCodigoCanonico, u.nombre AS UnidadNegocioNombreCanonico "
        f"{decision_select} "
        "FROM dbo.Finanzas_CxP_Sync c "
        "INNER JOIN dbo.Unidades_Negocio u "
        "  ON UPPER(LTRIM(RTRIM(c.UnidadNegocio))) = UPPER(LTRIM(RTRIM(u.codigo))) "
        " AND ISNULL(u.activo, 1) = 1 "
        f"{decision_join} "
        "WHERE " + " AND ".join(where) + " ORDER BY c.Saldo DESC"
    )
    return fetch_all_dict(sql, tuple(params))


def _cxp_row_for_ref(factura_id: str, unidades_permitidas=None):
    kind, value, decoded = _parse_cxp_factura_ref(factura_id)
    rows = _cxp_rows_canonico(
        unidades_permitidas=unidades_permitidas,
        cxp_sync_id=value if kind == "sync_id" else None,
        hash_origen=value if kind == "hash" else None,
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Factura CxP no encontrada en la fuente canonica o fuera de alcance RBAC.",
        )
    return rows[0], decoded


def _cxp_rows_for_refs(facturas_ids: List[str], unidades_permitidas=None):
    parsed = [_parse_cxp_factura_ref(fid) for fid in facturas_ids]
    sync_ids = sorted({value for kind, value, _ in parsed if kind == "sync_id"})
    hashes = sorted({value for kind, value, _ in parsed if kind == "hash"})
    rows = _cxp_rows_canonico(
        unidades_permitidas=unidades_permitidas,
        cxp_sync_ids=sync_ids,
        hash_origenes=hashes,
    )
    found_sync_ids = {int(row.get("CxpSyncID")) for row in rows if row.get("CxpSyncID") is not None}
    found_hashes = {str(row.get("HashOrigen") or "").lower() for row in rows if row.get("HashOrigen")}
    missing = [
        decoded
        for kind, value, decoded in parsed
        if (kind == "sync_id" and value not in found_sync_ids)
        or (kind == "hash" and value not in found_hashes)
    ]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=(
                "Una o mas facturas CxP no existen en la fuente canonica "
                f"o quedan fuera del alcance RBAC: {missing[:5]}"
            ),
        )
    return rows


def _get_cxp_usuario_id(current_user: Dict[str, Any]) -> Optional[int]:
    value = (
        current_user.get("_sql_usuario_id")
        or current_user.get("UsuarioID")
        or current_user.get("usuario_id")
    )
    if isinstance(value, bool):
        return None
    try:
        usuario_id = int(value)
    except (TypeError, ValueError):
        return None
    return usuario_id if usuario_id > 0 else None


def _normalizar_importe_decision(row: Dict[str, Any], data: "ActualizarDecisionPago") -> Decimal:
    try:
        saldo = Decimal(str(row.get("Saldo") or "0"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=409, detail="Saldo canonico invalido para la factura CxP.") from exc

    if saldo <= 0:
        raise HTTPException(status_code=409, detail="La factura CxP no tiene saldo pendiente.")

    if not data.decision_pago:
        return Decimal("0.00")

    if data.importe_a_pagar is None:
        importe = saldo
    else:
        try:
            importe = Decimal(str(data.importe_a_pagar))
        except InvalidOperation as exc:
            raise HTTPException(status_code=400, detail="importe_a_pagar invalido.") from exc

    if importe <= 0:
        raise HTTPException(status_code=400, detail="importe_a_pagar debe ser mayor a cero.")
    if importe > saldo:
        raise HTTPException(status_code=400, detail="importe_a_pagar no puede exceder el saldo canonico.")

    return importe.quantize(Decimal("0.01"))


def _cxp_upsert_decision(row: Dict[str, Any], data: "ActualizarDecisionPago", current_user: Dict[str, Any]) -> Decimal:
    hash_origen = str(row.get("HashOrigen") or "").strip().lower()
    unidad_pk = str(row.get("UnidadNegocioIDCanonica") or "").strip()
    if not hash_origen:
        raise HTTPException(
            status_code=409,
            detail="La factura CxP canonica no tiene HashOrigen; no se puede persistir decision.",
        )
    if not unidad_pk:
        raise HTTPException(
            status_code=409,
            detail="La factura CxP canonica no tiene unidad_negocio_pk.",
        )

    importe = _normalizar_importe_decision(row, data)
    decision_bit = 1 if data.decision_pago else 0
    usuario_id = _get_cxp_usuario_id(current_user)
    cxp_sync_id = int(row.get("CxpSyncID"))
    decision_pago_id = row.get("DecisionPagoIDCanonica")
    decision_pago_id = int(decision_pago_id) if decision_pago_id else None
    _cxp_block_if_pago_origen_locked(decision_pago_id)

    execute_sql(
        """
        UPDATE dbo.Finanzas_CxP_DecisionesPago
        SET
            CxpSyncID = %s,
            UnidadNegocioID = CONVERT(uniqueidentifier, %s),
            DecisionPago = %s,
            ImporteAPagar = %s,
            UsuarioID = %s,
            EstadoAutorizacion = CASE WHEN %s = 1 THEN 'PENDIENTE_AUTORIZACION' ELSE 'CANCELADO' END,
            AutorizadoPorUsuarioID = NULL,
            FechaAutorizacion = NULL,
            RechazadoPorUsuarioID = NULL,
            FechaRechazo = NULL,
            ComentarioAutorizacion = NULL,
            Activo = 1,
            FechaDecision = SYSUTCDATETIME(),
            FechaModificacion = SYSUTCDATETIME()
        WHERE HashOrigen = %s
          AND Activo = 1;

        IF @@ROWCOUNT = 0
        BEGIN
            INSERT INTO dbo.Finanzas_CxP_DecisionesPago (
                HashOrigen,
                CxpSyncID,
                UnidadNegocioID,
                DecisionPago,
                ImporteAPagar,
                UsuarioID,
                EstadoAutorizacion,
                Activo,
                FechaDecision,
                FechaAlta
            )
            VALUES (
                %s,
                %s,
                CONVERT(uniqueidentifier, %s),
                %s,
                %s,
                %s,
                CASE WHEN %s = 1 THEN 'PENDIENTE_AUTORIZACION' ELSE 'CANCELADO' END,
                1,
                SYSUTCDATETIME(),
                SYSUTCDATETIME()
            );
        END;
        """,
        (
            cxp_sync_id,
            unidad_pk,
            decision_bit,
            str(importe),
            usuario_id,
            decision_bit,
            hash_origen,
            hash_origen,
            cxp_sync_id,
            unidad_pk,
            decision_bit,
            str(importe),
            usuario_id,
            decision_bit,
        ),
    )
    _cxp_cancel_queue_pendiente(decision_pago_id)
    return importe


def _cxp_decision_row_for_hash(hash_origen: str) -> Dict[str, Any]:
    rows = fetch_all_dict(
        """
        SELECT TOP 1
            DecisionPagoID,
            HashOrigen,
            CxpSyncID,
            CONVERT(varchar(36), UnidadNegocioID) AS UnidadNegocioID,
            DecisionPago,
            ImporteAPagar,
            EstadoAutorizacion,
            Activo
        FROM dbo.Finanzas_CxP_DecisionesPago
        WHERE HashOrigen = %s
          AND Activo = 1
        ORDER BY DecisionPagoID DESC
        """,
        (hash_origen,),
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No existe decision canonica de pago para la CxP seleccionada.",
        )
    return rows[0]


def _cxp_queue_estados_for_decision(decision_pago_id: Optional[int]) -> List[str]:
    if not decision_pago_id or not _cxp_queue_schema_ready():
        return []
    rows = fetch_all_dict(
        """
        SELECT EstadoEnvio
        FROM dbo.Finanzas_CxP_PagosOrigenQueue
        WHERE DecisionPagoID = %s
          AND Activo = 1
          AND EstadoEnvio IN ('PENDIENTE', 'ERROR', 'EN_PROCESO', 'ENVIADO')
        """,
        (int(decision_pago_id),),
    )
    return [str(row.get("EstadoEnvio") or "").upper() for row in rows]


def _cxp_block_if_pago_origen_locked(decision_pago_id: Optional[int]) -> None:
    estados = set(_cxp_queue_estados_for_decision(decision_pago_id))
    if estados.intersection({"EN_PROCESO", "ENVIADO"}):
        raise HTTPException(
            status_code=409,
            detail=(
                "La decision de pago ya esta en proceso o enviada a origen; "
                "no puede modificarse desde el tablero."
            ),
        )


def _cxp_cancel_queue_pendiente(decision_pago_id: Optional[int]) -> None:
    if not decision_pago_id or not _cxp_queue_schema_ready():
        return
    execute_sql(
        """
        UPDATE dbo.Finanzas_CxP_PagosOrigenQueue
        SET
            EstadoEnvio = 'CANCELADO',
            Activo = 0,
            FechaModificacion = SYSUTCDATETIME()
        WHERE DecisionPagoID = %s
          AND Activo = 1
          AND EstadoEnvio IN ('PENDIENTE', 'ERROR');
        """,
        (int(decision_pago_id),),
    )



CXP_AUTHORIZATION_TYPE_CODE = "AUT_TES_PAGOS"
CXP_AUTHORIZATION_ENTITY_NAME = "FINANZAS_CXP_DECISION_PAGO"


def _cxp_authorization_entity_id(
    decision: Dict[str, Any],
) -> str:
    decision_id = decision.get("DecisionPagoID")

    if decision_id is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "La decision de pago no tiene "
                "DecisionPagoID canonico."
            ),
        )

    return str(int(decision_id))


def _cxp_get_canonical_authorization(
    decision: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    entidad_id = _cxp_authorization_entity_id(decision)

    rows = fetch_all_dict(
        """
        SELECT TOP 2
            A.AutorizacionID,
            A.FolioAutorizacion,
            A.EstatusAutorizacion,
            A.ModoAutorizacion,
            A.NivelActual,
            A.NivelFinalRequerido,
            A.FechaSolicitud,
            A.FechaResolucionFinal,
            A.UsuarioResolucionFinalID,
            A.EntidadNombre,
            A.EntidadID,
            A.FolioReferencia
        FROM dbo.Usuario_Autorizaciones AS A
        INNER JOIN dbo.Usuario_TiposAutorizacion AS TA
            ON TA.TipoAutorizacionID = A.TipoAutorizacionID
        WHERE TA.CodigoTipoAutorizacion = %s
          AND TA.Activo = 1
          AND A.EntidadNombre = %s
          AND A.EntidadID = %s
          AND A.Activo = 1
        ORDER BY A.AutorizacionID DESC;
        """,
        (
            CXP_AUTHORIZATION_TYPE_CODE,
            CXP_AUTHORIZATION_ENTITY_NAME,
            entidad_id,
        ),
    )

    if not rows:
        return None

    if len(rows) != 1:
        raise HTTPException(
            status_code=409,
            detail=(
                "Existe mas de una autorizacion activa "
                "para la decision de pago."
            ),
        )

    return rows[0]



def _cxp_authorization_visibility(
    decision: Dict[str, Any],
    current_user: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Resuelve visibilidad operativa de AUT_TES_PAGOS.

    FINANZAS_ADMINISTRAR no sustituye al autorizador asignado.
    La fuente de verdad es Usuario_AutorizacionesDetalle.
    """
    authorization = _cxp_get_canonical_authorization(decision)

    empty = {
        "autorizacion_id": None,
        "estado_autorizacion_canonica": None,
        "modo_autorizacion": None,
        "nivel_actual": None,
        "nivel_final_requerido": None,
        "usuario_autorizador_id": None,
        "nivel_autorizacion": None,
        "resultado_detalle": None,
        "es_autorizador_actual": False,
        "puede_resolver_autorizacion": False,
    }

    if not authorization:
        return empty

    usuario_id = (
        _get_cxp_usuario_id(current_user)
        if current_user
        else None
    )

    autorizacion_id = authorization.get("AutorizacionID")

    if autorizacion_id is None:
        return {
            **empty,
            "estado_autorizacion_canonica":
                authorization.get("EstatusAutorizacion"),
            "modo_autorizacion":
                authorization.get("ModoAutorizacion"),
            "nivel_actual":
                authorization.get("NivelActual"),
            "nivel_final_requerido":
                authorization.get("NivelFinalRequerido"),
        }

    rows = fetch_all_dict(
        """
        SELECT
            D.UsuarioAutorizadorID,
            D.NivelAutorizacion,
            D.Resultado,
            D.Activo
        FROM dbo.Usuario_AutorizacionesDetalle AS D
        WHERE D.AutorizacionID = %s
          AND D.Activo = 1
        ORDER BY
            D.NivelAutorizacion ASC,
            D.AutorizacionDetalleID ASC;
        """,
        (int(autorizacion_id),),
    )

    user_row = None

    if usuario_id is not None:
        for detail in rows:
            if int(detail.get("UsuarioAutorizadorID") or 0) == int(usuario_id):
                user_row = detail
                break

    estado = str(
        authorization.get("EstatusAutorizacion") or ""
    ).upper()

    resultado = (
        str(user_row.get("Resultado") or "").upper()
        if user_row
        else None
    )

    puede_resolver = bool(
        user_row
        and resultado == "PENDIENTE"
        and estado in ("PENDIENTE", "EN_PROCESO")
    )

    return {
        "autorizacion_id": autorizacion_id,
        "estado_autorizacion_canonica":
            authorization.get("EstatusAutorizacion"),
        "modo_autorizacion":
            authorization.get("ModoAutorizacion"),
        "nivel_actual":
            authorization.get("NivelActual"),
        "nivel_final_requerido":
            authorization.get("NivelFinalRequerido"),
        "usuario_autorizador_id": (
            user_row.get("UsuarioAutorizadorID")
            if user_row
            else None
        ),
        "nivel_autorizacion": (
            user_row.get("NivelAutorizacion")
            if user_row
            else None
        ),
        "resultado_detalle": resultado,
        "es_autorizador_actual": bool(user_row),
        "puede_resolver_autorizacion": puede_resolver,
    }


def _cxp_create_canonical_authorization(
    row: Dict[str, Any],
    decision: Dict[str, Any],
    current_user: Dict[str, Any],
) -> Dict[str, Any]:
    existing = _cxp_get_canonical_authorization(decision)

    if existing:
        return existing

    usuario_id = _get_cxp_usuario_id(current_user)

    unidad_id = str(
        row.get("UnidadNegocioIDCanonica") or ""
    ).strip()

    if not unidad_id:
        raise HTTPException(
            status_code=409,
            detail=(
                "La factura no tiene UnidadNegocioID "
                "canonica resoluble."
            ),
        )

    try:
        importe = Decimal(
            str(decision.get("ImporteAPagar") or "0")
        )
    except InvalidOperation as exc:
        raise HTTPException(
            status_code=409,
            detail="Importe canonico de pago invalido.",
        ) from exc

    if importe <= 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "La decision de pago no tiene importe "
                "mayor a cero."
            ),
        )

    decision_id = _cxp_authorization_entity_id(decision)

    folio_referencia = str(
        row.get("FolioFactura")
        or row.get("FolioEntrada")
        or decision_id
    ).strip()[:50]

    folio_autorizacion = (
        f"CXP-{decision_id}-{usuario_id}"
    )[:30]

    justificacion = (
        "Autorizacion mancomunada de pago CxP "
        f"DecisionPagoID={decision_id}"
    )

    execute_sql(
        """
        DECLARE @AutorizacionID BIGINT;
        DECLARE @UnidadNegocioID UNIQUEIDENTIFIER;

        SET @UnidadNegocioID = CONVERT(
            UNIQUEIDENTIFIER,
            %s
        );

        EXEC dbo.sp_Usuario_CrearAutorizacion
            @FolioAutorizacion = %s,
            @TipoAutorizacionCodigo = %s,
            @EntidadNombre = %s,
            @EntidadID = %s,
            @FolioReferencia = %s,
            @UsuarioSolicitanteID = %s,
            @Monto = %s,
            @MonedaID = NULL,
            @Justificacion = %s,
            @UnidadNegocioID = @UnidadNegocioID,
            @AutorizacionID = @AutorizacionID OUTPUT;
        """,
        (
            unidad_id,
            folio_autorizacion,
            CXP_AUTHORIZATION_TYPE_CODE,
            CXP_AUTHORIZATION_ENTITY_NAME,
            decision_id,
            folio_referencia,
            usuario_id,
            str(importe),
            justificacion,
        ),
    )

    created = _cxp_get_canonical_authorization(decision)

    if not created:
        raise HTTPException(
            status_code=500,
            detail=(
                "La autorizacion fue creada pero no "
                "pudo resolverse posteriormente."
            ),
        )

    return created


def _cxp_resolve_canonical_authorization(
    decision: Dict[str, Any],
    autorizar: bool,
    comentario: Optional[str],
    current_user: Dict[str, Any],
) -> Dict[str, Any]:
    auth = _cxp_get_canonical_authorization(decision)

    if not auth:
        raise HTTPException(
            status_code=409,
            detail=(
                "La decision de pago no tiene una "
                "autorizacion canonica activa."
            ),
        )

    usuario_id = _get_cxp_usuario_id(current_user)

    resultado = (
        "AUTORIZADA"
        if autorizar
        else "RECHAZADA"
    )

    comentario_normalizado = (
        (comentario or "").strip()[:2000]
        or None
    )

    execute_sql(
        """
        EXEC dbo.sp_Usuario_ResolverAutorizacion
            @AutorizacionID = %s,
            @UsuarioAutorizadorID = %s,
            @Resultado = %s,
            @Comentarios = %s;
        """,
        (
            int(auth["AutorizacionID"]),
            usuario_id,
            resultado,
            comentario_normalizado,
        ),
    )

    refreshed = _cxp_get_canonical_authorization(decision)

    if not refreshed:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible recuperar la autorizacion "
                "despues de resolverla."
            ),
        )

    return refreshed


def _cxp_project_authorization_state(
    decision: Dict[str, Any],
    authorization: Dict[str, Any],
) -> str:
    auth_state = str(
        authorization.get("EstatusAutorizacion") or ""
    ).strip().upper()

    mapping = {
        "PENDIENTE": "PENDIENTE_AUTORIZACION",
        "EN_PROCESO": "PENDIENTE_AUTORIZACION",
        "AUTORIZADA": "AUTORIZADO",
        "RECHAZADA": "RECHAZADO",
    }

    projected = mapping.get(auth_state)

    if not projected:
        raise HTTPException(
            status_code=409,
            detail=(
                "Estado canonico de autorizacion no "
                f"proyectable: {auth_state!r}."
            ),
        )

    execute_sql(
        """
        UPDATE dbo.Finanzas_CxP_DecisionesPago
        SET
            EstadoAutorizacion = %s,
            FechaModificacion = SYSUTCDATETIME()
        WHERE DecisionPagoID = %s
          AND Activo = 1;
        """,
        (
            projected,
            int(decision["DecisionPagoID"]),
        ),
    )

    return projected


# LEGACY_DEPRECATED_CXP_AUTHORIZATION:
# Conservado temporalmente para rollback controlado.
def _cxp_update_autorizacion(
    decision: Dict[str, Any],
    autorizar: bool,
    comentario: Optional[str],
    current_user: Dict[str, Any],
) -> None:
    if not bool(decision.get("DecisionPago")):
        raise HTTPException(
            status_code=409,
            detail="La CxP no esta marcada para pago; no puede autorizarse.",
        )
    try:
        importe = Decimal(str(decision.get("ImporteAPagar") or "0"))
    except InvalidOperation as exc:
        raise HTTPException(status_code=409, detail="Importe canonico de pago invalido.") from exc
    if autorizar and importe <= 0:
        raise HTTPException(
            status_code=409,
            detail="La CxP no tiene importe a pagar mayor a cero.",
        )

    usuario_id = _get_cxp_usuario_id(current_user)
    comentario_normalizado = (comentario or "").strip()[:500] or None
    if autorizar:
        execute_sql(
            """
            UPDATE dbo.Finanzas_CxP_DecisionesPago
            SET
                EstadoAutorizacion = 'AUTORIZADO',
                AutorizadoPorUsuarioID = %s,
                FechaAutorizacion = SYSUTCDATETIME(),
                RechazadoPorUsuarioID = NULL,
                FechaRechazo = NULL,
                ComentarioAutorizacion = %s,
                FechaModificacion = SYSUTCDATETIME()
            WHERE DecisionPagoID = %s
              AND Activo = 1;
            """,
            (usuario_id, comentario_normalizado, int(decision["DecisionPagoID"])),
        )
        return

    execute_sql(
        """
        UPDATE dbo.Finanzas_CxP_DecisionesPago
        SET
            EstadoAutorizacion = 'RECHAZADO',
            AutorizadoPorUsuarioID = NULL,
            FechaAutorizacion = NULL,
            RechazadoPorUsuarioID = %s,
            FechaRechazo = SYSUTCDATETIME(),
            ComentarioAutorizacion = %s,
            FechaModificacion = SYSUTCDATETIME()
        WHERE DecisionPagoID = %s
          AND Activo = 1;
        """,
        (usuario_id, comentario_normalizado, int(decision["DecisionPagoID"])),
    )


def _cxp_enqueue_pago_origen(decision: Dict[str, Any], current_user: Dict[str, Any]) -> None:
    usuario_id = _get_cxp_usuario_id(current_user)
    _cxp_block_if_pago_origen_locked(int(decision["DecisionPagoID"]))
    execute_sql(
        """
        UPDATE dbo.Finanzas_CxP_PagosOrigenQueue
        SET
            CxpSyncID = %s,
            ImporteAPagar = %s,
            EstadoEnvio = 'PENDIENTE',
            UsuarioAutorizacionID = %s,
            UltimoError = NULL,
            FechaProgramada = SYSUTCDATETIME(),
            FechaModificacion = SYSUTCDATETIME()
        WHERE DecisionPagoID = %s
          AND Activo = 1
          AND EstadoEnvio IN ('PENDIENTE', 'ERROR');

        IF @@ROWCOUNT = 0
           AND NOT EXISTS (
                SELECT 1
                FROM dbo.Finanzas_CxP_PagosOrigenQueue
                WHERE DecisionPagoID = %s
                  AND Activo = 1
                  AND EstadoEnvio IN ('PENDIENTE', 'EN_PROCESO', 'ENVIADO')
           )
        BEGIN
            INSERT INTO dbo.Finanzas_CxP_PagosOrigenQueue (
                DecisionPagoID,
                HashOrigen,
                UnidadNegocioID,
                CxpSyncID,
                ImporteAPagar,
                EstadoEnvio,
                FechaProgramada,
                UsuarioAutorizacionID,
                Activo,
                FechaAlta
            )
            VALUES (
                %s,
                %s,
                CONVERT(uniqueidentifier, %s),
                %s,
                %s,
                'PENDIENTE',
                SYSUTCDATETIME(),
                %s,
                1,
                SYSUTCDATETIME()
            );
        END;
        """,
        (
            decision.get("CxpSyncID"),
            str(decision.get("ImporteAPagar") or "0"),
            usuario_id,
            int(decision["DecisionPagoID"]),
            int(decision["DecisionPagoID"]),
            int(decision["DecisionPagoID"]),
            str(decision.get("HashOrigen") or "").lower(),
            str(decision.get("UnidadNegocioID") or ""),
            decision.get("CxpSyncID"),
            str(decision.get("ImporteAPagar") or "0"),
            usuario_id,
        ),
    )


def _cxp_factura_dict(r, current_user=None):
    dias = int(r.get('DiasVencido') or 0)
    saldo = float(r.get('Saldo') or 0)
    fe, fv = r.get('FechaEntrada'), r.get('FechaVencimiento')
    decision = bool(r.get('DecisionPagoCanonica'))
    importe_decision = float(r.get('ImporteAPagarCanonico') or 0) if decision else 0.0
    hash_origen = str(r.get('HashOrigen') or '').strip()
    fecha_decision = r.get('FechaDecisionPago')
    estado_autorizacion = r.get('EstadoAutorizacionPago')
    if decision and not estado_autorizacion:
        estado_autorizacion = 'PENDIENTE_AUTORIZACION'
    return {
        "factura_id": f"CXP_{hash_origen or r.get('CxpSyncID')}",
        "factura_sync_id": r.get('CxpSyncID'),
        "proveedor_id": r.get('ProveedorID'),
        "proveedor_nombre": r.get('ProveedorNombre') or 'N/A',
        "proveedor_rfc": r.get('ProveedorRFC') or '',
        "tipo_proveedor": r.get('TipoProveedor') or 'X',
        "tipo_proveedor_nombre": r.get('TipoProveedorNombre') or 'OTROS',
        "sucursal_id": r.get('UnidadNegocioCodigoCanonico') or r.get('UnidadNegocio'),
        "sucursal_nombre": r.get('UnidadNegocioNombreCanonico') or r.get('UnidadNegocioNombre'),
        "unidad_negocio_pk": r.get('UnidadNegocioIDCanonica'),
        "unidad_negocio_codigo": r.get('UnidadNegocioCodigoCanonico') or r.get('UnidadNegocio'),
        "folio_entrada": r.get('FolioEntrada') or '-',
        "folio_factura": r.get('FolioFactura') or '-',
        "fecha_entrada": str(fe)[:10] if fe else None,
        "fecha_vencimiento": str(fv)[:10] if fv else '-',
        "referencia": r.get('Referencia') or '-',
        "dias_vencida": dias,
        "importe_original": float(r.get('MontoOriginal') or 0),
        "saldo": saldo,
        "por_vencer": saldo if dias <= 0 else 0,
        "venc_1_30": saldo if 1 <= dias <= 30 else 0,
        "venc_31_60": saldo if 31 <= dias <= 60 else 0,
        "venc_61_90": saldo if 61 <= dias <= 90 else 0,
        "venc_91_plus": saldo if dias > 90 else 0,
        "decision_pago": decision,
        "importe_a_pagar": importe_decision,
        "estado_autorizacion_pago": estado_autorizacion or 'SIN_DECISION',
        "requiere_autorizacion_pago": decision and estado_autorizacion != 'AUTORIZADO',
        "fecha_decision_pago": str(fecha_decision)[:19] if fecha_decision else None,
        "fuente": r.get('Fuente'),
        **(
            _cxp_authorization_visibility(
                {
                    "DecisionPagoID": r.get("DecisionPagoIDCanonica"),
                },
                current_user,
            )
            if decision
            and r.get("DecisionPagoIDCanonica")
            else {
                "autorizacion_id": None,
                "estado_autorizacion_canonica": None,
                "modo_autorizacion": None,
                "nivel_actual": None,
                "nivel_final_requerido": None,
                "usuario_autorizador_id": None,
                "nivel_autorizacion": None,
                "resultado_detalle": None,
                "es_autorizador_actual": False,
                "puede_resolver_autorizacion": False,
            }
        ),
    }


def _cxp_listar_canonico(unidad_negocio_pk, tipo, solo_vencidas, solo_decision_pago=False, proveedor_id=None, fecha_corte=None, unidades_permitidas=None, current_user=None):
    facturas = [
        _cxp_factura_dict(r, current_user)
        for r in _cxp_rows_canonico(
            unidad_negocio_pk,
            tipo,
            solo_vencidas,
            proveedor_id,
            fecha_corte,
            unidades_permitidas,
        )
    ]
    if solo_decision_pago:
        facturas = [f for f in facturas if f["decision_pago"]]
    nombres = {'A': 'ALIMENTOS', 'B': 'BEBIDAS', 'X': 'OTROS'}
    tipos = {}
    for f in facturas:
        t = f['tipo_proveedor']
        if t not in tipos:
            tipos[t] = {"proveedor_id": t, "proveedor_nombre": f"{t} - {nombres.get(t, 'OTROS')}",
                        "proveedor_rfc": "", "cantidad_facturas": 0, "subtotal_importe": 0.0,
                        "subtotal_saldo": 0.0, "subtotal_a_pagar": 0.0,
                        "cantidad_vencidas": 0, "facturas": []}
        g = tipos[t]
        g["facturas"].append(f); g["cantidad_facturas"] += 1
        g["subtotal_importe"] += f["importe_original"]; g["subtotal_saldo"] += f["saldo"]
        if f["decision_pago"]:
            g["subtotal_a_pagar"] += f["importe_a_pagar"]
        if f["dias_vencida"] > 0:
            g["cantidad_vencidas"] += 1
    provs = [tipos[t] for t in ['A', 'B', 'X'] if t in tipos]
    total_a_pagar = round(sum(p["subtotal_a_pagar"] for p in provs), 2)
    totales = {
        "total_saldo": round(sum(p["subtotal_saldo"] for p in provs), 2),
        "total_importe": round(sum(p["subtotal_importe"] for p in provs), 2),
        "total_a_pagar": total_a_pagar,
        "total_decision_pago": total_a_pagar,
        "total_proveedores": len(provs),
        "cantidad_facturas": sum(p["cantidad_facturas"] for p in provs),
        "cantidad_vencidas": sum(p["cantidad_vencidas"] for p in provs),
        "facturas_con_decision": sum(1 for f in facturas if f["decision_pago"]),
    }
    return {"fuente": "CANONICO_EDARSAHUB", "proveedores": provs,
            "total_facturas": totales["cantidad_facturas"], "totales": totales}


def _cxp_resumen_canonico(unidad_negocio_pk, unidades_permitidas=None):
    rows = _cxp_rows_canonico(
        unidad_negocio_pk,
        unidades_permitidas=unidades_permitidas,
    )
    b = {'c': [0, 0.0], 'v1': [0, 0.0], 'v2': [0, 0.0], 'v3': [0, 0.0], 'v4': [0, 0.0]}
    total = 0.0; n = 0; total_decision = 0.0; n_decision = 0
    for r in rows:
        s = float(r.get('Saldo') or 0); d = int(r.get('DiasVencido') or 0)
        if s <= 0:
            continue
        n += 1; total += s
        if bool(r.get('DecisionPagoCanonica')):
            total_decision += float(r.get('ImporteAPagarCanonico') or 0)
            n_decision += 1
        k = 'c' if d <= 0 else 'v1' if d <= 30 else 'v2' if d <= 60 else 'v3' if d <= 90 else 'v4'
        b[k][0] += 1; b[k][1] += s
    bk = lambda k: {"cantidad": b[k][0], "monto": round(b[k][1], 2)}
    return {"fuente": "CANONICO_EDARSAHUB",
            "resumen": {"total_facturas": n, "total_saldo": round(total, 2),
                        "total_decision_pago": round(total_decision, 2),
                        "facturas_con_decision": n_decision},
            "antiguedad": {"corriente": bk('c'), "vencidas_1_30": bk('v1'), "vencidas_31_60": bk('v2'),
                           "vencidas_61_90": bk('v3'), "vencidas_90_plus": bk('v4'),
                           "total_facturas": n, "total_saldo": round(total, 2)}}


def _month_span_inclusive(fecha_inicio: date, fecha_fin: date) -> int:
    """Cantidad de meses calendario tocados por un rango inclusivo."""
    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=400,
            detail="fecha_referencia_fin no puede ser anterior a fecha_referencia_inicio.",
        )

    return (
        (fecha_fin.year - fecha_inicio.year) * 12
        + fecha_fin.month
        - fecha_inicio.month
        + 1
    )


def _decision_dashboard_period(
    fecha_referencia_inicio: Optional[str],
    fecha_referencia_fin: Optional[str],
):
    """
    Default: mes calendario anterior.

    El backend es autoridad del periodo efectivo; frontend no calcula
    el rango por su cuenta.
    """
    if bool(fecha_referencia_inicio) != bool(fecha_referencia_fin):
        raise HTTPException(
            status_code=400,
            detail=(
                "Debe enviar fecha_referencia_inicio y fecha_referencia_fin "
                "juntas, o ninguna para usar el mes anterior."
            ),
        )

    if fecha_referencia_inicio and fecha_referencia_fin:
        try:
            inicio = date.fromisoformat(fecha_referencia_inicio)
            fin = date.fromisoformat(fecha_referencia_fin)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Las fechas de referencia deben usar formato YYYY-MM-DD.",
            ) from exc
    else:
        hoy = date.today()
        primer_dia_mes_actual = hoy.replace(day=1)
        fin = primer_dia_mes_actual - timedelta(days=1)
        inicio = fin.replace(day=1)

    meses = _month_span_inclusive(inicio, fin)

    return inicio, fin, meses


def _decision_dashboard_compras(
    unidad_negocio_pk,
    unidades_permitidas,
    fecha_inicio: date,
    fecha_fin: date,
):
    """
    Compras históricas materializadas en EDARSAHUB.

    Fuente V1:
        dbo.Compras_Recepciones

    No LIVE, no MongoDB, no datos demo.
    """
    where = [
        "ISNULL(r.Activo, 1) = 1",
        "r.FechaRecepcion >= %s",
        "r.FechaRecepcion < DATEADD(DAY, 1, %s)",
    ]
    params = [
        fecha_inicio.isoformat(),
        fecha_fin.isoformat(),
    ]

    if unidad_negocio_pk and str(unidad_negocio_pk).lower() not in (
        "",
        "all",
        "todas",
    ):
        where.append("CONVERT(varchar(36), r.unidad_negocio_pk) = %s")
        params.append(str(unidad_negocio_pk))

    elif unidades_permitidas is not None:
        allowed = [
            str(value)
            for value in unidades_permitidas
            if value
        ]

        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            where.append(
                "CONVERT(varchar(36), r.unidad_negocio_pk) "
                f"IN ({placeholders})"
            )
            params.extend(allowed)
        else:
            where.append("1=0")

    sql = (
        "SELECT "
        "  CONVERT(varchar(36), r.unidad_negocio_pk) AS unidad_negocio_pk, "
        "  u.codigo AS unidad_codigo, "
        "  u.nombre AS unidad_nombre, "
        "  COUNT_BIG(*) AS recepciones, "
        "  SUM(ISNULL(r.Total, 0)) AS total_compras "
        "FROM dbo.Compras_Recepciones r "
        "INNER JOIN dbo.Unidades_Negocio u "
        "  ON u.id = r.unidad_negocio_pk "
        " AND ISNULL(u.activo, 1) = 1 "
        "WHERE "
        + " AND ".join(where)
        + " GROUP BY r.unidad_negocio_pk, u.codigo, u.nombre "
          "ORDER BY total_compras DESC"
    )

    return fetch_all_dict(sql, tuple(params))


def _decision_dashboard_canonico(
    unidad_negocio_pk,
    unidades_permitidas,
    fecha_referencia_inicio=None,
    fecha_referencia_fin=None,
):
    inicio, fin, meses = _decision_dashboard_period(
        fecha_referencia_inicio,
        fecha_referencia_fin,
    )

    compras_rows = _decision_dashboard_compras(
        unidad_negocio_pk,
        unidades_permitidas,
        inicio,
        fin,
    )

    cxp_rows = _cxp_rows_canonico(
        unidad_negocio_pk,
        unidades_permitidas=unidades_permitidas,
    )

    compras_por_unidad = {}

    for row in compras_rows:
        unidad_id = str(row.get("unidad_negocio_pk") or "")
        total_periodo = float(row.get("total_compras") or 0)

        compras_por_unidad[unidad_id] = {
            "unidad_negocio_pk": unidad_id,
            "unidad_codigo": row.get("unidad_codigo"),
            "unidad_nombre": row.get("unidad_nombre"),
            "recepciones": int(row.get("recepciones") or 0),
            "compras_periodo": round(total_periodo, 2),
            "promedio_mensual_compras": round(
                total_periodo / meses,
                2,
            ),
        }

    comprometido_por_unidad = {}
    autorizado_por_unidad = {}
    saldo_por_unidad = {}

    for row in cxp_rows:
        unidad_id = str(
            row.get("UnidadNegocioIDCanonica")
            or ""
        )

        saldo = float(row.get("Saldo") or 0)
        saldo_por_unidad[unidad_id] = (
            saldo_por_unidad.get(unidad_id, 0.0)
            + saldo
        )

        if bool(row.get("DecisionPagoCanonica")):
            importe = float(
                row.get("ImporteAPagarCanonico")
                or saldo
                or 0
            )

            comprometido_por_unidad[unidad_id] = (
                comprometido_por_unidad.get(
                    unidad_id,
                    0.0,
                )
                + importe
            )

            if (
                str(
                    row.get(
                        "EstadoAutorizacionPago"
                    )
                    or ""
                ).upper()
                == "AUTORIZADO"
            ):
                autorizado_por_unidad[unidad_id] = (
                    autorizado_por_unidad.get(
                        unidad_id,
                        0.0,
                    )
                    + importe
                )

    all_units = set(compras_por_unidad)
    all_units.update(saldo_por_unidad)
    all_units.update(comprometido_por_unidad)
    all_units.update(autorizado_por_unidad)

    unidades = []

    for unidad_id in sorted(all_units):
        base = compras_por_unidad.get(
            unidad_id,
            {
                "unidad_negocio_pk": unidad_id,
                "unidad_codigo": None,
                "unidad_nombre": None,
                "recepciones": 0,
                "compras_periodo": 0.0,
                "promedio_mensual_compras": 0.0,
            },
        )

        limite = float(
            base["promedio_mensual_compras"]
            or 0
        )

        comprometido = float(
            comprometido_por_unidad.get(
                unidad_id,
                0.0,
            )
        )

        autorizado = float(
            autorizado_por_unidad.get(
                unidad_id,
                0.0,
            )
        )

        disponible = max(
            limite - comprometido,
            0.0,
        )

        utilizacion = (
            (comprometido / limite) * 100
            if limite > 0
            else None
        )

        unidades.append({
            **base,
            "saldo_cxp": round(
                saldo_por_unidad.get(
                    unidad_id,
                    0.0,
                ),
                2,
            ),
            "limite_pago": round(limite, 2),
            "comprometido": round(
                comprometido,
                2,
            ),
            "autorizado": round(
                autorizado,
                2,
            ),
            "disponible": round(
                disponible,
                2,
            ),
            "porcentaje_utilizado": (
                round(utilizacion, 2)
                if utilizacion is not None
                else None
            ),
            "excede_limite": (
                comprometido > limite
                if limite > 0
                else comprometido > 0
            ),
        })

    compras_periodo = sum(
        row["compras_periodo"]
        for row in unidades
    )
    limite_pago = sum(
        row["limite_pago"]
        for row in unidades
    )
    comprometido = sum(
        row["comprometido"]
        for row in unidades
    )
    autorizado = sum(
        row["autorizado"]
        for row in unidades
    )
    saldo_cxp = sum(
        row["saldo_cxp"]
        for row in unidades
    )

    disponible = max(
        limite_pago - comprometido,
        0.0,
    )

    porcentaje = (
        round(
            (comprometido / limite_pago) * 100,
            2,
        )
        if limite_pago > 0
        else None
    )

    return {
        "fuente": "CANONICO_EDARSAHUB",
        "fuente_compras": "dbo.Compras_Recepciones",
        "fuente_cxp": "dbo.Finanzas_CxP_Sync",
        "periodo_referencia": {
            "fecha_inicio": inicio.isoformat(),
            "fecha_fin": fin.isoformat(),
            "meses": meses,
            "default_mes_anterior": (
                not fecha_referencia_inicio
                and not fecha_referencia_fin
            ),
        },
        "resumen": {
            "compras_periodo": round(
                compras_periodo,
                2,
            ),
            "promedio_mensual_compras": round(
                limite_pago,
                2,
            ),
            "limite_pago": round(
                limite_pago,
                2,
            ),
            "saldo_cxp": round(
                saldo_cxp,
                2,
            ),
            "comprometido": round(
                comprometido,
                2,
            ),
            "autorizado": round(
                autorizado,
                2,
            ),
            "disponible": round(
                disponible,
                2,
            ),
            "porcentaje_utilizado": porcentaje,
            "excede_limite": (
                comprometido > limite_pago
                if limite_pago > 0
                else comprometido > 0
            ),
        },
        "unidades": unidades,
        "contrato": {
            "comprometido": (
                "Decisiones de pago activas CxP; "
                "todavia no equivale a pago bancario ejecutado."
            ),
            "limite": (
                "Promedio mensual de compras del periodo "
                "de referencia."
            ),
        },
    }



def _decision_dashboard_drilldown(
    unidad_negocio_pk,
    unidades_permitidas,
    fecha_referencia_inicio=None,
    fecha_referencia_fin=None,
    proveedor_id=None,
    limit=200,
):
    """
    Máximo detalle disponible actualmente:
    recepción/entrada individual de compra.

    No usa Compras_RecepcionesDetalle porque la tabla todavía
    no tiene cobertura operativa suficiente.
    """
    inicio, fin, meses = _decision_dashboard_period(
        fecha_referencia_inicio,
        fecha_referencia_fin,
    )

    where = [
        "ISNULL(r.Activo, 1) = 1",
        "r.FechaRecepcion >= %s",
        "r.FechaRecepcion < DATEADD(DAY, 1, %s)",
    ]

    params = [
        inicio.isoformat(),
        fin.isoformat(),
    ]

    if unidad_negocio_pk and str(unidad_negocio_pk).lower() not in (
        "",
        "all",
        "todas",
    ):
        where.append(
            "CONVERT(varchar(36), r.unidad_negocio_pk) = %s"
        )
        params.append(str(unidad_negocio_pk))

    elif unidades_permitidas is not None:
        allowed = [
            str(value)
            for value in unidades_permitidas
            if value
        ]

        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            where.append(
                "CONVERT(varchar(36), r.unidad_negocio_pk) "
                f"IN ({placeholders})"
            )
            params.extend(allowed)
        else:
            where.append("1=0")

    if proveedor_id not in (None, ""):
        where.append(
            "CONVERT(varchar(100), r.ProveedorID) = %s"
        )
        params.append(str(proveedor_id))

    safe_limit = max(
        1,
        min(int(limit or 200), 500),
    )

    providers_sql = (
        "SELECT "
        " CONVERT(varchar(36), r.unidad_negocio_pk) AS unidad_negocio_pk, "
        " u.codigo AS unidad_codigo, "
        " u.nombre AS unidad_nombre, "
        " CONVERT(varchar(100), r.ProveedorID) AS proveedor_id, "
        " COALESCE(NULLIF(LTRIM(RTRIM(p.NombreComercial)), ''), "
        "          NULLIF(LTRIM(RTRIM(p.RazonSocial)), ''), "
        "          CONCAT('Proveedor ', CONVERT(varchar(100), r.ProveedorID))) "
        "     AS proveedor_nombre, "
        " COUNT_BIG(*) AS recepciones, "
        " SUM(ISNULL(r.Total, 0)) AS total_compras, "
        " AVG(CAST(ISNULL(r.Total, 0) AS decimal(18,2))) AS ticket_promedio "
        "FROM dbo.Compras_Recepciones r "
        "INNER JOIN dbo.Unidades_Negocio u "
        " ON u.id = r.unidad_negocio_pk "
        "AND ISNULL(u.activo, 1) = 1 "
        "LEFT JOIN dbo.Proveedor_Catalogo p "
        " ON p.ProveedorID = r.ProveedorID "
        "AND ISNULL(p.Activo, 1) = 1 "
        "WHERE "
        + " AND ".join(where)
        + " GROUP BY "
          "r.unidad_negocio_pk, u.codigo, u.nombre, r.ProveedorID, "
          "p.NombreComercial, p.RazonSocial "
          "ORDER BY total_compras DESC"
    )

    providers = fetch_all_dict(
        providers_sql,
        tuple(params),
    )

    receipts_sql = (
        f"SELECT TOP ({safe_limit}) "
        " CONVERT(varchar(36), r.unidad_negocio_pk) AS unidad_negocio_pk, "
        " u.codigo AS unidad_codigo, "
        " u.nombre AS unidad_nombre, "
        " CONVERT(varchar(100), r.ProveedorID) AS proveedor_id, "
        " COALESCE(NULLIF(LTRIM(RTRIM(p.NombreComercial)), ''), "
        "          NULLIF(LTRIM(RTRIM(p.RazonSocial)), ''), "
        "          CONCAT('Proveedor ', CONVERT(varchar(100), r.ProveedorID))) "
        "     AS proveedor_nombre, "
        " r.FolioRecepcion AS folio_recepcion, "
        " r.FechaRecepcion AS fecha_recepcion, "
        " ISNULL(r.Subtotal, 0) AS subtotal, "
        " ISNULL(r.ImpuestoTotal, 0) AS impuesto_total, "
        " ISNULL(r.Total, 0) AS total, "
        " r.EstatusRecepcionID AS estatus_recepcion_id, "
        " r.TieneIncidencias AS tiene_incidencias "
        "FROM dbo.Compras_Recepciones r "
        "INNER JOIN dbo.Unidades_Negocio u "
        " ON u.id = r.unidad_negocio_pk "
        "AND ISNULL(u.activo, 1) = 1 "
        "LEFT JOIN dbo.Proveedor_Catalogo p "
        " ON p.ProveedorID = r.ProveedorID "
        "AND ISNULL(p.Activo, 1) = 1 "
        "WHERE "
        + " AND ".join(where)
        + " ORDER BY r.FechaRecepcion DESC, r.FolioRecepcion DESC"
    )

    receipts = fetch_all_dict(
        receipts_sql,
        tuple(params),
    )

    total_periodo = sum(
        float(row.get("total_compras") or 0)
        for row in providers
    )

    return {
        "fuente": "CANONICO_EDARSAHUB",
        "fuente_compras": "dbo.Compras_Recepciones",
        "nivel_maximo": "RECEPCION_COMPRA",
        "detalle_producto_disponible": False,
        "periodo_referencia": {
            "fecha_inicio": inicio.isoformat(),
            "fecha_fin": fin.isoformat(),
            "meses": meses,
        },
        "filtros": {
            "unidad_negocio_pk": unidad_negocio_pk,
            "proveedor_id": proveedor_id,
        },
        "resumen": {
            "proveedores": len(providers),
            "recepciones_retornadas": len(receipts),
            "total_compras": round(total_periodo, 2),
        },
        "proveedores": [
            {
                "unidad_negocio_pk": str(
                    row.get("unidad_negocio_pk") or ""
                ),
                "unidad_codigo": row.get("unidad_codigo"),
                "unidad_nombre": row.get("unidad_nombre"),
                "proveedor_id": str(
                    row.get("proveedor_id") or ""
                ),
                "proveedor_nombre": (
                    row.get("proveedor_nombre")
                    or f"Proveedor {row.get('proveedor_id')}"
                ),
                "recepciones": int(
                    row.get("recepciones") or 0
                ),
                "total_compras": round(
                    float(row.get("total_compras") or 0),
                    2,
                ),
                "ticket_promedio": round(
                    float(row.get("ticket_promedio") or 0),
                    2,
                ),
            }
            for row in providers
        ],
        "recepciones": [
            {
                "unidad_negocio_pk": str(
                    row.get("unidad_negocio_pk") or ""
                ),
                "unidad_codigo": row.get("unidad_codigo"),
                "unidad_nombre": row.get("unidad_nombre"),
                "proveedor_id": str(
                    row.get("proveedor_id") or ""
                ),
                "proveedor_nombre": (
                    row.get("proveedor_nombre")
                    or f"Proveedor {row.get('proveedor_id')}"
                ),
                "folio_recepcion": row.get("folio_recepcion"),
                "fecha_recepcion": (
                    row.get("fecha_recepcion").isoformat()
                    if hasattr(
                        row.get("fecha_recepcion"),
                        "isoformat",
                    )
                    else str(
                        row.get("fecha_recepcion") or ""
                    )
                ),
                "subtotal": round(
                    float(row.get("subtotal") or 0),
                    2,
                ),
                "impuesto_total": round(
                    float(row.get("impuesto_total") or 0),
                    2,
                ),
                "total": round(
                    float(row.get("total") or 0),
                    2,
                ),
                "estatus_recepcion_id": row.get(
                    "estatus_recepcion_id"
                ),
                "tiene_incidencias": bool(
                    row.get("tiene_incidencias")
                ),
            }
            for row in receipts
        ],
    }



def _cxp_proveedores_canonico(unidad_negocio_pk, unidades_permitidas=None):
    rows = _cxp_rows_canonico(
        unidad_negocio_pk,
        unidades_permitidas=unidades_permitidas,
    )
    provs = {}
    for r in rows:
        pid = r.get('ProveedorID')
        if pid not in provs:
            provs[pid] = {"proveedor_id": pid, "proveedor_nombre": r.get('ProveedorNombre') or f"Proveedor {pid}",
                          "proveedor_rfc": r.get('ProveedorRFC') or '', "total_saldo": 0.0, "cantidad_facturas": 0}
        provs[pid]["total_saldo"] += float(r.get('Saldo') or 0)
        provs[pid]["cantidad_facturas"] += 1
    return {"fuente": "CANONICO_EDARSAHUB",
            "proveedores": sorted(provs.values(), key=lambda x: -x["total_saldo"])}


def _cxp_sucursales_canonico(unidades_permitidas=None):
    where = ["c.Activo=1", "c.Saldo>0", "ISNULL(c.EsDemo,0)=0"]
    params = []
    if unidades_permitidas is not None:
        allowed = [str(u) for u in unidades_permitidas if u]
        if allowed:
            placeholders = ",".join(["%s"] * len(allowed))
            where.append(f"CONVERT(varchar(36), u.id) IN ({placeholders})")
            params.extend(allowed)
        else:
            where.append("1=0")

    rows = fetch_all_dict(
        "SELECT CONVERT(varchar(36), u.id) unidad_negocio_pk, u.codigo, u.nombre, "
        "MAX(c.Fuente) fuente, COUNT(*) n, SUM(c.Saldo) saldo "
        "FROM dbo.Finanzas_CxP_Sync c "
        "INNER JOIN dbo.Unidades_Negocio u "
        "  ON UPPER(LTRIM(RTRIM(c.UnidadNegocio))) = UPPER(LTRIM(RTRIM(u.codigo))) "
        " AND ISNULL(u.activo, 1) = 1 "
        "WHERE " + " AND ".join(where) + " "
        "GROUP BY u.id, u.codigo, u.nombre ORDER BY saldo DESC",
        tuple(params),
    )
    return {"fuente": "CANONICO_EDARSAHUB",
            "sucursales": [{"SucursalID": r["unidad_negocio_pk"], "Nombre_Sucursal": r.get("nombre") or r["codigo"],
                            "unidad_negocio_pk": r["unidad_negocio_pk"], "codigo": r.get("codigo"),
                            "CantidadFacturas": int(r["n"] or 0), "SaldoTotal": float(r["saldo"] or 0),
                            "Sistema": r.get("fuente")} for r in rows]}

# ============================================================================
# SCHEMAS
# ============================================================================

class ActualizarDecisionPago(BaseModel):
    """Actualizar decisión de pago de una factura"""
    decision_pago: bool
    importe_a_pagar: Optional[float] = None

class ActualizarDecisionPagoMasivo(BaseModel):
    """Actualizar decisión de pago de múltiples facturas"""
    facturas_ids: List[str]  # CXP_<id_sync> o CXP_<hash_origen>
    decision_pago: bool

class AutorizarDecisionPago(BaseModel):
    """Autorizar o rechazar una decision de pago CxP."""
    autorizar: bool = True
    comentario: Optional[str] = None
    programar_envio_origen: bool = True

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("")
async def listar_facturas_pendientes(
    sucursal_id: Optional[str] = None,  # Deprecated: usar unidad_negocio_pk
    unidad_negocio_pk: Optional[str] = None,
    proveedor_id: Optional[str] = None,
    tipo_proveedor: Optional[str] = None,  # A=Alimentos, B=Bebidas, X=Otros
    fecha_corte: Optional[str] = None,  # YYYY-MM-DD
    solo_vencidas: bool = False,
    solo_decision_pago: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """
    Listar facturas/cuentas pendientes de pago.
    
    Lee exclusivamente dbo.Finanzas_CxP_Sync y aplica RBAC por unidad_negocio_pk.

    Filtros: unidad/sucursal legacy, proveedor, tipo (A/B/X), fecha de corte, solo vencidas.
    Agrupa por TIPO DE PROVEEDOR (A=Alimentos, B=Bebidas, X=Otros).
    """
    # === NO-LIVE: lee EXCLUSIVAMENTE de la tabla canónica Finanzas_CxP_Sync ===
    unidad_pk, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        unidad_negocio_pk or sucursal_id,
    )
    return _cxp_listar_canonico(
        unidad_pk,
        tipo_proveedor,
        solo_vencidas,
        solo_decision_pago,
        proveedor_id,
        fecha_corte,
        unidades_permitidas,
        current_user,
    )

@router.get("/resumen")
async def get_resumen_cuentas_por_pagar(
    sucursal_id: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Resumen ejecutivo de cuentas por pagar.
    
    Lee exclusivamente dbo.Finanzas_CxP_Sync y aplica RBAC por unidad_negocio_pk.
    """
    # === NO-LIVE: lee EXCLUSIVAMENTE de la tabla canónica Finanzas_CxP_Sync ===
    unidad_pk, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        unidad_negocio_pk or sucursal_id,
    )
    return _cxp_resumen_canonico(
        unidad_pk,
        unidades_permitidas,
    )

@router.get("/decision-dashboard")
async def get_decision_dashboard(
    unidad_negocio_pk: Optional[str] = None,
    fecha_referencia_inicio: Optional[str] = Query(
        default=None,
        description="Inicio del periodo histórico YYYY-MM-DD",
    ),
    fecha_referencia_fin: Optional[str] = Query(
        default=None,
        description="Fin del periodo histórico YYYY-MM-DD",
    ),
    aplicar_periodo_como_limite: bool = Query(
        default=False,
        description=(
            "Aplica el periodo solicitado como base efectiva "
            "del limite de pago. Requiere FINANZAS_ADMINISTRAR."
        ),
    ),
    current_user: Dict = Depends(get_current_user),
):
    """
    Tablero SQL-first de capacidad de pago.

    Default:
        mes calendario anterior.

    Un periodo alternativo solo puede sustituir el limite
    efectivo cuando aplicar_periodo_como_limite=True y el
    usuario posee FINANZAS_ADMINISTRAR.

    No LIVE, no MongoDB, no cálculos financieros en frontend.
    """
    require_any_finanzas_permission(
        current_user,
        (FINANZAS_VER,),
    )

    custom_period_requested = bool(
        fecha_referencia_inicio
        or fecha_referencia_fin
    )

    if aplicar_periodo_como_limite:
        if not (
            fecha_referencia_inicio
            and fecha_referencia_fin
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "El override del limite requiere fecha de "
                    "inicio y fecha de fin."
                ),
            )

        require_any_finanzas_permission(
            current_user,
            (FINANZAS_ADMINISTRAR,),
        )

        effective_start = fecha_referencia_inicio
        effective_end = fecha_referencia_fin

    else:
        # El endpoint principal nunca cambia silenciosamente
        # el limite por recibir fechas alternativas.
        #
        # Los periodos alternativos sin override autorizado
        # pertenecen exclusivamente al endpoint drilldown.
        effective_start = None
        effective_end = None

    unidad_pk, unidades_permitidas = (
        resolve_finanzas_unit_filter(
            current_user,
            unidad_negocio_pk,
            permission_code=FINANZAS_VER,
        )
    )

    result = _decision_dashboard_canonico(
        unidad_pk,
        unidades_permitidas,
        effective_start,
        effective_end,
    )

    periodo = result.setdefault(
        "periodo_referencia",
        {},
    )

    periodo["es_override_efectivo"] = bool(
        aplicar_periodo_como_limite
    )

    periodo["requiere_autorizacion_override"] = True

    periodo["permiso_override_v1"] = (
        FINANZAS_ADMINISTRAR
    )

    periodo["periodo_alternativo_ignorado"] = bool(
        custom_period_requested
        and not aplicar_periodo_como_limite
    )

    return result



@router.get("/decision-dashboard/drilldown")
async def get_decision_dashboard_drilldown(
    unidad_negocio_pk: Optional[str] = None,
    proveedor_id: Optional[str] = None,
    fecha_referencia_inicio: Optional[str] = Query(
        default=None,
    ),
    fecha_referencia_fin: Optional[str] = Query(
        default=None,
    ),
    limit: int = Query(
        default=200,
        ge=1,
        le=500,
    ),
    current_user: Dict = Depends(get_current_user),
):
    """
    Drilldown del promedio histórico hasta entrada/recepción individual.

    SQL-first.
    No LIVE.
    No MongoDB.
    """
    require_any_finanzas_permission(
        current_user,
        (FINANZAS_VER,),
    )

    unidad_pk, unidades_permitidas = (
        resolve_finanzas_unit_filter(
            current_user,
            unidad_negocio_pk,
            permission_code=FINANZAS_VER,
        )
    )

    return _decision_dashboard_drilldown(
        unidad_pk,
        unidades_permitidas,
        fecha_referencia_inicio,
        fecha_referencia_fin,
        proveedor_id,
        limit,
    )



@router.get("/proveedores")
async def listar_proveedores_con_saldo(
    sucursal_id: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Lista proveedores que tienen facturas pendientes - NO-LIVE (canónico)"""
    unidad_pk, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        unidad_negocio_pk or sucursal_id,
    )
    return _cxp_proveedores_canonico(
        unidad_pk,
        unidades_permitidas,
    )

@router.get("/sucursales")
async def listar_sucursales_cxp(
    include_hidden: bool = Query(default=False, description="Incluir sucursales ocultas"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista sucursales con datos de CxP.
    
    Lee exclusivamente dbo.Finanzas_CxP_Sync y aplica RBAC por unidad_negocio_pk.
    """
    # === NO-LIVE: lee EXCLUSIVAMENTE de la tabla canónica Finanzas_CxP_Sync ===
    _, unidades_permitidas = resolve_finanzas_unit_filter(current_user)
    return _cxp_sucursales_canonico(unidades_permitidas)

@router.put("/{factura_id}/decision-pago")
async def actualizar_decision_pago(
    factura_id: str,
    data: ActualizarDecisionPago,
    current_user: Dict = Depends(get_current_user)
):
    """Actualizar decision de pago sobre la fuente canonica CxP."""
    permission = require_any_finanzas_permission(
        current_user,
        (FINANZAS_EDITAR, FINANZAS_ADMINISTRAR),
    )
    _cxp_require_decisiones_schema()
    _, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        permission_code=permission["permission_code"],
    )
    row, factura_id_decoded = _cxp_row_for_ref(factura_id, unidades_permitidas)
    importe = _cxp_upsert_decision(row, data, current_user)

    from core.auditoria_helpers import registrar_auditoria_cxp

    await registrar_auditoria_cxp(
        current_user=current_user,
        accion='EDIT',
        factura_id=factura_id_decoded,
        factura_folio=row.get('FolioFactura') or row.get('FolioEntrada'),
        sucursal_id=row.get('UnidadNegocioCodigoCanonico'),
        valor_anterior={
            'decision_pago': bool(row.get('DecisionPagoCanonica')),
            'importe_a_pagar': float(row.get('ImporteAPagarCanonico') or 0),
        },
        valor_nuevo={
            'decision_pago': data.decision_pago,
            'importe_a_pagar': float(importe),
            'unidad_negocio_pk': row.get('UnidadNegocioIDCanonica'),
            'estado_autorizacion_pago': 'PENDIENTE_AUTORIZACION' if data.decision_pago else 'CANCELADO',
        },
        motivo='Decision canonica de pago CxP',
    )

    refreshed, _ = _cxp_row_for_ref(factura_id, unidades_permitidas)

    authorization = None

    if data.decision_pago:
        refreshed_hash = str(
            refreshed.get("HashOrigen") or ""
        ).strip().lower()

        refreshed_decision = _cxp_decision_row_for_hash(
            refreshed_hash
        )

        authorization = _cxp_create_canonical_authorization(
            refreshed,
            refreshed_decision,
            current_user,
        )

        _cxp_project_authorization_state(
            refreshed_decision,
            authorization,
        )

        refreshed, _ = _cxp_row_for_ref(
            factura_id,
            unidades_permitidas,
        )

    return {
        "success": True,
        "fuente": "CANONICO_EDARSAHUB",
        "factura_id": _cxp_factura_dict(refreshed, current_user)["factura_id"],
        "factura_sync_id": refreshed.get("CxpSyncID"),
        "decision_pago": data.decision_pago,
        "importe_a_pagar": float(importe),
        "autorizacion_id": (
            authorization.get("AutorizacionID")
            if authorization
            else None
        ),
        "estado_autorizacion_canonica": (
            authorization.get("EstatusAutorizacion")
            if authorization
            else None
        ),
        "factura": _cxp_factura_dict(refreshed, current_user),
    }


@router.post("/{factura_id}/decision-pago/autorizacion")
async def autorizar_decision_pago(
    factura_id: str,
    data: AutorizarDecisionPago,
    current_user: Dict = Depends(get_current_user)
):
    """
    Resuelve AUT_TES_PAGOS mediante el motor canonico.

    FINANZAS_ADMINISTRAR habilita el acceso al flujo,
    pero no reemplaza al autorizador asignado por matriz.
    """
    permission = require_any_finanzas_permission(
        current_user,
        (FINANZAS_ADMINISTRAR,),
    )

    _cxp_require_decisiones_schema()

    _, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        permission_code=permission["permission_code"],
    )

    row, factura_id_decoded = _cxp_row_for_ref(
        factura_id,
        unidades_permitidas,
    )

    hash_origen = str(
        row.get("HashOrigen") or ""
    ).strip().lower()

    decision = _cxp_decision_row_for_hash(hash_origen)

    if not bool(decision.get("DecisionPago")):
        raise HTTPException(
            status_code=409,
            detail=(
                "La CxP no esta marcada para pago; "
                "no puede autorizarse."
            ),
        )

    authorization = _cxp_resolve_canonical_authorization(
        decision,
        data.autorizar,
        data.comentario,
        current_user,
    )

    projected_state = _cxp_project_authorization_state(
        decision,
        authorization,
    )

    should_enqueue = (
        projected_state == "AUTORIZADO"
        and bool(data.programar_envio_origen)
    )

    if should_enqueue:
        _cxp_require_queue_schema()

        refreshed_decision = _cxp_decision_row_for_hash(
            hash_origen
        )

        _cxp_enqueue_pago_origen(
            refreshed_decision,
            current_user,
        )

    from core.auditoria_helpers import registrar_auditoria_cxp

    await registrar_auditoria_cxp(
        current_user=current_user,
        accion="EDIT",
        factura_id=factura_id_decoded,
        factura_folio=(
            row.get("FolioFactura")
            or row.get("FolioEntrada")
        ),
        sucursal_id=row.get(
            "UnidadNegocioCodigoCanonico"
        ),
        valor_anterior={
            "estado_autorizacion_pago":
                decision.get("EstadoAutorizacion"),
        },
        valor_nuevo={
            "autorizacion_id":
                authorization.get("AutorizacionID"),
            "estado_autorizacion_canonica":
                authorization.get("EstatusAutorizacion"),
            "estado_autorizacion_pago":
                projected_state,
            "programar_envio_origen":
                should_enqueue,
            "unidad_negocio_pk":
                row.get("UnidadNegocioIDCanonica"),
        },
        motivo=(
            "Resolucion AUT_TES_PAGOS mediante "
            "motor canonico de autorizaciones"
        ),
    )

    refreshed, _ = _cxp_row_for_ref(
        factura_id,
        unidades_permitidas,
    )

    return {
        "success": True,
        "fuente": "CANONICO_EDARSAHUB",
        "factura_id":
            _cxp_factura_dict(refreshed, current_user)["factura_id"],
        "autorizacion_id":
            authorization.get("AutorizacionID"),
        "estado_autorizacion_canonica":
            authorization.get("EstatusAutorizacion"),
        "estado_autorizacion_pago":
            projected_state,
        "programar_envio_origen":
            should_enqueue,
        "factura":
            _cxp_factura_dict(refreshed, current_user),
    }


@router.put("/decision-pago-masivo")
async def actualizar_decision_pago_masivo(
    data: ActualizarDecisionPagoMasivo,
    current_user: Dict = Depends(get_current_user)
):
    """Actualizar decision de pago de multiples facturas canonicas CxP."""
    if not data.facturas_ids:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos una factura CxP.")

    permission = require_any_finanzas_permission(
        current_user,
        (FINANZAS_EDITAR, FINANZAS_ADMINISTRAR),
    )
    _cxp_require_decisiones_schema()
    _, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        permission_code=permission["permission_code"],
    )
    rows = _cxp_rows_for_refs(data.facturas_ids, unidades_permitidas)

    actualizadas = 0
    monto_total = Decimal("0.00")
    for row in rows:
        importe = _cxp_upsert_decision(
            row,
            ActualizarDecisionPago(decision_pago=data.decision_pago),
            current_user,
        )
        actualizadas += 1
        monto_total += importe

    from core.auditoria_helpers import registrar_auditoria_cxp

    await registrar_auditoria_cxp(
        current_user=current_user,
        accion='EDIT',
        factura_id=f'MASIVO_{len(data.facturas_ids)}',
        valor_nuevo={
            'decision_pago': data.decision_pago,
            'cantidad_facturas': actualizadas,
            'monto_total': float(monto_total),
        },
        motivo='Decision masiva canonica de pago CxP',
    )

    return {
        "success": True,
        "fuente": "CANONICO_EDARSAHUB",
        "actualizadas": actualizadas,
        "total_solicitadas": len(data.facturas_ids),
        "monto_total": float(monto_total),
    }


@router.get("/{factura_id}")
async def get_factura_detalle(
    factura_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtener detalle de una factura desde la fuente canonica CxP."""
    _, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        permission_code=FINANZAS_VER,
    )
    row, _ = _cxp_row_for_ref(factura_id, unidades_permitidas)
    return {"fuente": "CANONICO_EDARSAHUB", "factura": _cxp_factura_dict(row, current_user)}
