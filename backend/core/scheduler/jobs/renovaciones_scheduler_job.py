from datetime import datetime, timedelta
from core.pool import execute_hub_query
from core.communications.dispatcher import dispatch_notification

def ejecutar_escaneo_renovaciones_job(dias_anticipacion: int = 30):
    """
    COSTOS-ALERTAS-001-G: Job automático para el Workflow de Renovaciones.
    Busca contratos o servicios comerciales recurrentes en el CRM próximos
    a vencer y despacha alertas preventivas de retención de forma local.
    """
    # 1. Calcular la fecha objetivo de vencimiento en base a los días de anticipación
    fecha_limite = (datetime.now() + timedelta(days=dias_anticipacion)).strftime('%Y-%m-%d %H:%M:%S')

    # 2. Consultar servicios o contratos próximos a vencer en el maestro transaccional
    # Se asume la estructura canónica de la cuenta comercial ligada a sus contratos
    query_vencimientos = """
        SELECT ContratoID, CuentaID, FolioContrato, FechaVencimiento, MontoRecurrente, UsuarioAsignadoID
        FROM dbo.CRM_Contratos
        WHERE Estatus = 'Activo' AND FechaVencimiento <= %s AND FechaVencimiento >= GETDATE()
    """
    contratos_por_vencer = execute_hub_query(query_vencimientos, (fecha_limite,))

    if not contratos_por_vencer:
        return {"status": "SUCCESS", "mensaje": "No se encontraron renovaciones críticas en el rango establecido."}

    alertas_enviadas = 0

    # 3. Iterar y procesar cada registro enviando la carga al despachador central
    for contrato in contratos_por_vencer:
        contrato_id = contrato["ContratoID"]
        folio = contrato["FolioContrato"]
        
        payload_renovacion = {
            "tipo": "ALERTA_RENOVACION_POSTVENTA",
            "contrato_id": contrato_id,
            "folio_contrato": folio,
            "monto_recurrente": float(contrato["MontoRecurrente"]),
            "fecha_vencimiento": str(contrato["FechaVencimiento"]),
            "dias_restantes": dias_anticipacion,
            "timestamp": datetime.now().isoformat()
        }

        # Despachar notificación asíncrona local (Email/Slack Corporativo)
        dispatch_notification(
            topic="comercial.alertas.renovaciones",
            payload=payload_renovacion,
            priority="MEDIUM"
        )
        alertas_enviadas += 1

        # Registrar la traza en la bitácora de auditoría transaccional de actividades (Fase 7)
        query_log_actividad = """
            INSERT INTO dbo.CRM_Actividades (CuentaID, TipoActividad, Asunto, NotasInteraccion, Estatus, UsuarioAsignadoID, FechaProgramada)
            VALUES (%s, 'Sistema', %s, %s, 'Completada', %s, GETDATE())
        """
        asunto_log = f"Alerta Automática: Renovación de Contrato {folio}"
        notas_log = f"El sistema generó una alerta preventiva. El contrato vence el {contrato['FechaVencimiento']}."
        execute_hub_query(query_log_actividad, (contrato["CuentaID"], asunto_log, notas_log, contrato["UsuarioAsignadoID"]))

    return {
        "status": "SUCCESS",
        "contratos_analizados": len(contratos_por_vencer),
        "alertas_despachadas": alertas_enviadas
    }
