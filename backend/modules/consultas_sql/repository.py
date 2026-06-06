"""
Repositorio SQL para Consultas SQL (queries y consultas custom)
Reemplaza endpoints MongoDB legacy
"""
import logging
from typing import Dict, List, Optional
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

logger = logging.getLogger(__name__)


class ConsultasSQLRepository:
    
    def _get_connection(self):
        return get_edarsahub_pymssql_connection()
    
    def list_consultas(self, tipo: str = None, modulo: str = None, activa: bool = True) -> List[Dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            sql = """
                SELECT 
                    ConsultaSQLID as id,
                    TipoConsulta as tipo_consulta,
                    NombreConsulta as nombre,
                    CodigoConsulta as codigo,
                    Descripcion as descripcion,
                    Categoria as categoria,
                    Modulo as modulo,
                    SystemType as system_type,
                    EmpresaID as empresa_id,
                    ServerID as server_id,
                    QuerySQL as query_sql,
                    ParametrosJSON as parametros_json,
                    EsPublica as es_publica,
                    Activa as activa,
                    CreatedAt as created_at,
                    CreatedBy as created_by
                FROM dbo.Sistema_ConsultasSQL
                WHERE 1=1
            """
            params = []
            
            if tipo:
                sql += " AND TipoConsulta = %s"
                params.append(tipo)
            if modulo:
                sql += " AND Modulo = %s"
                params.append(modulo)
            if activa is not None:
                sql += " AND Activa = %s"
                params.append(1 if activa else 0)
            
            sql += " ORDER BY Modulo, Categoria, NombreConsulta"
            
            cur.execute(sql, tuple(params) if params else None)
            return cur.fetchall() or []
        finally:
            conn.close()
    
    def get_consulta(self, consulta_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT 
                    ConsultaSQLID as id,
                    TipoConsulta as tipo_consulta,
                    NombreConsulta as nombre,
                    CodigoConsulta as codigo,
                    Descripcion as descripcion,
                    Categoria as categoria,
                    Modulo as modulo,
                    SystemType as system_type,
                    EmpresaID as empresa_id,
                    ServerID as server_id,
                    QuerySQL as query_sql,
                    ParametrosJSON as parametros_json,
                    EsPublica as es_publica,
                    Activa as activa,
                    CreatedAt as created_at,
                    CreatedBy as created_by,
                    UpdatedAt as updated_at
                FROM dbo.Sistema_ConsultasSQL
                WHERE ConsultaSQLID = %s
            """, (consulta_id,))
            return cur.fetchone()
        finally:
            conn.close()
    
    def create_consulta(self, payload: Dict, current_user: Dict) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dbo.Sistema_ConsultasSQL (
                    TipoConsulta, NombreConsulta, CodigoConsulta, Descripcion,
                    Categoria, Modulo, SystemType, EmpresaID, ServerID,
                    QuerySQL, ParametrosJSON, EsPublica, Activa, CreatedBy
                )
                OUTPUT INSERTED.ConsultaSQLID
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                payload.get("tipo_consulta", "QUERY"),
                payload.get("nombre", "Sin nombre"),
                payload.get("codigo"),
                payload.get("descripcion"),
                payload.get("categoria"),
                payload.get("modulo"),
                payload.get("system_type"),
                payload.get("empresa_id"),
                payload.get("server_id"),
                payload.get("query_sql", "SELECT 1"),
                payload.get("parametros_json"),
                1 if payload.get("es_publica") else 0,
                1,
                current_user.get("email")
            ))
            result = cur.fetchone()
            conn.commit()
            return {"id": result[0] if result else None, "success": True}
        except Exception as e:
            logger.error(f"Error create_consulta: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def update_consulta(self, consulta_id: int, payload: Dict, current_user: Dict) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE dbo.Sistema_ConsultasSQL
                SET
                    TipoConsulta = COALESCE(%s, TipoConsulta),
                    NombreConsulta = COALESCE(%s, NombreConsulta),
                    CodigoConsulta = %s,
                    Descripcion = %s,
                    Categoria = %s,
                    Modulo = %s,
                    SystemType = %s,
                    EmpresaID = %s,
                    ServerID = %s,
                    QuerySQL = COALESCE(%s, QuerySQL),
                    ParametrosJSON = %s,
                    EsPublica = %s,
                    Activa = %s,
                    UpdatedAt = GETDATE()
                WHERE ConsultaSQLID = %s
            """, (
                payload.get("tipo_consulta"),
                payload.get("nombre"),
                payload.get("codigo"),
                payload.get("descripcion"),
                payload.get("categoria"),
                payload.get("modulo"),
                payload.get("system_type"),
                payload.get("empresa_id"),
                payload.get("server_id"),
                payload.get("query_sql"),
                payload.get("parametros_json"),
                1 if payload.get("es_publica") else 0,
                1 if payload.get("activa", True) else 0,
                consulta_id
            ))
            conn.commit()
            return {"success": True, "updated": cur.rowcount > 0}
        except Exception as e:
            logger.error(f"Error update_consulta: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def delete_consulta(self, consulta_id: int) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE dbo.Sistema_ConsultasSQL
                SET Activa = 0, UpdatedAt = GETDATE()
                WHERE ConsultaSQLID = %s
            """, (consulta_id,))
            conn.commit()
            return {"success": True, "deleted": cur.rowcount > 0}
        except Exception as e:
            logger.error(f"Error delete_consulta: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()


_repo = None

def get_consultas_sql_repo() -> ConsultasSQLRepository:
    global _repo
    if _repo is None:
        _repo = ConsultasSQLRepository()
    return _repo
