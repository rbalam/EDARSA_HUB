# backend/modules/edge/sincronizador_catalogos_edge.py

import sqlite3
import httpx
import json
from typing import Dict, List, Any

class SincronizadorCatalogosEdge:
    def __init__(self, local_db_path: str = "edarsa_edge_device.db", hub_url: str = "http://api.edarashub.internal"):
        self.local_db_path = local_db_path
        self.hub_url = hub_url

    # ============================================================================
    # 1. SINCRONIZACIÓN DE PERSONAL Y MATRIZ DE ROLES (ERP ENTERPRISE)
    # ============================================================================
    async def jalar_y_actualizar_personal_local(self) -> bool:
        """
        Descarga la nómina activa y la matriz de permisos contables desde el Hub central.
        Reescribe la caché local para validar accesos y huellas digitales de meseros.
        """
        # Creación preventiva de tablas de personal en el Edge Cache
        with sqlite3.connect(self.local_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS local_personal_roles (
                    id_empleado TEXT PRIMARY KEY,
                    nombre_completo TEXT NOT NULL,
                    id_rol TEXT NOT NULL,
                    permite_cancelar INTEGER DEFAULT 0,
                    softrestaurant_user_id TEXT
                )
            ''')
            conn.commit()

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.hub_url}/v1/catalogos/personal-roles")
                if response.status_code != 200:
                    return False
                
                datos_personal = response.json().get("personal", [])
                
                # Volcado masivo atómico en la terminal móvil
                with sqlite3.connect(self.local_db_path) as conn:
                    cursor = conn.cursor()
                    for emp in datos_personal:
                        cursor.execute('''
                            INSERT INTO local_personal_roles (id_empleado, nombre_completo, id_rol, permite_cancelar, softrestaurant_user_id)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(id_empleado) DO UPDATE SET
                                nombre_completo=excluded.nombre_completo,
                                id_rol=excluded.id_rol,
                                permite_cancelar=excluded.permite_cancelar
                        ''', (emp["id_empleado"], emp["nombre_completo"], emp["id_rol"], emp["permite_cancelar"], emp.get("softrestaurant_user_id")))
                    conn.commit()
            return True
        except Exception:
            return False # Red inestable: la terminal retiene y trabaja con la nómina del turno previo

    # ============================================================================
    # 2. SINCRONIZACIÓN ELÁSTICA DE LA CARTA Y RECETAS (SOFT RESTAURANT / MOPRO)
    # ============================================================================
    async def jalar_y_actualizar_carta_elastica_local(self) -> bool:
        """
        Absorbe la estructura de venta de Soft Restaurant fusionada con las reglas
        de criticidad e ingredientes de Mopro, poblando la tabla catalogo_menu.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.hub_url}/v1/catalogos/carta-recetas")
                if response.status_code != 200:
                    return False
                
                paquete_carta = response.json().get("productos", [])

                with sqlite3.connect(self.local_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Limpieza y actualización limpia para evitar desfasamientos de códigos
                    for prod in paquete_carta:
                        # Actualizar tabla de productos del comandero (Paso 1)
                        cursor.execute('''
                            INSERT INTO catalogo_menu (
                                id_producto, nombre, unidad_negocio, precio_final, precio_neto, 
                                impuesto_iva, categoria_push, stock_local, stock_critico, softrestaurant_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id_producto) DO UPDATE SET
                                nombre=excluded.nombre,
                                precio_final=excluded.precio_final,
                                categoria_push=excluded.categoria_push
                        ''', (prod["id_producto"], prod["nombre_comercial"], prod["unidad_negocio"],
                              prod["precio_publico"], prod["precio_publico"] / 1.16, prod["precio_publico"] - (prod["precio_publico"] / 1.16),
                              prod["categoria_push"], prod.get("stock_actual_mopro", 99), 5, prod.get("softrestaurant_product_id")))

                        # Actualizar la tabla puente de recetas elásticas (Paso 2)
                        for insumo in prod.get("receta", []):
                            cursor.execute('''
                                INSERT INTO receta_insumos_elasticos (id_producto, id_insumo, nombre_insumo, tipo_insumo, cantidad_requerida)
                                VALUES (?, ?, ?, ?, ?)
                                ON CONFLICT(id_producto, id_insumo) DO UPDATE SET
                                    tipo_insumo=excluded.tipo_insumo,
                                    cantidad_requerida=excluded.cantidad_requerida
                            ''', (prod["id_producto"], insumo["id_insumo"], insumo["nombre_insumo"], 
                                  "CRITICO" if insumo["es_critico"] == 1 else "FLEXIBLE", insumo["cantidad_requerida_base"]))
                    
                    conn.commit()
            return True
        except Exception:
            return False
