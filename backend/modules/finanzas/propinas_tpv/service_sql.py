"""
EDARSA HUB - Service SQL para Propinas TPV
==========================================
Fecha: 15 de Abril de 2026
CAB: ARQUITECTURA_PROPINAS_TPV_v3.md

RESPONSABILIDADES:
- Lógica de negocio para Propinas TPV
- Orquestación de SQL Server (escritura) + MongoDB (cache/lectura)
- Cálculos de comisión
- Sincronización desde SoftRestaurant

PRINCIPIO ARQUITECTÓNICO:
- ESCRITURA: Siempre a SQL Server → Invalidar cache MongoDB
- LECTURA: Cache MongoDB → Si miss, SQL Server → Actualizar cache

IMPORTANTE:
- NO interfiere con tesoreria.py ni el tab actual de Cuadre Z
- Usa colecciones de cache NUEVAS (propinas_cache_*)
- Usa tablas SQL NUEVAS (propinas_tpv_*)
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from .sql_repository import PropinasTPVSQLRepository
from .cache_manager import PropinasCacheManager
from .repository import PropinasTPVRepository  # Para lectura de SoftRestaurant
from .models import (
    TipoDatoOrigen,
    EstadoCuadre,
    SincronizarResponse
)

logger = logging.getLogger(__name__)


class PropinasTPVSQLService:
    """
    Servicio refactorizado de Propinas TPV con arquitectura SQL + Cache.
    
    FLUJO DE DATOS:
    ===============
    
    SoftRestaurant (Lectura) → SQL Server (Persistencia) → MongoDB (Cache)
                                      ↓
                              Frontend (Consultas)
    
    OPERACIONES:
    - Sincronizar: Lee SoftRestaurant → Escribe SQL → Invalida Cache
    - Consultar: Intenta Cache → Si falla, lee SQL → Actualiza Cache
    - Modificar: Escribe SQL → Invalida Cache
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.sql_repo = PropinasTPVSQLRepository(db)
        self.cache = PropinasCacheManager(db)
        self.soft_repo = PropinasTPVRepository(db)  # Solo para leer de SoftRestaurant
    
    # =========================================================================
    # INICIALIZACIÓN
    # =========================================================================
    
    async def inicializar_modulo(self) -> Dict[str, Any]:
        """
        Inicializa el módulo de Propinas TPV.
        
        1. Crea tablas SQL en EDARSA HUB
        2. Crea índices de cache en MongoDB
        3. Inserta configuración GLOBAL si no existe
        
        Returns:
            Dict con resultado de inicialización
        """
        logger.info("Inicializando módulo de Propinas TPV (SQL + Cache)...")
        
        resultados = {
            'sql_tablas': None,
            'cache_indices': False,
            'config_default': False,
            'success': False
        }
        
        # 1. Crear tablas SQL
        try:
            sql_result = await self.sql_repo.crear_tablas()
            resultados['sql_tablas'] = sql_result
            logger.info(f"Tablas SQL: {sql_result}")
        except Exception as e:
            logger.error(f"Error creando tablas SQL: {e}")
            resultados['sql_tablas'] = {'error': str(e)}
        
        # 2. Crear índices de cache
        try:
            await self.cache.crear_indices()
            resultados['cache_indices'] = True
            logger.info("Índices de cache creados")
        except Exception as e:
            logger.warning(f"Error creando índices de cache: {e}")
        
        # 3. Verificar config GLOBAL
        try:
            config = await self.sql_repo.obtener_config_vigente()
            if config.get('id') != 'default':
                resultados['config_default'] = True
            logger.info("Configuración GLOBAL verificada")
        except Exception as e:
            logger.warning(f"Error verificando config: {e}")
        
        resultados['success'] = (
            resultados['sql_tablas'] and 
            resultados['sql_tablas'].get('success', False)
        )
        
        logger.info(f"Módulo inicializado: {resultados['success']}")
        return resultados
    
    # =========================================================================
    # SINCRONIZACIÓN (SoftRestaurant → SQL Server)
    # =========================================================================
    
    async def sincronizar_propinas(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        server_id: Optional[str] = None,
        usuario: str = "sistema"
    ) -> SincronizarResponse:
        """
        Sincroniza propinas desde SoftRestaurant a SQL Server.
        
        FLUJO:
        1. Obtener servidores SoftRestaurant activos
        2. Por cada servidor, usar query defensiva para leer propinas
        3. Calcular comisión 2%
        4. Upsert en SQL Server (tabla propinas_tpv_control)
        5. Invalidar cache MongoDB
        
        Args:
            fecha_inicio: Fecha inicio YYYY-MM-DD
            fecha_fin: Fecha fin YYYY-MM-DD
            server_id: Opcional - sincronizar solo un servidor
            usuario: Email del usuario que ejecuta
            
        Returns:
            SincronizarResponse con estadísticas
        """
        logger.info(f"Sincronización SQL: {fecha_inicio} a {fecha_fin}")
        
        # Obtener servidores SoftRestaurant
        filtro_servers = {'system_type': 'SoftRestaurant'}
        if server_id:
            filtro_servers['id'] = server_id
        
        servers = await self.db['servers'].find(filtro_servers, {'_id': 0}).to_list(100)
        
        if not servers:
            logger.warning("No se encontraron servidores SoftRestaurant")
            return SincronizarResponse(
                success=True,
                registros_creados=0,
                registros_actualizados=0,
                errores=[],
                detalle_por_servidor=[]
            )
        
        # Obtener configuración vigente
        config = await self.sql_repo.obtener_config_vigente()
        porcentaje_comision = config['parametros']['porcentaje_comision']
        
        total_creados = 0
        total_actualizados = 0
        errores = []
        detalle = []
        
        for server in servers:
            server_name = server.get('name', 'Desconocido')
            server_id_actual = server.get('id')
            
            try:
                logger.info(f"Procesando servidor: {server_name}")
                
                # Usar query defensiva del repositorio original
                resultado = await self.soft_repo.get_propinas_cortes_defensivo(
                    server, fecha_inicio, fecha_fin
                )
                
                # Verificar compatibilidad
                if not resultado['compatible']:
                    error_msg = resultado.get('error', 'Esquema no compatible')
                    errores.append({
                        'servidor': server_name,
                        'error': error_msg,
                        'schema': resultado.get('schema')
                    })
                    detalle.append({
                        'servidor': server_name,
                        'system_type': 'SoftRestaurant',
                        'status': 'NO_COMPATIBLE',
                        'error': error_msg
                    })
                    continue
                
                cortes = resultado['cortes']
                creados_server = 0
                actualizados_server = 0
                
                for corte in cortes:
                    # Usar propinas_tpv (de cheques.propinatarjeta) - DATO EXACTO
                    propinas_tpv = corte.get('propinas_tpv', 0)
                    
                    # Solo procesar si hay propinas TPV
                    if propinas_tpv <= 0:
                        continue
                    
                    # Calcular comisión 2%
                    comision = round(propinas_tpv * porcentaje_comision, 2)
                    monto_a_pagar = round(propinas_tpv - comision, 2)
                    
                    # Preparar documento para SQL
                    fecha_corte_dt = datetime.fromisoformat(
                        corte['fecha_corte'].replace('Z', '+00:00')
                    ) if isinstance(corte['fecha_corte'], str) else corte['fecha_corte']
                    
                    propina_data = {
                        'id': str(uuid.uuid4()),
                        'server_id': server_id_actual,
                        'sucursal_id': server_name,
                        'folio_corte': corte['folio_corte'],
                        'fecha_corte': fecha_corte_dt,
                        'estacion_id': corte.get('estacion_id'),
                        'turno_id': corte.get('turno_id'),
                        'server_name': server_name,
                        'system_type': 'SoftRestaurant',
                        'sucursal_nombre': server_name,
                        'empresa_id': server.get('database'),
                        'sincronizado_por': usuario,
                        'origen': {
                            'tipo_dato': TipoDatoOrigen.EXACTO.value,
                            'metodo_calculo': 'CHEQUES_PROPINATARJETA',
                            'confianza': 1.0,
                            'propinas_totales_corte': corte.get('propinas_totales', 0),
                            'ventas_tarjeta': corte.get('ventas_tarjeta', 0),
                            'ventas_totales': corte.get('ventas_totales', 0),
                            'ventas_efectivo': corte.get('ventas_efectivo', 0),
                            'propinas_tpv': propinas_tpv,
                            'total_cheques': corte.get('total_cheques', 0),
                            'saldo_corte': corte.get('saldo_corte', 0),
                            'formula_aplicada': 'SUM(cheques.propinatarjeta) por turno/corte',
                            'fecha_sincronizacion': datetime.now(timezone.utc),
                            'advertencia': None
                        },
                        'calculo': {
                            'config_aplicada_id': config.get('id'),
                            'porcentaje_comision': porcentaje_comision,
                            'comision_calculada': comision,
                            'monto_a_pagar_meseros': monto_a_pagar
                        }
                    }
                    
                    # Upsert en SQL Server
                    result = await self.sql_repo.upsert_propina(propina_data)
                    
                    if result['created']:
                        creados_server += 1
                    elif result['modified']:
                        actualizados_server += 1
                
                total_creados += creados_server
                total_actualizados += actualizados_server
                
                detalle.append({
                    'servidor': server_name,
                    'system_type': 'SoftRestaurant',
                    'cortes_encontrados': len(cortes),
                    'cortes_con_propinas': creados_server + actualizados_server,
                    'creados': creados_server,
                    'actualizados': actualizados_server,
                    'status': 'OK',
                    'destino': 'SQL Server EDARSA HUB'
                })
                
                logger.info(f"{server_name}: {creados_server} creados, {actualizados_server} actualizados en SQL")
                
            except Exception as e:
                error_msg = f"Error en {server_name}: {str(e)}"
                logger.error(error_msg)
                errores.append({'servidor': server_name, 'error': str(e)})
                detalle.append({
                    'servidor': server_name,
                    'system_type': 'SoftRestaurant',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        # Invalidar cache después de sincronización
        if total_creados > 0 or total_actualizados > 0:
            await self.cache.invalidar_listados()
            await self.cache.invalidar_resumenes()
            logger.info("Cache invalidado post-sincronización")
        
        logger.info(f"Sincronización SQL completada: {total_creados} creados, {total_actualizados} actualizados")
        
        return SincronizarResponse(
            success=len(errores) == 0,
            registros_creados=total_creados,
            registros_actualizados=total_actualizados,
            errores=errores,
            detalle_por_servidor=detalle
        )
    
    # =========================================================================
    # CONSULTAS (Cache → SQL)
    # =========================================================================
    
    async def obtener_propinas(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        server_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        estado: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Obtiene listado de propinas con cache.
        
        FLUJO:
        1. Buscar en cache MongoDB
        2. Si cache válido → retornar
        3. Si cache inválido → consultar SQL Server → actualizar cache → retornar
        """
        skip = (page - 1) * limit
        
        # 1. Intentar cache
        cached = await self.cache.get_listado_cache(
            fecha_inicio, fecha_fin, server_id, sucursal_id, estado, page, limit
        )
        
        if cached:
            logger.debug("Propinas servidas desde cache")
            return cached
        
        # 2. Consultar SQL Server
        propinas = await self.sql_repo.obtener_propinas(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            server_id=server_id,
            sucursal_id=sucursal_id,
            estado=estado,
            skip=skip,
            limit=limit
        )
        
        total = await self.sql_repo.contar_propinas(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            server_id=server_id,
            estado=estado
        )
        
        # Calcular totales
        totales = {
            'total_propinas_tpv': sum(p['origen']['propinas_tpv'] for p in propinas),
            'total_comision': sum(p['calculo']['comision_calculada'] for p in propinas),
            'total_a_pagar': sum(p['calculo']['monto_a_pagar_meseros'] for p in propinas),
            'total_pagado': sum(
                p['pago']['monto_pagado'] or 0
                for p in propinas
                if p['pago']['registrado']
            )
        }
        
        result = {
            'propinas': propinas,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit if total > 0 else 0,
            'totales': totales,
            'fuente': 'SQL Server EDARSA HUB'
        }
        
        # 3. Actualizar cache
        await self.cache.set_listado_cache(
            fecha_inicio, fecha_fin, server_id, sucursal_id, estado, page, limit,
            result
        )
        
        return result
    
    async def obtener_propina_por_id(self, propina_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una propina por ID con cache."""
        # Intentar cache
        cached = await self.cache.get_detalle_cache(propina_id)
        if cached:
            return cached
        
        # Consultar SQL
        propina = await self.sql_repo.obtener_propina_por_id(propina_id)
        
        if propina:
            await self.cache.set_detalle_cache(propina_id, propina)
        
        return propina
    
    async def obtener_resumen(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene resumen agregado con cache."""
        # Intentar cache
        cached = await self.cache.get_resumen_cache(fecha_inicio, fecha_fin, server_id)
        if cached:
            logger.debug("Resumen servido desde cache")
            cached['fuente'] = 'cache'
            return cached
        
        # Consultar SQL
        resumen = await self.sql_repo.obtener_resumen(fecha_inicio, fecha_fin, server_id)
        
        # Obtener conteo por estado
        estados = {}
        for estado in EstadoCuadre:
            count = await self.sql_repo.contar_propinas(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                server_id=server_id,
                estado=estado.value
            )
            estados[estado.value] = count
        
        result = {
            'periodo': {
                'inicio': fecha_inicio,
                'fin': fecha_fin
            },
            **resumen,
            'por_estado': estados,
            'fuente': 'SQL Server EDARSA HUB'
        }
        
        # Actualizar cache
        await self.cache.set_resumen_cache(fecha_inicio, fecha_fin, server_id, result)
        
        return result
    
    # =========================================================================
    # REGISTRO DE PAGO
    # =========================================================================
    
    async def registrar_pago(
        self,
        propina_id: str,
        monto_pagado: float,
        metodo: str,
        observaciones: Optional[str],
        usuario_id: str,
        usuario_email: str
    ) -> Dict[str, Any]:
        """
        Registra el pago de propinas a meseros.
        
        FLUJO:
        1. Validar que la propina existe y no tiene pago
        2. Registrar pago en SQL Server
        3. Invalidar cache
        4. Retornar propina actualizada
        """
        # Validar
        propina = await self.sql_repo.obtener_propina_por_id(propina_id)
        if not propina:
            raise ValueError(f"Propina {propina_id} no encontrada")
        
        if propina['pago']['registrado']:
            raise ValueError("Esta propina ya tiene un pago registrado")
        
        # Obtener tolerancia de config
        config = await self.sql_repo.obtener_config_vigente()
        tolerancia = config['parametros']['tolerancia_descuadre']
        
        # Registrar pago en SQL
        pago_data = {
            'monto_pagado': monto_pagado,
            'fecha_pago': datetime.now(timezone.utc),
            'metodo': metodo,
            'observaciones': observaciones
        }
        
        success = await self.sql_repo.registrar_pago(
            propina_id=propina_id,
            pago_data=pago_data,
            usuario_id=usuario_id,
            usuario_email=usuario_email,
            tolerancia=tolerancia
        )
        
        if not success:
            raise ValueError("Error al registrar el pago en SQL Server")
        
        # Invalidar cache
        await self.cache.invalidar_detalle(propina_id)
        await self.cache.invalidar_listados()
        await self.cache.invalidar_resumenes()
        
        # Retornar propina actualizada
        return await self.sql_repo.obtener_propina_por_id(propina_id)
    
    # =========================================================================
    # CONFIGURACIÓN
    # =========================================================================
    
    async def obtener_config(
        self,
        server_id: Optional[str] = None,
        sucursal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene configuración vigente con cache."""
        # Intentar cache
        cached = await self.cache.get_config_cache(server_id, None, sucursal_id)
        if cached:
            return cached
        
        # Consultar SQL
        config = await self.sql_repo.obtener_config_vigente(
            server_id=server_id,
            sucursal_id=sucursal_id
        )
        
        # Actualizar cache
        await self.cache.set_config_cache(server_id, None, sucursal_id, config)
        
        return config
    
    # =========================================================================
    # ESTADÍSTICAS DE CACHE
    # =========================================================================
    
    async def obtener_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache."""
        return await self.cache.obtener_stats()
    
    async def invalidar_cache_completo(self):
        """Invalida todo el cache."""
        await self.cache.invalidar_todo()
        return {"message": "Cache invalidado completamente"}
