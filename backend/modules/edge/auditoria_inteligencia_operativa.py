# backend/modules/edge/auditoria_inteligencia_operativa.py

import sqlite3
import json
import time
from typing import Dict, List, Any

class AuditoriaInteligenciaOperativa:
    def __init__(self, db_path: str = "edarsa_edge_device.db"):
        self.db_path = db_path

    # ============================================================================
    # 6.2. EL KDS VIDENTE: PREDICCIÓN DE DEMANDA EN PARRILLA / COCINA
    # ============================================================================
    def ejecutar_kds_vidente_predictivo(self, ocupacion_mesas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Monitorea la velocidad de ocupación del plano Live 3D y los perfiles CRM 
        para emitir alertas de producción a las estaciones antes de capturar el ticket.
        """
        conteo_perfil_premium = 0
        for mesa in ocupacion_mesas:
            if mesa.get("perfil_cliente") == "cortes_premium" and mesa.get("estado") == "VERDE":
                conteo_perfil_premium += 1

        alerta_kds = {
            "emitir_alerta_estacion": False,
            "estacion_destino": "cocina_parrilla",
            "mensaje_produccion": ""
        }

        # Regla predictiva: Alta concentración de clientes de cortes en tiempo corto
        if conteo_perfil_premium >= 3:
            alerta_kds.update({
                "emitir_alerta_estacion": True,
                "mensaje_produccion": "Se proyecta demanda alta de Tomahawk en los próximos 15 minutos. Sugerencia: Preparar estación de sellado."
            })
        
        return alerta_kds

    # ============================================================================
    # 6.3. CONTROL DE MERMA ACTIVO: REAJUSTE DINÁMICO DE SUB-RECETAS
    # ============================================================================
    def reajustar_receta_por_merma_critica(self, id_producto: str) -> Dict[str, Any]:
        """
        Si un insumo de alta rotación desciende más rápido de lo presupuestado, 
        modifica la sub-receta local para sugerir sustitutos y recalcular márgenes.
        """
        query = "SELECT stock_local, stock_critico, precio_final FROM catalogo_menu WHERE id_producto = ?"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, (id_producto,))
            producto = cursor.fetchone()

        resultado_reajuste = {"receta_modificada": False, "nuevo_precio_sugerido": 0.0}

        if producto and producto["stock_local"] <= producto["stock_critico"]:
            # Simulación de sustitución inteligente de insumo perecedero en la sub-receta
            nuevo_precio = producto["precio_final"] * 1.05 # Incremento paramétrico por escasez
            resultado_reajuste.update({
                "receta_modificada": True,
                "nuevo_precio_sugerido": round(nuevo_precio, 2),
                "instruccion_chef": "Insumo principal crítico. Utilizar alternativa homologada en rendimiento de EdarasHub."
            })
        
        return resultado_reajuste

    # ============================================================================
    # 6.4. AUDITORÍA DE FUGAS SILENCIOSAS: VALIDACIÓN CONTRA COLA FIFO
    # ============================================================================
    def auditar_entrega_fisica_vs_comanda(self, id_mesa: str, items_detectados_camara: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Contrasta los platos físicos salientes (visión computacional) contra las comandas 
        registradas en la cola FIFO local para aislar mermas o fraudes en tiempo real.
        """
        # Extraer el último ticket activo de la mesa en la base de datos local
        query = "SELECT payload_json FROM cola_sincronizacion_offline WHERE estado = 'PENDING_SYNC' ORDER BY creado_at DESC LIMIT 1"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()

        auditoria_status = {"discrepancia_detectada": False, "estado_auditoria": "OK"}

        if row:
            payload = json.loads(row["payload_json"])
            items_comandados = payload["registro_transaccion"]["items_comandados"]
            
            # Comparación de volúmenes de entrega física vs registros capturados
            for item_camara in items_detectados_camara:
                match = next((i for i in items_comandados if i["id_producto"] == item_camara["id_producto"]), None)
                
                if not match or match["cantidad"] < item_camara["cantidad"]:
                    auditoria_status.update({
                        "discrepancia_detectada": True,
                        "estado_auditoria": "FLAGGED_DISCREPANCY",
                        "detalles": f"Fuga silenciosa detectada en Mesa {id_mesa}. Ítem saliente no registrado en comanda FIFO."
                    })
                    break

        return auditoria_status
