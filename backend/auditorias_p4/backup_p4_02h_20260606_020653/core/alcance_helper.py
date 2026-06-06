from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
FASE 16: Helper de Resolución de Alcance Organizacional
========================================================
Resuelve el alcance del usuario para filtrado de datos.

ALCANCE DE ESTE ARCHIVO:
- Solo contiene la lógica mínima para resolver alcance en GET /api/users
- NO modifica rbac_helper.py
- NO modifica get_current_user()
- NO aplica a otros endpoints sin autorización

POLÍTICA DE RESOLUCIÓN:
1. SuperAdministrador → acceso global (sin filtro)
2. sec_roles_alcance con tipo GLOBAL → acceso global
3. sec_roles_alcance con tipo específico → empresas calculadas (UNIÓN de todos los roles)
4. Sin sec_roles_alcance → fallback a empresas_permitidas del usuario
5. Sin nada válido → conjunto vacío

REGLA DE COMBINACIÓN DE MÚLTIPLES ROLES:
Si el usuario tiene múltiples roles con distintos alcances, se aplica UNIÓN.
Ejemplo: Rol A tiene alcance EMPRESA X, Rol B tiene alcance EMPRESA Y
         → Usuario ve usuarios de EMPRESA X + EMPRESA Y
Esto es seguro porque no amplía más allá de lo asignado explícitamente.
"""

from typing import Dict, List, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResultadoAlcance:
    """Resultado de la resolución de alcance organizacional."""
    tiene_acceso_global: bool = False
    empresas_ids: List[str] = None
    fuente_alcance: str = "SIN_ALCANCE"
    
    def __post_init__(self):
        if self.empresas_ids is None:
            self.empresas_ids = []
    
    def to_dict(self) -> Dict:
        return {
            "tiene_acceso_global": self.tiene_acceso_global,
            "empresas_ids": self.empresas_ids,
            "fuente_alcance": self.fuente_alcance
        }


# =============================================================================
# RESOLVERS POR TIPO DE ALCANCE
# =============================================================================

async def _resolver_empresa(alcance_data: Dict, _db) -> Set[str]:
    """Resuelve empresas para alcance tipo EMPRESA."""
    empresa_id = alcance_data.get('empresa_id')
    return {empresa_id} if empresa_id else set()


async def _resolver_unidad(alcance_data: Dict, _db) -> Set[str]:
    """
    Resuelve empresas para alcance tipo UNIDAD.
    FASE 3-H: Migrado a EDARSAHUB SQL.
    """
    import pymssql
    
    empresas = set()
    unidades_ids = alcance_data.get('unidades_ids', [])
    
    if unidades_ids:
        conn = pymssql.connect(
            server=os.getenv('EDARSAHUB_SQL_HOST'), port=1433,
            user=os.getenv('EDARSAHUB_SQL_USER'), password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
            database='EDARSAHUB'
        )
        try:
            cursor = conn.cursor()
            
            # Buscar empresas por unidad via Sistema_Sucursales
            # (Las sucursales están asociadas a empresas, y las unidades son las empresas en este modelo)
            placeholders = ', '.join(['%s'] * len(unidades_ids))
            
            cursor.execute(f'''
                SELECT DISTINCT m.EmpresaMongoUUID
                FROM Sistema_Sucursales s
                JOIN Sistema_EmpresasMongoMap m ON s.EmpresaID = m.EmpresaID_SQL
                WHERE s.MongoUUID IN ({placeholders})
                   OR m.EmpresaMongoUUID IN ({placeholders})
                  AND s.Activo = 1
            ''', tuple(unidades_ids) + tuple(unidades_ids))
            
            for row in cursor.fetchall():
                if row[0]:
                    empresas.add(row[0])
        finally:
            conn.close()
    
    # Fallback: empresa_id directa
    if alcance_data.get('empresa_id'):
        empresas.add(alcance_data['empresa_id'])
    
    return empresas


async def _resolver_sucursal(alcance_data: Dict, _db) -> Set[str]:
    """
    Resuelve empresas para alcance tipo SUCURSAL.
    FASE 3-H: Migrado a EDARSAHUB SQL.
    """
    import pymssql
    
    empresas = set()
    sucursales_ids = alcance_data.get('sucursales_ids', [])
    
    if sucursales_ids:
        conn = pymssql.connect(
            server=os.getenv('EDARSAHUB_SQL_HOST'), port=1433,
            user=os.getenv('EDARSAHUB_SQL_USER'), password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
            database='EDARSAHUB'
        )
        try:
            cursor = conn.cursor()
            
            # Buscar empresa de cada sucursal
            placeholders = ', '.join(['%s'] * len(sucursales_ids))
            
            cursor.execute(f'''
                SELECT DISTINCT m.EmpresaMongoUUID
                FROM Sistema_Sucursales s
                JOIN Sistema_EmpresasMongoMap m ON s.EmpresaID = m.EmpresaID_SQL
                WHERE s.MongoUUID IN ({placeholders})
                  AND s.Activo = 1
            ''', tuple(sucursales_ids))
            
            for row in cursor.fetchall():
                if row[0]:
                    empresas.add(row[0])
        finally:
            conn.close()
    
    # Fallback: empresa_id directa
    if alcance_data.get('empresa_id'):
        empresas.add(alcance_data['empresa_id'])
    
    return empresas


async def _resolver_almacen(alcance_data: Dict, _db) -> Set[str]:
    """Resuelve empresas para alcance tipo ALMACEN."""
    empresa_id = alcance_data.get('empresa_id')
    return {empresa_id} if empresa_id else set()


# Mapa de resolvers por tipo
RESOLVERS_ALCANCE = {
    'EMPRESA': _resolver_empresa,
    'UNIDAD': _resolver_unidad,
    'SUCURSAL': _resolver_sucursal,
    'ALMACEN': _resolver_almacen,
}


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

async def resolver_alcance_usuarios(current_user: Dict, db) -> Dict:
    """
    Resuelve el alcance organizacional para filtrado de usuarios.
    
    Args:
        current_user: Diccionario con datos del usuario actual
        db: Instancia de la base de datos MongoDB
        
    Returns:
        Dict con tiene_acceso_global, empresas_ids, fuente_alcance
    """
    email = current_user.get('email', 'N/A')
    
    # PASO 1: SuperAdministrador → acceso global
    if current_user.get('role') == 'SuperAdministrador':
        logger.info(f"Alcance resuelto para {email}: SUPERADMIN (global)")
        return ResultadoAlcance(tiene_acceso_global=True, fuente_alcance="SUPERADMIN").to_dict()
    
    # PASO 2: Verificar sec_roles_alcance
    sec_roles_alcance = current_user.get('sec_roles_alcance', {})
    
    if sec_roles_alcance:
        empresas_acumuladas = set()
        
        for rol_codigo, alcance_data in sec_roles_alcance.items():
            tipo_alcance = alcance_data.get('tipo', '')
            
            # GLOBAL → acceso total inmediato
            if tipo_alcance == 'GLOBAL':
                logger.info(f"Alcance resuelto para {email}: GLOBAL (rol con alcance global)")
                return ResultadoAlcance(tiene_acceso_global=True, fuente_alcance="GLOBAL").to_dict()
            
            # Resolver según tipo
            resolver = RESOLVERS_ALCANCE.get(tipo_alcance)
            if resolver:
                empresas_acumuladas.update(await resolver(alcance_data, db))
        
        if empresas_acumuladas:
            logger.info(f"Alcance resuelto para {email}: RBAC ({len(empresas_acumuladas)} empresas)")
            return ResultadoAlcance(
                empresas_ids=list(empresas_acumuladas),
                fuente_alcance="RBAC"
            ).to_dict()
    
    # PASO 3: Fallback a empresas_permitidas
    empresas_permitidas = current_user.get('empresas_permitidas', [])
    
    if empresas_permitidas:
        logger.info(f"Alcance resuelto para {email}: FALLBACK_EMPRESAS ({len(empresas_permitidas)} empresas)")
        return ResultadoAlcance(
            empresas_ids=empresas_permitidas,
            fuente_alcance="FALLBACK_EMPRESAS"
        ).to_dict()
    
    # PASO 4: Sin alcance válido
    logger.warning(f"Alcance resuelto para {email}: SIN_ALCANCE (conjunto vacío)")
    return ResultadoAlcance().to_dict()


async def verificar_usuario_en_alcance(actor: Dict, target_user: Dict, db) -> Dict:
    """
    Verifica si un usuario objetivo está dentro del alcance del actor.
    
    Usado para validar operaciones PUT/DELETE sobre usuarios específicos.
    """
    # SuperAdmin puede operar sobre cualquiera
    if actor.get('role') == 'SuperAdministrador':
        return {"permitido": True, "razon": "SUPERADMIN"}
    
    # Resolver alcance del actor
    alcance = await resolver_alcance_usuarios(actor, db)
    
    # Acceso global
    if alcance['tiene_acceso_global']:
        return {"permitido": True, "razon": f"GLOBAL ({alcance['fuente_alcance']})"}
    
    # Verificar si target está en alcance
    if alcance['empresas_ids']:
        target_empresa = target_user.get('empresa_default_id')
        
        if target_empresa and target_empresa in alcance['empresas_ids']:
            return {"permitido": True, "razon": f"EN_ALCANCE ({alcance['fuente_alcance']})"}
        
        return {
            "permitido": False, 
            "razon": f"FUERA_DE_ALCANCE (actor: {alcance['fuente_alcance']}, target_empresa: {target_empresa})"
        }
    
    return {"permitido": False, "razon": "SIN_ALCANCE_VALIDO"}


__all__ = ['resolver_alcance_usuarios', 'verificar_usuario_en_alcance', 'ResultadoAlcance']
