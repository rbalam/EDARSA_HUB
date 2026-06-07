#!/usr/bin/env bash
set -euo pipefail

# FASE 8B - P2-2B  Frontend: Mis Tareas + Asignaciones (hardening de render/shape)
# Validado por el agente: bug 'token' undefined en getUserRole es real; lib/api exporta getToken.

FRONT_DIR="/app/frontend"
OUT_DIR="/app/auditorias_p5"
TS="$(date +%Y%m%d_%H%M%S)"
RAW="$OUT_DIR/FASE8B_P2_2B_FRONT_${TS}.txt"
ASIG_FILE="$FRONT_DIR/src/pages/ConfigAsignaciones.jsx"
TAREAS_FILE="$FRONT_DIR/src/pages/MisTareas.js"

mkdir -p "$OUT_DIR" /app/scripts
cd /app || exit 1
for f in "$ASIG_FILE" "$TAREAS_FILE"; do [ -f "$f" ] || { echo "ERROR: no existe $f"; exit 1; }; done

echo "FASE 8B - P2-2B  $(date)" | tee "$RAW"

echo "===== BACKUPS =====" | tee -a "$RAW"
for f in "$ASIG_FILE" "$TAREAS_FILE"; do cp "$f" "${f}.bak_${TS}"; echo "BACKUP ${f}.bak_${TS}" | tee -a "$RAW"; done

echo "===== PARCHE ConfigAsignaciones.jsx =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
p = Path("/app/frontend/src/pages/ConfigAsignaciones.jsx")
txt = p.read_text(encoding="utf-8"); original = txt
if "getToken" not in txt:
    txt = txt.replace("import api from '../lib/api';", "import api, { getToken } from '../lib/api';")
if "const ensureArray =" not in txt:
    anchor = "  const { toast } = useToast();\n"
    helper = "  const { toast } = useToast();\n  \n  const ensureArray = (value) => Array.isArray(value) ? value : [];\n  const asString = (value) => value === null || value === undefined ? '' : String(value);\n"
    txt = txt.replace(anchor, helper)
old_role = """  const getUserRole = () => {
    try {
      if (!token) return '';
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.role || '';
    } catch {
      return '';
    }
  };
"""
new_role = """  const getUserRole = () => {
    try {
      const token = typeof getToken === 'function' ? getToken() : '';
      if (!token) return '';
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.role || '';
    } catch {
      return '';
    }
  };
"""
txt = txt.replace(old_role, new_role)
txt = txt.replace("      setAsignaciones(response.data.data || []);", "      setAsignaciones(ensureArray(response.data?.data));")
txt = txt.replace("      setTotalAsignaciones(response.data.total || 0);", "      setTotalAsignaciones(response.data?.total || 0);")
txt = txt.replace("      setUnidadesNegocio(response.data.data || []);", "      setUnidadesNegocio(ensureArray(response.data?.data));")
txt = txt.replace("      return (response.data.data || []).filter(a => a.id);", "      return ensureArray(response.data?.data).filter(a => a?.id !== undefined && a?.id !== null && a?.id !== '');")
txt = txt.replace("      const activos = (response.data.users || response.data || []).filter(u => u.activo !== false);", "      const rawUsers = ensureArray(response.data?.users || (Array.isArray(response.data) ? response.data : []));\n      const activos = rawUsers.filter(u => u?.activo !== false);")
txt = txt.replace('<SelectItem key={u.id} value={u.id}>', '<SelectItem key={asString(u.id)} value={asString(u.id)}>')
txt = txt.replace("value={filtroUnidad || '__todas__'}", "value={asString(filtroUnidad || '__todas__')}")
txt = txt.replace("onValueChange={(v) => setFiltroUnidad(v === '__todas__' ? '' : v)}", "onValueChange={(v) => setFiltroUnidad(v === '__todas__' ? '' : asString(v))}")
if "P2_2B_FRONT_HARDENING" not in txt:
    txt = "// P2_2B_FRONT_HARDENING\n" + txt
if txt != original:
    p.write_text(txt, encoding="utf-8"); print("PATCHED ConfigAsignaciones.jsx")
else:
    print("NO CHANGE ConfigAsignaciones.jsx")
PY

echo "===== PARCHE MisTareas.js =====" | tee -a "$RAW"
python3 - <<'PY' | tee -a "$RAW"
from pathlib import Path
p = Path("/app/frontend/src/pages/MisTareas.js")
txt = p.read_text(encoding="utf-8"); original = txt
if "const ensureArray =" not in txt:
    anchor = "export default function MisTareas() {\n"
    helper = "export default function MisTareas() {\n  const ensureArray = (value) => Array.isArray(value) ? value : [];\n  const normalizeTareas = (data) => ({\n    pendientes: ensureArray(data?.pendientes),\n    en_proceso: ensureArray(data?.en_proceso),\n    completadas: ensureArray(data?.completadas),\n    total_pendientes: Number(data?.total_pendientes || 0),\n    total_en_proceso: Number(data?.total_en_proceso || 0),\n    solicitudes_pendientes_aprobar: Number(data?.solicitudes_pendientes_aprobar || 0),\n  });\n  const normalizePendientes = (data) => ({\n    urgentes: ensureArray(data?.urgentes),\n    catalogos: ensureArray(data?.catalogos),\n    proveedores: ensureArray(data?.proveedores),\n    nominas: ensureArray(data?.nominas),\n    contadores: {\n      urgentes: Number(data?.contadores?.urgentes || 0),\n      catalogos: Number(data?.contadores?.catalogos || 0),\n      proveedores: Number(data?.contadores?.proveedores || 0),\n      nominas: Number(data?.contadores?.nominas || 0),\n      total: Number(data?.contadores?.total || 0),\n    }\n  });\n"
    txt = txt.replace(anchor, helper)
txt = txt.replace("      setTareas(tareasData);", "      setTareas(normalizeTareas(tareasData));")
txt = txt.replace("      setMisPermisos(permisosData);", "      setMisPermisos({ puede_solicitar: !!permisosData?.puede_solicitar, puede_aprobar: !!permisosData?.puede_aprobar, catalogos_permitidos: ensureArray(permisosData?.catalogos_permitidos) });")
txt = txt.replace("      setCatalogosDisponibles(catalogosData.catalogos || []);", "      setCatalogosDisponibles(ensureArray(catalogosData?.catalogos));")
txt = txt.replace("      setMisSolicitudes(misSolicitudesData.solicitudes || []);", "      setMisSolicitudes(ensureArray(misSolicitudesData?.solicitudes));")
txt = txt.replace("        setPendientesUnificados(unificadosData);", "        setPendientesUnificados(normalizePendientes(unificadosData));")
txt = txt.replace("        const pendientes = (solicitudesData.solicitudes || []).filter(s => ", "        const pendientes = ensureArray(solicitudesData?.solicitudes).filter(s => ")
txt = txt.replace("        setSolicitudesPendientes(pendientes);", "        setSolicitudesPendientes(ensureArray(pendientes));")
txt = txt.replace("      setUsuarios(data.usuarios || []);", "      setUsuarios(ensureArray(data?.usuarios));")
txt = txt.replace("      setProveedores(response.data || []);", "      setProveedores(ensureArray(response.data));")
txt = txt.replace("      setServersDisponibles(response.data.filter(s => s.active) || []);", "      setServersDisponibles(ensureArray(response.data).filter(s => s?.active));")
txt = txt.replace("  const catalogosPorModulo = catalogosDisponibles.reduce((acc, cat) => {", "  const catalogosPorModulo = ensureArray(catalogosDisponibles).reduce((acc, cat) => {")
txt = txt.replace("  const proveedoresFiltrados = proveedores", "  const proveedoresFiltrados = ensureArray(proveedores)")
txt = txt.replace("  const proveedoresPendientesCount = proveedores.filter(s => s.status === 'pending').length;", "  const proveedoresPendientesCount = ensureArray(proveedores).filter(s => s?.status === 'pending').length;")
if "P2_2B_FRONT_HARDENING" not in txt:
    txt = "// P2_2B_FRONT_HARDENING\n" + txt
if txt != original:
    p.write_text(txt, encoding="utf-8"); print("PATCHED MisTareas.js")
else:
    print("NO CHANGE MisTareas.js")
PY

echo "===== BUILD FRONTEND (yarn) =====" | tee -a "$RAW"
cd "$FRONT_DIR" && yarn build >> "$RAW" 2>&1 && echo "BUILD_OK=1" | tee -a "$RAW" || echo "BUILD_OK=0" | tee -a "$RAW"

echo "===== REINICIO FRONTEND =====" | tee -a "$RAW"
sudo supervisorctl restart frontend || true
sleep 8
sudo supervisorctl status frontend | head -1 | tee -a "$RAW"

echo "===== EVIDENCIA =====" | tee -a "$RAW"
grep -cE "P2_2B_FRONT_HARDENING|ensureArray|const token = typeof getToken" "$ASIG_FILE" | tee -a "$RAW"
grep -cE "P2_2B_FRONT_HARDENING|normalizeTareas|ensureArray" "$TAREAS_FILE" | tee -a "$RAW"
echo "RAW_REPORT=$RAW" | tee -a "$RAW"
echo "OK - FASE 8B ejecutado" | tee -a "$RAW"
