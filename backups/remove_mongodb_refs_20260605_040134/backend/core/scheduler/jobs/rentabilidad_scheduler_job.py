from datetime import datetime
from core.pool import execute_hub_query
from modules.comercial.rentabilidad import evaluar_margen_pedido
from core.communications.dispatcher import dispatch_notification  # Despachador centralizado

def ejecutar_auditoria_rentabilidad_job():
    """
    COSTOS-ALERTAS-001-F: Job periódico del Scheduler.
    Escanea pedidos CRM pendientes de validación fiscal y audita sus márgenes
    utilizando el motor determinista local.
    """
    # 1. Consultar pedidos pendientes que no han sido validados o remisionados
    query_pedidos_pendientes = """
        SELECT PedidoID, FolioPedido, UsuarioCreadorID
        FROM dbo.Venta_Pedidos
        WHERE Estatus = 'Pendiente_Aprobacion' OR Estatus = 'Nuevo'
    """
    pedidos = execute_hub_query(query_pedidos_pendientes, ())
    
    if not pedidos:
        return {"status": "SUCCESS", "mensaje": "No se encontraron pedidos pendientes para auditar."}

    pedidos_auditados = 0
    alertas_disparadas = 0

    # 2. Iterar y procesar cada pedido a través del motor blindado de rentabilidad
    for ped in pedidos:
        pedido_id = ped["PedidoID"]
        folio = ped["FolioPedido"]
        
        try:
            # Evaluar margen con un umbral estricto del 15.0%
            analisis = evaluar_margen_pedido(pedido_id=pedido_id, umbral_minimo_margen=15.0)
            pedidos_auditados += 1

            # 3. Si el motor determina que requiere aprobación por bajo margen, disparar alerta
            if analisis["RequiereAprobacionDireccion"]:
                alertas_disparadas += 1
                
                # Estructurar la carga de notificación para el despachador central
                payload_alerta = {
                    "tipo": "ALERTA_RENTABILIDAD_COSTOS",
                    "pedido_id": pedido_id,
                    "folio": folio,
                    "margen_global": analisis["MargenGlobal"],
                    "utilidad_bruta": analisis["UtilidadBruta"],
                    "productos_afectados": len(analisis["ProductosEnAlerta"]),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Despachar notificación asíncrona/síncrona local (Email/Slack/WhatsApp según config)
                dispatch_notification(
                    topic="comercial.alertas.costos",
                    payload=payload_alerta,
                    priority="HIGH"
                )
                
                # Registrar el estatus de alerta en el historial del pedido para auditoría interna
                query_log_alerta = """
                    INSERT INTO dbo.CRM_OportunidadesHistorial (OportunidadID, EtapaAnteriorID, EtapaNuevaID, MontoAnterior, MontoNuevo, UsuarioModificadorID, Comentario)
                    VALUES (NULL, 0, 0, %s, %s, %s, %s)
                """
                # Nota: Adaptado a la estructura UNIQUEIDENTIFIER/Estructura de la Fase 6 si aplica
                # Se pasa un comentario directo para la bitácora de auditoría
                comentario_auditoria = f"Alerta COSTOS-001: Margen global caído al {analisis['MargenGlobal']}%."
                execute_hub_query(query_log_alerta, (analisis["TotalVenta"], analisis["UtilidadBruta"], ped["UsuarioCreadorID"], comentario_auditoria))

        except Exception as e:
            # Log de contingencia si un pedido específico falla en el parseo
            continue

    return {
        "status": "SUCCESS",
        "pedidos_procesados": pedidos_auditados,
        "alertas_emitidas": alertas_disparadas
    }
