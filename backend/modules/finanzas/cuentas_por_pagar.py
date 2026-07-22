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

from datetime import date
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


def _cxp_factura_dict(r):
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
    }


def _cxp_listar_canonico(unidad_negocio_pk, tipo, solo_vencidas, solo_decision_pago=False, proveedor_id=None, fecha_corte=None, unidades_permitidas=None):
    facturas = [
        _cxp_factura_dict(r)
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
    return {
        "success": True,
        "fuente": "CANONICO_EDARSAHUB",
        "factura_id": _cxp_factura_dict(refreshed)["factura_id"],
        "factura_sync_id": refreshed.get("CxpSyncID"),
        "decision_pago": data.decision_pago,
        "importe_a_pagar": float(importe),
        "factura": _cxp_factura_dict(refreshed),
    }


@router.post("/{factura_id}/decision-pago/autorizacion")
async def autorizar_decision_pago(
    factura_id: str,
    data: AutorizarDecisionPago,
    current_user: Dict = Depends(get_current_user)
):
    """
    Autorizar o rechazar una decision canonica de pago.

    Si se autoriza, solo se programa una cola canonica para carga a origen;
    el tablero no abre conexiones live ni escribe directamente al sistema origen.
    """
    permission = require_any_finanzas_permission(
        current_user,
        (FINANZAS_ADMINISTRAR,),
    )
    _cxp_require_decisiones_schema()
    if data.autorizar and data.programar_envio_origen:
        _cxp_require_queue_schema()

    _, unidades_permitidas = resolve_finanzas_unit_filter(
        current_user,
        permission_code=permission["permission_code"],
    )
    row, factura_id_decoded = _cxp_row_for_ref(factura_id, unidades_permitidas)
    hash_origen = str(row.get("HashOrigen") or "").strip().lower()
    decision = _cxp_decision_row_for_hash(hash_origen)

    _cxp_update_autorizacion(decision, data.autorizar, data.comentario, current_user)
    if data.autorizar and data.programar_envio_origen:
        _cxp_enqueue_pago_origen(decision, current_user)

    from core.auditoria_helpers import registrar_auditoria_cxp

    await registrar_auditoria_cxp(
        current_user=current_user,
        accion='EDIT',
        factura_id=factura_id_decoded,
        factura_folio=row.get('FolioFactura') or row.get('FolioEntrada'),
        sucursal_id=row.get('UnidadNegocioCodigoCanonico'),
        valor_anterior={
            'estado_autorizacion_pago': decision.get('EstadoAutorizacion'),
        },
        valor_nuevo={
            'estado_autorizacion_pago': 'AUTORIZADO' if data.autorizar else 'RECHAZADO',
            'programar_envio_origen': bool(data.autorizar and data.programar_envio_origen),
            'unidad_negocio_pk': row.get('UnidadNegocioIDCanonica'),
        },
        motivo='Autorizacion canonica de pago CxP',
    )

    refreshed, _ = _cxp_row_for_ref(factura_id, unidades_permitidas)
    return {
        "success": True,
        "fuente": "CANONICO_EDARSAHUB",
        "factura_id": _cxp_factura_dict(refreshed)["factura_id"],
        "estado_autorizacion_pago": 'AUTORIZADO' if data.autorizar else 'RECHAZADO',
        "programar_envio_origen": bool(data.autorizar and data.programar_envio_origen),
        "factura": _cxp_factura_dict(refreshed),
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
    return {"fuente": "CANONICO_EDARSAHUB", "factura": _cxp_factura_dict(row)}
