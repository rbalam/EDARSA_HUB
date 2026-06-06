from core.sql_first.connection_factory import get_edarsahub_pymssql_connection, get_external_sql_connection, get_edarsahub_connection
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Servicio de Menús Gobernados
==========================================
Sistema de menús dinámicos basados en SQL Server.
Los menús se muestran según permisos del usuario.
"""

import logging
from typing import Dict, Any, List, Optional
import pymssql
import os
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)


class MenuService:
    """Servicio para gestión de menús gobernados desde SQL Server."""
    
    def __init__(self):
        self.db_config = {
            'host': _edarsa_cfg.host,
            'user': _edarsa_cfg.user,
            'password': _edarsa_cfg.password,
            'database': _edarsa_cfg.database,
            'port': _edarsa_cfg.port
        }
    
    def _get_connection(self):
        return get_external_sql_connection(self.db_config)
    
    def obtener_modulos(self, solo_activos: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene todos los módulos del sistema.
        
        Returns:
            Lista de módulos con su configuración
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    ModuloID, Codigo, Nombre, Descripcion, Icono,
                    Orden, EsPrincipal, EsSatelite, EsPortal, URLExterna, Activo
                FROM Sistema_Modulos
            """
            if solo_activos:
                query += " WHERE Activo = 1"
            query += " ORDER BY Orden"
            
            cursor.execute(query)
            return cursor.fetchall() or []
            
        finally:
            conn.close()
    
    def obtener_menus_modulo(self, modulo_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los menús de un módulo específico.
        
        Args:
            modulo_id: ID del módulo
            
        Returns:
            Lista de menús del módulo
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT 
                    MenuID, ModuloID, MenuPadreID, Codigo, Nombre,
                    Descripcion, Icono, Ruta, Orden, RequierePermiso, Activo
                FROM Sistema_ModulosMenus
                WHERE ModuloID = %s AND Activo = 1
                ORDER BY Orden
            """, (modulo_id,))
            
            return cursor.fetchall() or []
            
        finally:
            conn.close()
    
    def obtener_menus_usuario(
        self, 
        usuario_id: str, 
        permisos_usuario: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los menús visibles para un usuario según sus permisos.
        
        Args:
            usuario_id: ID del usuario
            permisos_usuario: Lista de códigos de permiso del usuario
            
        Returns:
            Lista de módulos con sus menús filtrados por permisos
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener módulos activos
            cursor.execute("""
                SELECT 
                    m.ModuloID, m.Codigo, m.Nombre, m.Descripcion, m.Icono,
                    m.Orden, m.EsPrincipal, m.EsSatelite, m.EsPortal, m.URLExterna
                FROM Sistema_Modulos m
                WHERE m.Activo = 1
                ORDER BY m.Orden
            """)
            modulos = cursor.fetchall() or []
            
            resultado = []
            
            for modulo in modulos:
                # Obtener menús del módulo
                cursor.execute("""
                    SELECT 
                        MenuID, MenuPadreID, Codigo, Nombre, Descripcion,
                        Icono, Ruta, Orden, RequierePermiso
                    FROM Sistema_ModulosMenus
                    WHERE ModuloID = %s AND Activo = 1
                    ORDER BY Orden
                """, (modulo['ModuloID'],))
                
                menus = cursor.fetchall() or []
                
                # Filtrar menús por permisos
                menus_filtrados = []
                for menu in menus:
                    permiso_requerido = menu.get('RequierePermiso')
                    
                    # Si no requiere permiso específico o el usuario lo tiene
                    if not permiso_requerido or permiso_requerido in permisos_usuario:
                        menus_filtrados.append({
                            'id': menu['MenuID'],
                            'codigo': menu['Codigo'],
                            'nombre': menu['Nombre'],
                            'descripcion': menu['Descripcion'],
                            'icono': menu['Icono'],
                            'ruta': menu['Ruta'],
                            'orden': menu['Orden'],
                            'padre_id': menu['MenuPadreID']
                        })
                
                # Solo incluir módulo si tiene menús visibles
                if menus_filtrados:
                    resultado.append({
                        'id': modulo['ModuloID'],
                        'codigo': modulo['Codigo'],
                        'nombre': modulo['Nombre'],
                        'descripcion': modulo['Descripcion'],
                        'icono': modulo['Icono'],
                        'es_principal': modulo['EsPrincipal'],
                        'es_satelite': modulo['EsSatelite'],
                        'es_portal': modulo['EsPortal'],
                        'url_externa': modulo['URLExterna'],
                        'menus': menus_filtrados
                    })
            
            return resultado
            
        finally:
            conn.close()
    
    def obtener_arbol_menus(self) -> List[Dict[str, Any]]:
        """
        Obtiene el árbol completo de módulos y menús.
        
        Returns:
            Árbol jerárquico de módulos y menús
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener todos los módulos
            cursor.execute("""
                SELECT 
                    m.ModuloID, m.Codigo, m.Nombre, m.Descripcion, m.Icono,
                    m.Orden, m.EsPrincipal, m.EsSatelite, m.EsPortal
                FROM Sistema_Modulos m
                WHERE m.Activo = 1
                ORDER BY m.Orden
            """)
            modulos = cursor.fetchall() or []
            
            resultado = []
            
            for modulo in modulos:
                # Obtener menús del módulo
                cursor.execute("""
                    SELECT 
                        MenuID, MenuPadreID, Codigo, Nombre, Descripcion,
                        Icono, Ruta, Orden, RequierePermiso
                    FROM Sistema_ModulosMenus
                    WHERE ModuloID = %s AND Activo = 1
                    ORDER BY Orden
                """, (modulo['ModuloID'],))
                
                menus = cursor.fetchall() or []
                
                # Construir árbol de menús (padres e hijos)
                menus_raiz = []
                menus_hijos = {}
                
                for menu in menus:
                    menu_item = {
                        'id': menu['MenuID'],
                        'codigo': menu['Codigo'],
                        'nombre': menu['Nombre'],
                        'descripcion': menu['Descripcion'],
                        'icono': menu['Icono'],
                        'ruta': menu['Ruta'],
                        'orden': menu['Orden'],
                        'permiso': menu['RequierePermiso'],
                        'hijos': []
                    }
                    
                    if menu['MenuPadreID']:
                        if menu['MenuPadreID'] not in menus_hijos:
                            menus_hijos[menu['MenuPadreID']] = []
                        menus_hijos[menu['MenuPadreID']].append(menu_item)
                    else:
                        menus_raiz.append(menu_item)
                
                # Asignar hijos a padres
                for menu in menus_raiz:
                    if menu['id'] in menus_hijos:
                        menu['hijos'] = menus_hijos[menu['id']]
                
                resultado.append({
                    'id': modulo['ModuloID'],
                    'codigo': modulo['Codigo'],
                    'nombre': modulo['Nombre'],
                    'descripcion': modulo['Descripcion'],
                    'icono': modulo['Icono'],
                    'tipo': 'principal' if modulo['EsPrincipal'] else ('satelite' if modulo['EsSatelite'] else 'portal'),
                    'menus': menus_raiz
                })
            
            return resultado
            
        finally:
            conn.close()


# Singleton
_menu_service = None

def get_menu_service() -> MenuService:
    """Factory para obtener el servicio de menús."""
    global _menu_service
    if _menu_service is None:
        _menu_service = MenuService()
    return _menu_service
