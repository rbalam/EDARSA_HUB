"""
AnonymizerService — Enmascaramiento central de confidencialidad comercial.
==========================================================================
REGLA DE ORO: el usuario solo ve nombres reales cuando tiene permiso explícito.
Si no, recibe etiquetas comparativas anónimas y SIN identificadores técnicos.

Decisiones del usuario aplicadas:
- (1b) EDARSA = un único grupo provisional (sin entidad Grupo Corporativo todavía).
- (2b) Permisos benchmark aún NO sembrados → el contexto se deriva del ROL canónico
       (es_admin/es_superadmin/get_role_code). Documentado para migrar a permisos
       (`comercial.benchmark.*`) cuando se siembren, sin tocar a los consumidores.

Sin hardcode de identidades: los nombres reales provienen de SQL canónico.
Determinista dentro de una respuesta (mismo salt ⇒ mismas etiquetas).
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set

from core.rbac_helper_sql import es_admin, es_superadmin, get_role_code

logger = logging.getLogger(__name__)

# Campos técnicos que NUNCA deben salir si el usuario no es admin técnico.
CAMPOS_TECNICOS = frozenset({
    "server_id", "serverid", "sucursal_id", "sucursal_origen_id",
    "host", "database", "db", "rfc", "id_origen", "hash_origen",
    "sync_run_id", "id_transaccion", "numero_ticket", "unidad_negocio_pk",
})

# Etiquetas de comparables (A, B, C, ... AA, AB, ...).
def _alpha_label(i: int) -> str:
    s = ""
    i += 1
    while i > 0:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


class NivelConfidencialidad(str, Enum):
    """Nivel de visibilidad de identidades, de mayor a menor."""
    COMPLETO = "COMPLETO"            # ve todos los nombres + datos técnicos (admin técnico)
    GRUPO_NOMBRES = "GRUPO_NOMBRES"  # ve nombres reales de su grupo (sin técnicos)
    PROPIO_NOMBRES = "PROPIO_NOMBRES"  # ve solo sus unidades; resto anónimo
    ANONIMO = "ANONIMO"              # todo dentro de su scope, anónimo
    AGREGADO = "AGREGADO"            # solo agregados/benchmark (externos)


@dataclass
class ConfidentialityContext:
    """Qué puede ver un usuario. Derivado del RBAC canónico (sin hardcode)."""
    nivel: NivelConfidencialidad = NivelConfidencialidad.ANONIMO
    allowed_server_ids: Set[str] = field(default_factory=set)  # vacío = sin restricción
    ver_nombres_propios: bool = False
    ver_nombres_grupo: bool = False
    ver_datos_tecnicos: bool = False
    ver_nombres_externos: bool = False
    es_externo: bool = False

    def puede_ver_nombre_de(self, server_id: Optional[str], es_propia: bool) -> bool:
        if self.nivel == NivelConfidencialidad.COMPLETO:
            return True
        if es_propia:
            return self.ver_nombres_propios
        # unidad hermana (mismo grupo) no propia
        return self.ver_nombres_grupo


class AnonymizerService:
    """Servicio central de enmascaramiento. Sin estado (métodos estáticos)."""

    # -- Construcción del contexto desde el usuario (rol canónico) -------------
    @staticmethod
    def build_context(
        user: Optional[Dict[str, Any]],
        allowed_server_ids: Optional[Iterable[str]] = None,
    ) -> ConfidentialityContext:
        allowed = {str(s).strip().lower() for s in (allowed_server_ids or []) if s}
        es_portal = bool((user or {}).get("EsUsuarioPortal") or (user or {}).get("es_usuario_portal"))
        code = get_role_code(user)

        if es_superadmin(user):
            return ConfidentialityContext(
                nivel=NivelConfidencialidad.COMPLETO, allowed_server_ids=allowed,
                ver_nombres_propios=True, ver_nombres_grupo=True,
                ver_datos_tecnicos=True, ver_nombres_externos=False,
            )
        # Externos (portal proveedor/cliente): solo agregados, nada de nombres.
        if es_portal:
            return ConfidentialityContext(
                nivel=NivelConfidencialidad.AGREGADO, allowed_server_ids=allowed,
                es_externo=True,
            )
        # Admin / Dirección / Admin comercial: nombres del grupo, sin técnicos.
        if es_admin(user) or code in ("DIRECCION", "ADMIN_COMERCIAL", "CRM_ADMIN"):
            return ConfidentialityContext(
                nivel=NivelConfidencialidad.GRUPO_NOMBRES, allowed_server_ids=allowed,
                ver_nombres_propios=True, ver_nombres_grupo=True,
            )
        # Gerencias / supervisión: ven SUS unidades; el resto del grupo, anónimo.
        if code in ("GERENTE", "GERENTE_OPS", "GERENTE_UNIDAD", "SUPERVISOR", "AUDITOR"):
            return ConfidentialityContext(
                nivel=NivelConfidencialidad.PROPIO_NOMBRES, allowed_server_ids=allowed,
                ver_nombres_propios=True, ver_nombres_grupo=False,
            )
        # Analistas / visores / resto: todo anónimo dentro de su scope.
        return ConfidentialityContext(
            nivel=NivelConfidencialidad.ANONIMO, allowed_server_ids=allowed,
            ver_nombres_propios=False, ver_nombres_grupo=False,
        )

    # -- Helpers de scope ------------------------------------------------------
    @staticmethod
    def _es_propia(ctx: ConfidentialityContext, server_id: Optional[str]) -> bool:
        if not ctx.allowed_server_ids:  # sin restricción = todo es "propio"
            return True
        return str(server_id or "").strip().lower() in ctx.allowed_server_ids

    @staticmethod
    def _alias_map(server_ids: Iterable[Optional[str]], salt: str, prefijo: str) -> Dict[str, str]:
        """Mapa determinista server_id -> 'Prefijo A/B/C'. El orden NO depende
        del valor de las métricas (se ordena por hash con salt) para no filtrar
        ranking salvo que el consumidor lo pida explícitamente."""
        unicos = sorted(
            {str(s) for s in server_ids if s},
            key=lambda s: hashlib.sha256((salt + "|" + s).encode()).hexdigest(),
        )
        return {sid: f"{prefijo} {_alpha_label(i)}" for i, sid in enumerate(unicos)}

    # -- Enmascaramiento de filas ---------------------------------------------
    @staticmethod
    def anonymize_rows(
        rows: List[Dict[str, Any]],
        ctx: ConfidentialityContext,
        *,
        salt: str = "",
        id_key: str = "server_id",
        name_key: str = "unidad_negocio_nombre",
        prefijo_anon: str = "Unidad comparable",
        out_name_key: Optional[str] = None,
        own_ids: Optional[Iterable[Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Devuelve copias de las filas con el nombre enmascarado (si aplica) y
        sin campos técnicos (si el usuario no es admin técnico). Añade
        `nivel_anonimizacion_aplicado` por fila.

        own_ids: si se provee, define explícitamente qué valores de `id_key` son
        "propios" del usuario (útil cuando id_key NO es server_id, p.ej. el código
        de unidad, porque MPRO comparte server entre dos unidades)."""
        out_name_key = out_name_key or name_key
        own_set = {str(x) for x in own_ids} if own_ids is not None else None

        def _propia(row) -> bool:
            if own_set is not None:
                return str(row.get(id_key)) in own_set
            return AnonymizerService._es_propia(ctx, row.get(id_key))

        a_enmascarar = [
            r.get(id_key) for r in rows
            if not ctx.puede_ver_nombre_de(r.get(id_key), _propia(r))
        ]
        alias = AnonymizerService._alias_map(a_enmascarar, salt, prefijo_anon)

        result: List[Dict[str, Any]] = []
        for r in rows:
            row = dict(r)
            sid = r.get(id_key)
            if ctx.puede_ver_nombre_de(sid, _propia(r)):
                row[out_name_key] = r.get(name_key)
                nivel = "REAL"
            else:
                row[out_name_key] = alias.get(str(sid), f"{prefijo_anon} -")
                nivel = "ANONIMO"
            if not ctx.ver_datos_tecnicos:
                for k in list(row.keys()):
                    if k.lower() in CAMPOS_TECNICOS:
                        row.pop(k, None)
            row["nivel_anonimizacion_aplicado"] = nivel
            result.append(row)
        return result

    @staticmethod
    def strip_tecnicos(row: Dict[str, Any], ctx: ConfidentialityContext) -> Dict[str, Any]:
        """Quita campos técnicos de un dict suelto si el usuario no es admin técnico."""
        if ctx.ver_datos_tecnicos:
            return dict(row)
        return {k: v for k, v in row.items() if k.lower() not in CAMPOS_TECNICOS}
