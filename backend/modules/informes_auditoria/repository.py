"""
Repositorio SQL para Informes de Auditoría
Reemplaza endpoints MongoDB legacy
"""
import logging
from typing import Dict, List, Optional, Any
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

logger = logging.getLogger(__name__)


class InformesAuditoriaRepository:
    
    def _get_connection(self):
        return get_edarsahub_pymssql_connection()
    
    def list_informes(self, filtros: Dict = None) -> List[Dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            sql = """
                SELECT 
                    InformeAuditoriaID as id,
                    TipoInforme as tipo_informe,
                    TituloInforme as titulo_informe,
                    FolioReferencia as folio_referencia,
                    EmpresaID as empresa_id,
                    AreaAuditada as area_auditada,
                    FechaAuditoria as fecha_auditoria,
                    FechaInforme as fecha_informe,
                    EstadoInforme as estado_informe,
                    ResumenEjecutivo as resumen_ejecutivo,
                    Observaciones as observaciones,
                    Dictamen as dictamen,
                    DocumentoURL as documento_url,
                    ElaboradoPorUsuarioID as elaborado_por_usuario_id,
                    CreatedAt as created_at,
                    CreatedBy as created_by,
                    UpdatedAt as updated_at
                FROM dbo.Auditoria_Informes
                WHERE 1=1
            """
            params = []
            
            if filtros:
                if filtros.get('empresa_id'):
                    sql += " AND EmpresaID = %s"
                    params.append(filtros['empresa_id'])
                if filtros.get('estado'):
                    sql += " AND EstadoInforme = %s"
                    params.append(filtros['estado'])
                if filtros.get('tipo'):
                    sql += " AND TipoInforme = %s"
                    params.append(filtros['tipo'])
            
            sql += " ORDER BY FechaInforme DESC, CreatedAt DESC"
            
            cur.execute(sql, tuple(params) if params else None)
            return cur.fetchall() or []
        finally:
            conn.close()
    
    def get_informe(self, informe_id: int) -> Optional[Dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT 
                    InformeAuditoriaID as id,
                    TipoInforme as tipo_informe,
                    TituloInforme as titulo_informe,
                    FolioReferencia as folio_referencia,
                    EmpresaID as empresa_id,
                    AreaAuditada as area_auditada,
                    FechaAuditoria as fecha_auditoria,
                    FechaInforme as fecha_informe,
                    EstadoInforme as estado_informe,
                    ResumenEjecutivo as resumen_ejecutivo,
                    ContenidoJSON as contenido_json,
                    Observaciones as observaciones,
                    Dictamen as dictamen,
                    DocumentoURL as documento_url,
                    ElaboradoPorUsuarioID as elaborado_por_usuario_id,
                    CreatedAt as created_at,
                    CreatedBy as created_by,
                    UpdatedAt as updated_at
                FROM dbo.Auditoria_Informes
                WHERE InformeAuditoriaID = %s
            """, (informe_id,))
            return cur.fetchone()
        finally:
            conn.close()
    
    def create_informe(self, payload: Dict, current_user: Dict) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO dbo.Auditoria_Informes (
                    TipoInforme, TituloInforme, FolioReferencia, EmpresaID,
                    AreaAuditada, FechaAuditoria, FechaInforme, EstadoInforme,
                    ResumenEjecutivo, ContenidoJSON, Observaciones, Dictamen,
                    DocumentoURL, ElaboradoPorUsuarioID, CreatedBy
                )
                OUTPUT INSERTED.InformeAuditoriaID
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                payload.get("tipo_informe", "GENERAL"),
                payload.get("titulo_informe", "Sin título"),
                payload.get("folio_referencia"),
                payload.get("empresa_id"),
                payload.get("area_auditada"),
                payload.get("fecha_auditoria"),
                payload.get("fecha_informe"),
                payload.get("estado_informe", "BORRADOR"),
                payload.get("resumen_ejecutivo"),
                payload.get("contenido_json"),
                payload.get("observaciones"),
                payload.get("dictamen"),
                payload.get("documento_url"),
                current_user.get("UsuarioID") or current_user.get("id"),
                current_user.get("email")
            ))
            result = cur.fetchone()
            conn.commit()
            return {"id": result[0] if result else None, "success": True}
        except Exception as e:
            logger.error(f"Error create_informe: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def update_informe(self, informe_id: int, payload: Dict, current_user: Dict) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE dbo.Auditoria_Informes
                SET
                    TipoInforme = COALESCE(%s, TipoInforme),
                    TituloInforme = COALESCE(%s, TituloInforme),
                    FolioReferencia = %s,
                    EmpresaID = %s,
                    AreaAuditada = %s,
                    FechaAuditoria = %s,
                    FechaInforme = %s,
                    EstadoInforme = COALESCE(%s, EstadoInforme),
                    ResumenEjecutivo = %s,
                    ContenidoJSON = %s,
                    Observaciones = %s,
                    Dictamen = %s,
                    DocumentoURL = %s,
                    UpdatedAt = GETDATE()
                WHERE InformeAuditoriaID = %s
            """, (
                payload.get("tipo_informe"),
                payload.get("titulo_informe"),
                payload.get("folio_referencia"),
                payload.get("empresa_id"),
                payload.get("area_auditada"),
                payload.get("fecha_auditoria"),
                payload.get("fecha_informe"),
                payload.get("estado_informe"),
                payload.get("resumen_ejecutivo"),
                payload.get("contenido_json"),
                payload.get("observaciones"),
                payload.get("dictamen"),
                payload.get("documento_url"),
                informe_id
            ))
            
            # Registrar historial
            cur.execute("""
                INSERT INTO dbo.Auditoria_InformesHistorial (
                    InformeAuditoriaID, EventoTipo, EventoDetalle, UsuarioID, CreatedBy
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                informe_id,
                'EDICION',
                'Actualización de informe',
                current_user.get("UsuarioID") or current_user.get("id"),
                current_user.get("email")
            ))
            
            conn.commit()
            return {"success": True, "updated": cur.rowcount > 0}
        except Exception as e:
            logger.error(f"Error update_informe: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def delete_informe(self, informe_id: int, current_user: Dict) -> Dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            # Soft delete
            cur.execute("""
                UPDATE dbo.Auditoria_Informes
                SET EstadoInforme = 'CANCELADO', UpdatedAt = GETDATE()
                WHERE InformeAuditoriaID = %s
            """, (informe_id,))
            
            # Registrar historial
            cur.execute("""
                INSERT INTO dbo.Auditoria_InformesHistorial (
                    InformeAuditoriaID, EventoTipo, EventoDetalle, UsuarioID, CreatedBy
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                informe_id,
                'CANCELACION',
                'Informe cancelado',
                current_user.get("UsuarioID") or current_user.get("id"),
                current_user.get("email")
            ))
            
            conn.commit()
            return {"success": True, "deleted": cur.rowcount > 0}
        except Exception as e:
            logger.error(f"Error delete_informe: {e}")
            return {"success": False, "error": str(e)}
        finally:
            conn.close()


# Singleton
_repo = None

def get_informes_auditoria_repo() -> InformesAuditoriaRepository:
    global _repo
    if _repo is None:
        _repo = InformesAuditoriaRepository()
    return _repo
