# backend/modules/edge/orquestador_kds_core.py

import sqlite3
import json
import time
from typing import Dict, List, Any

class OrquestadorKDSCore:
    def __init__(self, db_path: str = "edarsa_edge_device.db"):
        self.db_path = db_path
        self._inicializar_tablas_kds()

    def _inicializar_tablas_kds(self) -> None:
        """
        Crea las estructuras de memoria de trabajo de cocina en el nodo local.
        Mantiene el estatus de preparación por cada estación en frío.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Cola FIFO de tickets en producción por estación
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kds_produccion_estaciones (
                    id_ticket_linea TEXT PRIMARY KEY,
                    id_transaccion_global TEXT NOT NULL,
                    id_mesa TEXT NOT NULL,
                    unidad_negocio TEXT NOT NULL, -- BARRA, COCINA_PARRILLA, REPOSTERIA
                    id_producto TEXT NOT NULL,
                    nombre_producto TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    tiempo_coccion_minutos INTEGER NOT NULL,
                    timestamp_liberacion INTEGER NOT NULL, -- Conteo regresivo para sincronía
                    estado_produccion TEXT DEFAULT 'RETENIDO' -- RETENIDO, PREPARANDO, LISTO
                )
            ''')
            conn.commit()

    # ============================================================================
    # 1. BALANCEADOR DE CARGAS Y RUTEO INTELIGENTE POR ESTACIÓN
    # ============================================================================
    def procesar_y_rutear_comanda_a_kds(self, payload_comanda: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Intercepta el payload universal inmutable de la tablet. Analiza los tiempos
        de cocción y rutea cada ítem a su respectiva unidad de producción física.
        """
        tx = payload_comanda["registro_transaccion"]
        id_tx = tx["id_transaccion_global"]
        id_mesa = tx["id_mesa"]
        items = tx["items_comandados"]

        lineas_procesadas = []
        tiempo_maximo_mesa = 0
        
        # Primero: Consultar tiempos de cocción teóricos en el Edge Cache local
        items_con_tiempos = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            for item in items:
                cursor.execute('''
                    SELECT unidad_negocio, cantidad_requerida_base as minutos_coccion 
                    FROM hub_recetas_explosion 
                    WHERE id_producto = ? LIMIT 1
                ''', (item["id_producto"],))
                receta = cursor.fetchone()
                
                # Valores paramétricos por defecto si no hay receta explícita inyectada
                minutos = int(receta["minutos_coccion"]) if receta and receta["minutos_coccion"] else 3
                unidad = receta["unidad_negocio"] if receta else "COCINA_PARRILLA"
                
                if minutos > tiempo_maximo_mesa:
                    tiempo_maximo_mesa = minutos
                
                items_con_tiempos.append({
                    "item": item,
                    "unidad": unidad,
                    "minutos": minutos
                })

        # Segundo: Calcular retenciones para lograr la entrega al mismo tiempo (Sincronía)
        timestamp_actual = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for objeto in items_con_tiempos:
                item = objeto["item"]
                unidad = objeto["unidad"]
                minutos_coccion = objeto["minutos"]
                
                # El algoritmo retiene los platos rápidos (ej: ensaladas) retrasando su liberación
                minutos_retencion = tiempo_maximo_mesa - minutos_coccion
                timestamp_liberacion = timestamp_actual + (minutos_retencion * 60)
                
                id_linea = f"LINE-{id_tx[:8]}-{item['id_producto']}"
                estado_inicial = "PREPARANDO" if minutos_retencion == 0 else "RETENIDO"

                cursor.execute('''
                    INSERT INTO kds_produccion_estaciones (
                        id_ticket_linea, id_transaccion_global, id_mesa, unidad_negocio, 
                        id_producto, nombre_producto, cantidad, tiempo_coccion_minutos, 
                        timestamp_liberacion, estado_produccion
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id_ticket_linea) DO NOTHING
                ''', (id_linea, id_tx, id_mesa, unidad, item["id_producto"], 
                      item.get("nombre", "Producto"), item["cantidad"], minutos_coccion, 
                      timestamp_liberacion, estado_inicial))
                
                lineas_procesadas.append({
                    "id_linea": id_linea,
                    "estacion": unidad,
                    "estado": estado_inicial,
                    "liberacion_en_segundos": minutos_retencion * 60
                })
            
            conn.commit()
            
        return lineas_procesadas

    # ============================================================================
    # 2. EVENT LOOP DE COCINA: CONTROLADOR DE RETENCIONES EN CALIENTE
    # ============================================================================
    def actualizar_reloj_retenciones_kds(self) -> List[str]:
        """
        Ciclo de eventos en background del servidor de piso. Monitorea los platos
        retenidos y los libera automáticamente cuando se cumple el tiempo de espera.
        """
        timestamp_actual = int(time.time())
        lineas_liberadas = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Buscar platos cuya retención de tiempo ya expiró
            cursor.execute('''
                SELECT id_ticket_linea FROM kds_produccion_estaciones 
                WHERE estado_produccion = 'RETENIDO' AND timestamp_liberacion <= ?
            ''', (timestamp_actual,))
            
            filas = cursor.fetchall()
            for fila in filas:
                lineas_liberadas.append(fila["id_ticket_linea"])
                
            if lineas_liberadas:
                # Modificar estatus en lote limpio para visualización de pantallas de cocina
                cursor.execute(f'''
                    UPDATE kds_produccion_estaciones 
                    SET estado_produccion = 'PREPARANDO' 
                    WHERE id_ticket_linea IN ({','.join(['?']*len(lineas_liberadas))})
                ''', lineas_liberadas)
                conn.commit()

        return lineas_liberadas
