"""
API Router para Tesorería - Cuadre de Cortes Z
PROTEGIDO CON RBAC (Fase 3.1)
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
from .repository_cortes_z import get_cortes_z_repository
from .repository_cuadres_z import get_cuadres_repository, calcular_fecha_deposito_esperada

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
    Lista los Cortes Z disponibles de todas las fuentes (SoftRestaurant + MPRO).
    PROTEGIDO: Filtra por empresas_permitidas del usuario.
    Incluye indicador si ya tiene cuadre registrado.
    
    REFACTORIZADO 2025-12-27: 
    - Eliminado fallback a datos DEMO
    - Usa server_registry centralizado para conexiones
    - Soporta filtro por server_id
    """
    try:
        # RBAC Fase 3.1: Obtener sucursales permitidas
        sucursales_permitidas = await get_user_sucursales_permitidas(current_user)
        
        repo_cuadres = await get_cuadres_repository()
        repo_cortes = await get_cortes_z_repository()
        
        # Consultar cortes desde SQL usando el registry centralizado
        if server_id:
            # Filtrar por servidor específico
            result = await repo_cortes.get_cortes_z_by_server_id(server_id, fecha_inicio, fecha_fin)
            if result.query_executed and result.status.is_success():
                cortes = result.data
                fuente = "SQL_REAL"
                fuentes_detalle = [result.to_dict()]
            else:
                # Error de conexión - reportar claramente, NO usar datos falsos
                return {
                    "cortes": [],
                    "total": 0,
                    "fecha_consulta": datetime.utcnow().isoformat(),
                    "fuente": "SQL_ERROR",
                    "error": result.error_message if hasattr(result, 'error_message') else "Error consultando servidor",
                    "fuentes_detalle": [result.to_dict()],
                    "advertencia": f"No se pudo conectar al servidor {server_id}. Verifique la configuración en Servidores."
                }
        else:
            # Consultar todos los servidores activos
            result = await repo_cortes.get_all_cortes_z_with_status(fecha_inicio, fecha_fin)
            cortes = result.get('cortes', [])
            fuente = result.get('data_source', 'SQL_REAL')
            fuentes_detalle = result.get('fuentes_detalle', [])
            
            # Si no hay servidores configurados o todos fallaron
            if not cortes and result.get('estado_general') in ['NO_SERVERS', 'SOURCE_UNREACHABLE']:
                return {
                    "cortes": [],
                    "total": 0,
                    "fecha_consulta": datetime.utcnow().isoformat(),
                    "fuente": "SQL_ERROR",
                    "fuentes_detalle": fuentes_detalle,
                    "advertencia": result.get('advertencia', 'No se pudieron consultar los servidores SQL. Verifique la configuración.')
                }
        
        # RBAC Fase 3.1: Filtrar por sucursales permitidas
        if sucursales_permitidas:
            cortes = filtrar_cortes_por_permisos(cortes, sucursales_permitidas)
        
        # Filtrar por sucursal si se especifica (filtro manual del usuario)
        if sucursal:
            cortes = [c for c in cortes if sucursal.lower() in c.get('sucursal_id', '').lower()]
        
        # Verificar cuáles ya tienen cuadre
        for corte in cortes:
            cuadre = await repo_cuadres.obtener_cuadre_por_folio(
                corte['folio_corte'],
                corte['sucursal_id']
            )
            corte['tiene_cuadre'] = cuadre is not None
            corte['cuadre_id'] = cuadre.get('id') if cuadre else None
            corte['estado_cuadre'] = cuadre.get('estado') if cuadre else None
            corte['fecha_deposito_esperada'] = calcular_fecha_deposito_esperada(corte['fecha_corte'])
        
        response = {
            "cortes": cortes,
            "total": len(cortes),
            "fecha_consulta": datetime.utcnow().isoformat(),
            "fuente": fuente
        }
        
        # Incluir detalle de fuentes si hay advertencias
        if fuentes_detalle:
            errores = [f for f in fuentes_detalle if f.get('status') not in ['SUCCESS_WITH_DATA', 'SUCCESS_EMPTY']]
            if errores:
                response['fuentes_con_error'] = len(errores)
                response['fuentes_detalle'] = fuentes_detalle
        
        return response
        
    except Exception as e:
        logger.error(f"Error listando cortes Z: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cortes-z/{sucursal}/{folio}")
async def obtener_corte_z(
    sucursal: str,
    folio: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene un corte Z específico por sucursal y folio"""
    try:
        repo_cortes = await get_cortes_z_repository()
        
        # Buscar en SoftRestaurant
        if sucursal.upper() in ['CIENFUEGOS', 'LA_ESTELAR', '130_MERIDA']:
            cortes = await repo_cortes.get_cortes_z_softrestaurant(
                sucursal.upper(),
                folio=folio
            )
        else:
            # Buscar en MPRO
            cortes = await repo_cortes.get_cortes_z_mpro(sucursal.upper())
            cortes = [c for c in cortes if c['folio_corte'] == folio]
        
        if not cortes:
            raise HTTPException(status_code=404, detail="Corte Z no encontrado")
        
        corte = cortes[0]
        corte['fecha_deposito_esperada'] = calcular_fecha_deposito_esperada(corte['fecha_corte'])
        
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
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: Dict = Depends(get_current_user)
):
    """Lista los cuadres registrados con filtros"""
    try:
        repo = await get_cuadres_repository()
        cuadres = await repo.listar_cuadres(
            estado=estado,
            sucursal_id=sucursal_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limit=limit,
            skip=skip
        )
        
        return {
            "cuadres": cuadres,
            "total": len(cuadres),
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        logger.error(f"Error listando cuadres: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuadres/resumen")
async def obtener_resumen_cuadres(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene resumen estadístico de cuadres"""
    try:
        repo = await get_cuadres_repository()
        resumen = await repo.obtener_resumen(fecha_inicio, fecha_fin)
        
        return {
            "resumen": resumen,
            "fecha_consulta": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error obteniendo resumen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cuadres/{cuadre_id}")
async def obtener_cuadre(
    cuadre_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene un cuadre específico por ID"""
    try:
        repo = await get_cuadres_repository()
        cuadre = await repo.obtener_cuadre(cuadre_id)
        
        if not cuadre:
            raise HTTPException(status_code=404, detail="Cuadre no encontrado")
        
        return cuadre
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo cuadre: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cuadres")
async def crear_cuadre(
    data: dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo cuadre para un Corte Z.
    El corte_z debe incluir los datos del corte a cuadrar.
    """
    from core.auditoria_helpers import registrar_auditoria_tesoreria
    
    try:
        repo = await get_cuadres_repository()
        
        # Verificar que no exista ya un cuadre para este corte
        corte_z = data.get('corte_z', {})
        folio_corte = corte_z.get('folio_corte')
        sucursal_id = corte_z.get('sucursal_id')
        
        if corte_z:
            existente = await repo.obtener_cuadre_por_folio(folio_corte, sucursal_id)
            if existente:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un cuadre para este corte (ID: {existente['id']})"
                )
        
        user_id = current_user.get('sub') or current_user.get('email')
        cuadre = await repo.crear_cuadre(data, user_id)
        
        # Calcular si hay descuadre
        diferencia = data.get('conteo_efectivo', {}).get('diferencia', 0) or 0
        tiene_descuadre = abs(diferencia) > 0
        
        # Registrar auditoría
        await registrar_auditoria_tesoreria(
            current_user=current_user,
            accion='CONFIRM',
            corte_id=cuadre.get('id'),
            folio_corte=folio_corte,
            sucursal_id=sucursal_id,
            valor_nuevo={
                'efectivo_contado': data.get('conteo_efectivo', {}).get('total_contado'),
                'diferencia': diferencia,
                'estado': cuadre.get('estado')
            },
            tiene_descuadre=tiene_descuadre,
            motivo='Crear cuadre de Corte Z'
        )
        
        return {
            "message": "Cuadre creado exitosamente",
            "cuadre": cuadre
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando cuadre: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cuadres/{cuadre_id}")
async def actualizar_cuadre(
    cuadre_id: str,
    data: dict,
    current_user: Dict = Depends(get_current_user)
):
    """Actualiza un cuadre existente (conteo, ficha de depósito, observaciones)"""
    from core.auditoria_helpers import registrar_auditoria_tesoreria
    
    try:
        repo = await get_cuadres_repository()
        
        # Obtener cuadre anterior para auditoría
        cuadre_anterior = await repo.obtener_cuadre(cuadre_id)
        
        cuadre = await repo.actualizar_cuadre(cuadre_id, data)
        
        if not cuadre:
            raise HTTPException(status_code=404, detail="Cuadre no encontrado")
        
        # Registrar auditoría de ajuste
        await registrar_auditoria_tesoreria(
            current_user=current_user,
            accion='EDIT',
            corte_id=cuadre_id,
            folio_corte=cuadre.get('corte_z', {}).get('folio_corte'),
            sucursal_id=cuadre.get('corte_z', {}).get('sucursal_id'),
            valor_anterior={
                'estado': cuadre_anterior.get('estado') if cuadre_anterior else None,
                'diferencia': cuadre_anterior.get('conteo_efectivo', {}).get('diferencia') if cuadre_anterior else None
            } if cuadre_anterior else None,
            valor_nuevo={
                'estado': cuadre.get('estado'),
                'diferencia': data.get('conteo_efectivo', {}).get('diferencia')
            },
            motivo='Ajustar cuadre existente'
        )
        
        return {
            "message": "Cuadre actualizado exitosamente",
            "cuadre": cuadre
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando cuadre: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cuadres/{cuadre_id}")
async def eliminar_cuadre(
    cuadre_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Elimina un cuadre"""
    try:
        repo = await get_cuadres_repository()
        eliminado = await repo.eliminar_cuadre(cuadre_id)
        
        if not eliminado:
            raise HTTPException(status_code=404, detail="Cuadre no encontrado")
        
        return {"message": "Cuadre eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando cuadre: {e}")
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
    """
    try:
        repo = await get_cuadres_repository()
        cuadre = await repo.obtener_cuadre(cuadre_id)
        
        if not cuadre:
            raise HTTPException(status_code=404, detail="Cuadre no encontrado")
        
        fecha_venta = cuadre['corte_z']['fecha_corte']
        fecha_deposito = data.get('fecha_deposito')
        importe_deposito = float(data.get('importe', 0))
        monto_esperado = cuadre['monto_esperado']
        
        # Validar fecha
        from .repository_cuadres_z import validar_fecha_deposito
        fecha_valida = validar_fecha_deposito(fecha_venta, fecha_deposito)
        
        # Validar importe (tolerancia de $5)
        diferencia = abs(importe_deposito - monto_esperado)
        importe_valido = diferencia <= 5
        
        # Actualizar ficha en el cuadre
        ficha_data = {
            'fecha_deposito': fecha_deposito,
            'banco': data.get('banco'),
            'referencia': data.get('referencia'),
            'cuenta': data.get('cuenta'),
            'sucursal_banco': data.get('sucursal_banco'),
            'importe': importe_deposito,
            'archivo_url': data.get('archivo_url'),
            'ocr_validado': True,
            'ocr_data': data
        }
        
        update_data = {
            'ficha_deposito': ficha_data
        }
        
        # Determinar estado
        if fecha_valida and importe_valido:
            update_data['estado'] = 'CUADRADO'
        elif importe_deposito > 0:
            update_data['estado'] = 'DESCUADRE'
        
        cuadre_actualizado = await repo.actualizar_cuadre(cuadre_id, update_data)
        
        return {
            "validacion": {
                "fecha_valida": fecha_valida,
                "fecha_esperada": calcular_fecha_deposito_esperada(fecha_venta),
                "importe_valido": importe_valido,
                "monto_esperado": monto_esperado,
                "diferencia": diferencia
            },
            "cuadre": cuadre_actualizado
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validando ficha: {e}")
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
    fuente_usada = "EDARSAHUB"
    
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
        fuente_usada = "SERVER_REGISTRY_FALLBACK"
    
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
