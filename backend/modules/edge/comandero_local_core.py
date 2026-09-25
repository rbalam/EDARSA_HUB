from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
import sqlite3
import json
import uuid
import time
from typing import Dict, List, Any, Optional

class ComanderoLocalCore:
    def __init__(self, db_path: str = "edarsa_edge_device.db"):
        self.db_path = db_path
        self._inicializar_base_datos_local()

    def _inicializar_base_datos_local(self) -> None:
        """
        Crea de forma inmutable la réplica local de lectura (Edge Cache) de EdarasHub
        y la cola de persistencia offline. Cero duplicación de tablas.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Réplica Local del Catálogo (Sincronizada en background desde EdarasHub)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS catalogo_menu (
                    id_producto TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    unidad_negocio TEXT NOT NULL, -- barra, cocina_parrilla, cocina_frios, reposteria
                    precio_final REAL NOT NULL,
                    precio_neto REAL NOT NULL,
                    impuesto_iva REAL NOT NULL,
                    categoria_push TEXT DEFAULT 'ninguna', -- baja_rotacion, temporada, causa_altruista
                    stock_local INTEGER NOT NULL,
                    stock_critico INTEGER NOT NULL,
                    sap_material_id TEXT,
                    softrestaurant_id TEXT,
                    odoo_product_id TEXT,
                    mopro_id TEXT
                )
            ''')
            
            # 2. Relación de Maridajes Ínclitos Unificada
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maridajes_menu (
                    id_producto_origen TEXT,
                    id_producto_sugerido TEXT,
                    prioridad_margen INTEGER DEFAULT 1,
                    argumento_pantalla TEXT,
                    PRIMARY KEY (id_producto_origen, id_producto_sugerido),
                    FOREIGN KEY(id_producto_origen) REFERENCES catalogo_menu(id_producto)
                )
            ''')
            
            # 3. Cola FIFO Inmutable de Persistencia Offline (El Escudo Resiliente)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cola_sincronizacion_offline (
                    uuid_transaccion TEXT PRIMARY KEY,
                    estado TEXT DEFAULT 'PENDING_SYNC', -- PENDING_SYNC, SYNCED
                    payload_json TEXT NOT NULL,
                    creado_at INTEGER NOT NULL
                )
            ''')
            conn.commit()

    # ============================================================================
    # OPERACIONES CRUD EN EDGE CACHE (Independencia de Red)
    # ============================================================================

    def edge_sincronizar_producto(self, prod: Dict[str, Any]) -> None:
        """
        Inserta o actualiza la carta nativa en la base de datos local.
        Mantiene los mapeos listos para migración a cualquier ERP.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO catalogo_menu (
                    id_producto, nombre, unidad_negocio, precio_final, precio_neto, 
                    impuesto_iva, categoria_push, stock_local, stock_critico, 
                    sap_material_id, softrestaurant_id, odoo_product_id, mopro_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_producto) DO UPDATE SET
                    nombre=excluded.nombre,
                    precio_final=excluded.precio_final,
                    precio_neto=excluded.precio_neto,
                    impuesto_iva=excluded.impuesto_iva,
                    stock_local=excluded.stock_local,
                    categoria_push=excluded.categoria_push
            ''', (prod['id_producto'], prod['nombre'], prod['unidad_negocio'], prod['precio_final'],
                  prod['precio_neto'], prod['impuesto_iva'], prod['categoria_push'], 
                  prod['stock_local'], prod['stock_critico'], prod.get('sap_id'), 
                  prod.get('soft_id'), prod.get('odoo_id'), prod.get('mopro_id')))
            conn.commit()

    def edge_dar_de_baja_producto(self, id_producto: str) -> None:
        """
        Inactiva o elimina un elemento del menú de forma local inmediata.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM catalogo_menu WHERE id_producto = ?", (id_producto,))
            cursor.execute("DELETE FROM maridajes_menu WHERE id_producto_origen = ?", (id_producto,))
            conn.commit()

    # ============================================================================
    # MOTOR TRANSACCIONAL OFFLINE (Cola FIFO con Idempotencia)
    # ============================================================================

    def registrar_comanda_offline(self, 
                                  mesa_id: str, 
                                  empleado_id: str, 
                                  tipo_comensal: str, 
                                  items: List[Dict], 
                                  totales: Dict, 
                                  contabilidad: Dict,
                                  rrr_attribution: Optional[Dict[str, Any]] = None) -> str:
        """
        Escribe la transacción directamente en el almacenamiento físico local.
        Asigna un UUID global inmutable para asegurar la idempotencia.
        """
        id_transaccion_global = str(uuid.uuid4())
        
        attribution = dict(rrr_attribution or {})
        attribution["source_transaction_uuid"] = id_transaccion_global

        payload_local = {
            "rrr_attribution": attribution,
            "offline_payload_control": {
                "sync_status": "PENDING_SYNC",
                "offline_interception_time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dispositivo_origen_id": "POS-MOBILE-EDGE-01"
            },
            "registro_transaccion": {
                "id_transaccion_global": id_transaccion_global,
                "id_mesa": mesa_id,
                "vendedor_id": empleado_id,
                "segmentacion_kpi": {
                    "tipo_comensal": tipo_comensal, # PUBLICO, SOCIO_CAVA, INVERSIONISTA, PERSONAL
                    "afecta_ticket_promedio_salon": 1 if tipo_comensal == "PUBLICO" else 0
                },
                "items_comandados": items,
                "totales_financieros": totales,
                "mapeo_contable_erp": contabilidad
            }
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Deducción automática del stock físico local por receta base
            for item in items:
                cursor.execute('''
                    UPDATE catalogo_menu 
                    SET stock_local = stock_local - ? 
                    WHERE id_producto = ?
                ''', (item['cantidad'], item['id_producto']))
            
            # Inyección inmutable en la cola FIFO local
            cursor.execute('''
                INSERT INTO cola_sincronizacion_offline (uuid_transaccion, payload_json, creado_at)
                VALUES (?, ?, ?)
            ''', (id_transaccion_global, json.dumps(payload_local), int(time.time())))
            
            conn.commit()
            
        return id_transaccion_global

    def despachar_cola_fifo_reconciliacion(self) -> List[Dict[str, Any]]:
        """
        Extrae las transacciones pendientes en orden cronológico estricto (FIFO).
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT payload_json FROM cola_sincronizacion_offline WHERE estado = 'PENDING_SYNC' ORDER BY creado_at ASC")
            return [json.loads(row['payload_json']) for row in cursor.fetchall()]

    def marcar_transaccion_sincronizada(self, uuid_transaccion: str) -> None:
        """
        Modifica el estado local tras recibir el visto bueno idempotente de EdarasHub.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cola_sincronizacion_offline SET estado = 'SYNCED' WHERE uuid_transaccion = ?", (uuid_transaccion,))
            conn.commit()
