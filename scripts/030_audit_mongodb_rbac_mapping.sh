#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/app}"
OUT="$ROOT/docs/reports/DIAGNOSTICO_MAPEO_RBAC_MONGO_A_SQL.md"

mkdir -p "$ROOT/docs/reports"

{
  echo "# DIAGNÓSTICO MAPEO RBAC MongoDB → Usuario_* SQL"
  echo ""
  echo "Generado: $(date -Iseconds)"
  echo ""
  echo "## Objetivo"
  echo ""
  echo "Diagnosticar dependencias de RBAC MongoDB antes de migrar usuarios hacia Usuario_* SQL."
  echo ""
  echo "## Regla"
  echo ""
  echo "- No migrar usuarios todavía."
  echo "- No borrar MongoDB todavía."
  echo "- No modificar asignaciones de usuarios todavía."
  echo "- Usuario_* es RBAC SQL canónico."
  echo "- Sistema_RBAC_* queda como transicional / NO_USAR_NUEVO."
  echo ""
  echo "## Colecciones MongoDB esperadas"
  echo ""
  echo "| Colección MongoDB | Tabla SQL destino | Prioridad | Estado |"
  echo "|---|---|---|---|"
  echo "| users | Usuario_Catalogo | P0 | Diagnóstico |"
  echo "| rbac_roles | Usuario_Roles | P0 | Diagnóstico |"
  echo "| rbac_usuarios_roles | Usuario_RolesAsignacion | P0 | Diagnóstico |"
  echo "| rbac_permisos | Usuario_PermisosRolModulo | P0 | Diagnóstico |"
  echo "| rbac_audit_log | Usuario_LogRBACVerificacion | P1 | Diagnóstico |"
  echo "| empresas | Global_Cat_Empresas | P0 | Diagnóstico |"
  echo "| sucursales_catalogo | RH_Cat_Sucursales / Unidades_Negocio | P1 | Diagnóstico |"
  echo "| sucursal_servidor_map | Unidades_Negocio / Servidores_Conexiones | P0 | Diagnóstico |"
  echo ""
  echo "## Referencias RBAC/Mongo encontradas en código"
  echo ""
  echo '```text'
  grep -Rni \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude="*.pyc" \
    "rbac_permisos\|rbac_roles\|rbac_usuarios_roles\|rbac_audit_log\|users\|motor.motor_asyncio\|AsyncIOMotor\|pymongo\|mongodb\|MongoDB" \
    "$ROOT/backend" "$ROOT/frontend" "$ROOT/docs" 2>/dev/null || true
  echo '```'
  echo ""
  echo "## Referencias Usuario_* SQL encontradas en código"
  echo ""
  echo '```text'
  grep -Rni \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude="*.pyc" \
    "Usuario_Catalogo\|Usuario_Roles\|Usuario_RolesAsignacion\|Usuario_Modulos\|Usuario_PermisosRolModulo\|Usuario_EmpresasAsignacion\|Usuario_SucursalesAsignacion\|Usuario_ServidoresAsignacion\|Usuario_LogRBACVerificacion" \
    "$ROOT/backend" "$ROOT/frontend" "$ROOT/docs" 2>/dev/null || true
  echo '```'
  echo ""
  echo "## Pendientes antes de migrar usuarios"
  echo ""
  echo "1. Exportar muestra controlada de colecciones MongoDB rbac_* sin secretos."
  echo "2. Comparar usuarios por email/login."
  echo "3. Comparar roles por código/nombre."
  echo "4. Comparar empresas por RFC/código/nombre."
  echo "5. Comparar unidades/sucursales/servidores."
  echo "6. Generar script de migración en modo dry-run."
  echo "7. Validar con usuario SUPERADMIN antes de ejecutar migración real."
} > "$OUT"

echo "Reporte generado: $OUT"
