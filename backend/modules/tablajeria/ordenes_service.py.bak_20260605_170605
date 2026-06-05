"""
EDARSA HUB - Tablajería Órdenes Service
=======================================
Servicio para gestión de órdenes de tablaje.

FASE 5: Crear, ejecutar, cerrar órdenes de producción.
FASE 4: Captura Directa (Mayo 2026)
"""

import logging
import pymssql
import uuid
import json
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, date, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from .schemas import (
    OrdenCreate, OrdenUpdate, EstatusOrden, TipoDerivado, TipoMerma,
    OrdenCapturaDirectaCreate
)

logger = logging.getLogger(__name__)

MEXICO_TZ = ZoneInfo("America/Mexico_City")


class TablajeriaOrdenesService:
    """
    Servicio de gestión de órdenes de tablajería.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        
    def _get_connection(self):
        """Conexión a EDARSAHUB SQL"""
        return pymssql.connect(
            server=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['username'],
            password=self.db_config['password'],
            login_timeout=30,
            timeout=60,
            autocommit=False
        )
    
    def _now_utc(self) -> datetime:
        return datetime.utcnow()
    
    def _today_mexico(self) -> date:
        return datetime.now(MEXICO_TZ).date()
    
    # ============================================================
    # GENERACIÓN DE FOLIO
    # ============================================================
    
    def _generar_folio(self, cursor, empresa_id: str) -> str:
        """
        Genera folio único para orden de tablaje.
        Formato: TBJ-{YYYYMMDD}-{SECUENCIAL:04d}
        """
        fecha_hoy = self._today_mexico()
        prefijo = f"TBJ-{fecha_hoy.strftime('%Y%m%d')}"
        
        # Obtener último secuencial del día
        cursor.execute("""
            SELECT MAX(FolioOrden) as ultimo
            FROM Operaciones_Tablaje_Ordenes
            WHERE EmpresaID = %s AND FolioOrden LIKE %s
        """, (empresa_id, f"{prefijo}%"))
        
        row = cursor.fetchone()
        if row and row['ultimo']:
            # Extraer secuencial del folio existente
            try:
                ultimo_seq = int(row['ultimo'].split('-')[-1])
                nuevo_seq = ultimo_seq + 1
            except (ValueError, IndexError):
                nuevo_seq = 1
        else:
            nuevo_seq = 1
        
        return f"{prefijo}-{nuevo_seq:04d}"
    
    # ============================================================
    # CREAR ORDEN
    # ============================================================
    
    def crear_orden(
        self,
        data: OrdenCreate,
        usuario_id: str
    ) -> Dict[str, Any]:
        """
        Crea una nueva orden de tablaje basada en una plantilla.
        
        Args:
            data: Datos de la orden
            usuario_id: UUID del usuario que crea
            
        Returns:
            Dict con la orden creada
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # 1. Validar que la plantilla existe y está PUBLICADA
            cursor.execute("""
                SELECT 
                    PlantillaID, NombrePlantilla, InsumoBaseCodigo, InsumoBaseNombre,
                    RendimientoEsperadoPorcentaje, MermaEsperadaPorcentaje,
                    ReglaCosteo, VersionActual, Estatus, EmpresaID
                FROM Operaciones_Tablaje_Plantillas
                WHERE PlantillaID = %s AND Activo = 1
            """, (data.plantilla_id,))
            
            plantilla = cursor.fetchone()
            if not plantilla:
                raise ValueError(f"Plantilla no encontrada: {data.plantilla_id}")
            
            if plantilla['Estatus'] not in ('PUBLICADA', 'SINCRONIZADA', 'VALIDADA'):
                raise ValueError(f"Plantilla no disponible para uso. Estatus: {plantilla['Estatus']}")
            
            # 2. Generar folio
            folio = self._generar_folio(cursor, data.empresa_id)
            
            # 3. Crear orden
            orden_id = str(uuid.uuid4())
            now_utc = self._now_utc()
            fecha_op = data.fecha_operacion_mexico or self._today_mexico()
            
            cursor.execute("""
                INSERT INTO Operaciones_Tablaje_Ordenes (
                    OrdenID, EmpresaID, UnidadNegocioID, SucursalID,
                    FolioOrden, PlantillaID, PlantillaVersion,
                    InsumoBaseCodigo, InsumoBaseNombre, LoteInsumo,
                    CantidadBasePlaneada, UnidadBaseID,
                    RendimientoEsperadoPorcentaje, MermaEsperadaPorcentaje,
                    EstatusOrden, FechaOperacionMexico, FechaProgramada,
                    OrigenOrden, AfectaInventario, Observaciones,
                    Activo, FechaAltaUTC, UsuarioAltaID
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                orden_id,
                data.empresa_id,
                data.unidad_negocio_id,
                data.sucursal_id,
                folio,
                data.plantilla_id,
                plantilla['VersionActual'],
                plantilla['InsumoBaseCodigo'],
                plantilla['InsumoBaseNombre'],
                data.lote_insumo,
                float(data.cantidad_base_planeada),
                None,  # UnidadBaseID
                float(plantilla['RendimientoEsperadoPorcentaje']) if plantilla['RendimientoEsperadoPorcentaje'] else None,
                float(plantilla['MermaEsperadaPorcentaje']) if plantilla['MermaEsperadaPorcentaje'] else None,
                EstatusOrden.BORRADOR.value,
                fecha_op,
                data.fecha_programada,
                'CAPTURA_DIRECTA',
                True,
                data.observaciones,
                True,
                now_utc,
                usuario_id
            ))
            
            # 4. Copiar detalles de la plantilla a la orden
            cursor.execute("""
                SELECT 
                    PlantillaDetalleID, ProductoDerivadoID, ProductoDerivadoCodigo,
                    ProductoDerivadoNombre, TipoDerivado, CantidadEsperada,
                    PorcentajeRendimientoEsperado, PorcentajeCostoAsignado,
                    EsMerma, EsSubproducto, UnidadDerivadoCodigo
                FROM Operaciones_Tablaje_PlantillasDetalle
                WHERE PlantillaID = %s AND Activo = 1
                ORDER BY OrdenVisual
            """, (data.plantilla_id,))
            
            detalles_plantilla = cursor.fetchall()
            
            for det in detalles_plantilla:
                detalle_id = str(uuid.uuid4())
                
                # Calcular cantidad esperada proporcional
                cantidad_esperada = None
                if det['CantidadEsperada'] and data.cantidad_base_planeada:
                    cantidad_esperada = float(det['CantidadEsperada']) * float(data.cantidad_base_planeada)
                
                cursor.execute("""
                    INSERT INTO Operaciones_Tablaje_OrdenesDetalle (
                        OrdenDetalleID, OrdenID, PlantillaDetalleID,
                        ProductoDerivadoID, ProductoDerivadoCodigo, ProductoDerivadoNombre,
                        TipoDerivado, CantidadEsperada, PorcentajeEsperado,
                        PorcentajeCostoAsignado, UnidadCodigo, GeneraMovimiento
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    detalle_id,
                    orden_id,
                    str(det['PlantillaDetalleID']),
                    det['ProductoDerivadoID'],
                    det['ProductoDerivadoCodigo'],
                    det['ProductoDerivadoNombre'],
                    det['TipoDerivado'],
                    cantidad_esperada,
                    float(det['PorcentajeRendimientoEsperado']) if det['PorcentajeRendimientoEsperado'] else None,
                    float(det['PorcentajeCostoAsignado']) if det['PorcentajeCostoAsignado'] else None,
                    det['UnidadDerivadoCodigo'],
                    not det['EsMerma']  # Mermas no generan movimiento de inventario directo
                ))
            
            conn.commit()
            
            logger.info(f"[TablajeriaOrdenes] Orden creada: {folio} (PlantillaID: {data.plantilla_id})")
            
            return {
                "orden_id": orden_id,
                "folio_orden": folio,
                "plantilla_id": data.plantilla_id,
                "plantilla_nombre": plantilla['NombrePlantilla'],
                "estatus_orden": EstatusOrden.BORRADOR.value,
                "cantidad_base_planeada": float(data.cantidad_base_planeada),
                "fecha_operacion_mexico": str(fecha_op),
                "detalles_count": len(detalles_plantilla)
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[TablajeriaOrdenes] Error creando orden: {e}")
            raise
        finally:
            conn.close()
    
    # ============================================================
    # FASE 4: CAPTURA DIRECTA (crear orden sin plantilla)
    # ============================================================
    
    def crear_orden_captura_directa(
        self, 
        data: 'OrdenCapturaDirectaCreate', 
        usuario_id: str
    ) -> Dict[str, Any]:
        """
        Fase 4: Captura Directa.
        Crea una orden de tablaje especificando manualmente el insumo y derivados.
        No requiere plantilla predefinida.
        
        Args:
            data: Datos de la orden con insumo base y detalles de derivados
            usuario_id: ID del usuario que crea la orden
        
        Returns:
            Dict con datos de la orden creada
        """
        from .schemas import EstatusOrden
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            now = datetime.now(timezone.utc)
            fecha_op = data.fecha_operacion_mexico or now.date()
            
            # Generar IDs
            orden_id = str(uuid.uuid4())
            
            # Generar folio
            folio = self._generar_folio(cursor, data.empresa_id)
            
            # Calcular rendimiento esperado
            total_esperado = sum(
                float(d.cantidad_esperada or 0) 
                for d in data.detalles 
                if d.tipo_derivado.value != 'MERMA'
            )
            rendimiento_esperado = (total_esperado / float(data.cantidad_base_planeada) * 100) if float(data.cantidad_base_planeada) > 0 else 0
            
            # Calcular merma esperada
            merma_esperada = sum(
                float(d.cantidad_esperada or 0) 
                for d in data.detalles 
                if d.tipo_derivado.value == 'MERMA'
            )
            merma_porcentaje = (merma_esperada / float(data.cantidad_base_planeada) * 100) if float(data.cantidad_base_planeada) > 0 else 0
            
            # Insertar orden (sin PlantillaID)
            # Nota: EmpresaID y ResponsableID son uniqueidentifier en SQL Server
            # Convertir a UUID si no es válido
            def to_uuid_safe(val):
                if not val:
                    return None
                val_str = str(val)
                # Si ya es UUID válido (con guiones), usarlo tal cual
                if len(val_str) == 36 and val_str.count('-') == 4:
                    return val_str
                # Generar UUID basado en el valor
                return str(uuid.uuid5(uuid.NAMESPACE_DNS, val_str))
            
            empresa_uuid = to_uuid_safe(data.empresa_id)
            unidad_uuid = to_uuid_safe(data.unidad_negocio_id)
            resp_uuid = to_uuid_safe(data.responsable_id or usuario_id)
            usuario_uuid = to_uuid_safe(usuario_id)
            
            # UUID especial para captura directa (sin plantilla)
            PLANTILLA_CAPTURA_DIRECTA = '00000000-0000-0000-0000-000000000001'
            
            cursor.execute("""
                INSERT INTO Operaciones_Tablaje_Ordenes (
                    OrdenID, EmpresaID, UnidadNegocioID, SucursalID,
                    PlantillaID, FolioOrden, EstatusOrden,
                    InsumoBaseCodigo, InsumoBaseNombre,
                    CantidadBasePlaneada, LoteInsumo,
                    RendimientoEsperadoPorcentaje, MermaEsperadaPorcentaje,
                    ResponsableID, Observaciones, OrigenOrden,
                    FechaOperacionMexico, FechaAltaUTC, UsuarioAltaID
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                orden_id,
                empresa_uuid,
                unidad_uuid,
                data.sucursal_id,
                PLANTILLA_CAPTURA_DIRECTA,
                folio,
                EstatusOrden.BORRADOR.value,
                data.insumo_base_codigo,
                data.insumo_base_nombre,
                float(data.cantidad_base_planeada),
                data.lote_insumo,
                round(rendimiento_esperado, 2),
                round(merma_porcentaje, 2),
                resp_uuid,
                data.observaciones,
                'CAPTURA_DIRECTA',  # Marcar origen
                fecha_op, now, usuario_uuid
            ))
            
            # Insertar detalles
            for idx, det in enumerate(data.detalles):
                detalle_id = str(uuid.uuid4())
                
                cursor.execute("""
                    INSERT INTO Operaciones_Tablaje_OrdenesDetalle (
                        OrdenDetalleID, OrdenID,
                        ProductoDerivadoCodigo, ProductoDerivadoNombre,
                        TipoDerivado, CantidadEsperada,
                        PorcentajeEsperado, UnidadCodigo,
                        GeneraMovimiento
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    detalle_id,
                    orden_id,
                    det.producto_derivado_codigo or f"PROD-{idx+1:03d}",
                    det.producto_derivado_nombre,
                    det.tipo_derivado.value,
                    float(det.cantidad_esperada or 0),
                    float(det.porcentaje_esperado or 0) if det.porcentaje_esperado else None,
                    'KG',
                    det.tipo_derivado.value != 'MERMA'
                ))
            
            conn.commit()
            
            logger.info(f"[TablajeriaOrdenes] Orden Captura Directa creada: {folio}")
            
            return {
                "orden_id": orden_id,
                "folio_orden": folio,
                "plantilla_id": None,
                "plantilla_nombre": "CAPTURA DIRECTA",
                "insumo_base": {
                    "codigo": data.insumo_base_codigo,
                    "nombre": data.insumo_base_nombre
                },
                "estatus_orden": EstatusOrden.BORRADOR.value,
                "cantidad_base_planeada": float(data.cantidad_base_planeada),
                "fecha_operacion_mexico": str(fecha_op),
                "detalles_count": len(data.detalles),
                "origen": "CAPTURA_DIRECTA"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[TablajeriaOrdenes] Error creando orden captura directa: {e}")
            raise
        finally:
            conn.close()
    
    # ============================================================
    # OBTENER ORDEN
    # ============================================================
    
    def obtener_orden(self, orden_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una orden con sus detalles"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Header
            cursor.execute("""
                SELECT 
                    o.*, p.NombrePlantilla
                FROM Operaciones_Tablaje_Ordenes o
                LEFT JOIN Operaciones_Tablaje_Plantillas p ON o.PlantillaID = p.PlantillaID
                WHERE o.OrdenID = %s
            """, (orden_id,))
            
            orden = cursor.fetchone()
            if not orden:
                return None
            
            # Convertir a dict y UUIDs
            result = dict(orden)
            for field in ['OrdenID', 'EmpresaID', 'UnidadNegocioID', 'PlantillaID',
                          'ResponsableID', 'EjecutorID', 'SupervisorID', 'AutorizadoPor',
                          'UsuarioAltaID', 'UsuarioModificacionID']:
                if result.get(field):
                    result[field] = str(result[field])
            
            # Detalles
            cursor.execute("""
                SELECT * FROM Operaciones_Tablaje_OrdenesDetalle
                WHERE OrdenID = %s
                ORDER BY TipoDerivado, ProductoDerivadoNombre
            """, (orden_id,))
            
            detalles = []
            for row in cursor.fetchall():
                d = dict(row)
                d['OrdenDetalleID'] = str(d['OrdenDetalleID'])
                d['OrdenID'] = str(d['OrdenID'])
                if d.get('PlantillaDetalleID'):
                    d['PlantillaDetalleID'] = str(d['PlantillaDetalleID'])
                detalles.append(d)
            
            result['detalles'] = detalles
            
            return result
            
        finally:
            conn.close()
    
    # ============================================================
    # LISTAR ÓRDENES
    # ============================================================
    
    def listar_ordenes(
        self,
        empresa_id: Optional[str] = None,
        estatus: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        plantilla_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Lista órdenes con filtros"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            query = """
                SELECT 
                    o.OrdenID, o.EmpresaID, o.FolioOrden, o.PlantillaID,
                    p.NombrePlantilla, o.InsumoBaseNombre,
                    o.CantidadBasePlaneada, o.CantidadBaseReal,
                    o.RendimientoEsperadoPorcentaje, o.RendimientoRealPorcentaje,
                    o.EstatusOrden, o.FechaOperacionMexico,
                    o.FechaInicioEjecucion, o.FechaCierre,
                    o.Activo, o.FechaAltaUTC
                FROM Operaciones_Tablaje_Ordenes o
                LEFT JOIN Operaciones_Tablaje_Plantillas p ON o.PlantillaID = p.PlantillaID
                WHERE o.Activo = 1
            """
            params = []
            
            if empresa_id:
                query += " AND o.EmpresaID = %s"
                params.append(empresa_id)
            if estatus:
                query += " AND o.EstatusOrden = %s"
                params.append(estatus)
            if fecha_desde:
                query += " AND o.FechaOperacionMexico >= %s"
                params.append(fecha_desde)
            if fecha_hasta:
                query += " AND o.FechaOperacionMexico <= %s"
                params.append(fecha_hasta)
            if plantilla_id:
                query += " AND o.PlantillaID = %s"
                params.append(plantilla_id)
            
            query += " ORDER BY o.FechaOperacionMexico DESC, o.FolioOrden DESC"
            query += " OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            params.extend([offset, limit])
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            ordenes = []
            for row in rows:
                o = dict(row)
                for field in ['OrdenID', 'EmpresaID', 'PlantillaID']:
                    if o.get(field):
                        o[field] = str(o[field])
                ordenes.append(o)
            
            # Contar total
            count_query = """
                SELECT COUNT(*) as total
                FROM Operaciones_Tablaje_Ordenes
                WHERE Activo = 1
            """
            count_params = []
            if empresa_id:
                count_query += " AND EmpresaID = %s"
                count_params.append(empresa_id)
            if estatus:
                count_query += " AND EstatusOrden = %s"
                count_params.append(estatus)
            
            cursor.execute(count_query, tuple(count_params) if count_params else None)
            total = cursor.fetchone()['total']
            
            return {
                "ordenes": ordenes,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        finally:
            conn.close()
    
    # ============================================================
    # INICIAR EJECUCIÓN
    # ============================================================
    
    def iniciar_ejecucion(self, orden_id: str, usuario_id: str) -> Dict[str, Any]:
        """
        Cambia estatus de BORRADOR/PLANEADA a EN_EJECUCION.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Verificar estatus actual
            cursor.execute("""
                SELECT EstatusOrden, FolioOrden FROM Operaciones_Tablaje_Ordenes
                WHERE OrdenID = %s AND Activo = 1
            """, (orden_id,))
            
            orden = cursor.fetchone()
            if not orden:
                raise ValueError("Orden no encontrada")
            
            if orden['EstatusOrden'] not in ('BORRADOR', 'PLANEADA'):
                raise ValueError(f"No se puede iniciar ejecución. Estatus actual: {orden['EstatusOrden']}")
            
            now_utc = self._now_utc()
            cursor.execute("""
                UPDATE Operaciones_Tablaje_Ordenes SET
                    EstatusOrden = %s,
                    FechaInicioEjecucion = %s,
                    EjecutorID = %s,
                    FechaModificacionUTC = %s,
                    UsuarioModificacionID = %s
                WHERE OrdenID = %s
            """, (
                EstatusOrden.EN_EJECUCION.value,
                now_utc,
                usuario_id,
                now_utc,
                usuario_id,
                orden_id
            ))
            
            conn.commit()
            
            logger.info(f"[TablajeriaOrdenes] Orden iniciada: {orden['FolioOrden']}")
            
            return {
                "orden_id": orden_id,
                "folio": orden['FolioOrden'],
                "estatus": EstatusOrden.EN_EJECUCION.value,
                "fecha_inicio": str(now_utc)
            }
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ============================================================
    # REGISTRAR RESULTADOS (EJECUTAR)
    # ============================================================
    
    def registrar_resultados(
        self,
        orden_id: str,
        cantidad_base_real: Decimal,
        peso_inicial_kg: Optional[Decimal],
        peso_final_kg: Optional[Decimal],
        detalles: List[Dict],
        usuario_id: str
    ) -> Dict[str, Any]:
        """
        Registra los resultados reales del tablaje.
        
        Args:
            orden_id: ID de la orden
            cantidad_base_real: Cantidad real de insumo base procesado
            peso_inicial_kg: Peso inicial en kg
            peso_final_kg: Peso final en kg
            detalles: Lista de resultados por derivado [{orden_detalle_id, cantidad_real, peso_real_kg}]
            usuario_id: Usuario que registra
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Verificar orden
            cursor.execute("""
                SELECT EstatusOrden, FolioOrden, RendimientoEsperadoPorcentaje, MermaEsperadaPorcentaje
                FROM Operaciones_Tablaje_Ordenes
                WHERE OrdenID = %s AND Activo = 1
            """, (orden_id,))
            
            orden = cursor.fetchone()
            if not orden:
                raise ValueError("Orden no encontrada")
            
            if orden['EstatusOrden'] != 'EN_EJECUCION':
                raise ValueError(f"La orden debe estar EN_EJECUCION. Estatus actual: {orden['EstatusOrden']}")
            
            now_utc = self._now_utc()
            
            # Actualizar detalles
            total_real = Decimal('0')
            total_merma = Decimal('0')
            
            for det in detalles:
                detalle_id = det.get('orden_detalle_id')
                cantidad_real = det.get('cantidad_real')
                peso_real = det.get('peso_real_kg')
                
                if not detalle_id:
                    continue
                
                # Obtener info del detalle
                cursor.execute("""
                    SELECT TipoDerivado, CantidadEsperada, PorcentajeEsperado
                    FROM Operaciones_Tablaje_OrdenesDetalle
                    WHERE OrdenDetalleID = %s
                """, (detalle_id,))
                
                det_info = cursor.fetchone()
                if not det_info:
                    continue
                
                # Calcular desviaciones
                desviacion_cantidad = None
                porcentaje_real = None
                
                if cantidad_real is not None and cantidad_base_real:
                    cantidad_real = Decimal(str(cantidad_real))
                    porcentaje_real = (cantidad_real / Decimal(str(cantidad_base_real))) * 100
                    
                    if det_info['CantidadEsperada']:
                        desviacion_cantidad = cantidad_real - Decimal(str(det_info['CantidadEsperada']))
                    
                    # Sumar a totales
                    if det_info['TipoDerivado'] == 'MERMA':
                        total_merma += cantidad_real
                    else:
                        total_real += cantidad_real
                
                cursor.execute("""
                    UPDATE Operaciones_Tablaje_OrdenesDetalle SET
                        CantidadReal = %s,
                        PesoRealKg = %s,
                        PorcentajeReal = %s,
                        DesviacionCantidad = %s,
                        FechaCaptura = %s,
                        UsuarioCapturaID = %s
                    WHERE OrdenDetalleID = %s
                """, (
                    float(cantidad_real) if cantidad_real else None,
                    float(peso_real) if peso_real else None,
                    float(porcentaje_real) if porcentaje_real else None,
                    float(desviacion_cantidad) if desviacion_cantidad else None,
                    now_utc,
                    usuario_id,
                    detalle_id
                ))
            
            # Calcular rendimiento y merma real
            rendimiento_real = None
            merma_real = None
            merma_real_kg = None
            
            if cantidad_base_real:
                cantidad_base_decimal = Decimal(str(cantidad_base_real))
                if total_real:
                    rendimiento_real = (total_real / cantidad_base_decimal) * 100
                if total_merma:
                    merma_real = (total_merma / cantidad_base_decimal) * 100
                    merma_real_kg = total_merma
                elif peso_inicial_kg and peso_final_kg:
                    # Calcular merma por diferencia de peso
                    merma_real_kg = Decimal(str(peso_inicial_kg)) - Decimal(str(peso_final_kg)) - total_real
                    if merma_real_kg > 0:
                        merma_real = (merma_real_kg / cantidad_base_decimal) * 100
            
            # Calcular desviación de rendimiento
            desviacion_rendimiento = None
            if rendimiento_real and orden['RendimientoEsperadoPorcentaje']:
                desviacion_rendimiento = float(rendimiento_real) - float(orden['RendimientoEsperadoPorcentaje'])
            
            # Actualizar orden
            cursor.execute("""
                UPDATE Operaciones_Tablaje_Ordenes SET
                    CantidadBaseReal = %s,
                    PesoInicialKg = %s,
                    PesoFinalKg = %s,
                    RendimientoRealPorcentaje = %s,
                    DesviacionRendimiento = %s,
                    MermaRealPorcentaje = %s,
                    MermaRealKg = %s,
                    FechaModificacionUTC = %s,
                    UsuarioModificacionID = %s
                WHERE OrdenID = %s
            """, (
                float(cantidad_base_real),
                float(peso_inicial_kg) if peso_inicial_kg else None,
                float(peso_final_kg) if peso_final_kg else None,
                float(rendimiento_real) if rendimiento_real else None,
                desviacion_rendimiento,
                float(merma_real) if merma_real else None,
                float(merma_real_kg) if merma_real_kg else None,
                now_utc,
                usuario_id,
                orden_id
            ))
            
            conn.commit()
            
            logger.info(f"[TablajeriaOrdenes] Resultados registrados: {orden['FolioOrden']}")
            
            return {
                "orden_id": orden_id,
                "folio": orden['FolioOrden'],
                "cantidad_base_real": float(cantidad_base_real),
                "rendimiento_real_porcentaje": float(rendimiento_real) if rendimiento_real else None,
                "merma_real_porcentaje": float(merma_real) if merma_real else None,
                "desviacion_rendimiento": desviacion_rendimiento,
                "detalles_actualizados": len(detalles)
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[TablajeriaOrdenes] Error registrando resultados: {e}")
            raise
        finally:
            conn.close()
    
    # ============================================================
    # CERRAR ORDEN
    # ============================================================
    
    def cerrar_orden(
        self,
        orden_id: str,
        usuario_id: str,
        observaciones: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cierra la orden después de la ejecución.
        Verifica si requiere autorización por desviaciones.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener orden
            cursor.execute("""
                SELECT 
                    o.*, p.ToleranciaRendimiento
                FROM Operaciones_Tablaje_Ordenes o
                LEFT JOIN Operaciones_Tablaje_Plantillas p ON o.PlantillaID = p.PlantillaID
                WHERE o.OrdenID = %s AND o.Activo = 1
            """, (orden_id,))
            
            orden = cursor.fetchone()
            if not orden:
                raise ValueError("Orden no encontrada")
            
            if orden['EstatusOrden'] != 'EN_EJECUCION':
                raise ValueError(f"Solo se pueden cerrar órdenes EN_EJECUCION. Estatus: {orden['EstatusOrden']}")
            
            # Verificar si hay resultados registrados
            if not orden['CantidadBaseReal']:
                raise ValueError("Debe registrar los resultados antes de cerrar la orden")
            
            now_utc = self._now_utc()
            
            # Verificar si requiere autorización por desviación
            requiere_autorizacion = False
            motivo_autorizacion = None
            tolerancia = float(orden['ToleranciaRendimiento'] or 5.0)
            
            if orden['DesviacionRendimiento'] is not None:
                if abs(orden['DesviacionRendimiento']) > tolerancia:
                    requiere_autorizacion = True
                    motivo_autorizacion = f"Desviación de rendimiento ({orden['DesviacionRendimiento']:.2f}%) excede tolerancia ({tolerancia}%)"
            
            nuevo_estatus = EstatusOrden.PENDIENTE_AUTORIZACION.value if requiere_autorizacion else EstatusOrden.CERRADA.value
            
            cursor.execute("""
                UPDATE Operaciones_Tablaje_Ordenes SET
                    EstatusOrden = %s,
                    FechaCierre = %s,
                    RequiereAutorizacion = %s,
                    MotivoAutorizacion = %s,
                    Observaciones = COALESCE(%s, Observaciones),
                    FechaModificacionUTC = %s,
                    UsuarioModificacionID = %s
                WHERE OrdenID = %s
            """, (
                nuevo_estatus,
                now_utc if not requiere_autorizacion else None,
                requiere_autorizacion,
                motivo_autorizacion,
                observaciones,
                now_utc,
                usuario_id,
                orden_id
            ))
            
            # Registrar rendimiento histórico (solo si hay rendimiento calculado)
            # NOTA: La tabla Operaciones_Tablaje_Rendimientos no permite NULL en RendimientoRealPorcentaje
            if orden.get('RendimientoRealPorcentaje') is not None:
                cursor.execute("""
                    INSERT INTO Operaciones_Tablaje_Rendimientos (
                        RendimientoID, OrdenID, EmpresaID, UnidadNegocioID,
                        FechaOperacionMexico, PlantillaID, NombrePlantilla,
                        InsumoBaseNombre, CantidadInsumoConsumido,
                        RendimientoEsperadoPorcentaje, RendimientoRealPorcentaje,
                        DesviacionPorcentaje, DentroTolerancia, FechaRegistroUTC
                    )
                    SELECT 
                        NEWID(), OrdenID, EmpresaID, UnidadNegocioID,
                        FechaOperacionMexico, PlantillaID, %s,
                        InsumoBaseNombre, CantidadBaseReal,
                        RendimientoEsperadoPorcentaje, RendimientoRealPorcentaje,
                        DesviacionRendimiento, %s, %s
                    FROM Operaciones_Tablaje_Ordenes
                    WHERE OrdenID = %s
                """, (
                    orden.get('NombrePlantilla'),
                    not requiere_autorizacion,
                    now_utc,
                    orden_id
                ))
            else:
                logger.warning(f"[TablajeriaOrdenes] Orden {orden['FolioOrden']} cerrada sin rendimiento calculado - no se registra en histórico")
            
            # Registrar mermas si hay
            if orden['MermaRealKg']:
                cursor.execute("""
                    INSERT INTO Operaciones_Tablaje_Mermas (
                        MermaID, OrdenID, EmpresaID, UnidadNegocioID,
                        FechaOperacionMexico, TipoMerma, Descripcion,
                        CantidadKg, PorcentajeSobreInsumo,
                        MermaEsperadaPorcentaje, DentroTolerancia,
                        RequiereAutorizacion, FechaRegistroUTC, UsuarioRegistroID
                    ) VALUES (
                        NEWID(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    orden_id,
                    str(orden['EmpresaID']),
                    str(orden['UnidadNegocioID']) if orden['UnidadNegocioID'] else None,
                    orden['FechaOperacionMexico'],
                    TipoMerma.OTRO.value,
                    'Merma general del tablaje',
                    float(orden['MermaRealKg']),
                    float(orden['MermaRealPorcentaje']) if orden['MermaRealPorcentaje'] else None,
                    float(orden['MermaEsperadaPorcentaje']) if orden['MermaEsperadaPorcentaje'] else None,
                    not requiere_autorizacion,
                    requiere_autorizacion,
                    now_utc,
                    usuario_id
                ))
            
            conn.commit()
            
            logger.info(f"[TablajeriaOrdenes] Orden cerrada: {orden['FolioOrden']} -> {nuevo_estatus}")
            
            return {
                "orden_id": orden_id,
                "folio": orden['FolioOrden'],
                "estatus": nuevo_estatus,
                "requiere_autorizacion": requiere_autorizacion,
                "motivo_autorizacion": motivo_autorizacion,
                "rendimiento_real": float(orden['RendimientoRealPorcentaje']) if orden['RendimientoRealPorcentaje'] else None,
                "desviacion": orden['DesviacionRendimiento']
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[TablajeriaOrdenes] Error cerrando orden: {e}")
            raise
        finally:
            conn.close()
    
    # ============================================================
    # CANCELAR ORDEN
    # ============================================================
    
    def cancelar_orden(
        self,
        orden_id: str,
        usuario_id: str,
        motivo: str
    ) -> Dict[str, Any]:
        """Cancela una orden (solo si no está CERRADA)"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT EstatusOrden, FolioOrden FROM Operaciones_Tablaje_Ordenes
                WHERE OrdenID = %s AND Activo = 1
            """, (orden_id,))
            
            orden = cursor.fetchone()
            if not orden:
                raise ValueError("Orden no encontrada")
            
            if orden['EstatusOrden'] in ('CERRADA', 'CANCELADA', 'REVERTIDA'):
                raise ValueError(f"No se puede cancelar orden con estatus: {orden['EstatusOrden']}")
            
            now_utc = self._now_utc()
            cursor.execute("""
                UPDATE Operaciones_Tablaje_Ordenes SET
                    EstatusOrden = %s,
                    Observaciones = CONCAT(COALESCE(Observaciones + ' | ', ''), 'CANCELADO: ' + %s),
                    FechaModificacionUTC = %s,
                    UsuarioModificacionID = %s
                WHERE OrdenID = %s
            """, (
                EstatusOrden.CANCELADA.value,
                motivo,
                now_utc,
                usuario_id,
                orden_id
            ))
            
            conn.commit()
            
            logger.info(f"[TablajeriaOrdenes] Orden cancelada: {orden['FolioOrden']}")
            
            return {
                "orden_id": orden_id,
                "folio": orden['FolioOrden'],
                "estatus": EstatusOrden.CANCELADA.value,
                "motivo": motivo
            }
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ============================================================
    # AUTORIZAR ORDEN
    # ============================================================
    
    def autorizar_orden(
        self,
        orden_id: str,
        usuario_id: str,
        aprobado: bool,
        comentarios: Optional[str] = None
    ) -> Dict[str, Any]:
        """Autoriza o rechaza una orden pendiente de autorización"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT EstatusOrden, FolioOrden, MotivoAutorizacion
                FROM Operaciones_Tablaje_Ordenes
                WHERE OrdenID = %s AND Activo = 1
            """, (orden_id,))
            
            orden = cursor.fetchone()
            if not orden:
                raise ValueError("Orden no encontrada")
            
            if orden['EstatusOrden'] != 'PENDIENTE_AUTORIZACION':
                raise ValueError(f"Orden no está pendiente de autorización. Estatus: {orden['EstatusOrden']}")
            
            now_utc = self._now_utc()
            nuevo_estatus = EstatusOrden.CERRADA.value if aprobado else EstatusOrden.OBSERVADA.value
            
            cursor.execute("""
                UPDATE Operaciones_Tablaje_Ordenes SET
                    EstatusOrden = %s,
                    AutorizadoPor = %s,
                    FechaAutorizacion = %s,
                    FechaCierre = CASE WHEN %s = 1 THEN %s ELSE FechaCierre END,
                    Observaciones = CONCAT(COALESCE(Observaciones + ' | ', ''), %s),
                    FechaModificacionUTC = %s,
                    UsuarioModificacionID = %s
                WHERE OrdenID = %s
            """, (
                nuevo_estatus,
                usuario_id,
                now_utc,
                aprobado,
                now_utc,
                f"{'APROBADO' if aprobado else 'RECHAZADO'}: {comentarios or ''}",
                now_utc,
                usuario_id,
                orden_id
            ))
            
            # Registrar en tabla de autorizaciones
            cursor.execute("""
                INSERT INTO Operaciones_Tablaje_Autorizaciones (
                    AutorizacionID, EmpresaID, TipoAutorizacion,
                    EntidadTipo, EntidadID, EntidadFolio,
                    SolicitanteID, MotivoSolicitud,
                    Estatus, AutorizadorID, FechaResolucionUTC, Comentarios,
                    FechaOperacionMexico
                )
                SELECT 
                    NEWID(), EmpresaID, 'DESVIACION_RENDIMIENTO',
                    'ORDEN', OrdenID, FolioOrden,
                    UsuarioAltaID, MotivoAutorizacion,
                    %s, %s, %s, %s, FechaOperacionMexico
                FROM Operaciones_Tablaje_Ordenes
                WHERE OrdenID = %s
            """, (
                'APROBADA' if aprobado else 'RECHAZADA',
                usuario_id,
                now_utc,
                comentarios,
                orden_id
            ))
            
            conn.commit()
            
            logger.info(f"[TablajeriaOrdenes] Orden {'autorizada' if aprobado else 'rechazada'}: {orden['FolioOrden']}")
            
            return {
                "orden_id": orden_id,
                "folio": orden['FolioOrden'],
                "estatus": nuevo_estatus,
                "aprobado": aprobado,
                "comentarios": comentarios
            }
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
