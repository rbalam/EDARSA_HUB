from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from core.security import get_current_user_dual_dependency
from modules.comercial_v2.routes import get_unidades_permitidas_v2

from .schemas import (
    CommercialDrilldownRequest,
    TemporalResolveRequest,
)
from .repository_operational import build_current_operation
from .repository_tickets import (
    get_ticket_detail,
    list_tickets,
)
from .service import build_drilldown
from modules.comercial_v2.repository_readonly import (
    _execute_readonly_query,
)
from modules.comercial_v2.routes import (
    _unidades_runtime_where_sql,
)
from core.comercial_temporal_availability import (
    build_temporal_availability,
)
from .temporal_selection import (
    TemporalSelectionError,
    resolve_temporal_selection,
)
from .ticket_identity import (
    TicketIdentityError,
    parse_ticket_pk,
)


router = APIRouter(
    prefix="/comercial/analytics",
    tags=["Commercial Analytics"],
)


@router.post("/drilldown")
async def commercial_drilldown(
    payload: CommercialDrilldownRequest,
    current_user: dict = Depends(get_current_user_dual_dependency()),
):
    try:
        allowed_units = await get_unidades_permitidas_v2(current_user)
        allowed_codes = [
            str(value)
            for value in (allowed_units or [])
            if value is not None
        ]

        if not allowed_codes:
            raise HTTPException(
                status_code=403,
                detail="El usuario no tiene unidades permitidas",
            )

        result = build_drilldown(
            payload,
            allowed_unit_codes=allowed_codes,
        )

        return {
            "success": True,
            "data": result,
        }

    except HTTPException:
        raise

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible construir el drill-down comercial",
        ) from exc



@router.get("/tickets")
async def commercial_tickets(
    fecha_inicio: str = Query(...),
    fecha_fin: str = Query(...),
    unidad_negocio_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    current_user: dict = Depends(get_current_user_dual_dependency()),
):
    try:
        allowed_units = await get_unidades_permitidas_v2(current_user)
        allowed_codes = [
            str(value)
            for value in (allowed_units or [])
            if value is not None
        ]

        result = list_tickets(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            allowed_unit_codes=allowed_codes,
            unidad_negocio_id=unidad_negocio_id,
            page=page,
            page_size=page_size,
        )

        return {
            "success": True,
            "data": result,
        }

    except HTTPException:
        raise

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar los tickets",
        ) from exc


@router.get("/tickets/{ticket_pk}")
async def commercial_ticket_detail(
    ticket_pk: str,
    current_user: dict = Depends(get_current_user_dual_dependency()),
):
    try:
        identity = parse_ticket_pk(ticket_pk)

        allowed_units = await get_unidades_permitidas_v2(current_user)
        allowed_codes = [
            str(value)
            for value in (allowed_units or [])
            if value is not None
        ]

        result = get_ticket_detail(
            identity=identity,
            allowed_unit_codes=allowed_codes,
        )

        return {
            "success": True,
            "data": result,
        }

    except HTTPException:
        raise

    except TicketIdentityError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible reconstruir el ticket",
        ) from exc



@router.get("/operacion-en-curso")
async def commercial_current_operation(
    current_user: dict = Depends(
        get_current_user_dual_dependency()
    ),
):
    try:
        allowed_units = await get_unidades_permitidas_v2(
            current_user
        )
        allowed_codes = [
            str(value)
            for value in (allowed_units or [])
            if value is not None
        ]

        result = build_current_operation(
            allowed_unit_codes=allowed_codes,
        )

        return {
            "success": True,
            "data": result,
        }

    except HTTPException:
        raise

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "No fue posible construir la operación "
                "en curso"
            ),
        ) from exc


@router.post("/temporal/resolve")
async def commercial_temporal_resolve(
    payload: TemporalResolveRequest,
    current_user: dict = Depends(
        get_current_user_dual_dependency()
    ),
):
    try:
        allowed_units = await get_unidades_permitidas_v2(
            current_user
        )

        allowed_codes = sorted({
            str(value).strip()
            for value in (allowed_units or [])
            if str(value or "").strip()
        })

        if not allowed_codes:
            raise HTTPException(
                status_code=403,
                detail="El usuario no tiene unidades permitidas",
            )

        try:
            scope_units = payload.resolve_unit_scope(
                allowed_codes
            )
        except PermissionError as exc:
            raise HTTPException(
                status_code=403,
                detail=str(exc),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            ) from exc

        availability = build_temporal_availability(
            units=scope_units,
            readonly_query=_execute_readonly_query,
            units_where_builder=_unidades_runtime_where_sql,
        )

        minimum_date = availability.get("fecha_minima")
        maximum_date = availability.get("fecha_maxima")

        if not minimum_date or not maximum_date:
            raise HTTPException(
                status_code=422,
                detail=(
                    "No existe cobertura temporal disponible "
                    "para las unidades seleccionadas"
                ),
            )

        selection = dict(payload.selection or {})

        if selection.get("mode") == "key_dates":
            raise HTTPException(
                status_code=501,
                detail=(
                    "El catálogo canónico de fechas clave "
                    "todavía no está habilitado"
                ),
            )

        resolved = resolve_temporal_selection(
            selection=selection,
            minimum_date=minimum_date,
            maximum_date=maximum_date,
        )

        return {
            "success": True,
            "data": {
                **resolved,
                "availability": availability,
                "unit_scope": scope_units,
            },
        }

    except HTTPException:
        raise

    except TemporalSelectionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "No fue posible resolver la selección temporal"
            ),
        ) from exc
