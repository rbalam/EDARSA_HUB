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

from core.security import get_current_user
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
    RepositoryCuadresZEdarsahub,
)
from .tesoreria_access import (
    TES_CUADRES_Z_CREAR,
    TES_CUADRES_Z_EDITAR,
    TES_CUADRES_Z_ELIMINAR,
    TES_CUADRES_Z_VALIDAR,
    TES_CUADRES_Z_VER,
    require_tesoreria_access_scope,
)

router = APIRouter(prefix="/finanzas/tesoreria", tags=["Tesorería"])
logger = logging.getLogger(__name__)



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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_VER)
        if server_id:
            scope.require_server_id(server_id)

        # FINANZAS-TESORERIA-SQL-001: Usar repositorio SQL
        repo_cortes = get_cortes_caja_repository_sql()
        repo_cuadres = get_cuadres_z_repository_sql()
        
        # Inicializar variables de estado
        source_status = 'FRESH'
        advertencia = None
        
        # Consultar cortes desde EDARSAHUB SQL (NO en vivo)
        if server_id:
            # Filtrar por servidor específico
            try:
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
                    'source_status': 'FRESH',
                    'row_count': len(cortes)
                }]
            except Exception as e:
                logger.error(f"[CORTES_Z_SQL] Error conexión EDARSAHUB (server_id={server_id}): {e}")
                cortes = []
                fuente = "EDARSAHUB_SQL"
                source_status = 'ERROR'
                fuentes_detalle = [{
                    'status': 'EDARSAHUB_UNREACHABLE',
                    'source_type': 'EDARSAHUB_SQL',
                    'source_id': 'Finanzas_CortesCaja',
                    'source_status': 'ERROR',
                    'row_count': 0,
                    'error_message': str(e)[:200]
                }]
                advertencia = f"EDARSAHUB SQL no disponible: {str(e)[:100]}"
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
            source_status = result.get('source_status', 'UNKNOWN')
            advertencia = result.get('advertencia')
        
        # ARQUITECTURA SQL-FIRST: Si EDARSAHUB no respondió, retornar estado controlado
        # NUNCA error 500 por falla de infraestructura externa
        if source_status == 'ERROR':
            logger.warning("[CORTES_Z_SQL] EDARSAHUB no disponible - retornando estado controlado")
            return {
                "cortes": [],
                "total": 0,
                "fecha_consulta": datetime.utcnow().isoformat(),
                "fuente": fuente,
                "source_type": "EDARSAHUB_SQL",
                "source_status": "EDARSAHUB_UNREACHABLE",
                "fuentes_detalle": fuentes_detalle,
                "advertencia": advertencia or "EDARSAHUB SQL no está respondiendo temporalmente."
            }
        
        # Defensa en profundidad: solo registros del alcance resuelto.
        cortes = scope.filter_records(cortes)
        
        # Filtrar por sucursal si se especifica (filtro manual del usuario)
        if sucursal:
            cortes = [c for c in cortes if sucursal.lower() in c.get('sucursal_nombre', '').lower()]
        
        # Verificar cuáles ya tienen cuadre y calcular fecha depósito
        for corte in cortes:
            # Buscar si existe cuadre en SQL
            filtros_busqueda = {
                'unidad_negocio_pk': corte.get('sucursal_id'),
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
            "source_type": "EDARSAHUB_SQL",
            "source_status": source_status if source_status else "FRESH",
            "fuentes_detalle": fuentes_detalle
        }
        
        logger.info(f"[CORTES_Z_SQL] Listados {len(cortes)} cortes desde EDARSAHUB SQL")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CORTES_Z_SQL] Error inesperado listando cortes: {e}")
        # Retornar estado controlado en lugar de error 500
        return {
            "cortes": [],
            "total": 0,
            "fecha_consulta": datetime.utcnow().isoformat(),
            "fuente": "EDARSAHUB_SQL",
            "source_type": "EDARSAHUB_SQL",
            "source_status": "ERROR",
            "fuentes_detalle": [{
                'status': 'ERROR',
                'source_type': 'EDARSAHUB_SQL',
                'source_id': 'Finanzas_CortesCaja',
                'error_message': str(e)[:200]
            }],
            "advertencia": f"Error interno consultando EDARSAHUB SQL: {str(e)[:100]}"
        }


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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_VER)
        repo_cortes = get_cortes_caja_repository_sql()
        
        # Buscar en EDARSAHUB SQL
        filtros = {
            'unidad_negocio_nombre': sucursal,
            'limit': 100
        }
        cortes = repo_cortes.listar_cortes_caja(filtros)
        cortes = scope.filter_records(cortes)

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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_VER)
        if server_id:
            scope.require_server_id(server_id)
        if sucursal_id:
            scope.require_unit_identifier(sucursal_id)

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
        
        # Filtrar por server_id o unidad_negocio_pk (SQL directo, sin MongoDB)
        if server_id:
            logger.info(f"[CUADRES_SQL] Filtrando por server_id={server_id}")
            cuadres = repo.listar_cuadres_z_por_server_id(server_id, filtros)
        elif sucursal_id:
            filtros['unidad_negocio_pk'] = sucursal_id
            cuadres = repo.listar_cuadres_z(filtros)
        else:
            if not scope.global_access:
                filtros['unidades_permitidas'] = sorted(scope.unit_ids)
            cuadres = repo.listar_cuadres_z(filtros)

        cuadres = scope.filter_records(cuadres)

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
    except HTTPException:
        raise
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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_VER)
        if server_id:
            scope.require_server_id(server_id)

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
            if not scope.global_access:
                filtros['unidades_permitidas'] = sorted(scope.unit_ids)
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
    except HTTPException:
        raise
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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_VER)

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

        scope.require_record(cuadre)

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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_CREAR)

        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()

        corte_z = data.get('corte_z', {})
        canonical_unit = scope.require_record(corte_z)
        user_id = current_user.get('sub') or current_user.get('email')
        user_nombre = current_user.get('nombre') or current_user.get('email')
        
        # Preparar datos para repositorio SQL
        cuadre_data = {
            'unidad_negocio_pk': canonical_unit.unidad_negocio_pk,
            'unidad_negocio_nombre': canonical_unit.unidad_negocio_nombre,
            'empresa_id': canonical_unit.empresa_id or None,
            'server_id': canonical_unit.server_id,
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
            sucursal_id=cuadre_data['unidad_negocio_pk'],
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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_EDITAR)

        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        try:
            cuadre_id_int = int(cuadre_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de cuadre inválido")
        
        existing = repo.obtener_cuadre_z(cuadre_id_int)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Cuadre no encontrado",
            )
        scope.require_record(existing)

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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_ELIMINAR)

        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        try:
            cuadre_id_int = int(cuadre_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de cuadre inválido")
        
        existing = repo.obtener_cuadre_z(cuadre_id_int)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Cuadre no encontrado",
            )
        scope.require_record(existing)

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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_EDITAR)
        repo = get_cuadres_z_repository_sql()

        try:
            cuadre_id_int = int(cuadre_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="ID de cuadre inválido",
            )

        existing = repo.obtener_cuadre_z(cuadre_id_int)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Cuadre no encontrado",
            )
        scope.require_record(existing)

        # Leer archivo
        contents = await file.read()
        
        # NOTA: OCR simulado (ver TODO). No se persiste el archivo en disco local
        # del pod (incompatible con despliegue). Al integrar OCR real, usar
        # almacenamiento de objetos (Emergent Object Storage).
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{cuadre_id}_{timestamp}_{file.filename}"
        
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
            "filepath": filename
        }
    except HTTPException:
        raise
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
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_VALIDAR)

        # FINANZAS-TESORERIA-MONGO-002: Usar repositorio SQL
        repo = get_cuadres_z_repository_sql()
        
        try:
            cuadre_id_int = int(cuadre_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de cuadre inválido")
        
        cuadre = repo.obtener_cuadre_z(cuadre_id_int)
        
        if not cuadre:
            raise HTTPException(status_code=404, detail="Cuadre no encontrado")

        scope.require_record(cuadre)

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


@router.get("/sucursales")
async def listar_sucursales(
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista las sucursales/servidores OPERATIVOS para consultar Cortes Z.
    
    Fuente única: catálogo canónico de unidades en EDARSAHUB SQL.
    Sin fallback, fuentes paralelas ni conexiones directas a POS.
    Solo devuelve unidades autorizadas por el alcance RBAC efectivo.
    """
    try:
        scope = require_tesoreria_access_scope(current_user, TES_CUADRES_Z_VER)
        return {"sucursales": scope.to_sucursales()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando sucursales operativas: {e}")
        return {
            "sucursales": [],
            "error": "No se pudo obtener la lista de servidores operativos",
            "advertencia": str(e)
        }
