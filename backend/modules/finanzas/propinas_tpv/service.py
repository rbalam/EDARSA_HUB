"""
Service para el módulo de Control de Propinas TPV
FASE 1 MVP - Solo SoftRestaurant

Responsabilidades:
- Lógica de negocio
- Cálculos de comisión
- Orquestación de sincronización

CAB Aprobado: 2026-04-14
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime


from .repository import PropinasTPVRepository
from .models import (
    TipoDatoOrigen,
    EstadoCuadre,
    SincronizarResponse
)
# FASE T2.4: Usar server_registry centralizado en lugar de MongoDB
from core.server_registry import list_operational_servers

logger = logging.getLogger(__name__)


class PropinasTPVService:
    """
    Servicio de lógica de negocio para control de propinas TPV.
    
    FASE 1 MVP - Solo SoftRestaurant:
    - La Estelar
    - Cienfuegos
    - 130 Mérida
    
    FUERA DE ALCANCE (FASE 2):
    - MPRO
    """
    
    def __init__(self, db: Any):
        self.db = db
        self.repository = PropinasTPVRepository(db)
    
    async def sincronizar_propinas(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        server_id: Optional[str] = None,
        usuario: str = "sistema"
    ) -> SincronizarResponse:
        """
        Sincroniza propinas desde servidores SoftRestaurant.
        
        PROCESO:
        1. Obtener servidores SoftRestaurant activos
        2. Para cada servidor, consultar cortes con propinas
        3. Calcular comisión 2%
        4. Guardar en propinas_control (upsert)
        
        Args:
            fecha_inicio: Fecha inicio YYYY-MM-DD
            fecha_fin: Fecha fin YYYY-MM-DD
            server_id: Opcional - sincronizar solo un servidor
            usuario: Email del usuario que ejecuta
            
        Returns:
            SincronizarResponse con estadísticas
        """
        logger.info(f"Iniciando sincronización de propinas: {fecha_inicio} a {fecha_fin}")
        
        # FASE T2.4: Obtener servidores desde EDARSAHUB via server_registry
        # Ya no usar MongoDB: self.db['servers']
        servers = list_operational_servers(system_type_filter='SoftRestaurant')
        
        # Filtrar por server_id específico si se proporciona
        if server_id:
            servers = [s for s in servers if s.get('id') == server_id]
        
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
        config = await self.repository.obtener_config_vigente()
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
                
                # FASE 1B: Usar query defensiva con detección de esquema
                resultado = await self.repository.get_propinas_cortes_defensivo(
                    server,
                    fecha_inicio,
                    fecha_fin
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
                        'error': error_msg,
                        'schema': resultado.get('schema')
                    })
                    continue
                
                cortes = resultado['cortes']
                creados_server = 0
                actualizados_server = 0
                
                for corte in cortes:
                    # Solo procesar si hay propinas
                    propinas_totales = corte['propinas_totales']
                    if propinas_totales <= 0:
                        continue
                    
                    # En SoftRestaurant FASE 1: asumimos que todas las propinas
                    # del concepto 9 son TPV (propinas pagadas = ya procesadas por caja)
                    propinas_tpv = propinas_totales
                    
                    # Calcular comisión
                    comision = round(propinas_tpv * porcentaje_comision, 2)
                    monto_a_pagar = round(propinas_tpv - comision, 2)
                    
                    # Preparar documento
                    fecha_corte_dt = datetime.fromisoformat(corte['fecha_corte'].replace('Z', '+00:00')) \
                        if isinstance(corte['fecha_corte'], str) else corte['fecha_corte']
                    
                    propina_doc = {
                        'id': str(uuid.uuid4()),
                        'server_id': server_id_actual,
                        'sucursal_id': server_name,  # En SoftRestaurant, servidor = sucursal
                        'folio_corte': corte['folio_corte'],
                        'fecha_corte': fecha_corte_dt,
                        'server_name': server_name,
                        'system_type': 'SoftRestaurant',
                        'sucursal_nombre': server_name,
                        'empresa_id': server.get('database'),  # Database como identificador de empresa
                        'origen': {
                            'tipo_dato': TipoDatoOrigen.EXACTO.value,
                            'metodo_calculo': 'CONCEPTO_9_CORTE',
                            'confianza': 1.0,
                            'propinas_totales_corte': propinas_totales,
                            'ventas_tarjeta': corte['ventas_tarjeta'],
                            'ventas_totales': corte['ventas_totales'],
                            'propinas_tpv': propinas_tpv,
                            'formula_aplicada': 'movtoscajadetalles WHERE idconcepto=9',
                            'fecha_sincronizacion': datetime.utcnow(),
                            'advertencia': None
                        },
                        'calculo': {
                            'config_aplicada_id': config.get('id'),
                            'porcentaje_comision': porcentaje_comision,
                            'comision_calculada': comision,
                            'monto_a_pagar_meseros': monto_a_pagar
                        }
                    }
                    
                    # Crear o actualizar
                    result = await self.repository.crear_o_actualizar_propina(propina_doc)
                    
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
                    'status': 'OK'
                })
                
                logger.info(f"{server_name}: {creados_server} creados, {actualizados_server} actualizados")
                
            except Exception as e:
                error_msg = f"Error en {server_name}: {str(e)}"
                logger.error(error_msg)
                errores.append({
                    'servidor': server_name,
                    'error': str(e)
                })
                detalle.append({
                    'servidor': server_name,
                    'system_type': 'SoftRestaurant',
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        logger.info(f"Sincronización completada: {total_creados} creados, {total_actualizados} actualizados")
        
        return SincronizarResponse(
            success=len(errores) == 0,
            registros_creados=total_creados,
            registros_actualizados=total_actualizados,
            errores=errores,
            detalle_por_servidor=detalle
        )
    
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
        Obtiene listado de propinas con filtros y paginación.
        """
        skip = (page - 1) * limit
        
        propinas = await self.repository.obtener_propinas(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            server_id=server_id,
            sucursal_id=sucursal_id,
            estado=estado,
            skip=skip,
            limit=limit
        )
        
        total = await self.repository.contar_propinas(
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
        
        return {
            'propinas': propinas,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit,
            'totales': totales
        }
    
    async def registrar_pago(
        self,
        propina_id: str,
        monto_pagado: float,
        metodo: str,
        observaciones: Optional[str],
        usuario: str
    ) -> Dict[str, Any]:
        """
        Registra el pago de propinas a meseros.
        """
        propina = await self.repository.obtener_propina_por_id(propina_id)
        if not propina:
            raise ValueError(f"Propina {propina_id} no encontrada")
        
        if propina['pago']['registrado']:
            raise ValueError("Esta propina ya tiene un pago registrado")
        
        pago_data = {
            'monto_pagado': monto_pagado,
            'fecha_pago': datetime.utcnow(),
            'metodo': metodo,
            'observaciones': observaciones
        }
        
        success = await self.repository.registrar_pago(
            propina_id,
            pago_data,
            usuario
        )
        
        if success:
            return await self.repository.obtener_propina_por_id(propina_id)
        else:
            raise ValueError("Error al registrar el pago")
    
    async def obtener_resumen(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene resumen agregado de propinas por período.
        """
        resumen = await self.repository.obtener_resumen(
            fecha_inicio,
            fecha_fin,
            server_id
        )
        
        # Obtener conteo por estado
        estados = {}
        for estado in EstadoCuadre:
            count = await self.repository.contar_propinas(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                server_id=server_id,
                estado=estado.value
            )
            estados[estado.value] = count
        
        return {
            'periodo': {
                'inicio': fecha_inicio,
                'fin': fecha_fin
            },
            **resumen,
            'por_estado': estados
        }
    
    async def obtener_config(
        self,
        server_id: Optional[str] = None,
        sucursal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene la configuración vigente.
        """
        return await self.repository.obtener_config_vigente(
            server_id=server_id,
            sucursal_id=sucursal_id
        )
    
    async def crear_config(
        self,
        config_data: Dict[str, Any],
        usuario: str
    ) -> str:
        """
        Crea una nueva configuración.
        """
        config_data['id'] = str(uuid.uuid4())
        config_data['created_at'] = datetime.utcnow()
        config_data['created_by'] = usuario
        config_data['updated_at'] = datetime.utcnow()
        config_data['updated_by'] = usuario
        
        return await self.repository.crear_config(config_data)
    
    async def actualizar_config(
        self,
        config_id: str,
        config_data: Dict[str, Any],
        usuario: str
    ) -> bool:
        """
        Actualiza una configuración existente.
        """
        return await self.repository.actualizar_config(
            config_id,
            config_data,
            usuario
        )
    
    async def listar_configs(self) -> List[Dict[str, Any]]:
        """
        Lista todas las configuraciones.
        """
        return await self.repository.listar_configs()
    
    async def inicializar_modulo(self):
        """
        Inicializa el módulo creando índices y config por defecto.
        Debe ejecutarse una vez.
        """
        logger.info("Inicializando módulo de Propinas TPV...")
        
        # Crear índices
        await self.repository.crear_indices()
        
        # Verificar si existe config GLOBAL
        config = await self.repository.obtener_config_vigente()
        if config.get('id') == 'default':
            # Crear config GLOBAL por defecto
            config_default = {
                'id': str(uuid.uuid4()),
                'alcance': {
                    'tipo': 'GLOBAL',
                    'server_id': None,
                    'empresa_id': None,
                    'sucursal_id': None
                },
                'vigencia': {
                    'fecha_inicio': datetime.utcnow(),
                    'fecha_fin': None,
                    'activa': True
                },
                'parametros': {
                    'porcentaje_comision': 0.02,
                    'tolerancia_descuadre': 5.0,
                    'dias_para_cuadrar': 1
                },
                'formas_pago_tpv_softrestaurant': {
                    'conceptos': [10, 11, 12],
                    'nombres': ['VISA', 'MASTERCARD', 'AMEX']
                },
                'created_at': datetime.utcnow(),
                'created_by': 'sistema',
                'updated_at': datetime.utcnow(),
                'updated_by': 'sistema',
                'motivo_cambio': 'Configuración inicial del módulo'
            }
            await self.repository.crear_config(config_default)
            logger.info("Configuración GLOBAL por defecto creada")
        
        logger.info("Módulo de Propinas TPV inicializado correctamente")
