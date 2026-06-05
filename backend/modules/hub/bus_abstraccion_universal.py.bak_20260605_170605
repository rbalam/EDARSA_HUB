# backend/modules/hub/bus_abstraccion_universal.py

import json
import time
from typing import Dict, Any, List

class BusAbstraccionUniversal:
    def __init__(self):
        self.sistema_origen = "EDARSA_HUB_CORE"

    # ============================================================================
    # 4.1. ADAPTADOR CONTABLE: GENERADOR DE ASIENTOS PLANOS (SAP / ORACLE / ODOO)
    # ============================================================================
    def mapear_a_asiento_contable_erp(self, payload_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Toma un ticket financiero inmutable de la cola FIFO y lo traduce a una póliza
        contable de partida doble parametrizable para cualquier ERP financiero.
        """
        tx_data = payload_ticket["registro_transaccion"]
        totales = tx_data["totales_financieros"]
        cuentas = tx_data["mapeo_contable_erp"]
        
        asiento_universal = {
            "ERP_Header": {
                "UUID_Idempotencia": tx_data["id_transaccion_global"],
                "Fecha_Contable": time.strftime("%Y-%m-%d"),
                "Tipo_Documento": "POLIZA_INGRESO_POS",
                "Referencia_Origen": f"Mesa_{tx_data['id_mesa']}"
            },
            "Asiento_Detalle": [
                {
                    "Linea": 1,
                    "Cuenta_Contable": cuentas["cuenta_caja_bancos"],
                    "Tipo_Movimiento": "DEBITO",
                    "Monto": totales["gran_total"],
                    "Concepto": f"Cierre Mesa {tx_data['id_mesa']} - Vendedor {tx_data['vendedor_id']}"
                },
                {
                    "Linea": 2,
                    "Cuenta_Contable": cuentas["cuenta_ingresos"],
                    "Tipo_Movimiento": "CREDITO",
                    "Monto": totales["subtotal_neto"],
                    "Concepto": "Ingreso Neto Alimentos y Bebidas Aislado"
                },
                {
                    "Linea": 3,
                    "Cuenta_Contable": cuentas["cuenta_impuestos"],
                    "Tipo_Movimiento": "CREDITO",
                    "Monto": totales["total_iva"],
                    "Concepto": "IVA Trasladado Regular Cobrado"
                }
            ]
        }
        return asiento_universal

    # ============================================================================
    # 4.2. ADAPTADOR DE RECURSOS HUMANOS: EXPORTADOR DE NÓMINA Y COMISIONES
    # ============================================================================
    def mapear_a_recursos_humanos_nomina(self, payload_ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae las métricas de rendimiento y propinas acumuladas del vendedor para
        su dispersión directa en los sistemas corporativos de nómina.
        """
        tx_data = payload_ticket["registro_transaccion"]
        totales = tx_data["totales_financieros"]
        
        payload_rrhh = {
            "ID_Empleado": tx_data["vendedor_id"],
            "Evento_Turno": {
                "UUID_Transaccion": tx_data["id_transaccion_global"],
                "Monto_Propina_Acumulada": totales.get("propina_sugerida", 0.0),
                "Afecta_Ticket_Promedio": tx_data.get("segmentacion_kpi", {}).get("afecta_ticket_promedio_salon", 1),
                "Monto_Venta_Individual": totales.get("gran_total", 0.0),
                "Fecha_Registro": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }
        return payload_rrhh

    # ============================================================================
    # 4.3. ADAPTADOR CRM LEALTAD: PUNTUACIÓN Y SEGMENTACIÓN DE CLIENTE
    # ============================================================================
    def mapear_a_crm_lealtad(self, payload_ticket: Dict[str, Any], cliente_id: str = None) -> Dict[str, Any]:
        """
        Genera el payload de acumulación de puntos y segmentación para el CRM
        de lealtad basado en el comportamiento de consumo del cliente.
        """
        tx_data = payload_ticket["registro_transaccion"]
        totales = tx_data["totales_financieros"]
        
        payload_crm = {
            "ID_Cliente_CRM": cliente_id,
            "Evento_Consumo": {
                "UUID_Transaccion": tx_data["id_transaccion_global"],
                "Monto_Base_Puntos": totales.get("subtotal_neto", 0.0),
                "Puntos_Generados": int(totales.get("subtotal_neto", 0.0) / 10),  # 1 punto por cada $10
                "Fecha_Evento": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "Mesa_Origen": tx_data["id_mesa"]
            }
        }
        return payload_crm

    # ============================================================================
    # 4.4. DESPACHADOR CENTRALIZADO DE PAYLOADS A SISTEMAS EXTERNOS
    # ============================================================================
    def despachar_a_sistemas_destino(self, payload_ticket: Dict[str, Any]) -> Dict[str, bool]:
        """
        Orquesta la distribución del payload a todos los sistemas integrados.
        Retorna el estado de éxito de cada adaptador.
        """
        resultados = {
            "erp_contable": False,
            "rrhh_nomina": False,
            "crm_lealtad": False
        }
        
        try:
            asiento = self.mapear_a_asiento_contable_erp(payload_ticket)
            # Aquí se integraría con el endpoint real del ERP
            resultados["erp_contable"] = True
        except Exception as e:
            print(f"[BUS ERROR] ERP Contable: {e}")
        
        try:
            nomina = self.mapear_a_recursos_humanos_nomina(payload_ticket)
            # Aquí se integraría con el endpoint real de RRHH
            resultados["rrhh_nomina"] = True
        except Exception as e:
            print(f"[BUS ERROR] RRHH Nómina: {e}")
        
        try:
            crm = self.mapear_a_crm_lealtad(payload_ticket)
            # Aquí se integraría con el endpoint real del CRM
            resultados["crm_lealtad"] = True
        except Exception as e:
            print(f"[BUS ERROR] CRM Lealtad: {e}")
        
        return resultados
