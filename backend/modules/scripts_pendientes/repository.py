"""
Repositorio SQL para Scripts Pendientes
Reemplaza endpoints MongoDB legacy
"""
import logging
from typing import Dict, List, Optional
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

logger = logging.getLogger(__name__)


class ScriptsPendientesRepository:
    
    def _get_connection(self):
        return get_edarsahub_pymssql_connection()
    
    def list_scripts(self, estado: str = None, modulo: str = None) -> List[Dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            sql = """
                SELECT 
                    ScriptPendienteID as id,
                    TipoScript as tipo_script,
                    NombreScript as nombre,
                    Descripcion as descripcion,
                    EstadoScript as estado,
                    Prioridad as prioridad,
                    Modulo as modulo,
                    EmpresaID as empresa_id,
                    ServerID as server_id,
                    ContenidoScript as contenido,
                    ParametrosJSON as parametros_json,
                    ResultadoJSON as resultado_json,
                    ErrorTexto as error,
                    FechaProgramada as fecha_programada,
                    FechaEjecucion as fecha_ejecucion,
                    CreatedAt as created_at,
                    CreatedBy as created_by
                FROM dbo.Sistema_ScriptsPendientes
                WHERE 1=1
            """
            params = []
            
            if estado:
                sql += " AND EstadoScript = %s"
                params.append(estado)
            if modulo:
                sql += " AND Modulo = %s"
                params.append(modulo)
            
            sql += " ORDER BY CASE Prioridad WHEN 'ALTA' THEN 1 WHEN 'MEDIA' THEN 2 ELSE 3 END, CreatedAt DESC"
            
            cur.execute(sql, tuple(params) if params else None)
            return cur.fetchall() or []
        finally:
            conn.close()
    
    def get_script(self, script_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT 
                    ScriptPendienteID as id,
                    TipoScript as tipo_script,
                    NombreScript as nombre,
                    Descripcion as descripcion,
                    EstadoScript as estado,
                    Prioridad as prioridad,
                    Modulo as modulo,
                    EmpresaID as empresa_id,
                    ServerID as server_id,
                    ContenidoScript as contenido,
                    ParametrosJSON as parametros_json,
                    ResultadoJSON as resultado_json,
                    ErrorTexto as error,
                    FechaProgramada as fecha_programada,
                    FechaEjecucion as fecha_ejecucion,
                    CreatedAt as created_at,
                    CreatedBy as created_by,
                    UpdatedAt as updated_at
                FROM dbo.Sistema_ScriptsPendientes
                WHERE ScriptPendienteID = %s
            """, (script_id,))
            return cur.fetchone()
        finally:
            conn.close()
    
    def create_script(self, payload: Dict, current_user: Dict) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dbo.Sistema_ScriptsPendientes (
                    TipoScript, NombreScript, Descripcion, EstadoScript, Prioridad,
                    Modulo, EmpresaID, ServerID, ContenidoScript, ParametrosJSON,
                    FechaProgramada, CreatedBy
                )
                OUTPUT INSERTED.ScriptPendienteID
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                payload.get("tipo_script", "SQL"),
                payload.get("nombre", "Script sin nombre"),
                payload.get("descripcion"),
                payload.get("estado", "PENDIENTE"),
                payload.get("prioridad", "MEDIA"),
                payload.get("modulo"),
                payload.get("empresa_id"),
                payload.get("server_id"),
                payload.get("contenido"),
                payload.get("parametros_json"),
                payload.get("fecha_programada"),
                current_user.get("email")
            ))
            result = cur.fetchone()
            conn.commit()
            return {"id": result[0] if result else None, "success": True}
        except Exception as e:
            logger.error(f"Error create_script: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def update_script(self, script_id: int, payload: Dict, current_user: Dict) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE dbo.Sistema_ScriptsPendientes
                SET
                    TipoScript = COALESCE(%s, TipoScript),
                    NombreScript = COALESCE(%s, NombreScript),
                    Descripcion = %s,
                    EstadoScript = COALESCE(%s, EstadoScript),
                    Prioridad = %s,
                    Modulo = %s,
                    EmpresaID = %s,
                    ServerID = %s,
                    ContenidoScript = %s,
                    ParametrosJSON = %s,
                    ResultadoJSON = %s,
                    ErrorTexto = %s,
                    FechaProgramada = %s,
                    FechaEjecucion = %s,
                    UpdatedAt = GETDATE()
                WHERE ScriptPendienteID = %s
            """, (
                payload.get("tipo_script"),
                payload.get("nombre"),
                payload.get("descripcion"),
                payload.get("estado"),
                payload.get("prioridad"),
                payload.get("modulo"),
                payload.get("empresa_id"),
                payload.get("server_id"),
                payload.get("contenido"),
                payload.get("parametros_json"),
                payload.get("resultado_json"),
                payload.get("error"),
                payload.get("fecha_programada"),
                payload.get("fecha_ejecucion"),
                script_id
            ))
            conn.commit()
            return {"success": True, "updated": cur.rowcount > 0}
        except Exception as e:
            logger.error(f"Error update_script: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def delete_script(self, script_id: int) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE dbo.Sistema_ScriptsPendientes
                SET EstadoScript = 'CANCELADO', UpdatedAt = GETDATE()
                WHERE ScriptPendienteID = %s
            """, (script_id,))
            conn.commit()
            return {"success": True, "deleted": cur.rowcount > 0}
        except Exception as e:
            logger.error(f"Error delete_script: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()


_repo = None

def get_scripts_pendientes_repo() -> ScriptsPendientesRepository:
    global _repo
    if _repo is None:
        _repo = ScriptsPendientesRepository()
    return _repo
