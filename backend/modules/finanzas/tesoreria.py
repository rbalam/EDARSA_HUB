"""
API Router para Tesorería - Cuadre de Cortes Z
PROTEGIDO CON RBAC (Fase 3.1)

FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
- Fecha: 2026-05-25
- Ya NO usa MongoDB (tesoreria_cuadres_z) como fuente productiva
- Usa repository_cuadres_z_edarsahub.py para operaciones de cuadres
- ServerID se resuelve desde EDARSAHUB SQL

FINANZAS-TESORERIA-SQL-001: Cortes de Caja migrados a SQL
- Fecha: 2026-05-25
- Ya NO consulta servidores origen en vivo
- Lee de Finanzas_CortesCaja (tabla sincronizada)
- Cumple máxima: "EDARSAHUB SQL es el cerebro"
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import base64
import os

from core.security import get_current_user, get_user_empresas_permitidas, get_servers_for_empresas
from .tesoreria_models import (
    CuadreCorteZCreate, CuadreCorteZUpdate, CuadreCorteZResponse,
    EstadoCuadre, ConteoEfectivo, FichaDeposito
)
# FINANZAS-TESORERIA-SQL-001: Usar repositorio SQL de Cortes de Caja
from .repository_cortes_caja_edarsahub import (
    get_cortes_caja_repository_sql,
    calcular_fecha_deposito_esperada
)
# FINANZAS-TESORERIA-MONGO-002: Migrado a repositorio SQL
from .repository_cuadres_z_edarsahub import (
    get_cuadres_z_repository_sql, 
    RepositoryCuadresZEdarsahub
)

router = APIRouter(prefix="/finanzas/tesoreria", tags=["Tesorería"])
logger = logging.getLogger(__name__)


async def get_user_sucursales_permitidas(current_user: Dict[str, Any]) -> List[str]:
    """
    RBAC Fase 3.1: Obtiene los CÓDIGOS de sucursales permitidas para el usuario.
    Retorna lista vacía si el usuario tiene acceso total (admin).
    
    Para Finanzas, usamos códigos de empresa ya que los datos demo usan códigos
    como 'CIENFUEGOS', 'LA_ESTELAR', etc.
    """
    from server import db
    
    empresas_permitidas = await get_user_empresas_permitidas(current_user)
    if not empresas_permitidas:
        return []  # Sin restricción (admin)
    
    # Obtener códigos de las empresas permitidas
    empresas = await db.empresas.find(
        {'id': {'$in': empresas_permitidas}},
        {'_id': 0, 'codigo': 1, 'nombre': 1}
    ).to_list(100)
    
    # Retornar códigos y nombres para matching flexible
    codigos = []
    for e in empresas:
        if e.get('codigo'):
            codigos.append(e['codigo'].upper())
        if e.get('nombre'):
            codigos.append(e['nombre'].upper())
    
    return codigos


def filtrar_cortes_por_permisos(cortes: List[Dict], codigos_permitidos: List[str]) -> List[Dict]:
    """Filtra cortes por códigos de sucursal permitidos. Si vacío, devuelve todo."""
    if not codigos_permitidos:
        return cortes
    
    resultado = []
    for c in cortes:
        suc_id = str(c.get('sucursal_id', '')).upper()
        suc_nombre = str(c.get('sucursal_nombre', '')).upper()
        
        # Verificar si algún código permitido coincide
        for codigo in codigos_permitidos:
            if codigo in suc_id or codigo in suc_nombre or suc_id in codigo:
                resultado.append(c)
                break
    
    return resultado


@router.get("/cortes-z")
async def listar_cortes_z(
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin YYYY-MM-DD"),
    sucursal: Optional[str] = Query(None, description="Filtrar por sucursal"),
    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID)"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista los Cortes Z disponibles desde EDARSAHUB SQL (Finanzas_CortesCaja).
    
    FINANZAS-TESORERIA-SQL-001: Migrado a EDARSAHUB SQL
    - Ya NO consulta servidores origen en vivo
    - Lee de tabla Finanzas_CortesCaja (sincronizada)
    - Cumple máxima: "EDARSAHUB SQL es el cerebro"
    
    PROTEGIDO: Filtra por empresas_permitidas del usuario.
    Incluye indicador si ya tiene cuadre registrado.
    """
    try:
        # RBAC Fase 3.1: Obtener sucursales permitidas
        sucursales_permitidas = await get_user_sucursales_permitidas(current_user)
        
        # FINANZAS-TESORERIA-SQL-001: Usar repositorio SQL
        repo_cortes = get_cortes_caja_repository_sql()
        repo_cuadres = get_cuadres_z_repository_sql()
        
        # Consultar cortes desde EDARSAHUB SQL (NO en vivo)
        if server_id:
            # Filtrar por servidor específico
            cortes = repo_cortes.listar_cortes_por_server_id(
                server_id=server_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                limit=200
            )
            fuente = "EDARSAHUB_SQL"
            fuentes_detalle = [{
                'status': 'SUCCESS_WITH_DATA' if cortes else 'SUCCESS_EMPTY',
                'source_type': 'EDARSAHUB_SQL',
                'source_id': 'Finanzas_CortesCaja',
                'row_count': len(cortes)
            }]
        else:
            # Consultar todos (sin filtro de servidor)
            result = repo_cortes.obtener_cortes_todos_servidores(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                limit=200
            )
            cortes = result.get('cortes', [])
            fuente = result.get('data_source', 'EDARSAHUB_SQL')
            fuentes_detalle = result.get('fuentes_detalle', [])
        
        # RBAC Fase 3.1: Filtrar por sucursales permitidas
        if sucursales_permitidas:
            cortes = filtrar_cortes_por_permisos(cortes, sucursales_permitidas)
        
        # Filtrar por sucursal si se especifica (filtro manual del usuario)
        if sucursal:
            cortes = [c for c in cortes if sucursal.lower() in c.get('sucursal_nombre', '').lower()]
        
        # Verificar cuáles ya tienen cuadre y calcular fecha depósito
        for corte in cortes:
            # Buscar si existe cuadre en SQL
            filtros_busqueda = {
                'unidad_negocio_id': corte.get('sucursal_id'),
                'limit': 10
            }
            cuadres_existentes = repo_cuadres.listar_cuadres_z(filtros_busqueda)
            cuadre_existente = None
            folio_corte = corte.get('folio_corte')
            for c in cuadres_existentes:
                if c.get('folio_corte') == folio_corte:
                    cuadre_existente = c
                    break
            
            corte['tiene_cuadre'] = cuadre_existente is not None
            corte['cuadre_id'] = cuadre_existente.get('cuadre_z_id') if cuadre_existente else None
            corte['estado_cuadre'] = cuadre_existente.get('estatus', {}).get('cuadre', {}).get('codigo') if cuadre_existente else None
            # Calcular fecha de depósito esperada
            corte['fecha_deposito_esperada'] = calcular_fecha_deposito_esperada(corte.get('fecha_corte'))
        
        response = {
            "cortes": cortes,
            "total": len(cortes),
            "fecha_consulta": datetime.utcnow().isoformat(),
            "fuente": fuente,
            "fuentes_detalle": fuentes_detalle
        }
        
        logger.info(f"[CORTES_Z_SQL] Listados {len(cortes)} cortes desde EDARSAHUB SQL")
        return response
        
    except Exception as e:
        logger.error(f"[CORTES_Z_SQL] Error listando cortes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cortes-z/{sucursal}/{folio}")
async def obtener_corte_z(
    sucursal: str,
    folio: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene un corte Z específico por sucursal y folio.
    
    FINANZAS-TESORERIA-SQL-001: Migrado a EDARSAHUB SQL
    """
    try:
        repo_cortes = get_cortes_caja_repository_sql()
        
        # Buscar en EDARSAHUB SQL
        filtros = {
            'unidad_negocio_nombre': sucursal,
            'limit': 100
        }
        cortes = repo_cortes.listar_cortes_caja(filtros)
        
        # Filtrar por folio
        cortes = [c for c in cortes if str(c.get('folio_corte', '')) == str(folio)]
        
        if not cortes:
            raise HTTPException(status_code=404, detail="Corte Z no encontrado")
        
        corte = cortes[0]
        corte['fecha_deposito_esperada'] = calcular_fecha_deposito_esperada(corte.get('fecha_corte'))
        
        return corte
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo corte Z: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuadres")
async def listar_cuadres(
    estado: Optional[str] = Query(None, description="Estado: PENDIENTE, EN_PROCESO, CUADRADO, DESCUADRE"),
    sucursal_id: Optional[str] = None,
    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID de unidad de negocio)"),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista los cuadres registrados con filtros.
    
    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
    - Ya NO usa MongoDB tesoreria_cuadres_z
    - Usa repository_cuadres_z_edarsahub.py
    - server_id se resuelve desde EDARSAHUB SQL
    """
    try:
        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        filtros = {
            'limit': limit,
            'offset': skip
        }
        
        if fecha_inicio:
            filtros['fecha_inicio'] = fecha_inicio
        if fecha_fin:
            filtros['fecha_fin'] = fecha_fin
        if estado:
            filtros['estatus_cuadre'] = estado
        
        # Filtrar por server_id o unidad_negocio_id (SQL directo, sin MongoDB)
        if server_id:
            logger.info(f"[CUADRES_SQL] Filtrando por server_id={server_id}")
            cuadres = repo.listar_cuadres_z_por_server_id(server_id, filtros)
        elif sucursal_id:
            filtros['unidad_negocio_id'] = sucursal_id
            cuadres = repo.listar_cuadres_z(filtros)
        else:
            cuadres = repo.listar_cuadres_z(filtros)
        
        return {
            "cuadres": cuadres,
            "total": len(cuadres),
            "limit": limit,
            "skip": skip,
            "fuente": "EDARSAHUB_SQL",  # Indicador de fuente
            "filtro_aplicado": {
                "server_id": server_id,
                "sucursal_id": sucursal_id
            }
        }
    except Exception as e:
        logger.error(f"[CUADRES_SQL] Error listando cuadres: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuadres/resumen")
async def obtener_resumen_cuadres(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    server_id: Optional[str] = Query(None, description="Filtrar por server_id (UUID de unidad de negocio)"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene resumen estadístico de cuadres.
    
    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
    - Ya NO usa MongoDB tesoreria_cuadres_z
    - Usa repository_cuadres_z_edarsahub.py
    """
    try:
        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        filtros = {}
        if fecha_inicio:
            filtros['fecha_inicio'] = fecha_inicio
        if fecha_fin:
            filtros['fecha_fin'] = fecha_fin
        
        if server_id:
            logger.info(f"[RESUMEN_SQL] Obteniendo resumen para server_id={server_id}")
            resultado = repo.obtener_resumen_por_server_id(server_id, filtros)
            resumen = resultado.get('resumen', {})
        else:
            resumen_data = repo.obtener_resumen_cuadres_z(filtros)
            # Formatear para compatibilidad con contrato frontend
            resumen = {
                'PENDIENTE': {'count': 0, 'total_esperado': 0, 'total_depositado': 0},
                'EN_PROCESO': {'count': 0, 'total_esperado': 0, 'total_depositado': 0},
                'CUADRADO': {'count': 0, 'total_esperado': 0, 'total_depositado': 0},
                'DESCUADRE': {'count': 0, 'total_esperado': 0, 'total_depositado': 0}
            }
            for r in resumen_data.get('por_estatus', []):
                estatus = r.get('estatus', 'PENDIENTE')
                if estatus in resumen:
                    resumen[estatus]['count'] = r['cantidad']
        
        return {
            "resumen": resumen,
            "fecha_consulta": datetime.utcnow().isoformat(),
            "fuente": "EDARSAHUB_SQL",
            "filtro_aplicado": {
                "server_id": server_id
            }
        }
    except Exception as e:
        logger.error(f"[RESUMEN_SQL] Error obteniendo resumen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuadres/{cuadre_id}")
async def obtener_cuadre(
    cuadre_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene un cuadre específico por ID.
    
    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
    """
    try:
        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        # Intentar convertir a int si es numérico
        try:
            cuadre_id_int = int(cuadre_id)
            cuadre = repo.obtener_cuadre_z(cuadre_id_int)
        except ValueError:
            # Si no es numérico, no existe en SQL
            cuadre = None
        
        if not cuadre:
            raise HTTPException(status_code=404, detail="Cuadre no encontrado")
        
        return {
            "cuadre": cuadre,
            "fuente": "EDARSAHUB_SQL"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CUADRE_SQL] Error obteniendo cuadre: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cuadres")
async def crear_cuadre(
    data: dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo cuadre para un Corte Z.
    
    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
    - Ya NO usa MongoDB tesoreria_cuadres_z
    - Usa repository_cuadres_z_edarsahub.py
    """
    from core.auditoria_helpers import registrar_auditoria_tesoreria
    
    try:
        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        corte_z = data.get('corte_z', {})
        user_id = current_user.get('sub') or current_user.get('email')
        user_nombre = current_user.get('nombre') or current_user.get('email')
        
        # Preparar datos para repositorio SQL
        cuadre_data = {
            'unidad_negocio_id': corte_z.get('sucursal_id') or corte_z.get('server_id'),
            'unidad_negocio_nombre': corte_z.get('sucursal_nombre') or corte_z.get('nombre_servidor'),
            'empresa_id': corte_z.get('empresa_id'),
            'server_id': corte_z.get('server_id') or corte_z.get('sucursal_id'),
            'sistema_origen': corte_z.get('sistema_origen', 'MANUAL'),
            'fecha_operacion': corte_z.get('fecha_corte'),
            'fecha_corte': corte_z.get('fecha_corte'),
            'folio_corte': corte_z.get('folio_corte'),
            'folio_z': corte_z.get('folio_z'),
            'caja_id': corte_z.get('caja_id'),
            'caja_nombre': corte_z.get('caja_nombre'),
            'cajero_id': corte_z.get('cajero_id'),
            'cajero_nombre': corte_z.get('cajero_nombre'),
            'turno_id': corte_z.get('turno_id'),
            'total_venta': corte_z.get('total_venta', 0),
            'total_efectivo': corte_z.get('total_efectivo', 0),
            'total_tarjeta_debito': corte_z.get('total_tarjeta_debito', 0),
            'total_tarjeta_credito': corte_z.get('total_tarjeta_credito', 0),
            'total_tarjeta_total': corte_z.get('total_tarjeta', 0),
            'total_depositar': corte_z.get('monto_a_depositar', 0),
            'conteo_efectivo': data.get('conteo_efectivo', {}),
            'ficha_deposito': data.get('ficha_deposito', {}),
            'estatus_cuadre': 'PENDIENTE',
            'estatus_tesoreria': 'PENDIENTE',
            'observaciones': data.get('observaciones'),
            'fuente_original': 'WEB_APP'
        }
        
        resultado = repo.crear_cuadre_z(cuadre_data, user_id, user_nombre)
        
        if not resultado.get('success'):
            raise HTTPException(
                status_code=400,
                detail=resultado.get('mensaje', 'Error al crear cuadre')
            )
        
        # Registrar auditoría
        await registrar_auditoria_tesoreria(
            current_user=current_user,
            accion='CONFIRM',
            corte_id=str(resultado.get('cuadre_z_id')),
            folio_corte=corte_z.get('folio_corte'),
            sucursal_id=cuadre_data['unidad_negocio_id'],
            valor_nuevo={
                'cuadre_z_id': resultado.get('cuadre_z_id'),
                'fuente': 'EDARSAHUB_SQL'
            },
            motivo='Crear cuadre de Corte Z (SQL)'
        )
        
        return {
            "message": "Cuadre creado exitosamente",
            "cuadre_z_id": resultado.get('cuadre_z_id'),
            "fuente": "EDARSAHUB_SQL"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CUADRE_SQL] Error creando cuadre: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cuadres/{cuadre_id}")
async def actualizar_cuadre(
    cuadre_id: str,
    data: dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza un cuadre existente (conteo, ficha de depósito, observaciones).
    
    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
    """
    from core.auditoria_helpers import registrar_auditoria_tesoreria
    
    try:
        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        try:
            cuadre_id_int = int(cuadre_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de cuadre inválido")
        
        user_id = current_user.get('sub') or current_user.get('email')
        user_nombre = current_user.get('nombre') or current_user.get('email')
        
        resultado = repo.actualizar_cuadre_z(cuadre_id_int, data, user_id, user_nombre)
        
        if not resultado.get('success'):
            raise HTTPException(
                status_code=404 if resultado.get('accion') == 'no_encontrado' else 400,
                detail=resultado.get('mensaje', 'Error al actualizar cuadre')
            )
        
        # Registrar auditoría
        await registrar_auditoria_tesoreria(
            current_user=current_user,
            accion='EDIT',
            corte_id=cuadre_id,
            valor_nuevo=data,
            motivo='Actualizar cuadre (SQL)'
        )
        
        return {
            "message": "Cuadre actualizado exitosamente",
            "cuadre_z_id": cuadre_id_int,
            "fuente": "EDARSAHUB_SQL"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CUADRE_SQL] Error actualizando cuadre: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cuadres/{cuadre_id}")
async def eliminar_cuadre(
    cuadre_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Elimina un cuadre (soft delete - marca Activo=0).
    
    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
    """
    try:
        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        try:
            cuadre_id_int = int(cuadre_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de cuadre inválido")
        
        # Soft delete: marcar como inactivo
        resultado = repo.actualizar_cuadre_z(cuadre_id_int, {'activo': False})
        
        if not resultado.get('success'):
            raise HTTPException(status_code=404, detail="Cuadre no encontrado")
        
        return {
            "message": "Cuadre eliminado exitosamente",
            "fuente": "EDARSAHUB_SQL"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CUADRE_SQL] Error eliminando cuadre: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cuadres/{cuadre_id}/ficha-deposito")
async def subir_ficha_deposito(
    cuadre_id: str,
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Sube una imagen de ficha de depósito y la procesa con OCR.
    Devuelve los datos extraídos para validación.
    """
    try:
        # Leer archivo
        contents = await file.read()
        
        # Guardar temporalmente
        upload_dir = "/app/uploads/fichas_deposito"
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{cuadre_id}_{timestamp}_{file.filename}"
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(contents)
        
        # Por ahora devolver datos simulados del OCR
        # TODO: Integrar OCR real (Google Vision, Azure, etc.)
        ocr_data = {
            "archivo_url": f"/uploads/fichas_deposito/{filename}",
            "ocr_procesado": True,
            "datos_extraidos": {
                "banco": "BBVA",
                "fecha_deposito": None,  # El usuario debe confirmar
                "referencia": None,
                "importe": None,
                "cuenta": None
            },
            "requiere_validacion_manual": True
        }
        
        return {
            "message": "Ficha cargada exitosamente. Valide los datos extraídos.",
            "ocr_data": ocr_data,
            "filepath": filepath
        }
    except Exception as e:
        logger.error(f"Error subiendo ficha de depósito: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cuadres/{cuadre_id}/validar-ficha")
async def validar_ficha_deposito(
    cuadre_id: str,
    data: dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Valida los datos de la ficha de depósito contra el corte Z.
    Verifica: importe, fecha (día hábil siguiente).
    
    FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL
    """
    try:
        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        try:
            cuadre_id_int = int(cuadre_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de cuadre inválido")
        
        cuadre = repo.obtener_cuadre_z(cuadre_id_int)
        
        if not cuadre:
            raise HTTPException(status_code=404, detail="Cuadre no encontrado")
        
        fecha_venta = cuadre.get('fecha_corte')
        fecha_deposito = data.get('fecha_deposito')
        importe_deposito = float(data.get('importe', 0))
        monto_esperado = cuadre.get('cuadre', {}).get('total_depositar', 0)
        
        # Validar fecha
        from .repository_cortes_z import calcular_fecha_deposito_esperada
        fecha_esperada = calcular_fecha_deposito_esperada(fecha_venta)
        fecha_valida = fecha_esperada == fecha_deposito
        
        # Validar importe (tolerancia de $5)
        diferencia = abs(importe_deposito - monto_esperado)
        importe_valido = diferencia <= 5
        
        # Actualizar ficha en el cuadre
        update_data = {
            'ficha_deposito_url': data.get('archivo_url'),
            'ficha_deposito_fecha': fecha_deposito,
            'ficha_deposito_monto': importe_deposito,
            'ficha_deposito_validada': fecha_valida and importe_valido
        }
        
        # Determinar estado
        if fecha_valida and importe_valido:
            update_data['estatus_cuadre'] = 'CUADRADO'
        elif importe_deposito > 0:
            update_data['estatus_cuadre'] = 'DESCUADRE'
        
        user_id = current_user.get('sub') or current_user.get('email')
        user_nombre = current_user.get('nombre') or current_user.get('email')
        
        resultado = repo.actualizar_cuadre_z(cuadre_id_int, update_data, user_id, user_nombre)
        
        return {
            "validacion": {
                "fecha_valida": fecha_valida,
                "fecha_esperada": fecha_esperada,
                "importe_valido": importe_valido,
                "monto_esperado": monto_esperado,
                "diferencia": diferencia
            },
            "cuadre_z_id": cuadre_id_int,
            "actualizado": resultado.get('success', False),
            "fuente": "EDARSAHUB_SQL"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CUADRE_SQL] Error validando ficha: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_tesoreria_sucursales_operativas() -> List[Dict]:
    """
    P1-FASE4A: Obtiene sucursales/servidores OPERATIVOS para Cuadre de Cortes Z.
    
    FUENTE PRIMARIA: EDARSAHUB.Servidores_Conexiones
    FALLBACK: MongoDB (solo si EDARSAHUB falla, con warning)
    
    Criterios operativos:
    - activo = True
    - visible_en_operaciones = True
    - tipo_conexion != 'CORE' y != 'API_LOCAL'
    - system_type in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']
    
    NOTA TÉCNICA: MongoDB se mantiene como registry legacy parcial para fallback.
    EDARSAHUB es la fuente maestra operativa.
    """
    sucursales = []
    
    try:
        # FUENTE PRIMARIA: EDARSAHUB SQL
        from core.db import execute_sql_query
        from core.server_registry import EDARSAHUB_CONFIG
        
        query = """
        SELECT 
            id,
            nombre,
            system_type,
            tipo_conexion,
            activo,
            visible_en_operaciones,
            host,
            port
        FROM Servidores_Conexiones
        WHERE activo = 1
          AND visible_en_operaciones = 1
          AND (tipo_conexion != 'CORE' OR tipo_conexion IS NULL)
          AND (tipo_conexion != 'API_LOCAL' OR tipo_conexion IS NULL)
        ORDER BY nombre
        """
        
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        if results:
            logger.info(f"[TESORERIA][EDARSAHUB_HIT] Obtenidos {len(results)} servidores operativos desde EDARSAHUB")
            
            for row in results:
                system_type = (row.get('system_type') or '').upper()
                
                # Solo incluir sistemas de Tesorería (SoftRestaurant y MPRO)
                if system_type not in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']:
                    continue
                
                # Determinar fuente para el frontend
                if system_type in ['SOFTRESTAURANT', 'SR']:
                    fuente = 'SOFTRESTAURANT'
                elif system_type in ['MANAGEMENTPRO', 'MPRO']:
                    fuente = 'MPRO'
                else:
                    fuente = system_type or 'UNKNOWN'
                
                sucursales.append({
                    "id": str(row.get('id')),
                    "nombre": row.get('nombre', ''),
                    "fuente": fuente,
                    "system_type": system_type,
                    "activo": bool(row.get('activo', True))
                })
            
            return sucursales
        else:
            logger.warning("[TESORERIA][EDARSAHUB_EMPTY] EDARSAHUB no retornó servidores, intentando fallback MongoDB")
            
    except Exception as e:
        logger.warning(f"[TESORERIA][EDARSAHUB_ERROR] Error consultando EDARSAHUB: {e}. Usando fallback server_registry.")
    
    # FALLBACK: server_registry.py (FASE T2.2: Reemplaza MongoDB)
    # Este fallback usa la capa centralizada que también lee de EDARSAHUB
    try:
        from core.server_registry import list_operational_servers
        
        logger.info("[TESORERIA][REGISTRY_FALLBACK] Usando server_registry.py como fallback")
        
        registry_servers = list_operational_servers()
        
        for s in registry_servers:
            # Verificar visible_en_operaciones
            vis_op = s.get('visible_en_operaciones')
            
            if vis_op is None or not vis_op:
                # No visible en operaciones - excluir
                continue
            
            system_type = (s.get('system_type') or s.get('system_type_normalized') or '').upper()
            
            # Solo incluir sistemas de Tesorería (SoftRestaurant y MPRO)
            if system_type not in ['SOFTRESTAURANT', 'SR', 'MANAGEMENTPRO', 'MPRO']:
                continue
            
            if system_type in ['SOFTRESTAURANT', 'SR']:
                fuente = 'SOFTRESTAURANT'
            elif system_type in ['MANAGEMENTPRO', 'MPRO']:
                fuente = 'MPRO'
            else:
                fuente = system_type or 'UNKNOWN'
            
            sucursales.append({
                "id": s.get('id'),
                "nombre": s.get('name') or s.get('nombre', ''),
                "fuente": fuente,
                "system_type": system_type,
                "activo": s.get('active', True)
            })
        
        logger.info(f"[TESORERIA][REGISTRY_FALLBACK] Obtenidos {len(sucursales)} servidores operativos desde server_registry")
        
    except Exception as e:
        logger.error(f"[TESORERIA][REGISTRY_ERROR] Error en fallback server_registry: {e}")
    
    return sucursales


@router.get("/sucursales")
async def listar_sucursales(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista las sucursales/servidores OPERATIVOS para consultar Cortes Z.
    
    P1-FASE4A: Usa EDARSAHUB como fuente primaria.
    FASE T2.2: Fallback migrado a server_registry.py (elimina MongoDB).
    Solo devuelve servidores con visible_en_operaciones = True.
    """
    try:
        sucursales = await get_tesoreria_sucursales_operativas()
        
        return {"sucursales": sucursales}
        
    except Exception as e:
        logger.error(f"Error listando sucursales operativas: {e}")
        return {
            "sucursales": [],
            "error": "No se pudo obtener la lista de servidores operativos",
            "advertencia": str(e)
        }
