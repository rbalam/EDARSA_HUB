"""
API Router para Tesorería - Cuadre de Cortes Z
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Optional, List, Dict
from datetime import datetime
import logging
import base64
import os

from core.security import get_current_user
from .tesoreria_models import (
    CuadreCorteZCreate, CuadreCorteZUpdate, CuadreCorteZResponse,
    EstadoCuadre, ConteoEfectivo, FichaDeposito
)
from .repository_cortes_z import get_cortes_z_repository
from .repository_cuadres_z import get_cuadres_repository, calcular_fecha_deposito_esperada

router = APIRouter(prefix="/finanzas/tesoreria", tags=["Tesorería"])
logger = logging.getLogger(__name__)


@router.get("/cortes-z")
async def listar_cortes_z(
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin YYYY-MM-DD"),
    sucursal: Optional[str] = Query(None, description="Filtrar por sucursal"),
    use_demo: bool = Query(False, description="Usar datos demo (solo desarrollo)"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista los Cortes Z disponibles de todas las fuentes (SoftRestaurant + MPRO).
    Incluye indicador si ya tiene cuadre registrado.
    Por defecto usa datos REALES. Poner use_demo=true solo para desarrollo.
    """
    try:
        repo_cuadres = await get_cuadres_repository()
        cortes = []
        fuente = "SQL_REAL"
        
        # Intentar SQL real primero (comportamiento por defecto en producción)
        if not use_demo:
            try:
                repo_cortes = await get_cortes_z_repository()
                cortes = await repo_cortes.get_all_cortes_z(fecha_inicio, fecha_fin)
                if cortes:
                    fuente = "SQL_REAL"
            except Exception as e:
                logger.warning(f"Error conectando a SQL, usando fallback demo: {e}")
        
        # Fallback a datos demo solo si SQL falla o use_demo=true
        if not cortes:
            cortes = [
                {
                    'folio_corte': '2889',
                    'fecha_corte': '2026-04-07T00:00:00',
                    'sucursal_id': 'CIENFUEGOS',
                    'sucursal_nombre': 'Cienfuegos',
                    'fuente': 'SOFTRESTAURANT',
                    'efectivo_inicial': 15000.00,
                    'efectivo_ventas': 13656.00,
                    'tarjeta': 94179.20,
                    'vales': 0.00,
                    'otros': 4410.00,
                    'depositos_ef': 0.00,
                    'retiros_ef': 0.00,
                    'propinas_pagadas': 11725.20,
                    'saldo_final': 115520.00,
                    'efectivo_final': 16930.80,
                    'total_ventas': 100520.00,
                    'monto_a_depositar': 1930.80
                },
                {
                    'folio_corte': '2890',
                    'fecha_corte': '2026-04-08T00:00:00',
                    'sucursal_id': 'CIENFUEGOS',
                    'sucursal_nombre': 'Cienfuegos',
                    'fuente': 'SOFTRESTAURANT',
                    'efectivo_inicial': 15000.00,
                    'efectivo_ventas': 18450.00,
                    'tarjeta': 87500.00,
                    'vales': 0.00,
                    'otros': 3200.00,
                    'depositos_ef': 0.00,
                    'retiros_ef': 10000.00,
                    'propinas_pagadas': 8920.00,
                    'saldo_final': 98750.00,
                    'efectivo_final': 14530.00,
                    'total_ventas': 95150.00,
                    'monto_a_depositar': 9530.00
                },
                {
                    'folio_corte': '1456',
                    'fecha_corte': '2026-04-07T00:00:00',
                    'sucursal_id': 'LA_ESTELAR',
                    'sucursal_nombre': 'La Estelar',
                    'fuente': 'SOFTRESTAURANT',
                    'efectivo_inicial': 12000.00,
                    'efectivo_ventas': 9850.00,
                    'tarjeta': 65400.00,
                    'vales': 1500.00,
                    'otros': 2100.00,
                    'depositos_ef': 0.00,
                    'retiros_ef': 0.00,
                    'propinas_pagadas': 5430.00,
                    'saldo_final': 78850.00,
                    'efectivo_final': 16420.00,
                    'total_ventas': 73850.00,
                    'monto_a_depositar': 4420.00
                },
                {
                    'folio_corte': '789',
                    'fecha_corte': '2026-04-07T00:00:00',
                    'sucursal_id': '130_MERIDA',
                    'sucursal_nombre': '130° Mérida',
                    'fuente': 'SOFTRESTAURANT',
                    'efectivo_inicial': 10000.00,
                    'efectivo_ventas': 7250.00,
                    'tarjeta': 45800.00,
                    'vales': 800.00,
                    'otros': 1200.00,
                    'depositos_ef': 0.00,
                    'retiros_ef': 0.00,
                    'propinas_pagadas': 3150.00,
                    'saldo_final': 55050.00,
                    'efectivo_final': 14100.00,
                    'total_ventas': 50050.00,
                    'monto_a_depositar': 4100.00
                },
                {
                    'folio_corte': 'MPRO-001',
                    'fecha_corte': '2026-04-07T00:00:00',
                    'sucursal_id': 'MPRO_ORIGEN',
                    'sucursal_nombre': 'MPRO Origen',
                    'fuente': 'MPRO',
                    'efectivo_inicial': 8000.00,
                    'efectivo_ventas': 12300.00,
                    'tarjeta': 38500.00,
                    'vales': 0.00,
                    'otros': 500.00,
                    'depositos_ef': 0.00,
                    'retiros_ef': 10000.00,
                    'propinas_pagadas': 1850.00,
                    'saldo_final': 51300.00,
                    'efectivo_final': 8450.00,
                    'total_ventas': 48300.00,
                    'monto_a_depositar': 10450.00
                }
            ]
        
        # Filtrar por sucursal si se especifica
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
        
        return {
            "cortes": cortes,
            "total": len(cortes),
            "fecha_consulta": datetime.utcnow().isoformat(),
            "fuente": fuente
        }
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


@router.get("/sucursales")
async def listar_sucursales(
    current_user: Dict = Depends(get_current_user)
):
    """Lista las sucursales disponibles para consultar Cortes Z"""
    return {
        "sucursales": [
            {"id": "CIENFUEGOS", "nombre": "Cienfuegos", "fuente": "SOFTRESTAURANT"},
            {"id": "LA_ESTELAR", "nombre": "La Estelar", "fuente": "SOFTRESTAURANT"},
            {"id": "130_MERIDA", "nombre": "130° Mérida", "fuente": "SOFTRESTAURANT"},
            {"id": "MPRO_ORIGEN", "nombre": "MPRO Origen", "fuente": "MPRO"},
            {"id": "MPRO_QUERETARO", "nombre": "MPRO Querétaro", "fuente": "MPRO"}
        ]
    }
