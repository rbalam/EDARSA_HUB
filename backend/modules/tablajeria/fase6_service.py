"""
EDARSA HUB - Tablajería Fase 6: Inventarios, Costeo y Contabilidad
===================================================================
Servicio que gestiona la afectación de inventarios, costeo de producción
y generación de pólizas contables para órdenes de tablaje.

Fecha: Mayo 2026
"""

import logging
import pymssql
import uuid
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timezone
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TipoMovimiento(str, Enum):
    SALIDA_INSUMO = "SALIDA_INSUMO"
    ENTRADA_DERIVADO = "ENTRADA_DERIVADO"
    SALIDA_MERMA = "SALIDA_MERMA"
    AJUSTE_INVENTARIO = "AJUSTE_INVENTARIO"


class TipoPoliza(str, Enum):
    PRODUCCION = "PRODUCCION"
    MERMA = "MERMA"
    AJUSTE = "AJUSTE"


class EstatusPoliza(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONTABILIZADA = "CONTABILIZADA"
    ERROR = "ERROR"


@dataclass
class ConfigContable:
    """Configuración contable por empresa."""
    empresa_id: str
    cuenta_almacen_insumos: str = "1151-001"
    cuenta_almacen_productos: str = "1152-001"
    cuenta_produccion_proceso: str = "1153-001"
    cuenta_costo_ventas: str = "5101-001"
    cuenta_merma_operativa: str = "5102-001"
    cuenta_merma_extraordinaria: str = "5103-001"
    cuenta_variacion_costo: str = "5104-001"
    generar_poliza_automatica: bool = True
    afectar_inventario_automatico: bool = True
    tolerancia_variacion: float = 5.0


class TablajeriaFase6Service:
    """
    Servicio de Fase 6: Inventarios, Costeo y Contabilidad.
    
    Funcionalidades:
    - Afectación de inventarios al cerrar órdenes
    - Costeo de producción por reglas (proporcional, fijo, residual)
    - Generación de pólizas contables
    """
    
    def __init__(self, db_config: Dict = None):
        """Inicializa el servicio con configuración de BD."""
        self.db_config = db_config or {
            'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
            'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
            'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
            'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
            'password': os.environ.get('EDARSAHUB_PASSWORD', '')
        }
        self._config_cache: Dict[str, ConfigContable] = {}
    
    def _get_connection(self):
        """Obtiene conexión a la BD."""
        return pymssql.connect(
            server=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['username'],
            password=self.db_config['password'],
            timeout=30,
            login_timeout=15
        )
    
    def _now_utc(self) -> datetime:
        return datetime.now(timezone.utc)
    
    # =========================================================================
    # CONFIGURACIÓN CONTABLE
    # =========================================================================
    
    def obtener_config_contable(self, empresa_id: str) -> ConfigContable:
        """Obtiene la configuración contable de una empresa."""
        if empresa_id in self._config_cache:
            return self._config_cache[empresa_id]
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute("""
                SELECT * FROM Tablajeria_ConfigContable
                WHERE EmpresaID = %s AND Activo = 1
            """, (empresa_id,))
            
            row = cursor.fetchone()
            if row:
                config = ConfigContable(
                    empresa_id=empresa_id,
                    cuenta_almacen_insumos=row.get('CuentaAlmacenInsumos') or "1151-001",
                    cuenta_almacen_productos=row.get('CuentaAlmacenProductos') or "1152-001",
                    cuenta_produccion_proceso=row.get('CuentaProduccionEnProceso') or "1153-001",
                    cuenta_costo_ventas=row.get('CuentaCostoVentas') or "5101-001",
                    cuenta_merma_operativa=row.get('CuentaMermaOperativa') or "5102-001",
                    cuenta_merma_extraordinaria=row.get('CuentaMermaExtraordinaria') or "5103-001",
                    cuenta_variacion_costo=row.get('CuentaVariacionCosto') or "5104-001",
                    generar_poliza_automatica=bool(row.get('GenerarPolizaAutomatica', True)),
                    afectar_inventario_automatico=bool(row.get('AfectarInventarioAutomatico', True)),
                    tolerancia_variacion=float(row.get('ToleranciaVariacionPorcentaje') or 5.0)
                )
            else:
                # Config por defecto
                config = ConfigContable(empresa_id=empresa_id)
            
            self._config_cache[empresa_id] = config
            return config
            
        finally:
            conn.close()
    
    def guardar_config_contable(self, config: ConfigContable, usuario_id: str) -> bool:
        """Guarda la configuración contable de una empresa."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Verificar si existe
            cursor.execute("""
                SELECT ConfigID FROM Tablajeria_ConfigContable
                WHERE EmpresaID = %s
            """, (config.empresa_id,))
            
            if cursor.fetchone():
                # Update
                cursor.execute("""
                    UPDATE Tablajeria_ConfigContable SET
                        CuentaAlmacenInsumos = %s,
                        CuentaAlmacenProductos = %s,
                        CuentaProduccionEnProceso = %s,
                        CuentaCostoVentas = %s,
                        CuentaMermaOperativa = %s,
                        CuentaMermaExtraordinaria = %s,
                        CuentaVariacionCosto = %s,
                        GenerarPolizaAutomatica = %s,
                        AfectarInventarioAutomatico = %s,
                        ToleranciaVariacionPorcentaje = %s,
                        FechaModificacion = GETUTCDATE()
                    WHERE EmpresaID = %s
                """, (
                    config.cuenta_almacen_insumos,
                    config.cuenta_almacen_productos,
                    config.cuenta_produccion_proceso,
                    config.cuenta_costo_ventas,
                    config.cuenta_merma_operativa,
                    config.cuenta_merma_extraordinaria,
                    config.cuenta_variacion_costo,
                    config.generar_poliza_automatica,
                    config.afectar_inventario_automatico,
                    config.tolerancia_variacion,
                    config.empresa_id
                ))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO Tablajeria_ConfigContable (
                        EmpresaID, CuentaAlmacenInsumos, CuentaAlmacenProductos,
                        CuentaProduccionEnProceso, CuentaCostoVentas,
                        CuentaMermaOperativa, CuentaMermaExtraordinaria,
                        CuentaVariacionCosto, GenerarPolizaAutomatica,
                        AfectarInventarioAutomatico, ToleranciaVariacionPorcentaje
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    config.empresa_id,
                    config.cuenta_almacen_insumos,
                    config.cuenta_almacen_productos,
                    config.cuenta_produccion_proceso,
                    config.cuenta_costo_ventas,
                    config.cuenta_merma_operativa,
                    config.cuenta_merma_extraordinaria,
                    config.cuenta_variacion_costo,
                    config.generar_poliza_automatica,
                    config.afectar_inventario_automatico,
                    config.tolerancia_variacion
                ))
            
            conn.commit()
            
            # Invalidar cache
            if config.empresa_id in self._config_cache:
                del self._config_cache[config.empresa_id]
            
            logger.info(f"[FASE6] Config contable guardada para empresa {config.empresa_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[FASE6] Error guardando config: {e}")
            return False
        finally:
            conn.close()
    
    # =========================================================================
    # AFECTACIÓN DE INVENTARIOS
    # =========================================================================
    
    def afectar_inventario_orden(
        self,
        orden_id: str,
        usuario_id: str
    ) -> Dict[str, Any]:
        """
        Afecta el inventario basado en una orden cerrada.
        
        Movimientos:
        1. SALIDA_INSUMO: Resta el insumo base del almacén
        2. ENTRADA_DERIVADO: Suma productos derivados al almacén
        3. SALIDA_MERMA: Registra mermas (si es inventariable)
        
        Returns:
            Dict con resumen de movimientos generados
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener datos de la orden
            cursor.execute("""
                SELECT 
                    o.OrdenID, o.EmpresaID, o.SucursalID, o.FolioOrden,
                    o.InsumoBaseCodigo, o.InsumoBaseNombre, o.LoteInsumo,
                    o.CantidadBaseReal, o.MermaRealKg,
                    o.EstatusOrden, o.FechaOperacionMexico
                FROM Operaciones_Tablaje_Ordenes o
                WHERE o.OrdenID = %s AND o.Activo = 1
            """, (orden_id,))
            
            orden = cursor.fetchone()
            if not orden:
                raise ValueError("Orden no encontrada")
            
            if orden['EstatusOrden'] not in ('CERRADA', 'PENDIENTE_AUTORIZACION'):
                raise ValueError(f"Solo se puede afectar inventario de órdenes cerradas. Estatus: {orden['EstatusOrden']}")
            
            config = self.obtener_config_contable(str(orden['EmpresaID']))
            
            if not config.afectar_inventario_automatico:
                logger.info(f"[FASE6] Afectación automática deshabilitada para empresa {orden['EmpresaID']}")
                return {"movimientos": 0, "mensaje": "Afectación automática deshabilitada"}
            
            movimientos = []
            now = self._now_utc()
            
            # 1. SALIDA_INSUMO - Consumo del insumo base
            if orden['CantidadBaseReal'] and orden['InsumoBaseCodigo']:
                mov_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO Tablajeria_MovimientosInventario (
                        MovimientoID, OrdenID, TipoMovimiento,
                        ProductoCodigo, ProductoNombre,
                        AlmacenOrigenID, Cantidad, LoteProducto,
                        FechaMovimiento, UsuarioID, Referencia
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    mov_id, orden_id, TipoMovimiento.SALIDA_INSUMO.value,
                    orden['InsumoBaseCodigo'], orden['InsumoBaseNombre'],
                    str(orden['SucursalID']) if orden['SucursalID'] else None,
                    float(orden['CantidadBaseReal']),
                    orden['LoteInsumo'],
                    now, usuario_id, orden['FolioOrden']
                ))
                movimientos.append({
                    "tipo": TipoMovimiento.SALIDA_INSUMO.value,
                    "producto": orden['InsumoBaseCodigo'],
                    "cantidad": float(orden['CantidadBaseReal'])
                })
            
            # 2. ENTRADA_DERIVADO - Productos producidos
            # Nota: OrdenesDetalle no tiene EsInventariable, usamos GeneraMovimiento y TipoDerivado
            cursor.execute("""
                SELECT 
                    OrdenDetalleID, ProductoDerivadoCodigo, ProductoDerivadoNombre,
                    CantidadReal, TipoDerivado, GeneraMovimiento
                FROM Operaciones_Tablaje_OrdenesDetalle
                WHERE OrdenID = %s AND CantidadReal > 0 AND GeneraMovimiento = 1
            """, (orden_id,))
            
            detalles = cursor.fetchall()
            for det in detalles:
                mov_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO Tablajeria_MovimientosInventario (
                        MovimientoID, OrdenID, TipoMovimiento,
                        ProductoCodigo, ProductoNombre,
                        AlmacenDestinoID, Cantidad,
                        FechaMovimiento, UsuarioID, Referencia
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    mov_id, orden_id, TipoMovimiento.ENTRADA_DERIVADO.value,
                    det['ProductoDerivadoCodigo'], det['ProductoDerivadoNombre'],
                    str(orden['SucursalID']) if orden['SucursalID'] else None,
                    float(det['CantidadReal']),
                    now, usuario_id, orden['FolioOrden']
                ))
                movimientos.append({
                    "tipo": TipoMovimiento.ENTRADA_DERIVADO.value,
                    "producto": det['ProductoDerivadoCodigo'],
                    "cantidad": float(det['CantidadReal'])
                })
            
            # 3. SALIDA_MERMA - Mermas (si las hay)
            if orden['MermaRealKg'] and float(orden['MermaRealKg']) > 0:
                mov_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO Tablajeria_MovimientosInventario (
                        MovimientoID, OrdenID, TipoMovimiento,
                        ProductoCodigo, ProductoNombre,
                        AlmacenOrigenID, Cantidad,
                        FechaMovimiento, UsuarioID, Referencia
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    mov_id, orden_id, TipoMovimiento.SALIDA_MERMA.value,
                    'MERMA-TABLAJE', f"Merma de {orden['InsumoBaseNombre']}",
                    str(orden['SucursalID']) if orden['SucursalID'] else None,
                    float(orden['MermaRealKg']),
                    now, usuario_id, orden['FolioOrden']
                ))
                movimientos.append({
                    "tipo": TipoMovimiento.SALIDA_MERMA.value,
                    "producto": "MERMA-TABLAJE",
                    "cantidad": float(orden['MermaRealKg'])
                })
            
            # Marcar orden como afectada
            cursor.execute("""
                UPDATE Operaciones_Tablaje_Ordenes SET
                    AfectaInventario = 1,
                    MovimientoInventarioGenerado = 1,
                    FechaModificacionUTC = %s
                WHERE OrdenID = %s
            """, (now, orden_id))
            
            conn.commit()
            
            logger.info(f"[FASE6] Inventario afectado para orden {orden['FolioOrden']}: {len(movimientos)} movimientos")
            
            return {
                "orden_id": orden_id,
                "folio": orden['FolioOrden'],
                "movimientos_generados": len(movimientos),
                "detalle": movimientos
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[FASE6] Error afectando inventario: {e}")
            raise
        finally:
            conn.close()
    
    # =========================================================================
    # COSTEO DE PRODUCCIÓN
    # =========================================================================
    
    def calcular_costeo_orden(
        self,
        orden_id: str,
        costo_unitario_insumo: Decimal,
        costos_adicionales: Dict[str, Decimal] = None,
        usuario_id: str = None
    ) -> Dict[str, Any]:
        """
        Calcula y registra el costeo de producción de una orden.
        
        Args:
            orden_id: ID de la orden
            costo_unitario_insumo: Costo por unidad del insumo base
            costos_adicionales: Dict con {mano_obra, indirectos, energia, otros}
            usuario_id: Usuario que realiza el costeo
            
        Returns:
            Dict con resumen del costeo
        """
        costos = costos_adicionales or {}
        conn = self._get_connection()
        
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener orden y plantilla
            cursor.execute("""
                SELECT 
                    o.OrdenID, o.EmpresaID, o.FolioOrden,
                    o.InsumoBaseCodigo, o.InsumoBaseNombre,
                    o.CantidadBaseReal, 
                    p.ReglaCosteo
                FROM Operaciones_Tablaje_Ordenes o
                LEFT JOIN Operaciones_Tablaje_Plantillas p ON o.PlantillaID = p.PlantillaID
                WHERE o.OrdenID = %s AND o.Activo = 1
            """, (orden_id,))
            
            orden = cursor.fetchone()
            if not orden:
                raise ValueError("Orden no encontrada")
            
            if not orden['CantidadBaseReal']:
                raise ValueError("Orden sin cantidad real registrada")
            
            # Calcular costo total del insumo
            cantidad_insumo = Decimal(str(orden['CantidadBaseReal']))
            costo_total_insumo = cantidad_insumo * costo_unitario_insumo
            
            # Costos adicionales
            costo_mano_obra = Decimal(str(costos.get('mano_obra', 0)))
            costo_indirectos = Decimal(str(costos.get('indirectos', 0)))
            costo_energia = Decimal(str(costos.get('energia', 0)))
            otros_costos = Decimal(str(costos.get('otros', 0)))
            
            costo_total_produccion = (
                costo_total_insumo + 
                costo_mano_obra + 
                costo_indirectos + 
                costo_energia + 
                otros_costos
            )
            
            # Obtener detalles de producción
            # Nota: OrdenesDetalle no tiene EsInventariable, se infiere de TipoDerivado
            cursor.execute("""
                SELECT 
                    OrdenDetalleID, ProductoDerivadoCodigo, ProductoDerivadoNombre,
                    TipoDerivado, CantidadReal, PorcentajeCostoAsignado,
                    GeneraMovimiento
                FROM Operaciones_Tablaje_OrdenesDetalle
                WHERE OrdenID = %s AND CantidadReal > 0
            """, (orden_id,))
            
            detalles = cursor.fetchall()
            
            # Calcular cantidad total producida
            total_producido = sum(
                Decimal(str(d['CantidadReal'] or 0)) 
                for d in detalles 
                if d['TipoDerivado'] != 'MERMA'
            )
            
            # Costo unitario promedio
            costo_unitario_promedio = (
                costo_total_produccion / total_producido 
                if total_producido > 0 else Decimal('0')
            )
            
            # Regla de costeo
            regla = orden.get('ReglaCosteo') or 'PROPORCIONAL'
            
            # Guardar costeo principal
            costeo_id = str(uuid.uuid4())
            now = self._now_utc()
            
            cursor.execute("""
                INSERT INTO Tablajeria_CosteoProduccion (
                    CosteoID, OrdenID, FechaCosteo,
                    InsumoBaseCodigo, InsumoBaseNombre,
                    CantidadInsumoConsumida, CostoUnitarioInsumo, CostoTotalInsumo,
                    CostoManoObra, CostoIndirectos, CostoEnergia, OtrosCostos,
                    CostoTotalProduccion, CostoUnitarioPromedio,
                    ReglaCosteoAplicada, UsuarioID
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                costeo_id, orden_id, now,
                orden['InsumoBaseCodigo'], orden['InsumoBaseNombre'],
                float(cantidad_insumo), float(costo_unitario_insumo), float(costo_total_insumo),
                float(costo_mano_obra), float(costo_indirectos),
                float(costo_energia), float(otros_costos),
                float(costo_total_produccion), float(costo_unitario_promedio),
                regla, usuario_id
            ))
            
            # Calcular y guardar costeo por producto derivado
            detalles_costeo = []
            
            for det in detalles:
                cantidad = Decimal(str(det['CantidadReal'] or 0))
                
                if regla == 'PROPORCIONAL':
                    # Costo proporcional a la cantidad producida
                    if total_producido > 0:
                        porcentaje = (cantidad / total_producido) * 100
                        costo_asignado = costo_total_produccion * (cantidad / total_producido)
                    else:
                        porcentaje = Decimal('0')
                        costo_asignado = Decimal('0')
                elif regla == 'FIJO' and det['PorcentajeCostoAsignado']:
                    # Costo fijo según porcentaje definido en plantilla
                    porcentaje = Decimal(str(det['PorcentajeCostoAsignado']))
                    costo_asignado = costo_total_produccion * (porcentaje / 100)
                else:
                    # Default: proporcional
                    if total_producido > 0:
                        porcentaje = (cantidad / total_producido) * 100
                        costo_asignado = costo_total_produccion * (cantidad / total_producido)
                    else:
                        porcentaje = Decimal('0')
                        costo_asignado = Decimal('0')
                
                costo_unitario = costo_asignado / cantidad if cantidad > 0 else Decimal('0')
                
                # Inferir EsInventariable: si no es MERMA y genera movimiento
                es_inventariable = det['TipoDerivado'] != 'MERMA' and det.get('GeneraMovimiento', True)
                
                detalle_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO Tablajeria_CosteoDetalle (
                        DetalleID, CosteoID, OrdenDetalleID,
                        ProductoCodigo, ProductoNombre, TipoDerivado,
                        CantidadProducida, PorcentajeCostoAsignado,
                        CostoAsignado, CostoUnitario, EsInventariable
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    detalle_id, costeo_id, det['OrdenDetalleID'],
                    det['ProductoDerivadoCodigo'], det['ProductoDerivadoNombre'],
                    det['TipoDerivado'],
                    float(cantidad), float(porcentaje),
                    float(costo_asignado), float(costo_unitario),
                    es_inventariable
                ))
                
                detalles_costeo.append({
                    "producto": det['ProductoDerivadoCodigo'],
                    "cantidad": float(cantidad),
                    "porcentaje": float(porcentaje),
                    "costo_asignado": float(costo_asignado),
                    "costo_unitario": float(costo_unitario)
                })
            
            conn.commit()
            
            logger.info(f"[FASE6] Costeo calculado para orden {orden['FolioOrden']}: ${float(costo_total_produccion):,.2f}")
            
            return {
                "costeo_id": costeo_id,
                "orden_id": orden_id,
                "folio": orden['FolioOrden'],
                "regla_aplicada": regla,
                "resumen": {
                    "costo_insumo": float(costo_total_insumo),
                    "costo_mano_obra": float(costo_mano_obra),
                    "costo_indirectos": float(costo_indirectos),
                    "costo_energia": float(costo_energia),
                    "otros_costos": float(otros_costos),
                    "costo_total": float(costo_total_produccion),
                    "costo_unitario_promedio": float(costo_unitario_promedio)
                },
                "detalles": detalles_costeo
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[FASE6] Error calculando costeo: {e}")
            raise
        finally:
            conn.close()
    
    # =========================================================================
    # PÓLIZAS CONTABLES
    # =========================================================================
    
    def generar_poliza_produccion(
        self,
        orden_id: str,
        usuario_id: str
    ) -> Dict[str, Any]:
        """
        Genera la póliza contable para una orden de producción.
        
        Asientos:
        - Cargo: Almacén Productos Terminados
        - Cargo: Merma (si aplica)
        - Abono: Almacén Materia Prima
        - Cargo/Abono: Variación Costo (si hay diferencia)
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Obtener costeo de la orden
            cursor.execute("""
                SELECT 
                    c.*, o.FolioOrden, o.EmpresaID, o.FechaOperacionMexico,
                    o.MermaRealKg
                FROM Tablajeria_CosteoProduccion c
                JOIN Operaciones_Tablaje_Ordenes o ON c.OrdenID = o.OrdenID
                WHERE c.OrdenID = %s
            """, (orden_id,))
            
            costeo = cursor.fetchone()
            if not costeo:
                raise ValueError("No existe costeo para esta orden. Primero calcule el costeo.")
            
            config = self.obtener_config_contable(str(costeo['EmpresaID']))
            
            if not config.generar_poliza_automatica:
                return {"mensaje": "Generación automática de pólizas deshabilitada"}
            
            poliza_id = str(uuid.uuid4())
            now = self._now_utc()
            fecha_poliza = costeo['FechaOperacionMexico'] or now.date()
            
            # Crear póliza
            numero_poliza = f"PRD-{costeo['FolioOrden']}"
            concepto = f"Producción tablaje - {costeo['FolioOrden']} - {costeo['InsumoBaseNombre']}"
            monto_total = float(costeo['CostoTotalProduccion'] or 0)
            
            cursor.execute("""
                INSERT INTO Tablajeria_PolizasContables (
                    PolizaID, OrdenID, TipoPoliza, NumeroPoliza,
                    FechaPoliza, Concepto, MontoTotal, UsuarioID
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                poliza_id, orden_id, TipoPoliza.PRODUCCION.value,
                numero_poliza, fecha_poliza, concepto, monto_total, usuario_id
            ))
            
            # Crear asientos
            asientos = []
            linea = 1
            
            # 1. Cargo: Almacén Productos Terminados
            costo_productos = float(costeo['CostoTotalProduccion'] or 0) - float(costeo.get('MermaRealKg') or 0) * 10  # Estimado merma
            asiento_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO Tablajeria_PolizasDetalle (
                    AsientoID, PolizaID, NumeroLinea,
                    CuentaContable, NombreCuenta, Concepto,
                    Debe, Haber, Referencia
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                asiento_id, poliza_id, linea,
                config.cuenta_almacen_productos, "Almacén Productos Terminados",
                f"Entrada producción {costeo['FolioOrden']}",
                costo_productos, 0, costeo['FolioOrden']
            ))
            asientos.append({
                "linea": linea, "cuenta": config.cuenta_almacen_productos,
                "debe": costo_productos, "haber": 0
            })
            linea += 1
            
            # 2. Cargo: Merma (si hay)
            if costeo.get('MermaRealKg') and float(costeo['MermaRealKg']) > 0:
                costo_merma = float(costeo['MermaRealKg']) * float(costeo['CostoUnitarioInsumo'] or 0)
                asiento_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO Tablajeria_PolizasDetalle (
                        AsientoID, PolizaID, NumeroLinea,
                        CuentaContable, NombreCuenta, Concepto,
                        Debe, Haber, Referencia
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    asiento_id, poliza_id, linea,
                    config.cuenta_merma_operativa, "Merma Operativa",
                    f"Merma tablaje {costeo['FolioOrden']}",
                    costo_merma, 0, costeo['FolioOrden']
                ))
                asientos.append({
                    "linea": linea, "cuenta": config.cuenta_merma_operativa,
                    "debe": costo_merma, "haber": 0
                })
                linea += 1
            
            # 3. Abono: Almacén Materia Prima
            asiento_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO Tablajeria_PolizasDetalle (
                    AsientoID, PolizaID, NumeroLinea,
                    CuentaContable, NombreCuenta, Concepto,
                    Debe, Haber, Referencia
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                asiento_id, poliza_id, linea,
                config.cuenta_almacen_insumos, "Almacén Materia Prima",
                f"Salida insumo {costeo['InsumoBaseNombre']}",
                0, monto_total, costeo['FolioOrden']
            ))
            asientos.append({
                "linea": linea, "cuenta": config.cuenta_almacen_insumos,
                "debe": 0, "haber": monto_total
            })
            
            conn.commit()
            
            logger.info(f"[FASE6] Póliza generada: {numero_poliza}")
            
            return {
                "poliza_id": poliza_id,
                "numero_poliza": numero_poliza,
                "tipo": TipoPoliza.PRODUCCION.value,
                "fecha": str(fecha_poliza),
                "concepto": concepto,
                "monto_total": monto_total,
                "asientos": asientos,
                "estatus": EstatusPoliza.PENDIENTE.value
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"[FASE6] Error generando póliza: {e}")
            raise
        finally:
            conn.close()
    
    # =========================================================================
    # PROCESO COMPLETO AL CERRAR ORDEN
    # =========================================================================
    
    def procesar_cierre_completo(
        self,
        orden_id: str,
        costo_unitario_insumo: Decimal,
        costos_adicionales: Dict[str, Decimal] = None,
        usuario_id: str = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el proceso completo de Fase 6 al cerrar una orden:
        1. Afectar inventarios
        2. Calcular costeo
        3. Generar póliza contable
        
        Returns:
            Dict con resumen de todo el proceso
        """
        resultado = {
            "orden_id": orden_id,
            "inventario": None,
            "costeo": None,
            "poliza": None,
            "errores": []
        }
        
        try:
            # 1. Afectar inventario
            try:
                resultado["inventario"] = self.afectar_inventario_orden(orden_id, usuario_id)
            except Exception as e:
                resultado["errores"].append(f"Error inventario: {str(e)}")
                logger.error(f"[FASE6] Error en inventario: {e}")
            
            # 2. Calcular costeo
            try:
                resultado["costeo"] = self.calcular_costeo_orden(
                    orden_id, costo_unitario_insumo, costos_adicionales, usuario_id
                )
            except Exception as e:
                resultado["errores"].append(f"Error costeo: {str(e)}")
                logger.error(f"[FASE6] Error en costeo: {e}")
            
            # 3. Generar póliza (solo si hay costeo)
            if resultado["costeo"]:
                try:
                    resultado["poliza"] = self.generar_poliza_produccion(orden_id, usuario_id)
                except Exception as e:
                    resultado["errores"].append(f"Error póliza: {str(e)}")
                    logger.error(f"[FASE6] Error en póliza: {e}")
            
            resultado["exito"] = len(resultado["errores"]) == 0
            
            logger.info(f"[FASE6] Proceso completo para orden {orden_id}: {'OK' if resultado['exito'] else 'CON ERRORES'}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"[FASE6] Error en proceso completo: {e}")
            resultado["errores"].append(str(e))
            resultado["exito"] = False
            return resultado


# Factory function
def get_tablajeria_fase6_service(db_config: Dict = None) -> TablajeriaFase6Service:
    """Obtiene instancia del servicio Fase 6."""
    return TablajeriaFase6Service(db_config)
