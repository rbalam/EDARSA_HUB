# backend/modules/hub/modulo_financiero_proyectos.py

import sqlite3
import json
import time
from typing import Dict, Any, List

class ModuloFinancieroProyectos:
    def __init__(self, db_path: str = "edarsa_edge_device.db"):
        self.db_path = db_path
        self._configurar_tablas_proyectos()

    def _configurar_tablas_proyectos(self) -> None:
        """
        Inicializa las estructuras de base de datos para la contabilidad aislada
        de eventos especiales (Centros de Costo de Proyecto - CCP).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Catálogo de Proyectos / Eventos Especiales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS centros_costo_proyecto (
                    id_proyecto TEXT PRIMARY KEY,
                    nombre_evento TEXT NOT NULL,
                    cliente_crm_id TEXT NOT NULL,
                    pax_pactados INTEGER NOT NULL,
                    presupuesto_ingreso REAL NOT NULL,
                    estado TEXT DEFAULT 'ACTIVO' -- ACTIVO, LIQUIDADO, CERRADO
                )
            ''')
            # Transacciones financieras vinculadas al proyecto (Ingresos, Compras, Gastos)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transacciones_proyecto (
                    id_movimiento TEXT PRIMARY KEY,
                    id_proyecto TEXT,
                    tipo_flujo TEXT NOT NULL, -- INGRESO_ANTICIPO, COMPRA_INSUMO, GASTO_OPERATIVO
                    descripcion TEXT NOT NULL,
                    monto_neto REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(id_proyecto) REFERENCES centros_costo_proyecto(id_proyecto)
                )
            ''')
            conn.commit()

    # ============================================================================
    # INYECCIÓN DE FLUJOS (COMPRAS, GASTOS E INGRESOS)
    # ============================================================================
    def registrar_movimiento_proyecto(self, id_proyecto: str, tipo_flujo: str, descripcion: str, monto: float) -> None:
        """
        Asigna de forma inmutable cada peso gastado o recibido directamente al proyecto,
        protegiendo las métricas del restaurante diario de cualquier distorsión.
        """
        id_movimiento = f"MOV-{int(time.time())}-{descripcion[:4].upper()}"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transacciones_proyecto (id_movimiento, id_proyecto, tipo_flujo, descripcion, monto_neto, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (id_movimiento, id_proyecto, tipo_flujo, descripcion, monto, time.strftime("%Y-%m-%dT%H:%M:%SZ")))
            conn.commit()

    # ============================================================================
    # MOTOR DE RENTABILIDAD REAL (P&L POR EVENTO)
    # ============================================================================
    def calcular_pnl_evento_puro(self, id_proyecto: str) -> Dict[str, Any]:
        """
        Calcula de forma matemática el costeo real, utilidad o pérdida del evento,
        junto con el desglose exacto para el tablero corporativo.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 1. Obtener datos base del proyecto (CRM)
            cursor.execute("SELECT * FROM centros_costo_proyecto WHERE id_proyecto = ?", (id_proyecto,))
            proyecto = cursor.fetchone()
            if not proyecto:
                return {"error": "El Centro de Costo de Proyecto no existe."}

            # 2. Totalizar los flujos financieros
            cursor.execute("SELECT tipo_flujo, SUM(monto_neto) as total FROM transacciones_proyecto WHERE id_proyecto = ? GROUP BY tipo_flujo", (id_proyecto,))
            movimientos = cursor.fetchall()
            
            totales = {"INGRESO_ANTICIPO": 0.0, "COMPRA_INSUMO": 0.0, "GASTO_OPERATIVO": 0.0}
            for mov in movimientos:
                totales[mov["tipo_flujo"]] = mov["total"]

        # Cálculos de rentabilidad puros
        ingresos_totales = totales["INGRESO_ANTICIPO"]
        costos_totales = totales["COMPRA_INSUMO"] + totales["GASTO_OPERATIVO"]
        utilidad_neta = ingresos_totales - costos_totales
        
        # Margen de utilidad porcentual
        margen_utilidad_porcentaje = (utilidad_neta / ingresos_totales * 100) if ingresos_totales > 0 else 0.0
        costo_por_pax_real = (costos_totales / proyecto["pax_pactados"]) if proyecto["pax_pactados"] > 0 else 0.0

        return {
            "id_proyecto": id_proyecto,
            "nombre_evento": proyecto["nombre_evento"],
            "kpis_pax": {
                "pax_pactados": proyecto["pax_pactados"],
                "costo_real_por_pax": round(costo_por_pax_real, 2)
            },
            "balance_financiero": {
                "ingresos_reconocidos": ingresos_totales,
                "costo_compras_insumos": totales["COMPRA_INSUMO"],
                "gasto_operativo_directo": totales["GASTO_OPERATIVO"],
                "costo_total_acumulado": costos_totales
            },
            "resultado_operacional": {
                "utilidad_o_perdida_neta": round(utilidad_neta, 2),
                "margen_utilidad_porcentaje": round(margen_utilidad_porcentaje, 2),
                "rentable": utilidad_neta > 0
            }
        }
