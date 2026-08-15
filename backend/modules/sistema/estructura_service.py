from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Servicio de Estructura Organizacional (FASE 2)
============================================================

Servicio AISLADO para consulta de estructura organizacional.
- Solo lectura
- No modifica datos funcionales
- No participa en validación de permisos
- Desacoplado del flujo principal

Creado: Diciembre 2025
Fase: FASE 2 - Visualización
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

# Configurar logger para bitácora interna
logger = logging.getLogger("estructura_service")


class EstructuraService:
    """
    Servicio para consultar estructura organizacional.
    Solo lectura - no modifica datos funcionales.
    """
    
    def __init__(self, db):
        self.db = db
    

    def _sql_rows(self, sql: str, params: tuple = ()) -> list:
        from modules.compras.sync_service import get_edarsahub_connection
        conn = get_edarsahub_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, params)
            return cur.fetchall() or []
        finally:
            conn.close()

    def _sql_one(self, sql: str, params: tuple = ()) -> dict:
        rows = self._sql_rows(sql, params)
        return rows[0] if rows else None

    def _sql_exec(self, sql: str, params: tuple = ()) -> None:
        from modules.compras.sync_service import get_edarsahub_connection
        conn = get_edarsahub_connection()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _sql_next_id(self, table: str, col: str) -> int:
        row = self._sql_one(f"SELECT ISNULL(MAX({col}),0)+1 AS NextID FROM dbo.{table} WITH (UPDLOCK,HOLDLOCK)")
        return int((row or {}).get("NextID") or 1)

    async def get_estructura_organizacional(self) -> Dict:
        """
        Obtiene la estructura organizacional completa.
        Retorna empresas con sus unidades y sucursales.
        
        NOTA: Si db es None (SQL-only mode), retorna estructura vacía.
        """
        try:
            # SQL-FIRST P3: estructura desde Sistema_Empresas, Unidades_Negocio y Sistema_Sucursales
            empresas = self._sql_rows("""
                SELECT EmpresaID, CodigoEmpresa, NombreEmpresa, NombreComercial
                FROM dbo.Sistema_Empresas
                WHERE Activo=1
                ORDER BY NombreEmpresa
            """)

            unidades = self._sql_rows("""
                SELECT
                    id,
                    codigo,
                    nombre,
                    server_id,
                    sucursal_origen_id,
                    system_type,
                    activo,
                    orden
                FROM dbo.Unidades_Negocio
                WHERE ISNULL(activo,1)=1
                ORDER BY orden, nombre
            """)

            sucursales = self._sql_rows("""
                SELECT
                    s.SucursalID,
                    s.CodigoSucursal,
                    s.NombreSucursal,
                    s.EmpresaID,
                    s.MongoUUID,
                    u.id AS UnidadNegocioPK
                FROM dbo.Sistema_Sucursales s
                INNER JOIN dbo.Sistema_SucursalServidorMapeo m
                  ON m.SucursalID = s.SucursalID
                 AND ISNULL(m.Activo,0)=1
                INNER JOIN dbo.Unidades_Negocio u
                  ON LOWER(CONVERT(nvarchar(100), u.server_id))
                     =
                     LOWER(CONVERT(nvarchar(100), m.ServidorID))
                 AND (
                        NULLIF(
                            LTRIM(RTRIM(CONVERT(nvarchar(50), u.sucursal_origen_id))),
                            ''
                        )
                        =
                        NULLIF(
                            LTRIM(RTRIM(CONVERT(nvarchar(50), m.SucursalOrigenID))),
                            ''
                        )
                        OR (
                            NULLIF(
                                LTRIM(RTRIM(CONVERT(nvarchar(50), u.sucursal_origen_id))),
                                ''
                            ) IS NULL
                            AND
                            NULLIF(
                                LTRIM(RTRIM(CONVERT(nvarchar(50), m.SucursalOrigenID))),
                                ''
                            ) IS NULL
                        )
                     )
                WHERE
                    ISNULL(s.Activo,0)=1
                    AND ISNULL(u.activo,1)=1
                ORDER BY s.NombreSucursal
            """)

            sucursales_por_unidad = {}
            for suc in sucursales:
                key = str(suc.get("UnidadNegocioPK") or "")
                sucursales_por_unidad.setdefault(key, []).append({
                    "id": suc.get("SucursalID"),
                    "codigo": suc.get("CodigoSucursal"),
                    "nombre": suc.get("NombreSucursal"),
                    "mongo_uuid": suc.get("MongoUUID")
                })

            unidades_data = []
            for unidad in unidades:
                unidad_id = unidad.get("id")
                unidades_data.append({
                    "id": str(unidad_id),
                    "codigo": unidad.get("codigo"),
                    "nombre": unidad.get("nombre"),
                    "tipo_unidad": unidad.get("system_type") or "SIN_CLASIFICAR",
                    "visible_usuario": True,
                    "sucursales": sucursales_por_unidad.get(str(unidad_id), [])
                })

            resultado = []
            for empresa in empresas:
                resultado.append({
                    "id": empresa.get("EmpresaID"),
                    "codigo": empresa.get("CodigoEmpresa"),
                    "nombre": empresa.get("NombreComercial") or empresa.get("NombreEmpresa"),
                    "unidades_negocio": unidades_data
                })

            return {
                "empresas": resultado,
                "total_empresas": len(resultado),
                "total_unidades": len(unidades_data),
                "total_sucursales": len(sucursales),
                "fase": "FASE_2_SQL_FIRST",
                "estado": "SOLO_VISUALIZACION"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estructura: {e}")
            return {
                "empresas": [],
                "total_empresas": 0,
                "error": "Error interno",
                "fase": "FASE_2"
            }
    
    async def get_mapeo_servidores(self) -> Dict:
        """
        Obtiene el mapeo entre servidores y sucursales.
        Solo lectura informativa.
        """
        try:
            rows = self._sql_rows("""
                SELECT
                    m.ServidorID,
                    m.SucursalID,
                    m.SucursalOrigenID,
                    m.MongoSucursalUUID,
                    s.CodigoSucursal,
                    s.NombreSucursal,
                    s.EmpresaID,
                    u.id AS UnidadNegocioPK
                FROM dbo.Sistema_SucursalServidorMapeo m
                LEFT JOIN dbo.Sistema_Sucursales s
                  ON s.SucursalID=m.SucursalID
                LEFT JOIN dbo.Unidades_Negocio u
                  ON LOWER(CONVERT(nvarchar(100), u.server_id))
                     =
                     LOWER(CONVERT(nvarchar(100), m.ServidorID))
                 AND (
                        NULLIF(
                            LTRIM(RTRIM(CONVERT(nvarchar(50), u.sucursal_origen_id))),
                            ''
                        )
                        =
                        NULLIF(
                            LTRIM(RTRIM(CONVERT(nvarchar(50), m.SucursalOrigenID))),
                            ''
                        )
                        OR (
                            NULLIF(
                                LTRIM(RTRIM(CONVERT(nvarchar(50), u.sucursal_origen_id))),
                                ''
                            ) IS NULL
                            AND
                            NULLIF(
                                LTRIM(RTRIM(CONVERT(nvarchar(50), m.SucursalOrigenID))),
                                ''
                            ) IS NULL
                        )
                     )
                 AND ISNULL(u.activo,1)=1
                WHERE m.Activo=1
                ORDER BY s.NombreSucursal
            """)

            resultado = []
            for r in rows:
                resultado.append({
                    "server_id": str(r.get("ServidorID")),
                    "server_name": None,
                    "server_type": None,
                    "sucursal_id": r.get("SucursalID"),
                    "sucursal_origen_id": r.get("SucursalOrigenID"),
                    "sucursal_nombre": r.get("NombreSucursal"),
                    "unidad_negocio_pk": (
                        str(r.get("UnidadNegocioPK"))
                        if r.get("UnidadNegocioPK")
                        else None
                    ),
                    "empresa_id": r.get("EmpresaID"),
                    "mongo_sucursal_uuid": r.get("MongoSucursalUUID")
                })

            return {
                "mapeos": resultado,
                "total": len(resultado),
                "fase": "FASE_2_SQL_FIRST",
                "nota": "Mapeo informativo - servidor es dimension tecnica"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo mapeos: {e}")
            return {
                "mapeos": [],
                "total": 0,
                "error": "Error interno"
            }
    
    async def get_permisos_catalogo_v2(self) -> Dict:
        """
        Obtiene el catálogo de permisos v2.
        Solo informativo - no reemplaza catálogo legacy.
        """
        try:
            permisos = self._sql_rows("""
                SELECT TOP 500
                    m.CodigoModulo,
                    m.NombreModulo,
                    m.Ruta,
                    a.CodigoAccion,
                    a.NombreAccion,
                    r.CodigoRol,
                    r.NombreRol,
                    prm.Permitido,
                    prm.RequiereAutorizacion
                FROM dbo.Usuario_PermisosRolModulo prm
                INNER JOIN dbo.Usuario_Modulos m ON m.ModuloID=prm.ModuloID
                INNER JOIN dbo.Usuario_Acciones a ON a.AccionID=prm.AccionID
                INNER JOIN dbo.Usuario_Roles r ON r.RolID=prm.RolID
                WHERE prm.Activo=1 AND m.Activo=1 AND r.Activo=1
                ORDER BY m.OrdenMenu, m.NombreModulo, a.NombreAccion
            """)

            por_modulo = {}
            for perm in permisos:
                modulo = perm.get("CodigoModulo") or "sin_modulo"
                por_modulo.setdefault(modulo, []).append({
                    "codigo": f"{perm.get('CodigoModulo')}.{perm.get('CodigoAccion')}",
                    "submodulo": perm.get("Ruta"),
                    "accion": perm.get("CodigoAccion"),
                    "descripcion": perm.get("NombreAccion"),
                    "rol": perm.get("CodigoRol"),
                    "permitido": bool(perm.get("Permitido")),
                    "requiere_autorizacion": bool(perm.get("RequiereAutorizacion"))
                })

            return {
                "permisos_por_modulo": por_modulo,
                "total_permisos": len(permisos),
                "total_modulos": len(por_modulo),
                "fase": "FASE_2_SQL_FIRST",
                "nota": "Catalogo informativo desde RBAC canónico SQL"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo permisos: {e}")
            return {
                "permisos_por_modulo": {},
                "total_permisos": 0,
                "error": "Error interno"
            }
    
    async def escribir_bitacora(
        self,
        usuario_id: str,
        usuario_email: str,
        accion: str,
        recurso: str,
        resultado: str = "OK",
        detalles: Dict = None
    ) -> bool:
        """
        Escribe en bitácora de forma DESACOPLADA.
        Si falla, no rompe el flujo principal.
        Registra error internamente pero no lo propaga.
        """
        try:
            import json
            usuario_int = None
            row = self._sql_one("""
                SELECT TOP 1 UsuarioID
                FROM dbo.Usuario_Catalogo
                WHERE CodigoUsuario=%s OR Email=%s OR Username=%s OR CONVERT(VARCHAR(50), PublicUUID)=%s
            """, (usuario_id, usuario_email, usuario_id, usuario_id))
            if row:
                usuario_int = row.get("UsuarioID")

            detalle = json.dumps({
                "accion": accion,
                "recurso": recurso,
                "detalles": detalles or {},
                "fase": "FASE_2_SQL_FIRST"
            }, ensure_ascii=False, default=str)

            self._sql_exec("""
                INSERT INTO dbo.Usuario_LogAccesos (
                    LogAccesoID, UsuarioID, TipoEvento, Resultado, Detalle, FechaEvento
                )
                VALUES (%s,%s,%s,%s,%s,SYSDATETIME())
            """, (
                self._sql_next_id("Usuario_LogAccesos", "LogAccesoID"),
                usuario_int,
                accion[:30],
                resultado[:20],
                detalle[:1000]
            ))
            return True
        except Exception as e:
            # Log interno - NO propagar error al flujo principal
            logger.warning(f"Bitacora FASE2 fallo (no critico): {e}")
            return False


# Factory function
def get_estructura_service(db) -> EstructuraService:
    """
    Obtiene instancia del servicio.
    
    NOTA: MongoDB ELIMINADO - Este servicio puede recibir db=None.
    En ese caso, retornará respuestas stub vacías.
    """
    return EstructuraService(db)


__all__ = ['EstructuraService', 'get_estructura_service']
