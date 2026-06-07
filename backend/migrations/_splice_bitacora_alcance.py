"""Splicer puntual: reemplaza la bitácora RBAC legacy (Mongo) por la versión
SQL-First y ELIMINA los endpoints /admin/alcance/* legacy (Mongo muerto, 0
consumidores; el alcance canónico vive en /api/config-asignaciones)."""
import io

PATH = "/app/backend/server.py"

NEW_BITACORA = '''@api_router.get("/admin/bitacora")
async def get_bitacora_rbac(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    email: Optional[str] = None,
    resultado: Optional[str] = None,
    tipo: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """Bitácora RBAC SQL-First (solo SuperAdministrador). Lee de
    dbo.Usuario_RBAC_Bitacora. Filtros: fecha_inicio/fecha_fin (YYYY-MM-DD),
    email (LIKE), resultado (exitoso|fallido|parcial), tipo (ASIGNAR|REVOCAR)."""
    if not es_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede acceder a la bitácora RBAC")
    if limit > 100:
        limit = 100
    total, eventos = rbac_pilot_service.get_bitacora(
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, email=email,
        resultado=resultado, tipo=tipo, skip=skip, limit=limit,
    )
    paginas_total = (total + limit - 1) // limit if total > 0 else 1
    pagina_actual = (skip // limit) + 1
    return {
        "total": total,
        "pagina": pagina_actual,
        "paginas_total": paginas_total,
        "limit": limit,
        "eventos": eventos,
    }


@api_router.get("/admin/bitacora/{evento_id}")
async def get_bitacora_evento_detalle(
    evento_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Detalle de un evento de bitácora RBAC (solo SuperAdministrador)."""
    if not es_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede acceder a la bitácora RBAC")
    evento = rbac_pilot_service.get_bitacora_evento(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento


# ==============================================================================
# FIN FASE 12 - BITÁCORA RBAC (SQL-First)
# ==============================================================================


'''

REMOVED_ALCANCE = '''# ==============================================================================
# FASE 14 - ALCANCE ORGANIZACIONAL: ELIMINADO (SQL-First)
# Los endpoints /admin/alcance/* legacy (Mongo, 0 consumidores) fueron retirados.
# El alcance canónico vive en /api/config-asignaciones
# (Usuario_EmpresasAsignacion / Usuario_SucursalesAsignacion).
# ==============================================================================


'''

with io.open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1) Reemplazar bitácora legacy
b_start = '@api_router.get("/admin/bitacora")\n'
b_end = '# ==============================================================================\n# FASE 13: PERFILES PREDEFINIDOS RBAC'
s = content.find(b_start)
e = content.find(b_end)
if s == -1 or e == -1 or e < s:
    raise SystemExit(f"Bitácora anchors no encontrados (s={s}, e={e})")
content = content[:s] + NEW_BITACORA + content[e:]
print("OK: bitácora reemplazada por SQL-First")

# 2) Eliminar alcance legacy
a_start = '@api_router.get("/admin/alcance/empresas")\n'
a_end = '# Incluir el router después de definir TODOS los endpoints'
s2 = content.find(a_start)
e2 = content.find(a_end)
if s2 == -1 or e2 == -1 or e2 < s2:
    raise SystemExit(f"Alcance anchors no encontrados (s={s2}, e={e2})")
content = content[:s2] + REMOVED_ALCANCE + content[e2:]
print("OK: alcance legacy eliminado")

with io.open(PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("server.py reescrito.")
