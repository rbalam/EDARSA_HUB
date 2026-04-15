"""
Repository para el módulo de Control de Propinas TPV
FASE 1 MVP - Solo SoftRestaurant
FASE 1B - Query defensiva con detección de esquema

Responsabilidades:
- Consultas SQL a SoftRestaurant (SOLO LECTURA)
- Operaciones CRUD en MongoDB (colecciones nuevas)
- Detección automática de esquema por servidor

CAB Aprobado: 2026-04-14
Estabilización: 2026-04-15
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.db import execute_sql_query
from .schema_detector import SoftRestaurantSchemaDetector, get_schema_summary

logger = logging.getLogger(__name__)


class PropinasTPVRepository:
    """
    Repository para operaciones de datos del módulo de propinas TPV.
    
    IMPORTANTE - REGLAS DE AISLAMIENTO:
    1. SQL Server: SOLO operaciones SELECT (lectura)
    2. MongoDB: SOLO escribe en colecciones nuevas (propinas_control, propinas_config)
    3. NO modifica colecciones existentes
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection_control = db['propinas_control']
        self.collection_config = db['propinas_config']
    
    # ========================================================================
    # QUERIES SQL SERVER - SOFTRESTAURANT (SOLO LECTURA)
    # ========================================================================
    
    async def get_propinas_cortes_softrestaurant(
        self,
        server: Dict[str, Any],
        fecha_inicio: str,
        fecha_fin: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene propinas agregadas por corte desde SoftRestaurant.
        
        Fuente: movtoscajadetalles (concepto 9 = Propinas Pagadas)
        Tipo de dato: EXACTO
        
        Args:
            server: Diccionario con datos de conexión del servidor
            fecha_inicio: Fecha inicio formato YYYY-MM-DD
            fecha_fin: Fecha fin formato YYYY-MM-DD
            
        Returns:
            Lista de cortes con propinas
        """
        # Formatear fechas para SoftRestaurant (YYYYMMDD)
        f_ini = fecha_inicio.replace('-', '')
        f_fin = fecha_fin.replace('-', '')
        
        query = f"""
        SELECT 
            mc.folio AS folio_corte,
            mc.fecha AS fecha_corte,
            mc.idestacion AS estacion_id,
            ISNULL(e.descripcion, 'Sin estación') AS estacion_nombre,
            
            -- Propinas totales del corte (concepto 9 = Propinas Pagadas)
            ISNULL((
                SELECT SUM(d.importe) 
                FROM movtoscajadetalles d 
                WHERE d.idmovtocaja = mc.idmovtocaja 
                  AND d.idconcepto = 9
            ), 0) AS propinas_totales,
            
            -- Ventas con tarjeta (conceptos 10, 11, 12 = Visa/MC/Amex)
            ISNULL((
                SELECT SUM(d.importe) 
                FROM movtoscajadetalles d 
                WHERE d.idmovtocaja = mc.idmovtocaja 
                  AND d.idconcepto IN (10, 11, 12)
            ), 0) AS ventas_tarjeta,
            
            -- Ventas totales del corte
            ISNULL(mc.saldo, 0) AS ventas_totales,
            
            -- Efectivo del corte
            ISNULL((
                SELECT SUM(d.importe) 
                FROM movtoscajadetalles d 
                WHERE d.idmovtocaja = mc.idmovtocaja 
                  AND d.idconcepto = 2
            ), 0) AS ventas_efectivo

        FROM movtoscaja mc
        LEFT JOIN estaciones e ON mc.idestacion = e.idestacion
        WHERE mc.idtipomovtocaja = 3  -- Corte Z
          AND mc.fecha >= '{f_ini} 00:00:00'
          AND mc.fecha <= '{f_fin} 23:59:59'
        ORDER BY mc.fecha DESC
        """
        
        try:
            logger.info(f"Consultando propinas SoftRestaurant: {server['name']} [{fecha_inicio} - {fecha_fin}]")
            
            result = execute_sql_query(
                server['host'],
                server['port'],
                server['database'],
                server['username'],
                server['password'],
                query
            )
            
            cortes = []
            for row in result or []:
                fecha_val = row.get('fecha_corte')
                fecha_iso = fecha_val.isoformat() if hasattr(fecha_val, 'isoformat') else str(fecha_val)
                
                cortes.append({
                    'folio_corte': str(row.get('folio_corte', '')),
                    'fecha_corte': fecha_iso,
                    'estacion_id': str(row.get('estacion_id', '')),
                    'estacion_nombre': row.get('estacion_nombre', 'Sin estación'),
                    'propinas_totales': float(row.get('propinas_totales', 0) or 0),
                    'ventas_tarjeta': float(row.get('ventas_tarjeta', 0) or 0),
                    'ventas_totales': float(row.get('ventas_totales', 0) or 0),
                    'ventas_efectivo': float(row.get('ventas_efectivo', 0) or 0)
                })
            
            logger.info(f"SoftRestaurant {server['name']}: {len(cortes)} cortes encontrados")
            return cortes
            
        except Exception as e:
            logger.error(f"Error consultando propinas de {server['name']}: {e}")
            raise
    
    async def get_propinas_cortes_defensivo(
        self,
        server: Dict[str, Any],
        fecha_inicio: str,
        fecha_fin: str
    ) -> Dict[str, Any]:
        """
        FASE 1B: Query defensiva que detecta el esquema antes de consultar.
        
        Esta versión:
        1. Detecta automáticamente las columnas disponibles
        2. Construye la query adaptada al esquema
        3. Retorna tanto los datos como info del esquema
        
        Args:
            server: Diccionario con datos de conexión del servidor
            fecha_inicio: Fecha inicio formato YYYY-MM-DD
            fecha_fin: Fecha fin formato YYYY-MM-DD
            
        Returns:
            Dict con: cortes, schema, compatible, errores
        """
        result = {
            'cortes': [],
            'schema': None,
            'compatible': False,
            'error': None,
            'server_name': server.get('name', 'Desconocido'),
            'query_usada': None
        }
        
        try:
            # Paso 1: Detectar esquema
            logger.info(f"Detectando esquema para {server['name']}...")
            schema = SoftRestaurantSchemaDetector.detect_schema(server)
            result['schema'] = get_schema_summary(schema)
            result['compatible'] = schema.get('compatible', False)
            
            if not schema.get('compatible'):
                result['error'] = f"Esquema no compatible: {schema.get('compatibility_issues', [])}"
                logger.warning(f"{server['name']}: {result['error']}")
                return result
            
            # Paso 2: Construir query adaptada
            query = SoftRestaurantSchemaDetector.build_propinas_query(
                schema, fecha_inicio, fecha_fin
            )
            result['query_usada'] = query[:500] + '...' if len(query) > 500 else query
            
            # Paso 3: Ejecutar query
            logger.info(f"Ejecutando query defensiva para {server['name']}...")
            rows = execute_sql_query(
                server['host'],
                server['port'],
                server['database'],
                server['username'],
                server['password'],
                query
            )
            
            # Paso 4: Procesar resultados
            cortes = []
            estrategia_detectada = None
            for row in rows or []:
                fecha_val = row.get('fecha_corte')
                fecha_iso = fecha_val.isoformat() if hasattr(fecha_val, 'isoformat') else str(fecha_val)
                
                # Capturar estrategia usada
                if not estrategia_detectada:
                    estrategia_detectada = row.get('estrategia_usada', 'DESCONOCIDA')
                
                cortes.append({
                    'folio_corte': str(row.get('folio_corte', '')),
                    'fecha_corte': fecha_iso,
                    'estacion_id': str(row.get('estacion_id', 'N/A')),
                    'turno_id': str(row.get('turno_id', 'N/A')),
                    'corte_id': str(row.get('corte_id', '')),
                    # Propinas TPV es el valor principal (de cheques.propinatarjeta)
                    'propinas_tpv': float(row.get('propinas_tpv', 0) or 0),
                    'propinas_totales': float(row.get('propinas_totales', 0) or 0),
                    'ventas_tarjeta': float(row.get('ventas_tarjeta', 0) or 0),
                    'ventas_efectivo': float(row.get('ventas_efectivo', 0) or 0),
                    'ventas_totales': float(row.get('ventas_totales', 0) or 0),
                    'total_cheques': int(row.get('total_cheques', 0) or 0),
                    'saldo_corte': float(row.get('saldo_corte', 0) or 0),
                })
            
            result['cortes'] = cortes
            result['estrategia_usada'] = estrategia_detectada
            logger.info(f"{server['name']}: {len(cortes)} cortes encontrados (estrategia: {estrategia_detectada})")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error en query defensiva para {server['name']}: {e}")
        
        return result
    
    async def detectar_esquema_servidor(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """
        Solo detecta y retorna el esquema de un servidor, sin consultar datos.
        Útil para diagnóstico y validación.
        """
        schema = SoftRestaurantSchemaDetector.detect_schema(server)
        return get_schema_summary(schema)
    
    # ========================================================================
    # OPERACIONES MONGODB - COLECCIÓN propinas_control
    # ========================================================================
    
    async def crear_o_actualizar_propina(
        self,
        propina_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea o actualiza un registro de propina.
        Usa upsert para evitar duplicados basado en llave única.
        
        Llave única: server_id + sucursal_id + folio_corte + fecha_corte
        """
        filtro = {
            'server_id': propina_data['server_id'],
            'sucursal_id': propina_data['sucursal_id'],
            'folio_corte': propina_data['folio_corte'],
            'fecha_corte': propina_data['fecha_corte']
        }
        
        # Solo actualizar campos de origen y cálculo, preservar pago y cuadre si existen
        update_data = {
            '$set': {
                'server_name': propina_data['server_name'],
                'system_type': propina_data['system_type'],
                'sucursal_nombre': propina_data['sucursal_nombre'],
                'empresa_id': propina_data.get('empresa_id'),
                'origen': propina_data['origen'],
                'calculo': propina_data['calculo'],
                'updated_at': datetime.utcnow()
            },
            '$setOnInsert': {
                'id': propina_data['id'],
                'pago': {
                    'registrado': False,
                    'monto_pagado': None,
                    'fecha_pago': None,
                    'metodo': None,
                    'registrado_por': None,
                    'observaciones': None
                },
                'cuadre': {
                    'estado': 'PENDIENTE',
                    'diferencia': None,
                    'fecha_cuadre': None,
                    'observaciones': None
                },
                'created_at': datetime.utcnow()
            }
        }
        
        result = await self.collection_control.update_one(
            filtro,
            update_data,
            upsert=True
        )
        
        return {
            'created': result.upserted_id is not None,
            'modified': result.modified_count > 0
        }
    
    async def obtener_propinas(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        server_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Obtiene propinas con filtros opcionales"""
        filtro = {}
        
        if fecha_inicio:
            filtro['fecha_corte'] = {'$gte': datetime.fromisoformat(fecha_inicio)}
        if fecha_fin:
            if 'fecha_corte' in filtro:
                filtro['fecha_corte']['$lte'] = datetime.fromisoformat(fecha_fin + 'T23:59:59')
            else:
                filtro['fecha_corte'] = {'$lte': datetime.fromisoformat(fecha_fin + 'T23:59:59')}
        if server_id:
            filtro['server_id'] = server_id
        if sucursal_id:
            filtro['sucursal_id'] = sucursal_id
        if estado:
            filtro['cuadre.estado'] = estado
        
        cursor = self.collection_control.find(
            filtro, 
            {'_id': 0}
        ).sort('fecha_corte', -1).skip(skip).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def contar_propinas(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        server_id: Optional[str] = None,
        estado: Optional[str] = None
    ) -> int:
        """Cuenta propinas con filtros"""
        filtro = {}
        if fecha_inicio:
            filtro['fecha_corte'] = {'$gte': datetime.fromisoformat(fecha_inicio)}
        if fecha_fin:
            if 'fecha_corte' in filtro:
                filtro['fecha_corte']['$lte'] = datetime.fromisoformat(fecha_fin + 'T23:59:59')
            else:
                filtro['fecha_corte'] = {'$lte': datetime.fromisoformat(fecha_fin + 'T23:59:59')}
        if server_id:
            filtro['server_id'] = server_id
        if estado:
            filtro['cuadre.estado'] = estado
        
        return await self.collection_control.count_documents(filtro)
    
    async def obtener_propina_por_id(self, propina_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una propina por su ID"""
        return await self.collection_control.find_one(
            {'id': propina_id},
            {'_id': 0}
        )
    
    async def registrar_pago(
        self,
        propina_id: str,
        pago_data: Dict[str, Any],
        usuario: str
    ) -> bool:
        """Registra el pago de propinas y actualiza estado de cuadre"""
        propina = await self.obtener_propina_por_id(propina_id)
        if not propina:
            return False
        
        # Calcular diferencia
        monto_a_pagar = propina['calculo']['monto_a_pagar_meseros']
        monto_pagado = pago_data['monto_pagado']
        diferencia = abs(monto_a_pagar - monto_pagado)
        
        # Obtener tolerancia de config
        config = await self.obtener_config_vigente()
        tolerancia = config.get('parametros', {}).get('tolerancia_descuadre', 5.0)
        
        # Determinar estado de cuadre
        if diferencia <= tolerancia:
            estado_cuadre = 'CUADRADO'
        else:
            estado_cuadre = 'DESCUADRE'
        
        result = await self.collection_control.update_one(
            {'id': propina_id},
            {
                '$set': {
                    'pago': {
                        'registrado': True,
                        'monto_pagado': monto_pagado,
                        'fecha_pago': pago_data.get('fecha_pago', datetime.utcnow()),
                        'metodo': pago_data.get('metodo', 'EFECTIVO'),
                        'registrado_por': usuario,
                        'observaciones': pago_data.get('observaciones')
                    },
                    'cuadre': {
                        'estado': estado_cuadre,
                        'diferencia': diferencia,
                        'fecha_cuadre': datetime.utcnow(),
                        'observaciones': None
                    },
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def obtener_resumen(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene resumen agregado de propinas"""
        match_stage = {
            'fecha_corte': {
                '$gte': datetime.fromisoformat(fecha_inicio),
                '$lte': datetime.fromisoformat(fecha_fin + 'T23:59:59')
            }
        }
        if server_id:
            match_stage['server_id'] = server_id
        
        pipeline = [
            {'$match': match_stage},
            {
                '$group': {
                    '_id': None,
                    'total_propinas_tpv': {'$sum': '$origen.propinas_tpv'},
                    'total_comision': {'$sum': '$calculo.comision_calculada'},
                    'total_a_pagar': {'$sum': '$calculo.monto_a_pagar_meseros'},
                    'total_pagado': {
                        '$sum': {
                            '$cond': [
                                {'$eq': ['$pago.registrado', True]},
                                '$pago.monto_pagado',
                                0
                            ]
                        }
                    },
                    'registros': {'$sum': 1}
                }
            }
        ]
        
        result = await self.collection_control.aggregate(pipeline).to_list(length=1)
        
        if result:
            data = result[0]
            data.pop('_id', None)
            data['pendiente_pago'] = data['total_a_pagar'] - data['total_pagado']
            return data
        
        return {
            'total_propinas_tpv': 0,
            'total_comision': 0,
            'total_a_pagar': 0,
            'total_pagado': 0,
            'pendiente_pago': 0,
            'registros': 0
        }
    
    # ========================================================================
    # OPERACIONES MONGODB - COLECCIÓN propinas_config
    # ========================================================================
    
    async def obtener_config_vigente(
        self,
        server_id: Optional[str] = None,
        empresa_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        fecha: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene la configuración vigente aplicando jerarquía:
        SUCURSAL > EMPRESA > GLOBAL
        """
        if fecha is None:
            fecha = datetime.utcnow()
        
        base_filter = {
            'vigencia.activa': True,
            'vigencia.fecha_inicio': {'$lte': fecha},
            '$or': [
                {'vigencia.fecha_fin': None},
                {'vigencia.fecha_fin': {'$gte': fecha}}
            ]
        }
        
        # 1. Buscar config de SUCURSAL específica
        if sucursal_id and server_id:
            config = await self.collection_config.find_one(
                {
                    **base_filter,
                    'alcance.tipo': 'SUCURSAL',
                    'alcance.server_id': server_id,
                    'alcance.sucursal_id': sucursal_id
                },
                {'_id': 0}
            )
            if config:
                return config
        
        # 2. Buscar config de EMPRESA
        if empresa_id and server_id:
            config = await self.collection_config.find_one(
                {
                    **base_filter,
                    'alcance.tipo': 'EMPRESA',
                    'alcance.server_id': server_id,
                    'alcance.empresa_id': empresa_id
                },
                {'_id': 0}
            )
            if config:
                return config
        
        # 3. Buscar config GLOBAL (fallback)
        config = await self.collection_config.find_one(
            {
                **base_filter,
                'alcance.tipo': 'GLOBAL'
            },
            {'_id': 0}
        )
        
        if config:
            return config
        
        # 4. Retornar config por defecto si no existe ninguna
        return {
            'id': 'default',
            'alcance': {'tipo': 'GLOBAL'},
            'vigencia': {'activa': True, 'fecha_inicio': datetime.utcnow()},
            'parametros': {
                'porcentaje_comision': 0.02,
                'tolerancia_descuadre': 5.0,
                'dias_para_cuadrar': 1
            },
            'formas_pago_tpv_softrestaurant': {
                'conceptos': [10, 11, 12],
                'nombres': ['VISA', 'MASTERCARD', 'AMEX']
            }
        }
    
    async def crear_config(self, config_data: Dict[str, Any]) -> str:
        """Crea una nueva configuración"""
        await self.collection_config.insert_one(config_data)
        return config_data['id']
    
    async def actualizar_config(
        self,
        config_id: str,
        config_data: Dict[str, Any],
        usuario: str
    ) -> bool:
        """Actualiza una configuración existente"""
        config_data['updated_at'] = datetime.utcnow()
        config_data['updated_by'] = usuario
        
        result = await self.collection_config.update_one(
            {'id': config_id},
            {'$set': config_data}
        )
        return result.modified_count > 0
    
    async def listar_configs(self) -> List[Dict[str, Any]]:
        """Lista todas las configuraciones"""
        cursor = self.collection_config.find({}, {'_id': 0})
        return await cursor.to_list(length=100)
    
    # ========================================================================
    # INICIALIZACIÓN DE ÍNDICES
    # ========================================================================
    
    async def crear_indices(self):
        """
        Crea los índices necesarios para las colecciones.
        Debe ejecutarse una vez al inicializar el módulo.
        """
        # Índice único compuesto para propinas_control
        await self.collection_control.create_index(
            [
                ('server_id', 1),
                ('sucursal_id', 1),
                ('folio_corte', 1),
                ('fecha_corte', 1)
            ],
            unique=True,
            name='uk_propinas_corte'
        )
        
        # Índices de búsqueda frecuente
        await self.collection_control.create_index(
            [('fecha_corte', -1), ('cuadre.estado', 1)],
            name='idx_fecha_estado'
        )
        
        await self.collection_control.create_index(
            [('server_id', 1), ('fecha_corte', -1)],
            name='idx_server_fecha'
        )
        
        # Índices para propinas_config
        await self.collection_config.create_index(
            [('alcance.tipo', 1), ('vigencia.activa', 1)],
            name='idx_config_alcance'
        )
        
        logger.info("Índices de propinas_tpv creados correctamente")
