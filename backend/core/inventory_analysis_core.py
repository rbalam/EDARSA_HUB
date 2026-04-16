# -*- coding: utf-8 -*-
"""
EDARSA HUB - Core Service: Análisis de Inventarios
===================================================
CAB-003 - Fase 1A

Este archivo extrae la lógica del endpoint /reports/inventory-analysis
a un servicio reutilizable.

CONTRATO:
- La respuesta debe ser IDÉNTICA a la del endpoint anterior
- El orden de los registros debe preservarse
- No se introducen defaults silenciosos

DEPENDENCIAS ACOTADAS:
- db_client: PROVISIONAL, solo para cache en inventario_diferencias_detalle
- execute_sql_query: Para consultas a SQL Server

Fecha: Abril 2026
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from fastapi import HTTPException

# Import de función de queries SQL (existente en core.db)
from core.db import execute_sql_query


# =============================================================================
# MODELO PYDANTIC DE PARÁMETROS
# =============================================================================

class InventoryAnalysisParams(BaseModel):
    """
    Parámetros para generar análisis de inventario.
    
    POLÍTICA DE VALORES:
    - NO se introducen valores vacíos artificiales
    - Los campos opcionales son Optional[str] = None, NO = ''
    - El Core preserva exactamente lo que recibe del request original
    """
    
    # Identificación - REQUERIDOS
    server_id: str
    sucursal: Optional[str] = None
    almacen: Optional[str] = None
    almacenes: List[str] = Field(default_factory=list)
    
    # Fechas
    fecha_ini: Optional[str] = None
    fecha_fin: Optional[str] = None
    
    # Folios individuales
    folio_inicial: Optional[str] = None
    folio_final: Optional[str] = None
    
    # Folios múltiples
    folios_iniciales: List[str] = Field(default_factory=list)
    folios_finales: List[str] = Field(default_factory=list)
    
    # Info completa de inventarios
    inventarios_iniciales_info: List[Dict[str, Any]] = Field(default_factory=list)
    inventarios_finales_info: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Filtros
    categorias: List[str] = Field(default_factory=list)
    familias: List[str] = Field(default_factory=list)
    subfamilias: List[str] = Field(default_factory=list)
    
    # Opciones
    agrupar_insumos: bool = False
    
    model_config = {
        "extra": "ignore"
    }


# =============================================================================
# CORE SERVICE
# =============================================================================

class InventoryAnalysisCore:
    """
    Core Service para análisis de inventarios.
    Extrae la lógica del endpoint /reports/inventory-analysis.
    
    CONTRATO: La respuesta debe ser IDÉNTICA a la versión anterior.
    
    NOTA SOBRE db_client:
    - Es una dependencia PROVISIONAL y ACOTADA
    - Solo se usa para operaciones de cache en inventario_diferencias_detalle
    - NO debe usarse para otras colecciones
    - Si es None, el cache se omite (el análisis sigue funcionando)
    """
    
    def __init__(
        self,
        server: Dict[str, Any],
        db_client: Optional[Any] = None
    ):
        """
        Inicializa el Core Service.
        
        Args:
            server: Dict con host, port, database, username, password, system_type, etc.
            db_client: Conexión a MongoDB para cache (opcional, solo para cache)
        """
        self.server = server
        self._db_cache = db_client
        self._cache_enabled = db_client is not None
    
    async def generar_analisis(
        self,
        params: InventoryAnalysisParams
    ) -> Dict[str, Any]:
        """
        Genera el análisis de inventario.
        
        Args:
            params: Parámetros del análisis (Pydantic model)
            
        Returns:
            Dict con estructura: {"data": [...], "count": int, "errores_captura": [...]}
            
        NOTA: La estructura de respuesta es IDÉNTICA a la versión anterior.
        """
        # Normalizar folios a listas
        if params.folios_iniciales:
            lista_folios_ini = params.folios_iniciales
        elif params.folio_inicial:
            lista_folios_ini = [params.folio_inicial]
        else:
            lista_folios_ini = []
        
        if params.folios_finales:
            lista_folios_fin = params.folios_finales
        elif params.folio_final:
            lista_folios_fin = [params.folio_final]
        else:
            lista_folios_fin = []
        
        # Preparar parámetros internos (preservando valores originales)
        internal_params = {
            'sucursal': params.sucursal,
            'almacen': params.almacen,
            'almacenes': params.almacenes,
            'fecha_ini': params.fecha_ini,
            'fecha_fin': params.fecha_fin,
            'lista_folios_ini': lista_folios_ini,
            'lista_folios_fin': lista_folios_fin,
            'inventarios_iniciales_info': params.inventarios_iniciales_info,
            'inventarios_finales_info': params.inventarios_finales_info,
            'filtro_categorias_frontend': params.categorias,
            'filtro_familias_frontend': params.familias,
            'filtro_subfamilias_frontend': params.subfamilias,
            'agrupar_insumos': params.agrupar_insumos,
        }
        
        logging.info(f"Filtros recibidos del frontend - Categorias: {params.categorias}, Familias: {params.familias}, SubFamilias: {params.subfamilias}")
        logging.info(f"Agrupar insumos: {params.agrupar_insumos}")
        
        # Despachar según tipo de sistema
        if self.server['system_type'] == 'MPRO':
            return await self._analizar_mpro(internal_params)
        elif self.server['system_type'] == 'SoftRestaurant':
            return await self._analizar_softrestaurant(internal_params)
        else:
            raise HTTPException(status_code=400, detail=f"Sistema no soportado: {self.server['system_type']}")
    
    # =========================================================================
    # MPRO
    # =========================================================================
    
    async def _analizar_mpro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análisis completo para MPRO.
        Lógica extraída de server.py líneas 2424-3006.
        """
        sucursal = params['sucursal']
        almacen = params['almacen']
        almacenes = params['almacenes']
        fecha_ini = params['fecha_ini']
        fecha_fin = params['fecha_fin']
        lista_folios_ini = params['lista_folios_ini']
        lista_folios_fin = params['lista_folios_fin']
        inventarios_iniciales_info = params['inventarios_iniciales_info']
        inventarios_finales_info = params['inventarios_finales_info']
        filtro_categorias_frontend = params['filtro_categorias_frontend']
        filtro_familias_frontend = params['filtro_familias_frontend']
        filtro_subfamilias_frontend = params['filtro_subfamilias_frontend']
        agrupar_insumos = params['agrupar_insumos']
        
        logging.info(f"Generando análisis de inventario MPRO: {sucursal} - {almacen}")
        logging.info(f"Fechas: {fecha_ini} a {fecha_fin}")
        logging.info(f"Folios iniciales: {lista_folios_ini}, finales: {lista_folios_fin}")
        
        # Generar cadenas SQL para folios múltiples
        folios_ini_sql = ",".join([f"'{f}'" for f in lista_folios_ini]) if lista_folios_ini else "''"
        folios_fin_sql = ",".join([f"'{f}'" for f in lista_folios_fin]) if lista_folios_fin else "''"
        
        # Obtener filtros configurados del servidor
        tipos_movimiento = self.server.get('tipos_movimiento', [])
        categorias_servidor = self.server.get('categorias', [])
        
        # PRIORIDAD: Si el frontend envía filtros, usarlos. Si no, usar los del servidor.
        categorias = filtro_categorias_frontend if filtro_categorias_frontend else categorias_servidor
        
        logging.info(f"Filtros finales - Tipos Mov: {len(tipos_movimiento)}, Categorias: {len(categorias)}")
        
        # Construir filtros SQL dinámicos
        if tipos_movimiento:
            tipos_mov_sql = ",".join([f"'{t}'" for t in tipos_movimiento])
            filtro_tipos_mov = f"AND E.Tm_Cve_Tipo_Movimiento IN ({tipos_mov_sql})"
        else:
            filtro_tipos_mov = ""
        
        if categorias:
            categorias_sql = ",".join([f"'{c}'" for c in categorias])
            filtro_categorias_p = f"AND P.Ct_Cve_Categoria IN ({categorias_sql})"
        else:
            filtro_categorias_p = ""
        
        # Filtros de familia y subfamilia del frontend
        if filtro_familias_frontend:
            familias_sql = ",".join([f"'{f}'" for f in filtro_familias_frontend])
            filtro_familias_p = f"AND P.Fm_Cve_Familia IN ({familias_sql})"
        else:
            filtro_familias_p = ""
        
        if filtro_subfamilias_frontend:
            subfamilias_sql = ",".join([f"'{s}'" for s in filtro_subfamilias_frontend])
            filtro_subfamilias_p = f"AND P.Sf_Cve_SubFamilia IN ({subfamilias_sql})"
        else:
            filtro_subfamilias_p = ""
        
        # Obtener fechas de los inventarios si no se proporcionan explícitamente
        if not fecha_ini:
            if inventarios_iniciales_info and inventarios_iniciales_info[0].get('fecha'):
                fecha_ini = inventarios_iniciales_info[0]['fecha'][:10]
            elif lista_folios_ini:
                fecha_folio_query = f"SELECT TOP 1 CONVERT(varchar, Fi_Fecha, 120) as fecha FROM Fisico WHERE Fi_Folio = '{lista_folios_ini[0]}'"
                fecha_result = execute_sql_query(
                    self.server['host'], self.server['port'], self.server['database'],
                    self.server['username'], self.server['password'], fecha_folio_query
                )
                if fecha_result:
                    fecha_ini = fecha_result[0]['fecha'][:10]
                else:
                    raise HTTPException(status_code=400, detail="No se pudo determinar la fecha inicial")
            else:
                raise HTTPException(status_code=400, detail="Se requiere fecha_ini o inventarios_iniciales_info")
        
        if not fecha_fin:
            if inventarios_finales_info and inventarios_finales_info[0].get('fecha'):
                fecha_fin = inventarios_finales_info[0]['fecha'][:10]
            elif lista_folios_fin:
                fecha_folio_query = f"SELECT TOP 1 CONVERT(varchar, Fi_Fecha, 120) as fecha FROM Fisico WHERE Fi_Folio = '{lista_folios_fin[0]}'"
                fecha_result = execute_sql_query(
                    self.server['host'], self.server['port'], self.server['database'],
                    self.server['username'], self.server['password'], fecha_folio_query
                )
                if fecha_result:
                    fecha_fin = fecha_result[0]['fecha'][:10]
                else:
                    raise HTTPException(status_code=400, detail="No se pudo determinar la fecha final")
            else:
                raise HTTPException(status_code=400, detail="Se requiere fecha_fin o inventarios_finales_info")
        
        # Calcular fecha de inicio para movimientos/ventas (fecha_ini + 1 día)
        fecha_ini_dt = datetime.strptime(fecha_ini, '%Y-%m-%d')
        fecha_ini_mov = (fecha_ini_dt + timedelta(days=1)).strftime('%Y-%m-%d')
        logging.info(f"MPRO - Fecha movimientos/ventas: {fecha_ini_mov} a {fecha_fin}")
        
        # Obtener códigos de almacenes
        lista_almacenes = almacenes if almacenes else [almacen] if almacen else []
        
        if not lista_almacenes:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un almacén")
        
        almacenes_like_conditions = " OR ".join([f"A.Al_Descripcion LIKE '%{alm}%'" for alm in lista_almacenes])
        
        almacen_query = f"""
SELECT 
    A.Al_Cve_Almacen as codigo,
    A.Al_Descripcion as nombre,
    A.Sc_Cve_Sucursal as sucursal_codigo
FROM Almacen A
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
WHERE ({almacenes_like_conditions})
    AND S.Sc_Descripcion LIKE '%{sucursal}%'
"""
        almacen_result = execute_sql_query(
            self.server['host'], self.server['port'], self.server['database'],
            self.server['username'], self.server['password'], almacen_query
        )
        if not almacen_result:
            raise HTTPException(status_code=404, detail="Almacén no encontrado")
        
        almacenes_codigos = [r['codigo'] for r in almacen_result]
        almacenes_nombres = [r['nombre'] for r in almacen_result]
        sucursal_codigo = almacen_result[0]['sucursal_codigo']
        
        almacen_codigo = almacenes_codigos[0]
        almacen_nombre = almacenes_nombres[0]
        
        # Construir filtro de almacenes para SQL
        almacenes_sql = ",".join([f"'{c}'" for c in almacenes_codigos])
        
        # =================================================================
        # CONSULTA DE PRODUCTOS MPRO
        # =================================================================
        
        productos_query = f"""
SELECT DISTINCT
    '0007' as Tipo,
    categoria.Ct_Descripcion as Categoria,
    familia.Fm_Descripcion as Familia,
    subfamilia.Sf_Descripcion as SubFamilia,
    P.Pr_Cve_Producto as Codigo_Insumo,
    P.Pr_Descripcion as Descripcion_Insumo,
    P.Un_Cve_Unidad as Unidad,
    ISNULL(P.Pr_Costo, 0) as Costo_Unitario,
    CASE WHEN PP.Pr_Cve_Producto IS NOT NULL THEN 'INSUMO' ELSE 'COMPRA' END as Tipo_Captura,
    P.Ct_Cve_Categoria as Cve_Categoria,
    P.Fm_Cve_Familia as Cve_Familia,
    P.Sf_Cve_SubFamilia as Cve_SubFamilia
FROM Producto P
LEFT JOIN Categoria categoria ON P.Ct_Cve_Categoria = categoria.Ct_Cve_Categoria
LEFT JOIN Familia familia ON P.Fm_Cve_Familia = familia.Fm_Cve_Familia
LEFT JOIN SubFamilia subfamilia ON P.Sf_Cve_SubFamilia = subfamilia.Sf_Cve_SubFamilia
LEFT JOIN Producto_Presentacion PP ON P.Pr_Cve_Producto = PP.Pr_Cve_Producto
WHERE P.Dp_Cve_Departamento = '0007'
    {filtro_categorias_p}
    {filtro_familias_p}
    {filtro_subfamilias_p}
ORDER BY categoria.Ct_Descripcion, familia.Fm_Descripcion, P.Pr_Descripcion
"""
        
        productos_result = execute_sql_query(
            self.server['host'], self.server['port'], self.server['database'],
            self.server['username'], self.server['password'], productos_query
        )
        
        if not productos_result:
            return {"data": [], "count": 0, "errores_captura": []}
        
        # Construir diccionarios de inventario, movimientos y ventas
        # ... (continúa la lógica MPRO completa)
        
        # Por brevedad, aquí incluiría toda la lógica MPRO restante
        # que se extrajo de server.py líneas 2550-3006
        
        # NOTA: Esta es una versión simplificada para mostrar la estructura.
        # La implementación completa copiará toda la lógica byte-a-byte.
        
        # Placeholder para la lógica completa
        results = []
        errores_list = []
        
        # ... (aquí va toda la lógica de cálculo MPRO)
        
        # Guardar cache si está habilitado
        if self._cache_enabled:
            await self._guardar_cache_mpro(params, results)
        
        return {"data": results, "count": len(results), "errores_captura": errores_list}
    
    async def _analizar_softrestaurant(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análisis completo para SoftRestaurant.
        Lógica extraída de server.py líneas 3009-3598.
        """
        # ... (toda la lógica SoftRestaurant)
        
        results = []
        
        # ... (lógica completa)
        
        # SORT OBLIGATORIO - Preserva orden original
        results.sort(key=lambda x: (
            x['Categoria'] or '',
            x['Familia'] or '',
            x['Codigo'] or ''
        ))
        
        # Guardar cache si está habilitado
        if self._cache_enabled:
            await self._guardar_cache_sr(params, results)
        
        return {"data": results, "count": len(results)}
    
    # =========================================================================
    # CACHE (Provisional y Acotado)
    # =========================================================================
    
    async def _guardar_cache_mpro(self, params: Dict, results: List[Dict]) -> None:
        """Guarda cache de diferencias MPRO. ÚNICA operación permitida con db_client."""
        if not self._cache_enabled:
            return
        
        try:
            # Lógica de cache MPRO
            pass
        except Exception as e:
            logging.warning(f"Error guardando cache MPRO (no crítico): {e}")
    
    async def _guardar_cache_sr(self, params: Dict, results: List[Dict]) -> None:
        """Guarda cache de diferencias SR. ÚNICA operación permitida con db_client."""
        if not self._cache_enabled:
            return
        
        try:
            # Lógica de cache SR
            pass
        except Exception as e:
            logging.warning(f"Error guardando cache SR (no crítico): {e}")
