"""
EDARSA HUB - Cache Manager para Propinas TPV
============================================
Fecha: 15 de Abril de 2026
CAB: ARQUITECTURA_PROPINAS_TPV_v3.md

RESPONSABILIDADES:
- Gestión de cache en MongoDB
- Invalidación automática de cache
- TTL configurable por tipo de cache

PRINCIPIO ARQUITECTÓNICO:
- MongoDB = Solo cache de lectura rápida
- SQL Server = Fuente de verdad (gestionado por sql_repository.py)

COLECCIONES DE CACHE (nuevas, no interfieren con existentes):
- propinas_cache_listado: Cache de listados
- propinas_cache_resumen: Cache de agregaciones
- propinas_cache_config: Cache de configuración

IMPORTANTE:
- Este manager NO toca colecciones existentes
- NO interfiere con tesoreria_cuadres_z
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import hashlib
import json


logger = logging.getLogger(__name__)


class PropinasCacheManager:
    """
    Gestor de cache MongoDB para el módulo de Propinas TPV.
    
    Estrategia:
    - Cache de lectura: Se consulta primero, si TTL válido se retorna
    - Invalidación: Al escribir en SQL, se invalida cache relacionado
    - TTL configurable por tipo de cache
    """
    
    # TTL en segundos por tipo de cache
    TTL_LISTADO = 300      # 5 minutos
    TTL_RESUMEN = 300      # 5 minutos
    TTL_CONFIG = 3600      # 1 hora
    TTL_DETALLE = 600      # 10 minutos
    
    def __init__(self, db: Any):
        """
        Inicializa el gestor de cache.
        
        Args:
            db: Conexión a MongoDB
        """
        self.db = db
        self.cache_listado = db['propinas_cache_listado']
        self.cache_resumen = db['propinas_cache_resumen']
        self.cache_config = db['propinas_cache_config']
        self.cache_detalle = db['propinas_cache_detalle']
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _generar_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """
        Genera una clave única para el cache basada en parámetros.
        
        Args:
            prefix: Prefijo del tipo de cache
            params: Parámetros de la consulta
            
        Returns:
            String hash único
        """
        # Filtrar None y ordenar para consistencia
        filtered = {k: v for k, v in sorted(params.items()) if v is not None}
        params_json = json.dumps(filtered, sort_keys=True, default=str)
        hash_value = hashlib.sha256(params_json.encode()).hexdigest()[:32]
        return f"{prefix}:{hash_value}"
    
    def _es_cache_valido(self, cache_doc: Optional[Dict], ttl_seconds: int) -> bool:
        """
        Verifica si un documento de cache es válido.
        
        Args:
            cache_doc: Documento de cache
            ttl_seconds: TTL en segundos
            
        Returns:
            True si el cache es válido
        """
        if not cache_doc:
            return False
        
        cached_at = cache_doc.get('cached_at')
        if not cached_at:
            return False
        
        # Asegurar timezone aware
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        edad = (now - cached_at).total_seconds()
        
        return edad < ttl_seconds
    
    # =========================================================================
    # CACHE DE LISTADO
    # =========================================================================
    
    async def get_listado_cache(
        self,
        fecha_inicio: Optional[str],
        fecha_fin: Optional[str],
        server_id: Optional[str],
        sucursal_id: Optional[str],
        estado: Optional[str],
        page: int,
        limit: int
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene listado de propinas desde cache.
        
        Returns:
            Dict con propinas y metadatos, o None si no hay cache válido
        """
        cache_key = self._generar_cache_key('listado', {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'server_id': server_id,
            'sucursal_id': sucursal_id,
            'estado': estado,
            'page': page,
            'limit': limit
        })
        
        try:
            cache_doc = await self.cache_listado.find_one(
                {'_key': cache_key},
                {'_id': 0}
            )
            
            if self._es_cache_valido(cache_doc, self.TTL_LISTADO):
                logger.debug(f"Cache HIT: listado ({cache_key[:20]}...)")
                return cache_doc.get('data')
            
            logger.debug(f"Cache MISS: listado ({cache_key[:20]}...)")
            return None
            
        except Exception as e:
            logger.warning(f"Error leyendo cache listado: {e}")
            return None
    
    async def set_listado_cache(
        self,
        fecha_inicio: Optional[str],
        fecha_fin: Optional[str],
        server_id: Optional[str],
        sucursal_id: Optional[str],
        estado: Optional[str],
        page: int,
        limit: int,
        data: Dict[str, Any]
    ):
        """
        Guarda listado de propinas en cache.
        
        Args:
            data: Diccionario con propinas y metadatos
        """
        cache_key = self._generar_cache_key('listado', {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'server_id': server_id,
            'sucursal_id': sucursal_id,
            'estado': estado,
            'page': page,
            'limit': limit
        })
        
        try:
            await self.cache_listado.update_one(
                {'_key': cache_key},
                {
                    '$set': {
                        '_key': cache_key,
                        'cached_at': datetime.now(timezone.utc),
                        'data': data,
                        'params': {
                            'fecha_inicio': fecha_inicio,
                            'fecha_fin': fecha_fin,
                            'server_id': server_id,
                            'sucursal_id': sucursal_id,
                            'estado': estado,
                            'page': page,
                            'limit': limit
                        }
                    }
                },
                upsert=True
            )
            logger.debug(f"Cache SET: listado ({cache_key[:20]}...)")
            
        except Exception as e:
            logger.warning(f"Error escribiendo cache listado: {e}")
    
    # =========================================================================
    # CACHE DE RESUMEN
    # =========================================================================
    
    async def get_resumen_cache(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        server_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene resumen de propinas desde cache.
        """
        cache_key = self._generar_cache_key('resumen', {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'server_id': server_id
        })
        
        try:
            cache_doc = await self.cache_resumen.find_one(
                {'_key': cache_key},
                {'_id': 0}
            )
            
            if self._es_cache_valido(cache_doc, self.TTL_RESUMEN):
                logger.debug(f"Cache HIT: resumen ({cache_key[:20]}...)")
                return cache_doc.get('data')
            
            return None
            
        except Exception as e:
            logger.warning(f"Error leyendo cache resumen: {e}")
            return None
    
    async def set_resumen_cache(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        server_id: Optional[str],
        data: Dict[str, Any]
    ):
        """
        Guarda resumen de propinas en cache.
        """
        cache_key = self._generar_cache_key('resumen', {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'server_id': server_id
        })
        
        try:
            await self.cache_resumen.update_one(
                {'_key': cache_key},
                {
                    '$set': {
                        '_key': cache_key,
                        'cached_at': datetime.now(timezone.utc),
                        'data': data
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            logger.warning(f"Error escribiendo cache resumen: {e}")
    
    # =========================================================================
    # CACHE DE DETALLE
    # =========================================================================
    
    async def get_detalle_cache(self, propina_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalle de una propina desde cache."""
        try:
            cache_doc = await self.cache_detalle.find_one(
                {'propina_id': propina_id},
                {'_id': 0}
            )
            
            if self._es_cache_valido(cache_doc, self.TTL_DETALLE):
                return cache_doc.get('data')
            
            return None
            
        except Exception as e:
            logger.warning(f"Error leyendo cache detalle: {e}")
            return None
    
    async def set_detalle_cache(self, propina_id: str, data: Dict[str, Any]):
        """Guarda detalle de una propina en cache."""
        try:
            await self.cache_detalle.update_one(
                {'propina_id': propina_id},
                {
                    '$set': {
                        'propina_id': propina_id,
                        'cached_at': datetime.now(timezone.utc),
                        'data': data
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            logger.warning(f"Error escribiendo cache detalle: {e}")
    
    # =========================================================================
    # CACHE DE CONFIGURACIÓN
    # =========================================================================
    
    async def get_config_cache(
        self,
        server_id: Optional[str],
        empresa_id: Optional[str],
        sucursal_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Obtiene configuración desde cache."""
        cache_key = self._generar_cache_key('config', {
            'server_id': server_id,
            'empresa_id': empresa_id,
            'sucursal_id': sucursal_id
        })
        
        try:
            cache_doc = await self.cache_config.find_one(
                {'_key': cache_key},
                {'_id': 0}
            )
            
            if self._es_cache_valido(cache_doc, self.TTL_CONFIG):
                return cache_doc.get('data')
            
            return None
            
        except Exception as e:
            logger.warning(f"Error leyendo cache config: {e}")
            return None
    
    async def set_config_cache(
        self,
        server_id: Optional[str],
        empresa_id: Optional[str],
        sucursal_id: Optional[str],
        data: Dict[str, Any]
    ):
        """Guarda configuración en cache."""
        cache_key = self._generar_cache_key('config', {
            'server_id': server_id,
            'empresa_id': empresa_id,
            'sucursal_id': sucursal_id
        })
        
        try:
            await self.cache_config.update_one(
                {'_key': cache_key},
                {
                    '$set': {
                        '_key': cache_key,
                        'cached_at': datetime.now(timezone.utc),
                        'data': data
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            logger.warning(f"Error escribiendo cache config: {e}")
    
    # =========================================================================
    # INVALIDACIÓN DE CACHE
    # =========================================================================
    
    async def invalidar_listados(self, server_id: Optional[str] = None):
        """
        Invalida cache de listados.
        
        Args:
            server_id: Si se especifica, solo invalida ese servidor
        """
        try:
            filtro = {}
            if server_id:
                filtro['params.server_id'] = server_id
            
            result = await self.cache_listado.delete_many(filtro)
            logger.info(f"Cache invalidado: {result.deleted_count} listados")
            
        except Exception as e:
            logger.warning(f"Error invalidando cache listados: {e}")
    
    async def invalidar_resumenes(self, server_id: Optional[str] = None):
        """Invalida cache de resúmenes."""
        try:
            filtro = {}
            if server_id:
                filtro['params.server_id'] = server_id
            
            result = await self.cache_resumen.delete_many(filtro)
            logger.info(f"Cache invalidado: {result.deleted_count} resúmenes")
            
        except Exception as e:
            logger.warning(f"Error invalidando cache resúmenes: {e}")
    
    async def invalidar_detalle(self, propina_id: str):
        """Invalida cache de un detalle específico."""
        try:
            await self.cache_detalle.delete_one({'propina_id': propina_id})
            logger.debug(f"Cache invalidado: detalle {propina_id}")
            
        except Exception as e:
            logger.warning(f"Error invalidando cache detalle: {e}")
    
    async def invalidar_configs(self):
        """Invalida todo el cache de configuración."""
        try:
            result = await self.cache_config.delete_many({})
            logger.info(f"Cache invalidado: {result.deleted_count} configs")
            
        except Exception as e:
            logger.warning(f"Error invalidando cache configs: {e}")
    
    async def invalidar_todo(self):
        """Invalida todo el cache de propinas."""
        await self.invalidar_listados()
        await self.invalidar_resumenes()
        await self.invalidar_configs()
        
        try:
            await self.cache_detalle.delete_many({})
        except Exception as e:
            logger.warning(f"Error invalidando cache detalles: {e}")
        
        logger.info("Todo el cache de propinas ha sido invalidado")
    
    # =========================================================================
    # ÍNDICES
    # =========================================================================
    
    async def crear_indices(self):
        """
        Crea índices necesarios para las colecciones de cache.
        Incluye TTL index para limpieza automática.
        """
        try:
            # Índice único por clave
            await self.cache_listado.create_index('_key', unique=True)
            await self.cache_resumen.create_index('_key', unique=True)
            await self.cache_config.create_index('_key', unique=True)
            await self.cache_detalle.create_index('propina_id', unique=True)
            
            # TTL index para limpieza automática (1 hora de vida máxima)
            await self.cache_listado.create_index(
                'cached_at', 
                expireAfterSeconds=3600,
                name='ttl_listado'
            )
            await self.cache_resumen.create_index(
                'cached_at', 
                expireAfterSeconds=3600,
                name='ttl_resumen'
            )
            await self.cache_detalle.create_index(
                'cached_at', 
                expireAfterSeconds=3600,
                name='ttl_detalle'
            )
            
            logger.info("Índices de cache de propinas creados")
            
        except Exception as e:
            logger.warning(f"Error creando índices de cache: {e}")
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    async def obtener_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Dict con conteos y estadísticas
        """
        try:
            stats = {
                'listados': await self.cache_listado.count_documents({}),
                'resumenes': await self.cache_resumen.count_documents({}),
                'configs': await self.cache_config.count_documents({}),
                'detalles': await self.cache_detalle.count_documents({}),
                'ttl': {
                    'listado_segundos': self.TTL_LISTADO,
                    'resumen_segundos': self.TTL_RESUMEN,
                    'config_segundos': self.TTL_CONFIG,
                    'detalle_segundos': self.TTL_DETALLE
                }
            }
            stats['total'] = sum([
                stats['listados'], 
                stats['resumenes'], 
                stats['configs'],
                stats['detalles']
            ])
            return stats
            
        except Exception as e:
            logger.warning(f"Error obteniendo stats de cache: {e}")
            return {'error': str(e)}
