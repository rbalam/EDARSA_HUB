"""
SQL Compat Bridge Repository
Proporciona compatibilidad con endpoints legacy usando las nuevas tablas SQL
"""
import logging
from typing import Dict, List, Optional, Any
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

logger = logging.getLogger(__name__)


class SQLCompatBridgeRepository:
    
    def _get_connection(self):
        return get_edarsahub_pymssql_connection()
    
    # =========================================================
    # CONSULTAS CUSTOM
    # =========================================================
    def listar_consultas_custom(self) -> List[Dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT
                    ConsultaSQLID as id,
                    TipoConsulta as tipo,
                    NombreConsulta as nombre,
                    CodigoConsulta as codigo,
                    Descripcion as descripcion,
                    Categoria as categoria,
                    Modulo as modulo,
                    SystemType as sistema,
                    EmpresaID as empresa_id,
                    ServerID as server_id,
                    QuerySQL as sql,
                    ParametrosJSON as parametros_json,
                    ConfiguracionJSON as configuracion_json,
                    EsPublica as es_publica,
                    Activa as activa,
                    CreatedAt as created_at,
                    CreatedBy as created_by
                FROM dbo.Sistema_ConsultasSQL
                WHERE ISNULL(Activa, 1) = 1
                  AND TipoConsulta = 'CUSTOM'
                ORDER BY NombreConsulta
            """)
            return cur.fetchall() or []
        finally:
            conn.close()

    def crear_consulta_custom(self, payload: Dict, current_user: Dict) -> int:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dbo.Sistema_ConsultasSQL (
                    TipoConsulta, NombreConsulta, CodigoConsulta, Descripcion,
                    Categoria, Modulo, SystemType, EmpresaID, ServerID,
                    QuerySQL, ParametrosJSON, ConfiguracionJSON, EsPublica, Activa, CreatedBy
                )
                VALUES ('CUSTOM', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
            """, (
                payload.get("nombre"),
                payload.get("codigo"),
                payload.get("descripcion"),
                payload.get("categoria"),
                payload.get("modulo"),
                payload.get("sistema"),
                payload.get("empresa_id"),
                payload.get("server_id"),
                payload.get("sql"),
                payload.get("parametros_json"),
                payload.get("configuracion_json"),
                1 if payload.get("es_publica") else 0,
                current_user.get("email") or str(current_user.get("id"))
            ))
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def actualizar_consulta_custom(self, consulta_id: int, payload: Dict, current_user: Dict) -> int:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE dbo.Sistema_ConsultasSQL
                SET
                    NombreConsulta = %s,
                    CodigoConsulta = %s,
                    Descripcion = %s,
                    Categoria = %s,
                    Modulo = %s,
                    SystemType = %s,
                    EmpresaID = %s,
                    ServerID = %s,
                    QuerySQL = %s,
                    ParametrosJSON = %s,
                    ConfiguracionJSON = %s,
                    EsPublica = %s,
                    UpdatedAt = GETDATE(),
                    UpdatedBy = %s
                WHERE ConsultaSQLID = %s
                  AND TipoConsulta = 'CUSTOM'
                  AND ISNULL(Activa, 1) = 1
            """, (
                payload.get("nombre"),
                payload.get("codigo"),
                payload.get("descripcion"),
                payload.get("categoria"),
                payload.get("modulo"),
                payload.get("sistema"),
                payload.get("empresa_id"),
                payload.get("server_id"),
                payload.get("sql"),
                payload.get("parametros_json"),
                payload.get("configuracion_json"),
                1 if payload.get("es_publica") else 0,
                current_user.get("email") or str(current_user.get("id")),
                consulta_id
            ))
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def eliminar_consulta_custom(self, consulta_id: int, current_user: Dict) -> int:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE dbo.Sistema_ConsultasSQL
                SET Activa = 0, UpdatedAt = GETDATE(), UpdatedBy = %s
                WHERE ConsultaSQLID = %s AND TipoConsulta = 'CUSTOM'
            """, (current_user.get("email") or str(current_user.get("id")), consulta_id))
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    # =========================================================
    # SCRIPTS PENDIENTES / EXPLORADOR
    # =========================================================
    def listar_scripts_pendientes_por_server(self, server_id: str) -> List[Dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT
                    ScriptPendienteID as id,
                    TipoScript as tipo,
                    NombreScript as titulo,
                    Descripcion as descripcion,
                    EstadoScript as estado,
                    Prioridad as prioridad,
                    Modulo as modulo,
                    ServerID as server_id,
                    ContenidoScript as script,
                    ParametrosJSON as parametros_json,
                    ResultadoJSON as resultado_json,
                    ErrorTexto as error,
                    FechaProgramada as fecha_programada,
                    FechaEjecucion as fecha_ejecucion,
                    CreatedAt as created_at,
                    CreatedBy as created_by
                FROM dbo.Sistema_ScriptsPendientes
                WHERE ServerID = %s
                ORDER BY CreatedAt DESC
            """, (server_id,))
            return cur.fetchall() or []
        finally:
            conn.close()

    def guardar_script_pendiente(self, server_id: str, payload: Dict, current_user: Dict) -> int:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dbo.Sistema_ScriptsPendientes (
                    TipoScript, NombreScript, Descripcion, EstadoScript, Prioridad,
                    Modulo, ServerID, ContenidoScript, CreatedBy
                )
                VALUES ('SQL', %s, %s, 'PENDIENTE', 'MEDIA', 'EXPLORADOR_BD', %s, %s, %s)
            """, (
                payload.get("titulo"),
                payload.get("descripcion") or payload.get("titulo"),
                server_id,
                payload.get("script"),
                current_user.get("email") or str(current_user.get("id"))
            ))
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()


_repo = None

def get_sql_compat_bridge_repo() -> SQLCompatBridgeRepository:
    global _repo
    if _repo is None:
        _repo = SQLCompatBridgeRepository()
    return _repo
