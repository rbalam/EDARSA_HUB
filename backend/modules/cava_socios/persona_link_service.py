"""
EDARSA HUB - Cava de Socios Persona Link Service
================================================
Orquestación transaccional para vincular la membresía Cava con la identidad BOS.

Reglas:
- SocioID sigue siendo la identidad operacional de la membresía.
- PersonaID apunta a dbo.Gobierno_Persona.
- ClienteID, cuando aplica, se vincula vía dbo.Gobierno_PersonaVinculo.
- No hay matching automático por nombre, email o teléfono.
- La desvinculación de Cava no elimina Persona ni vínculos canónicos.
"""

import uuid
from typing import Any, Dict, List, Optional

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection


class CavaSociosPersonaLinkService:
    """Integración transaccional Cava -> BOS Persona."""

    def _get_connection(self):
        return get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)

    @staticmethod
    def _normalize_uuid(value: Optional[str]) -> Optional[str]:
        if value in (None, ""):
            return None
        return str(uuid.UUID(str(value)))

    @staticmethod
    def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    def buscar_personas(self, search: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Búsqueda explícita para selección humana; no realiza matching automático."""
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            params: List[Any] = []
            where = ["p.Activo = 1"]
            term = self._normalize_optional_text(search)
            if term:
                like = f"%{term}%"
                where.append(
                    "(p.Nombre LIKE %s OR p.ApellidoPaterno LIKE %s OR "
                    "p.ApellidoMaterno LIKE %s OR p.RFC = %s OR p.CURP = %s)"
                )
                params.extend([like, like, like, term.upper(), term.upper()])
            params.append(limit)
            cur.execute(
                f"""
                SELECT TOP (%s)
                    p.PersonaID,
                    CONVERT(varchar(36), p.PublicUUID) AS PublicUUID,
                    p.Nombre,
                    p.ApellidoPaterno,
                    p.ApellidoMaterno,
                    p.RFC,
                    p.CURP,
                    p.Activo
                FROM dbo.Gobierno_Persona p
                WHERE {' AND '.join(where)}
                ORDER BY p.Nombre, p.ApellidoPaterno, p.PersonaID
                """,
                [params[-1]] + params[:-1],
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def obtener_link(self, socio_id: str, empresa_id: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                """
                SELECT
                    CONVERT(varchar(36), s.SocioID) AS SocioID,
                    CONVERT(varchar(36), s.EmpresaID) AS EmpresaID,
                    s.NumeroSocio,
                    s.NombreCompleto,
                    s.PersonaID,
                    p.PersonaID AS PersonaExiste,
                    CONVERT(varchar(36), p.PublicUUID) AS PersonaPublicUUID,
                    p.Nombre,
                    p.ApellidoPaterno,
                    p.ApellidoMaterno,
                    p.RFC,
                    p.CURP,
                    p.Activo AS PersonaActiva
                FROM dbo.CavaSocios_Socios s
                LEFT JOIN dbo.Gobierno_Persona p ON p.PersonaID = s.PersonaID
                WHERE s.SocioID = %s AND s.EmpresaID = %s
                """,
                (socio_id, empresa_id),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Socio no encontrado o no pertenece a esta empresa")

            links: List[Dict[str, Any]] = []
            if row.get("PersonaID") is not None:
                cur.execute(
                    """
                    SELECT
                        v.VinculoID,
                        v.ClienteID,
                        v.EsPrincipal,
                        v.Activo,
                        c.CodigoCliente,
                        c.RazonSocial,
                        c.NombreComercial,
                        c.Activo AS ClienteActivo
                    FROM dbo.Gobierno_PersonaVinculo v
                    LEFT JOIN dbo.Cliente_Catalogo c ON c.ClienteID = v.ClienteID
                    WHERE v.PersonaID = %s
                      AND v.Activo = 1
                    ORDER BY v.EsPrincipal DESC, v.VinculoID
                    """,
                    (row["PersonaID"],),
                )
                links = [dict(item) for item in cur.fetchall()]

            return {
                "socio_id": row["SocioID"],
                "empresa_id": row["EmpresaID"],
                "numero_socio": row["NumeroSocio"],
                "nombre_completo": row["NombreCompleto"],
                "persona_id": int(row["PersonaID"]) if row.get("PersonaID") is not None else None,
                "persona": None if row.get("PersonaID") is None else {
                    "persona_id": int(row["PersonaID"]),
                    "public_uuid": row.get("PersonaPublicUUID"),
                    "nombre": row.get("Nombre"),
                    "apellido_paterno": row.get("ApellidoPaterno"),
                    "apellido_materno": row.get("ApellidoMaterno"),
                    "rfc": row.get("RFC"),
                    "curp": row.get("CURP"),
                    "activo": bool(row.get("PersonaActiva")),
                },
                "vinculos": links,
            }
        finally:
            conn.close()

    def _locked_socio(self, cur, socio_id: str, empresa_id: str) -> Dict[str, Any]:
        cur.execute(
            """
            SELECT SocioID, PersonaID
            FROM dbo.CavaSocios_Socios WITH (UPDLOCK, HOLDLOCK)
            WHERE SocioID = %s AND EmpresaID = %s
            """,
            (socio_id, empresa_id),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Socio no encontrado o no pertenece a esta empresa")
        return row

    def _ensure_persona(self, cur, persona_id: int) -> None:
        cur.execute(
            "SELECT PersonaID FROM dbo.Gobierno_Persona WHERE PersonaID = %s AND Activo = 1",
            (persona_id,),
        )
        if not cur.fetchone():
            raise ValueError("Persona canónica no encontrada o inactiva")

    def _ensure_cliente_link(
        self,
        cur,
        persona_id: int,
        cliente_id: Optional[int],
        usuario_sql_id: int,
    ) -> Optional[int]:
        if cliente_id is None:
            return None

        cur.execute(
            "SELECT ClienteID FROM dbo.Cliente_Catalogo WHERE ClienteID = %s AND Activo = 1",
            (cliente_id,),
        )
        if not cur.fetchone():
            raise ValueError("Cliente canónico no encontrado o inactivo")

        cur.execute(
            """
            SELECT VinculoID, PersonaID, Activo
            FROM dbo.Gobierno_PersonaVinculo WITH (UPDLOCK, HOLDLOCK)
            WHERE ClienteID = %s
            """,
            (cliente_id,),
        )
        existing = cur.fetchone()
        if existing:
            if int(existing["PersonaID"]) != int(persona_id):
                raise ValueError("El cliente canónico ya está vinculado a otra Persona")
            if not bool(existing["Activo"]):
                cur.execute(
                    """
                    UPDATE dbo.Gobierno_PersonaVinculo
                    SET Activo = 1
                    WHERE VinculoID = %s
                    """,
                    (existing["VinculoID"],),
                )
            return int(existing["VinculoID"])

        cur.execute(
            """
            INSERT INTO dbo.Gobierno_PersonaVinculo
                (PersonaID, ClienteID, EsPrincipal, Activo, UsuarioAltaID)
            OUTPUT INSERTED.VinculoID
            VALUES (%s, %s, 1, 1, %s)
            """,
            (persona_id, cliente_id, usuario_sql_id),
        )
        inserted = cur.fetchone()
        return int(inserted["VinculoID"])

    def _update_socio_persona(
        self,
        cur,
        socio_id: str,
        empresa_id: str,
        persona_id: Optional[int],
        usuario_public_uuid: Optional[str],
    ) -> None:
        actor_uuid = self._normalize_uuid(usuario_public_uuid)
        cur.execute(
            """
            UPDATE dbo.CavaSocios_Socios
            SET PersonaID = %s,
                FechaModificacion = SYSUTCDATETIME(),
                UsuarioModificacionID = COALESCE(%s, UsuarioModificacionID)
            WHERE SocioID = %s AND EmpresaID = %s
            """,
            (persona_id, actor_uuid, socio_id, empresa_id),
        )

    def vincular_persona_existente(
        self,
        socio_id: str,
        empresa_id: str,
        persona_id: int,
        cliente_id: Optional[int],
        usuario_sql_id: int,
        usuario_public_uuid: Optional[str],
    ) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            socio = self._locked_socio(cur, socio_id, empresa_id)
            current = socio.get("PersonaID")
            if current is not None and int(current) != int(persona_id):
                raise ValueError("El socio ya está vinculado a otra Persona; desvincule explícitamente primero")

            self._ensure_persona(cur, persona_id)
            vinculo_id = self._ensure_cliente_link(cur, persona_id, cliente_id, usuario_sql_id)

            if current is None:
                self._update_socio_persona(
                    cur, socio_id, empresa_id, persona_id, usuario_public_uuid
                )

            conn.commit()
            return {
                "socio_id": str(socio_id),
                "persona_id": int(persona_id),
                "cliente_id": int(cliente_id) if cliente_id is not None else None,
                "vinculo_id": vinculo_id,
                "idempotent": current is not None and int(current) == int(persona_id),
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def crear_persona_y_vincular(
        self,
        socio_id: str,
        empresa_id: str,
        persona: Dict[str, Any],
        cliente_id: Optional[int],
        usuario_sql_id: int,
        usuario_public_uuid: Optional[str],
    ) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            socio = self._locked_socio(cur, socio_id, empresa_id)
            if socio.get("PersonaID") is not None:
                raise ValueError("El socio ya tiene PersonaID; no se creará una identidad duplicada")

            rfc = self._normalize_optional_text(persona.get("rfc"))
            curp = self._normalize_optional_text(persona.get("curp"))
            rfc = rfc.upper() if rfc else None
            curp = curp.upper() if curp else None

            if rfc:
                cur.execute(
                    "SELECT PersonaID FROM dbo.Gobierno_Persona WHERE RFC = %s",
                    (rfc,),
                )
                if cur.fetchone():
                    raise ValueError("Ya existe una Persona con ese RFC; seleccione la Persona existente")
            if curp:
                cur.execute(
                    "SELECT PersonaID FROM dbo.Gobierno_Persona WHERE CURP = %s",
                    (curp,),
                )
                if cur.fetchone():
                    raise ValueError("Ya existe una Persona con ese CURP; seleccione la Persona existente")

            cur.execute(
                """
                INSERT INTO dbo.Gobierno_Persona
                    (Nombre, ApellidoPaterno, ApellidoMaterno, RFC, CURP,
                     FechaNacimiento, Nacionalidad, UsuarioActualizacionID)
                OUTPUT INSERTED.PersonaID
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    self._normalize_optional_text(persona.get("nombre")),
                    self._normalize_optional_text(persona.get("apellido_paterno")),
                    self._normalize_optional_text(persona.get("apellido_materno")),
                    rfc,
                    curp,
                    persona.get("fecha_nacimiento"),
                    self._normalize_optional_text(persona.get("nacionalidad")),
                    usuario_sql_id,
                ),
            )
            inserted = cur.fetchone()
            persona_id = int(inserted["PersonaID"])

            vinculo_id = self._ensure_cliente_link(
                cur, persona_id, cliente_id, usuario_sql_id
            )
            self._update_socio_persona(
                cur, socio_id, empresa_id, persona_id, usuario_public_uuid
            )
            conn.commit()
            return {
                "socio_id": str(socio_id),
                "persona_id": persona_id,
                "cliente_id": int(cliente_id) if cliente_id is not None else None,
                "vinculo_id": vinculo_id,
                "created_persona": True,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def desvincular_persona(
        self,
        socio_id: str,
        empresa_id: str,
        usuario_public_uuid: Optional[str],
    ) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            socio = self._locked_socio(cur, socio_id, empresa_id)
            current = socio.get("PersonaID")
            if current is None:
                conn.commit()
                return {
                    "socio_id": str(socio_id),
                    "persona_id_anterior": None,
                    "idempotent": True,
                    "canonical_records_deleted": False,
                }

            self._update_socio_persona(
                cur, socio_id, empresa_id, None, usuario_public_uuid
            )
            conn.commit()
            return {
                "socio_id": str(socio_id),
                "persona_id_anterior": int(current),
                "idempotent": False,
                "canonical_records_deleted": False,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_cava_socios_persona_link_service() -> CavaSociosPersonaLinkService:
    return CavaSociosPersonaLinkService()
