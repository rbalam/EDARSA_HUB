# backend/modules/edge/motor_inventario_parametrico.py

import sqlite3
import json
from typing import Dict, Any, List

class MotorInventarioParametrico:
    def __init__(self, db_path: str = "edarsa_edge_device.db"):
        self.db_path = db_path
        self._inicializar_tabla_configuracion_cliente()

    def _inicializar_tabla_configuracion_cliente(self) -> None:
        """
        Crea la tabla que almacena las preferencias operativas del cliente
        por cada unidad de negocio. El cliente manda sobre el sistema.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracion_inventario_unidad (
                    unidad_negocio TEXT PRIMARY KEY, -- barra, cocina_parrilla, etc.
                    control_inventario_activo INTEGER DEFAULT 0, -- 0 = Falso (Venta Libre), 1 = Verdadero
                    permitir_negativos_criticos INTEGER DEFAULT 1, -- 1 = Permitir vender sin stock cargado
                    permitir_negativos_flexibles INTEGER DEFAULT 1
                )
            ''')
            conn.commit()

    # ============================================================================
    # EVALUADOR DE FLUJO OPERATIVO PARAMETRIZABLE
    # ============================================================================
    def evaluar_permiso_venta_tablet(self, id_producto: str, unidad_negocio: str) -> Dict[str, Any]:
        """
        Interroga primero la preferencia del cliente. Si el control de inventario
        está apagado para esa unidad, autoriza la venta en milisegundos sin mirar stock.
        """
        # 1. Leer los interruptores (Flags) de la unidad de negocio
        query_config = "SELECT * FROM configuracion_inventario_unidad WHERE unidad_negocio = ?"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query_config, (unidad_negocio,))
            config = cursor.fetchone()

        # Si el cliente no ha configurado nada o la unidad está en VENTA LIBRE por defecto:
        if not config or config["control_inventario_activo"] == 0:
            return {
                "permitir_venta": True,
                "estado_ui": "DISPONIBLE_VENTA_LIBRE",
                "motivo": f"Unidad {unidad_negocio} configurada en modo libre: Comandar y Cobrar."
            }

        # 2. Si el inventario SÍ está activo, evaluar los insumos de la receta
        query_receta = '''
            SELECT r.tipo_insumo, c.stock_local, r.nombre_insumo
            FROM receta_insumos_elasticos r
            JOIN catalogo_menu c ON r.id_insumo = c.id_producto
            WHERE r.id_producto = ?
        '''
        with sqlite3.connect(self.db_path) as conn:
            cursor.execute(query_receta, (id_producto,))
            insumos = cursor.fetchall()

        permitir_venta = True
        motivo_estado = "Stock Óptimo"
        estado_ui = "DISPONIBLE"

        for insumo in insumos:
            if insumo["stock_local"] <= 0:
                if insumo["tipo_insumo"] == "CRITICO":
                    # Si el ingrediente es crítico pero el cliente configuró permitir negativos críticos:
                    if config["permitir_negativos_criticos"] == 1:
                        estado_ui = "DISPONIBLE_NEGATIVO"
                        motivo_estado = f"Venta permitida en negativo para insumo crítico: {insumo['nombre_insumo']}"
                    else:
                        permitir_venta = False
                        motivo_estado = f"Bloqueado por quiebre de insumo crítico: {insumo['nombre_insumo']}"
                        estado_ui = "BLOQUEADO"
                        break
                else:
                    # Insumo flexible agotado (sal, condimento)
                    if config["permitir_negativos_flexibles"] == 1:
                        estado_ui = "DISPONIBLE_NEGATIVO"
                        motivo_estado = f"Insumo flexible en negativo: {insumo['nombre_insumo']}"
                    else:
                        permitir_venta = False
                        motivo_estado = f"Bloqueado por insumo flexible: {insumo['nombre_insumo']}"
                        estado_ui = "BLOQUEADO"
                        break

        return {
            "permitir_venta": permitir_venta,
            "estado_ui": estado_ui,
            "motivo": motivo_estado
        }
