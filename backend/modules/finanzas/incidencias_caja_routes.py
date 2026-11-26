"""Cajas V1: bootstrap HTTP protegido, sin persistencia ni catalogos supuestos.

No emite folios ni permite POST hasta certificar SQL y resolutores canonicos.
El registro de este router se efectua en el modulo Comercial ya montado.
"""
from fastapi import APIRouter, Depends, HTTPException

from core.security import get_current_user
from core.rbac_sql.service import RBACSQLService
from modules.finanzas.incidencias_caja_access import CAJAS_INCIDENCIAS_CREAR
from modules.finanzas.incidencias_caja_contracts import TipoIncidenciaCaja

router = APIRouter(prefix="/comercial/cajas", tags=["Cajas V1"])


@router.get("/bootstrap")
def obtener_bootstrap_cajas(current_user=Depends(get_current_user)):
    """Exige identidad SQL y RBAC antes de exponer capacidades de Caja."""
    if not isinstance(current_user, dict):
        raise HTTPException(status_code=403, detail="IDENTIDAD_SQL_INVALIDA")
    value = (
        current_user.get("_sql_usuario_id")
        or current_user.get("UsuarioID")
        or current_user.get("usuario_id")
    )
    if isinstance(value, bool):
        raise HTTPException(status_code=403, detail="IDENTIDAD_SQL_INVALIDA")
    try:
        usuario_id = int(value)
    except (ValueError, TypeError, OverflowError):
        raise HTTPException(status_code=403, detail="IDENTIDAD_SQL_INVALIDA") from None
    if usuario_id <= 0:
        raise HTTPException(status_code=403, detail="IDENTIDAD_SQL_INVALIDA")
    try:
        scope = RBACSQLService.get_permission_scope_by_code(
            usuario_id, CAJAS_INCIDENCIAS_CREAR
        )
    except Exception:
        raise HTTPException(status_code=503, detail="RBAC_SQL_NO_VERIFICABLE") from None
    if not isinstance(scope, dict) or scope.get("permitido") not in (True, 1):
        raise HTTPException(status_code=403, detail="CAJAS_INCIDENCIAS_CREAR_DENEGADO")

    return {
        "autorizado": False,
        "registro_habilitado": False,
        "razon": "CAJAS_SQL_PERSISTENCE_NOT_CERTIFIED",
        "tipos_referencia": [tipo.value for tipo in TipoIncidenciaCaja],
        "motivos": [],
        "contexto": None,
    }
