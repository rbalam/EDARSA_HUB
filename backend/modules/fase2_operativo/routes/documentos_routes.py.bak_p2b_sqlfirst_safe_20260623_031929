from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Rutas de Documentos - API para generación de documentos.
CAB-003 | EDARSA HUB - Fase 2B.2 / 2B.3
PROTEGIDO CON RBAC (Fase 3.1)

Endpoints para generar y descargar documentos (Excel, PDF).
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Dict, Any
import logging

from ..db_utils import get_database
from ..services.excel_service import get_excel_service
from ..services.pdf_service import get_pdf_service
from ..services.document_data_service import (
    get_document_data_service,
    WorkflowNoEncontradoError
)

# RBAC - Fase 3.1
from core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documentos", tags=["Documentos"])


@router.get("/workflow/{workflow_id}/excel")
async def descargar_excel_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Genera y descarga el reporte Excel de un workflow.
    
    El archivo contiene 4 hojas:
    - Resumen: Información ejecutiva
    - Diferencias: Detalle de diferencias de inventario
    - Justificaciones: Registro de justificaciones
    - Auditoria: Historial de decisiones
    
    Args:
        workflow_id: ID del workflow
        
    Returns:
        StreamingResponse con el archivo Excel
        
    Raises:
        404: Workflow no encontrado
        500: Error al generar el documento
    """
    try:
        db = get_database()
        excel_service = get_excel_service(db)
        
        # Generar Excel
        excel_buffer = await excel_service.generar_excel_workflow(workflow_id)
        
        # Crear nombre de archivo
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_{workflow_id}_{timestamp}.xlsx"
        
        logger.info(f"Excel generado: {filename}")
        
        # Registrar en colección documentos_generados
        try:
            db.documentos_generados.insert_one({
                "workflow_id": workflow_id,
                "tipo_documento": "EXCEL",
                "nombre_archivo": filename,
                "fecha_generacion": datetime.now(timezone.utc).isoformat(),
                "generado_por": "sistema"  # En el futuro: usuario autenticado
            })
        except Exception as e:
            # No bloquear si falla el log
            logger.warning(f"Error al registrar documento: {e}")
        
        # Devolver como descarga
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except WorkflowNoEncontradoError as e:
        logger.warning(f"Workflow no encontrado: {workflow_id}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error al generar Excel: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al generar documento: {str(e)}"
        )


@router.get("/workflow/{workflow_id}/pdf")
async def descargar_pdf_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Genera y descarga el resumen ejecutivo en PDF de un workflow.
    
    El PDF incluye:
    - Información general del workflow
    - Métricas clave
    - Diferencias relevantes (top 10)
    - Estado de auditoría
    
    Para el detalle completo, use el endpoint de Excel.
    
    Args:
        workflow_id: ID del workflow
        
    Returns:
        StreamingResponse con el archivo PDF
        
    Raises:
        404: Workflow no encontrado
        500: Error al generar el documento
    """
    try:
        db = get_database()
        pdf_service = get_pdf_service(db)
        
        # Generar PDF
        pdf_buffer = await pdf_service.generar_pdf_workflow(workflow_id)
        
        # Crear nombre de archivo
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"resumen_workflow_{workflow_id}_{timestamp}.pdf"
        
        logger.info(f"PDF generado: {filename}")
        
        # Registrar en colección documentos_generados
        try:
            db.documentos_generados.insert_one({
                "workflow_id": workflow_id,
                "tipo_documento": "PDF",
                "nombre_archivo": filename,
                "fecha_generacion": datetime.now(timezone.utc).isoformat(),
                "generado_por": "sistema"
            })
        except Exception as e:
            # No bloquear si falla el log
            logger.warning(f"Error al registrar documento PDF: {e}")
        
        # Devolver como descarga
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except WorkflowNoEncontradoError as e:
        logger.warning(f"Workflow no encontrado para PDF: {workflow_id}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error al generar PDF: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al generar documento PDF: {str(e)}"
        )


@router.get("/workflow/{workflow_id}/datos")
async def obtener_datos_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene los datos completos de un workflow para documentos.
    
    Útil para previsualizar antes de descargar o para debugging.
    
    Args:
        workflow_id: ID del workflow
        
    Returns:
        Datos completos del workflow
        
    Raises:
        404: Workflow no encontrado
    """
    try:
        db = get_database()
        data_service = get_document_data_service(db)
        
        datos = await data_service.obtener_datos_completos_workflow(workflow_id)
        
        return {
            "success": True,
            "data": datos
        }
        
    except WorkflowNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error al obtener datos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener datos: {str(e)}"
        )


@router.get("/workflow/{workflow_id}/resumen")
async def obtener_resumen_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene un resumen rápido del workflow.
    
    Args:
        workflow_id: ID del workflow
        
    Returns:
        Resumen básico del workflow
    """
    try:
        db = get_database()
        data_service = get_document_data_service(db)
        
        resumen = await data_service.obtener_resumen_rapido(workflow_id)
        
        return {
            "success": True,
            "data": resumen
        }
        
    except WorkflowNoEncontradoError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error al obtener resumen: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener resumen: {str(e)}"
        )


@router.get("/historial")
async def obtener_historial_documentos(
    workflow_id: str = None,
    tipo: str = None,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene el historial de documentos generados.
    
    Args:
        workflow_id: Filtrar por workflow (opcional)
        tipo: Filtrar por tipo de documento (opcional)
        limit: Límite de resultados
        
    Returns:
        Lista de documentos generados
    """
    try:
        import asyncio
        from core.sql_first.db import get_sql_connection

        where = ["1=1"]
        params: list = []
        if workflow_id:
            where.append("WorkflowID = %s"); params.append(workflow_id)
        if tipo:
            where.append("TipoDocumento = %s"); params.append(tipo.upper())
        where_sql = " AND ".join(where)

        def _run():
            conn = get_sql_connection()
            cur = conn.cursor(as_dict=True)
            cur.execute(f"SELECT COUNT(*) AS total FROM Operativo_DocumentosGenerados WHERE {where_sql}", tuple(params))
            total = cur.fetchone()["total"]
            cur.execute(f"""
                SELECT DocumentoID AS id, WorkflowID AS workflow_id, TipoDocumento AS tipo_documento,
                       NombreArchivo AS nombre_archivo, URLDescarga AS url_descarga, Formato AS formato,
                       TamanioBytes AS tamanio_bytes, UsuarioGeneradorID AS usuario_generador_id,
                       Estado AS estado, FechaGeneracion AS fecha_generacion, FechaExpiracion AS fecha_expiracion
                FROM Operativo_DocumentosGenerados
                WHERE {where_sql}
                ORDER BY FechaGeneracion DESC
                OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
            """, tuple(params) + (limit,))
            rows = list(cur.fetchall())
            cur.close(); conn.close()
            return total, rows

        total, documentos = await asyncio.get_event_loop().run_in_executor(None, _run)
        
        return {
            "success": True,
            "items": documentos,
            "total": total
        }
        
    except Exception as e:
        logger.error(f"Error al obtener historial: {e}")
        return {"success": True, "items": [], "total": 0}
