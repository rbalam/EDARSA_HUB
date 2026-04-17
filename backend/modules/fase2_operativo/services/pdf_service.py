"""
Servicio de Generación de PDF - Resumen Ejecutivo
CAB-003 | EDARSA HUB - Fase 2B.3

Genera PDF de resumen ejecutivo para workflows.
Consume datos desde DocumentDataService (fuente única).
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from io import BytesIO
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

from .document_data_service import (
    DocumentDataService, 
    get_document_data_service,
    WorkflowNoEncontradoError
)

logger = logging.getLogger(__name__)

# Límite de diferencias a mostrar en PDF
MAX_DIFERENCIAS_PDF = 10


class PDFServiceError(Exception):
    """Excepción base para errores del servicio PDF."""
    pass


class PDFService:
    """
    Servicio para generar PDFs de resumen ejecutivo de workflows.
    
    Genera un documento PDF con:
    1. Encabezado con título e identificadores
    2. Información general del workflow
    3. Métricas clave
    4. Diferencias relevantes (top N)
    5. Estado de auditoría
    6. Pie de página con paginación
    """
    
    # Colores corporativos
    COLOR_PRIMARIO = colors.HexColor("#1E40AF")  # Azul EDARSA
    COLOR_SECUNDARIO = colors.HexColor("#475569")  # Gris
    COLOR_EXITO = colors.HexColor("#16A34A")  # Verde
    COLOR_ERROR = colors.HexColor("#DC2626")  # Rojo
    COLOR_ADVERTENCIA = colors.HexColor("#D97706")  # Naranja
    COLOR_FONDO = colors.HexColor("#F8FAFC")  # Gris claro
    
    def __init__(self, db):
        """
        Inicializa el servicio.
        
        Args:
            db: Conexión a la base de datos
        """
        self.data_service = get_document_data_service(db)
        self._setup_styles()
    
    def _setup_styles(self):
        """Configura los estilos de párrafo para el PDF."""
        self.styles = getSampleStyleSheet()
        
        # Título principal
        self.styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=self.COLOR_PRIMARIO,
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        # Subtítulo de sección
        self.styles.add(ParagraphStyle(
            name='Seccion',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=self.COLOR_PRIMARIO,
            spaceBefore=16,
            spaceAfter=8,
            borderPadding=4
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLOR_SECUNDARIO,
            spaceAfter=4
        ))
        
        # Texto destacado
        self.styles.add(ParagraphStyle(
            name='Destacado',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        ))
        
        # Nota pequeña
        self.styles.add(ParagraphStyle(
            name='Nota',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER,
            spaceBefore=8
        ))
    
    async def generar_pdf_workflow(self, workflow_id: str) -> BytesIO:
        """
        Genera un PDF de resumen ejecutivo para un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            BytesIO con el contenido del PDF
            
        Raises:
            WorkflowNoEncontradoError: Si el workflow no existe
        """
        logger.info(f"Generando PDF para workflow: {workflow_id}")
        
        # Obtener datos desde la fuente única
        datos = await self.data_service.obtener_datos_completos_workflow(workflow_id)
        
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Construir contenido
        elementos = []
        
        # 1. Encabezado
        elementos.extend(self._crear_encabezado(datos))
        
        # 2. Información general
        elementos.extend(self._crear_info_general(datos))
        
        # 3. Métricas clave
        elementos.extend(self._crear_metricas(datos))
        
        # 4. Diferencias relevantes
        elementos.extend(self._crear_diferencias(datos))
        
        # 5. Auditoría
        elementos.extend(self._crear_auditoria(datos))
        
        # 6. Nota final
        elementos.extend(self._crear_nota_final(datos))
        
        # Construir PDF con pie de página
        doc.build(
            elementos,
            onFirstPage=self._pie_pagina,
            onLaterPages=self._pie_pagina
        )
        
        buffer.seek(0)
        logger.info(f"PDF generado exitosamente para workflow: {workflow_id}")
        
        return buffer
    
    def _crear_encabezado(self, datos: Dict[str, Any]) -> List:
        """Crea el encabezado del PDF."""
        elementos = []
        metadata = datos["metadata"]
        
        # Título
        elementos.append(Paragraph(
            "REPORTE DE WORKFLOW DE INVENTARIO",
            self.styles['TituloPrincipal']
        ))
        
        # Subtítulo con fecha
        fecha_gen = self._formatear_fecha(metadata.get("fecha_generacion"))
        elementos.append(Paragraph(
            f"Resumen Ejecutivo - Generado: {fecha_gen}",
            self.styles['Nota']
        ))
        
        elementos.append(Spacer(1, 8*mm))
        
        # Línea separadora
        elementos.append(HRFlowable(
            width="100%",
            thickness=1,
            color=self.COLOR_PRIMARIO,
            spaceBefore=4,
            spaceAfter=8
        ))
        
        return elementos
    
    def _crear_info_general(self, datos: Dict[str, Any]) -> List:
        """Crea la sección de información general."""
        elementos = []
        resumen = datos["resumen"]
        
        elementos.append(Paragraph(
            "INFORMACION GENERAL",
            self.styles['Seccion']
        ))
        
        # Tabla de información
        info_data = [
            ["Workflow ID:", resumen.get("workflow_id", "N/A")],
            ["Procesado ID:", resumen.get("procesado_id", "N/A")],
            ["Sucursal:", resumen.get("sucursal_id", "N/A")],
            ["Estado:", self._formatear_estado(resumen.get("estado_workflow", ""))],
            ["Ciclo:", str(resumen.get("ciclo_actual", 1))],
            ["Fecha Creacion:", self._formatear_fecha(resumen.get("fecha_creacion"))],
        ]
        
        tabla = Table(info_data, colWidths=[4*cm, 12*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLOR_SECUNDARIO),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 4*mm))
        
        return elementos
    
    def _crear_metricas(self, datos: Dict[str, Any]) -> List:
        """Crea la sección de métricas clave."""
        elementos = []
        metricas = datos["resumen"]["metricas"]
        
        elementos.append(Paragraph(
            "METRICAS CLAVE",
            self.styles['Seccion']
        ))
        
        # Tabla de métricas en 2 columnas
        valor_total = metricas.get("valor_total_diferencia", 0)
        valor_formateado = f"${valor_total:,.2f}"
        
        metricas_data = [
            ["Total Diferencias:", str(metricas.get("total_diferencias", 0)),
             "Productos Faltantes:", str(metricas.get("productos_faltantes", 0))],
            ["Justificadas:", str(metricas.get("diferencias_justificadas", 0)),
             "Productos Sobrantes:", str(metricas.get("productos_sobrantes", 0))],
            ["Pendientes:", str(metricas.get("diferencias_pendientes", 0)),
             "Total Tareas:", str(metricas.get("total_tareas", 0))],
        ]
        
        tabla = Table(metricas_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLOR_SECUNDARIO),
            ('TEXTCOLOR', (2, 0), (2, -1), self.COLOR_SECUNDARIO),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), self.COLOR_FONDO),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 4*mm))
        
        # Valor total destacado
        color_valor = self.COLOR_ERROR if valor_total < 0 else self.COLOR_EXITO
        elementos.append(Paragraph(
            f"<b>VALOR TOTAL DIFERENCIA:</b> <font color='{color_valor.hexval()}'>{valor_formateado}</font>",
            self.styles['TextoNormal']
        ))
        
        elementos.append(Spacer(1, 4*mm))
        
        return elementos
    
    def _crear_diferencias(self, datos: Dict[str, Any]) -> List:
        """Crea la sección de diferencias relevantes."""
        elementos = []
        diferencias = datos["diferencias"]
        total = len(diferencias)
        
        elementos.append(Paragraph(
            "DIFERENCIAS RELEVANTES",
            self.styles['Seccion']
        ))
        
        if not diferencias:
            elementos.append(Paragraph(
                "No se registraron diferencias en este workflow.",
                self.styles['TextoNormal']
            ))
            return elementos
        
        # Limitar a las diferencias más relevantes (por valor absoluto)
        diferencias_ordenadas = sorted(
            diferencias,
            key=lambda x: abs(x.get("diferencia_costo", x.get("diferencia_valor", 0)) or 0),
            reverse=True
        )[:MAX_DIFERENCIAS_PDF]
        
        # Header de la tabla
        header = ["Codigo", "Producto", "Dif. Cant.", "Valor Dif.", "Justif."]
        tabla_data = [header]
        
        for dif in diferencias_ordenadas:
            codigo = dif.get("codigo_producto", dif.get("producto_id", ""))[:12]
            nombre = dif.get("nombre_producto", dif.get("descripcion_producto", ""))[:25]
            dif_cant = dif.get("diferencia_cantidad", 0)
            dif_valor = dif.get("diferencia_costo", dif.get("diferencia_valor", 0)) or 0
            justificada = "Si" if dif.get("tiene_justificacion") else "No"
            
            tabla_data.append([
                codigo,
                nombre,
                str(int(dif_cant)) if dif_cant else "0",
                f"${dif_valor:,.2f}",
                justificada
            ])
        
        tabla = Table(tabla_data, colWidths=[2.5*cm, 6*cm, 2*cm, 3*cm, 1.5*cm])
        tabla.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_PRIMARIO),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            # Alternar filas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLOR_FONDO]),
            # Bordes
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, self.COLOR_PRIMARIO),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            # Padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elementos.append(tabla)
        
        # Nota si hay más diferencias
        if total > MAX_DIFERENCIAS_PDF:
            elementos.append(Spacer(1, 2*mm))
            elementos.append(Paragraph(
                f"<i>Mostrando {MAX_DIFERENCIAS_PDF} de {total} diferencias. "
                f"Descargue el archivo Excel para ver el detalle completo.</i>",
                self.styles['Nota']
            ))
        
        elementos.append(Spacer(1, 4*mm))
        
        return elementos
    
    def _crear_auditoria(self, datos: Dict[str, Any]) -> List:
        """Crea la sección de auditoría."""
        elementos = []
        auditoria_info = datos["resumen"]["auditoria"]
        decisiones = datos["auditoria"]
        
        elementos.append(Paragraph(
            "ESTADO DE AUDITORIA",
            self.styles['Seccion']
        ))
        
        if not auditoria_info.get("tiene_decision"):
            elementos.append(Paragraph(
                "Sin decisiones de auditoria registradas para este workflow.",
                self.styles['TextoNormal']
            ))
            elementos.append(Spacer(1, 4*mm))
            return elementos
        
        # Última decisión
        decision = auditoria_info.get("ultima_decision", "N/A")
        color_decision = self._color_decision(decision)
        
        elementos.append(Paragraph(
            f"<b>Ultima Decision:</b> <font color='{color_decision}'>{decision}</font>",
            self.styles['TextoNormal']
        ))
        
        elementos.append(Paragraph(
            f"<b>Auditor:</b> {auditoria_info.get('auditor', 'N/A')}",
            self.styles['TextoNormal']
        ))
        
        elementos.append(Paragraph(
            f"<b>Fecha Decision:</b> {self._formatear_fecha(auditoria_info.get('fecha_ultima_decision'))}",
            self.styles['TextoNormal']
        ))
        
        # Mostrar comentarios de la última decisión si existen
        if decisiones:
            ultima = decisiones[0]
            comentarios = ultima.get("comentarios", "")
            if comentarios:
                elementos.append(Spacer(1, 2*mm))
                elementos.append(Paragraph(
                    f"<b>Comentarios:</b> {comentarios}",
                    self.styles['TextoNormal']
                ))
        
        elementos.append(Spacer(1, 4*mm))
        
        return elementos
    
    def _crear_nota_final(self, datos: Dict[str, Any]) -> List:
        """Crea la nota final del documento."""
        elementos = []
        
        elementos.append(Spacer(1, 8*mm))
        elementos.append(HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.lightgrey,
            spaceBefore=4,
            spaceAfter=8
        ))
        
        elementos.append(Paragraph(
            "Este documento es un resumen ejecutivo. "
            "Para el detalle completo de diferencias, justificaciones y auditoria, "
            "descargue el archivo Excel correspondiente.",
            self.styles['Nota']
        ))
        
        return elementos
    
    def _pie_pagina(self, canvas_obj, doc):
        """Dibuja el pie de página en cada hoja."""
        canvas_obj.saveState()
        
        # Línea
        canvas_obj.setStrokeColor(colors.lightgrey)
        canvas_obj.line(2*cm, 1.5*cm, A4[0] - 2*cm, 1.5*cm)
        
        # Texto
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        
        # Izquierda: Sistema
        canvas_obj.drawString(
            2*cm, 
            1*cm, 
            "EDARSA HUB - Sistema de Gestion Operativa"
        )
        
        # Derecha: Página
        canvas_obj.drawRightString(
            A4[0] - 2*cm,
            1*cm,
            f"Pagina {doc.page}"
        )
        
        canvas_obj.restoreState()
    
    def _formatear_fecha(self, fecha_str: str) -> str:
        """Formatea una fecha ISO a formato legible."""
        if not fecha_str:
            return "N/A"
        
        try:
            if isinstance(fecha_str, str):
                fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                return fecha.strftime("%d/%m/%Y %H:%M")
            return str(fecha_str)
        except Exception:
            return str(fecha_str)
    
    def _formatear_estado(self, estado: str) -> str:
        """Formatea el estado del workflow."""
        estados = {
            "PENDIENTE_ASIGNACION": "Pendiente de Asignacion",
            "EN_REVISION": "En Revision",
            "PENDIENTE_JUSTIFICACION": "Pendiente de Justificacion",
            "JUSTIFICADO": "Justificado",
            "EN_AUDITORIA": "En Auditoria",
            "CERRADO": "Cerrado",
            "ESCALADO": "Escalado"
        }
        return estados.get(estado, estado)
    
    def _color_decision(self, decision: str) -> str:
        """Retorna el color hex para una decisión."""
        colores = {
            "APROBADO": self.COLOR_EXITO.hexval(),
            "RECHAZADO": self.COLOR_ERROR.hexval(),
            "DEVUELTO_PARA_CORRECCION": self.COLOR_ADVERTENCIA.hexval()
        }
        return colores.get(decision, self.COLOR_SECUNDARIO.hexval())


# Singleton del servicio
_pdf_service = None


def get_pdf_service(db) -> PDFService:
    """
    Obtiene instancia del servicio de PDF.
    
    Args:
        db: Conexión a la base de datos
        
    Returns:
        Instancia de PDFService
    """
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService(db)
    return _pdf_service
