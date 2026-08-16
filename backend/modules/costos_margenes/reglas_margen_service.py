from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
COSTOS-ALERTAS-001-C: Service para Reglas de Margen Esperado

EDARSAHUB SQL es el cerebro. CERO MongoDB.

Lógica de negocio para:
- Validación de reglas
- Resolución jerárquica: Producto > Subfamilia > Familia > Grupo
- Cálculo de severidad
"""

from datetime import datetime
from typing import Optional, List, Dict, Tuple
from decimal import Decimal
import logging

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG
from modules.costos_margenes.configuracion_repository import resolver_configuracion_efectiva
from modules.costos_margenes.reglas_margen_repository import (
    listar_reglas,
    obtener_regla_por_id,
    verificar_duplicado_regla,
    crear_regla,
    actualizar_regla,
    desactivar_regla,
    resolver_regla_aplicable,
    obtener_umbrales_severidad,
    determinar_severidad,
    obtener_estadisticas_reglas,
    cargar_reglas_margen_vigentes,
)

logger = logging.getLogger(__name__)


def _get_conn() -> Tuple[str, int, str, str, str]:
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
    )


# =============================================================================
# CONSTANTES Y VALIDACIÓN
# =============================================================================

def _safe_decimal(value):
    """
    Convierte valores numericos SQL a Decimal sin introducir
    defaults de negocio.

    None permanece None.
    """
    if value is None:
        return None

    if isinstance(value, Decimal):
        return value

    return Decimal(str(value))


NIVELES_APLICACION_VALIDOS = ['GRUPO', 'FAMILIA', 'SUBFAMILIA', 'PRODUCTO']
SEVERIDADES_VALIDAS = ['INFORMATIVA', 'MEDIA', 'ALTA', 'CRITICA']


class AlertasMargenError(Exception):
    """Excepción personalizada para errores de alertas de margen."""
    def __init__(self, mensaje: str, codigo: str = 'ERROR'):
        self.mensaje = mensaje
        self.codigo = codigo
        super().__init__(self.mensaje)


def _validar_nivel_aplicacion(nivel: str) -> None:
    """Valida que el nivel de aplicación sea válido."""
    if nivel not in NIVELES_APLICACION_VALIDOS:
        raise AlertasMargenError(
            f"Nivel de aplicación inválido: {nivel}. Valores válidos: {NIVELES_APLICACION_VALIDOS}",
            'NIVEL_INVALIDO'
        )


def _validar_severidad(severidad: str) -> None:
    """Valida que la severidad sea válida."""
    if severidad not in SEVERIDADES_VALIDAS:
        raise AlertasMargenError(
            f"Severidad inválida: {severidad}. Valores válidos: {SEVERIDADES_VALIDAS}",
            'SEVERIDAD_INVALIDA'
        )


def _validar_porcentaje(valor: float, nombre: str, minimo: float = 0, maximo: float = 100) -> None:
    """Valida que un porcentaje esté en rango válido."""
    if valor < minimo or valor > maximo:
        raise AlertasMargenError(
            f"{nombre} debe estar entre {minimo}% y {maximo}%. Valor recibido: {valor}%",
            'PORCENTAJE_INVALIDO'
        )


def _validar_vigencia(fecha_inicio: Optional[datetime], fecha_fin: Optional[datetime]) -> None:
    """Valida que las fechas de vigencia sean coherentes."""
    if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
        raise AlertasMargenError(
            "La fecha de fin debe ser posterior a la fecha de inicio",
            'VIGENCIA_INVALIDA'
        )


# =============================================================================
# SERVICIO DE REGLAS
# =============================================================================

def listar_reglas_margen(
    nivel_aplicacion: Optional[str] = None,
    solo_activas: bool = True,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
) -> Dict:
    """
    Lista reglas de margen con filtros.

    Args:
        nivel_aplicacion: Filtrar por nivel (GRUPO, FAMILIA, SUBFAMILIA, PRODUCTO)
        solo_activas: Solo reglas activas y vigentes
        empresa_id: Filtrar por empresa
        sucursal_id: Filtrar por sucursal
        page: Página
        page_size: Tamaño de página

    Returns:
        Dict con reglas y metadatos de paginación
    """
    if nivel_aplicacion:
        _validar_nivel_aplicacion(nivel_aplicacion)

    reglas, total = listar_reglas(
        nivel_aplicacion=nivel_aplicacion,
        solo_activas=solo_activas,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        server_id=server_id,
        page=page,
        page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return {
        'reglas': reglas,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


def obtener_regla(regla_id: str) -> Dict:
    """
    Obtiene una regla por su ID.

    Args:
        regla_id: UUID de la regla

    Returns:
        Dict con la regla

    Raises:
        AlertasMargenError si no existe
    """
    regla = obtener_regla_por_id(regla_id)
    if not regla:
        raise AlertasMargenError(f"Regla no encontrada: {regla_id}", 'REGLA_NO_ENCONTRADA')
    return regla


def crear_regla_margen(
    nivel_aplicacion: str,
    entidad_codigo: str,
    margen_esperado: float,
    producto_id: Optional[int] = None,
    costo_maximo: Optional[float] = None,
    utilidad_minima: Optional[float] = None,
    severidad_base: str = 'MEDIA',
    descripcion: Optional[str] = None,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    creado_por: str = 'SISTEMA'
) -> Dict:
    """
    Crea una nueva regla de margen esperado.

    Args:
        nivel_aplicacion: GRUPO, FAMILIA, SUBFAMILIA, PRODUCTO
        entidad_codigo: Código de la entidad según el nivel
        margen_esperado: Porcentaje de margen esperado (0-100)
        costo_maximo: Porcentaje máximo de costo (opcional)
        utilidad_minima: Porcentaje mínimo de utilidad (opcional)
        severidad_base: INFORMATIVA, MEDIA, ALTA, CRITICA
        descripcion: Descripción de la regla
        empresa_id: Empresa (opcional)
        sucursal_id: Sucursal (opcional)
        server_id: Servidor (opcional)
        fecha_inicio: Fecha de inicio de vigencia
        fecha_fin: Fecha de fin de vigencia
        creado_por: Usuario que crea

    Returns:
        Dict con la regla creada

    Raises:
        AlertasMargenError si hay error de validación
    """
    # Validaciones
    _validar_nivel_aplicacion(nivel_aplicacion)
    _validar_severidad(severidad_base)
    _validar_porcentaje(margen_esperado, 'Margen esperado')

    if costo_maximo is not None:
        _validar_porcentaje(costo_maximo, 'Costo máximo')

    if utilidad_minima is not None:
        _validar_porcentaje(utilidad_minima, 'Utilidad mínima', minimo=-100)

    _validar_vigencia(fecha_inicio, fecha_fin)

    if nivel_aplicacion == 'PRODUCTO':
        if producto_id is None or int(producto_id) <= 0:
            raise AlertasMargenError(
                "ProductoID canónico requerido para una nueva regla PRODUCTO",
                'PRODUCTO_ID_CANONICO_REQUERIDO'
            )

        conn = _get_conn()
        rows = execute_sql_query_params(
            *conn,
            "SELECT ProductoID FROM dbo.Producto_Catalogo WHERE ProductoID = %s",
            (int(producto_id),),
        )

        if not rows:
            raise AlertasMargenError(
                f"ProductoID canónico inexistente: {producto_id}",
                'PRODUCTO_ID_CANONICO_NO_EXISTE'
            )
    elif not entidad_codigo or not entidad_codigo.strip():
        raise AlertasMargenError(
            f"Debe especificar un código de entidad para nivel {nivel_aplicacion}",
            'ENTIDAD_REQUERIDA'
        )

    entidad_normalizada = (
        entidad_codigo.strip()
        if entidad_codigo
        else ''
    )

    # Verificar duplicado
    if verificar_duplicado_regla(
        nivel_aplicacion,
        entidad_normalizada,
        empresa_id,
        sucursal_id,
        producto_id=producto_id,
    ):
        raise AlertasMargenError(
            f"Ya existe una regla activa para {nivel_aplicacion}={entidad_codigo}",
            'REGLA_DUPLICADA'
        )

    # Crear regla
    regla = crear_regla(
        nivel_aplicacion=nivel_aplicacion,
        entidad_codigo=entidad_normalizada,
        margen_esperado=margen_esperado,
        producto_id=producto_id,
        costo_maximo=costo_maximo,
        utilidad_minima=utilidad_minima,
        severidad_base=severidad_base,
        descripcion=descripcion,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        server_id=server_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        creado_por=creado_por
    )

    logger.info(f"[ALERTAS_MARGEN_SERVICE] Regla creada: {regla['regla_id']} - {nivel_aplicacion}={entidad_codigo}")

    return regla


def actualizar_regla_margen(
    regla_id: str,
    margen_esperado: Optional[float] = None,
    costo_maximo: Optional[float] = None,
    utilidad_minima: Optional[float] = None,
    severidad_base: Optional[str] = None,
    descripcion: Optional[str] = None,
    fecha_fin: Optional[datetime] = None,
    modificado_por: str = 'SISTEMA'
) -> Dict:
    """
    Actualiza una regla de margen existente.

    Args:
        regla_id: UUID de la regla
        margen_esperado: Nuevo margen esperado
        costo_maximo: Nuevo costo máximo
        utilidad_minima: Nueva utilidad mínima
        severidad_base: Nueva severidad
        descripcion: Nueva descripción
        fecha_fin: Nueva fecha de fin
        modificado_por: Usuario que modifica

    Returns:
        Dict con la regla actualizada

    Raises:
        AlertasMargenError si hay error
    """
    # Verificar que existe
    regla_actual = obtener_regla_por_id(regla_id)
    if not regla_actual:
        raise AlertasMargenError(f"Regla no encontrada: {regla_id}", 'REGLA_NO_ENCONTRADA')

    # Validaciones
    if margen_esperado is not None:
        _validar_porcentaje(margen_esperado, 'Margen esperado')

    if costo_maximo is not None:
        _validar_porcentaje(costo_maximo, 'Costo máximo')

    if utilidad_minima is not None:
        _validar_porcentaje(utilidad_minima, 'Utilidad mínima', minimo=-100)

    if severidad_base:
        _validar_severidad(severidad_base)

    # Actualizar
    regla = actualizar_regla(
        regla_id=regla_id,
        margen_esperado=margen_esperado,
        costo_maximo=costo_maximo,
        utilidad_minima=utilidad_minima,
        severidad_base=severidad_base,
        descripcion=descripcion,
        fecha_fin=fecha_fin,
        modificado_por=modificado_por
    )

    logger.info(f"[ALERTAS_MARGEN_SERVICE] Regla actualizada: {regla_id}")

    return regla


def desactivar_regla_margen(regla_id: str, modificado_por: str = 'SISTEMA') -> Dict:
    """
    Desactiva una regla de margen.

    Args:
        regla_id: UUID de la regla
        modificado_por: Usuario que desactiva

    Returns:
        Dict con mensaje de éxito

    Raises:
        AlertasMargenError si no existe
    """
    if not desactivar_regla(regla_id, modificado_por):
        raise AlertasMargenError(f"Regla no encontrada: {regla_id}", 'REGLA_NO_ENCONTRADA')

    logger.info(f"[ALERTAS_MARGEN_SERVICE] Regla desactivada: {regla_id}")

    return {'mensaje': 'Regla desactivada correctamente', 'regla_id': regla_id}


# =============================================================================
# RESOLUCIÓN JERÁRQUICA
# =============================================================================

def resolver_margen_esperado(
    producto_id: Optional[int] = None,
    producto_clave: Optional[str] = None,
    subfamilia_codigo: Optional[str] = None,
    familia_codigo: Optional[str] = None,
    grupo_codigo: Optional[str] = None,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
    usuario_id: Optional[int] = None,
) -> Dict:
    """
    Resolucion canonica y atomica del margen efectivo.

    Precedencia efectiva del reporte:

        USUARIO
        > PRODUCTO
        > SUBFAMILIA
        > FAMILIA
        > GRUPO
        > UNIDAD
        > EMPRESA

    USUARIO representa exclusivamente un override personal
    previamente autorizado y persistido para el reporte.

    La configuracion personal permanece separada de las reglas
    organizacionales y no modifica la fuente de verdad empresarial.

    Si el usuario no tiene un margen personal configurado,
    la resolucion continua por la cascada canonica de negocio.

    Ningun consumidor debe reconstruir esta precedencia.
    No existen defaults funcionales hardcodeados.
    """

    unidad_pk = str(
        unidad_negocio_pk or ""
    ).strip()

    config_efectiva = None

    if unidad_pk and usuario_id is not None:
        config_efectiva = resolver_configuracion_efectiva(
            unidad_pk,
            usuario_id=usuario_id,
        )

        margen_config = config_efectiva.get(
            "margen_minimo_porcentaje"
        )

        fuente_config = (
            config_efectiva
            .get("fuentes", {})
            .get("margen_minimo_porcentaje")
        )

        if (
            usuario_id is not None
            and margen_config is not None
            and fuente_config == "USUARIO"
        ):
            margen_float = float(
                margen_config
            )

            resultado = {
                "regla": None,
                "fuente": "USUARIO",
                "margen_esperado": margen_float,
                "margen_efectivo": margen_float,
                "fuente_margen_efectivo": "USUARIO",
                "estado": "MARGEN_EFECTIVO_RESUELTO",
                "mensaje": (
                    "Margen efectivo resuelto desde "
                    "override personal autorizado"
                ),
                "empresa_id": config_efectiva.get(
                    "empresa_id"
                ),
                "unidad_negocio_pk": config_efectiva.get(
                    "unidad_negocio_pk"
                ),
                "usuario_id": usuario_id,
            }

            logger.debug(
                "[MARGEN_CANONICO] "
                "usuario=%s producto=%s subfamilia=%s "
                "familia=%s grupo=%s unidad=%s "
                "fuente=USUARIO margen=%s",
                usuario_id,
                producto_clave,
                subfamilia_codigo,
                familia_codigo,
                grupo_codigo,
                unidad_pk,
                margen_float,
            )

            return resultado

    resultado = resolver_regla_aplicable(
        producto_id=producto_id,
        producto_clave=producto_clave,
        subfamilia_codigo=subfamilia_codigo,
        familia_codigo=familia_codigo,
        grupo_codigo=grupo_codigo,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        server_id=server_id,
    )

    if resultado["fuente"] != "SIN_REGLA":
        margen = resultado.get(
            "margen_esperado"
        )

        resultado["margen_efectivo"] = margen
        resultado["fuente_margen_efectivo"] = (
            resultado["fuente"]
        )
        resultado["estado"] = (
            "MARGEN_EFECTIVO_RESUELTO"
        )
        resultado["usuario_id"] = usuario_id
        resultado["mensaje"] = (
            f"Margen efectivo resuelto desde "
            f"{resultado['fuente']}: {margen}%"
        )

        logger.debug(
            "[MARGEN_CANONICO] "
            "usuario=%s producto=%s subfamilia=%s "
            "familia=%s grupo=%s unidad=%s "
            "fuente=%s margen=%s",
            usuario_id,
            producto_clave,
            subfamilia_codigo,
            familia_codigo,
            grupo_codigo,
            unidad_pk,
            resultado["fuente"],
            margen,
        )

        return resultado

    if unidad_pk:
        if config_efectiva is None:
            config_efectiva = resolver_configuracion_efectiva(
                unidad_pk,
                usuario_id=usuario_id,
            )

        margen_config = config_efectiva.get(
            "margen_minimo_porcentaje"
        )

        fuente_config = (
            config_efectiva
            .get("fuentes", {})
            .get("margen_minimo_porcentaje")
        )

        if (
            margen_config is not None
            and fuente_config in {
                "UNIDAD",
                "EMPRESA",
            }
        ):
            margen_float = float(
                margen_config
            )

            resultado = {
                "regla": None,
                "fuente": fuente_config,
                "margen_esperado": margen_float,
                "margen_efectivo": margen_float,
                "fuente_margen_efectivo":
                    fuente_config,
                "estado":
                    "MARGEN_EFECTIVO_RESUELTO",
                "mensaje": (
                    f"Margen efectivo resuelto desde "
                    f"{fuente_config}: {margen_float}%"
                ),
                "empresa_id": config_efectiva.get(
                    "empresa_id"
                ),
                "unidad_negocio_pk":
                    config_efectiva.get(
                        "unidad_negocio_pk"
                    ),
                "usuario_id": usuario_id,
            }

            logger.debug(
                "[MARGEN_CANONICO] "
                "usuario=%s producto=%s subfamilia=%s "
                "familia=%s grupo=%s unidad=%s "
                "fuente=%s margen=%s",
                usuario_id,
                producto_clave,
                subfamilia_codigo,
                familia_codigo,
                grupo_codigo,
                unidad_pk,
                fuente_config,
                margen_float,
            )

            return resultado

    resultado["margen_efectivo"] = None
    resultado["fuente_margen_efectivo"] = None
    resultado["usuario_id"] = usuario_id
    resultado["estado"] = "SIN_MARGEN_EFECTIVO"
    resultado["mensaje"] = (
        "No existe override personal, regla especifica "
        "ni configuracion organizacional aplicable"
    )

    logger.debug(
        "[MARGEN_CANONICO] "
        "usuario=%s producto=%s subfamilia=%s "
        "familia=%s grupo=%s unidad=%s "
        "fuente=SIN_REGLA margen=None",
        usuario_id,
        producto_clave,
        subfamilia_codigo,
        familia_codigo,
        grupo_codigo,
        unidad_pk,
    )

    return resultado


def evaluar_margen_producto(
    margen_actual: float,
    producto_id: Optional[int] = None,
    producto_clave: Optional[str] = None,
    subfamilia_codigo: Optional[str] = None,
    familia_codigo: Optional[str] = None,
    grupo_codigo: Optional[str] = None,
    precio_venta: Optional[float] = None,
    costo_receta: Optional[float] = None,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
    usuario_id: Optional[int] = None,
) -> Dict:
    """
    Evalúa el margen de un producto contra su margen esperado y determina severidad.

    NOTA: Este es un endpoint de prueba. El motor de evaluación masiva
    se implementará en COSTOS-ALERTAS-001-E.

    Args:
        margen_actual: Margen actual del producto (%)
        producto_clave: Clave del producto
        subfamilia_codigo: Código de subfamilia
        familia_codigo: Código de familia
        grupo_codigo: Código de grupo
        precio_venta: Precio de venta
        costo_receta: Costo de receta
        empresa_id: Empresa
        sucursal_id: Sucursal
        server_id: Servidor

    Returns:
        Dict con evaluación completa
    """
    # Resolver regla aplicable
    regla_resultado = resolver_margen_esperado(
        producto_id=producto_id,
        producto_clave=producto_clave,
        subfamilia_codigo=subfamilia_codigo,
        familia_codigo=familia_codigo,
        grupo_codigo=grupo_codigo,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        server_id=server_id,
        unidad_negocio_pk=unidad_negocio_pk,
        usuario_id=usuario_id,
    )

    # Si no hay regla, no hay evaluación
    if regla_resultado['fuente'] == 'SIN_REGLA':
        return {
            'tiene_alerta': False,
            'estado': 'SIN_REGLA_MARGEN_ESPERADO',
            'mensaje': 'No hay regla de margen esperado configurada para este producto',
            'margen_actual': margen_actual,
            'margen_esperado': None,
            'diferencia_puntos': None,
            'severidad': None,
            'regla_aplicada': None,
            'fuente_regla': 'SIN_REGLA'
        }

    margen_esperado = regla_resultado['margen_esperado']
    diferencia_puntos = margen_esperado - margen_actual

    # Determinar si hay alerta
    tiene_alerta = diferencia_puntos > 0  # Margen actual está debajo del esperado

    # Calcular condiciones especiales
    utilidad_negativa = False
    costo_mayor_precio = False

    if precio_venta is not None and costo_receta is not None:
        utilidad = precio_venta - costo_receta
        utilidad_negativa = utilidad < 0
        costo_mayor_precio = costo_receta > precio_venta

    # Determinar severidad
    severidad = None
    if tiene_alerta:
        severidad = determinar_severidad(diferencia_puntos, utilidad_negativa, costo_mayor_precio)

    # Calcular pérdida por unidad
    perdida_por_unidad = None
    if tiene_alerta and precio_venta and costo_receta:
        utilidad_actual = precio_venta - costo_receta
        utilidad_esperada = precio_venta * (margen_esperado / 100)
        perdida_por_unidad = utilidad_esperada - utilidad_actual

    return {
        'tiene_alerta': tiene_alerta,
        'estado': 'ALERTA_MARGEN_BAJO' if tiene_alerta else 'MARGEN_OK',
        'mensaje': f"Margen actual ({margen_actual:.1f}%) está {diferencia_puntos:.1f} puntos debajo del esperado ({margen_esperado:.1f}%)" if tiene_alerta else f"Margen actual ({margen_actual:.1f}%) cumple o supera el esperado ({margen_esperado:.1f}%)",
        'margen_actual': margen_actual,
        'margen_esperado': margen_esperado,
        'diferencia_puntos': round(diferencia_puntos, 2) if diferencia_puntos else 0,
        'severidad': severidad,
        'utilidad_negativa': utilidad_negativa,
        'costo_mayor_precio': costo_mayor_precio,
        'perdida_por_unidad': round(perdida_por_unidad, 2) if perdida_por_unidad else None,
        'regla_aplicada': regla_resultado['regla'],
        'fuente_regla': regla_resultado['fuente']
    }


# =============================================================================
# ESTADÍSTICAS Y UMBRALES
# =============================================================================

def obtener_umbrales() -> List[Dict]:
    """
    Obtiene los umbrales de severidad configurados.

    Returns:
        Lista de umbrales
    """
    return obtener_umbrales_severidad()


def obtener_estadisticas() -> Dict:
    """
    Obtiene estadísticas de las reglas configuradas.

    Returns:
        Dict con estadísticas
    """
    return obtener_estadisticas_reglas()


def _seleccionar_regla_margen_desde_contexto(
    reglas: List[Dict],
    *,
    producto_id: Optional[int] = None,
    producto_clave: Optional[str] = None,
    subfamilia_codigo: Optional[str] = None,
    familia_codigo: Optional[str] = None,
    grupo_codigo: Optional[str] = None,
) -> Dict:
    """
    Seleccion semantica canonica de regla especifica.

    Unica precedencia:

        PRODUCTO
        > SUBFAMILIA
        > FAMILIA
        > GRUPO

    El repositorio solo carga datos.
    Esta funcion define la prioridad.

    Para reglas del mismo nivel conserva el desempate historico:
        Empresa especifica
        > Sucursal especifica
        > Server especifico
        > global
        > FechaCreacion DESC
    """

    niveles = (
        (
            "PRODUCTO",
            "producto_id",
            producto_id,
            False,
        ),
        (
            "PRODUCTO",
            "producto_clave",
            producto_clave,
            True,
        ),
        (
            "SUBFAMILIA",
            "subfamilia_codigo",
            subfamilia_codigo,
            False,
        ),
        (
            "FAMILIA",
            "familia_codigo",
            familia_codigo,
            False,
        ),
        (
            "GRUPO",
            "grupo_codigo",
            grupo_codigo,
            False,
        ),
    )

    def scope_rank(regla: Dict):
        return (
            0
            if regla.get("empresa_id") is not None
            else 1,
            0
            if regla.get("sucursal_id") is not None
            else 1,
            0
            if regla.get("server_id") is not None
            else 1,
        )

    for nivel, campo, valor, solo_legacy in niveles:
        if valor is None or str(valor).strip() == "":
            continue

        candidatos = [
            regla
            for regla in reglas
            if (
                str(
                    regla.get(
                        "nivel_aplicacion"
                    )
                    or ""
                ).upper()
                == nivel
                and (
                    not solo_legacy
                    or regla.get("producto_id") is None
                )
                and str(
                    regla.get(campo)
                    or ""
                )
                == str(valor)
            )
        ]

        if not candidatos:
            continue

        candidatos.sort(
            key=lambda regla: (
                scope_rank(regla),
                regla.get(
                    "fecha_creacion"
                ),
            ),
            reverse=False,
        )

        mejor_scope = scope_rank(
            candidatos[0]
        )

        mismo_scope = [
            regla
            for regla in candidatos
            if scope_rank(regla)
            == mejor_scope
        ]

        mismo_scope.sort(
            key=lambda regla: (
                regla.get(
                    "fecha_creacion"
                )
            ),
            reverse=True,
        )

        row = mismo_scope[0]

        margen = float(
            _safe_decimal(
                row.get(
                    "margen_esperado"
                )
            )
        )

        return {
            "regla": {
                "regla_id":
                    row.get(
                        "regla_id"
                    ),
                "nivel_aplicacion":
                    row.get(
                        "nivel_aplicacion"
                    ),
                "entidad_codigo":
                    row.get(campo),
                "margen_esperado":
                    margen,
                "costo_maximo":
                    (
                        float(
                            _safe_decimal(
                                row.get(
                                    "costo_maximo"
                                )
                            )
                        )
                        if row.get(
                            "costo_maximo"
                        )
                        is not None
                        else None
                    ),
                "utilidad_minima":
                    (
                        float(
                            _safe_decimal(
                                row.get(
                                    "utilidad_minima"
                                )
                            )
                        )
                        if row.get(
                            "utilidad_minima"
                        )
                        is not None
                        else None
                    ),
                "severidad_base":
                    row.get(
                        "severidad_base"
                    ),
                "descripcion":
                    row.get(
                        "descripcion"
                    ),
            },
            "fuente": nivel,
            "margen_esperado":
                margen,
        }

    return {
        "regla": None,
        "fuente": "SIN_REGLA",
        "margen_esperado": None,
    }


def resolver_margenes_esperados_batch(
    productos: List[Dict],
    *,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
    usuario_id: Optional[int] = None,
) -> List[Dict]:
    """
    Resuelve margen efectivo para un lote sin N+1.

    El batch NO define una segunda cascada.
    Reutiliza:
    - configuración efectiva;
    - selector semántico canónico de reglas.

    Resultado por producto:
    - margen_efectivo
    - fuente_margen_efectivo
    """

    items = list(
        productos or []
    )

    if not items:
        return []

    unidad_pk = str(
        unidad_negocio_pk or ""
    ).strip()

    config_efectiva = None

    if unidad_pk:
        config_efectiva = resolver_configuracion_efectiva(
            unidad_pk,
            usuario_id=usuario_id,
        )

    margen_config = (
        config_efectiva.get(
            "margen_minimo_porcentaje"
        )
        if config_efectiva
        else None
    )

    fuente_config = (
        config_efectiva
        .get("fuentes", {})
        .get(
            "margen_minimo_porcentaje"
        )
        if config_efectiva
        else None
    )

    if (
        usuario_id is not None
        and margen_config is not None
        and fuente_config == "USUARIO"
    ):
        margen_usuario = float(
            margen_config
        )

        return [
            {
                **item,
                "margen_efectivo":
                    margen_usuario,
                "fuente_margen_efectivo":
                    "USUARIO",
            }
            for item in items
        ]

    reglas = cargar_reglas_margen_vigentes(
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        server_id=server_id,
    )

    resultados = []

    for item in items:
        resultado_regla = (
            _seleccionar_regla_margen_desde_contexto(
                reglas,
                producto_id=item.get(
                    "producto_id"
                ),
                producto_clave=item.get(
                    "producto_clave"
                ),
                subfamilia_codigo=item.get(
                    "subfamilia_codigo"
                ),
                familia_codigo=item.get(
                    "familia_codigo"
                ),
                grupo_codigo=item.get(
                    "grupo_codigo"
                ),
            )
        )

        if (
            resultado_regla[
                "fuente"
            ]
            != "SIN_REGLA"
        ):
            resultados.append(
                {
                    **item,
                    "margen_efectivo":
                        resultado_regla[
                            "margen_esperado"
                        ],
                    "fuente_margen_efectivo":
                        resultado_regla[
                            "fuente"
                        ],
                }
            )

            continue

        if (
            margen_config is not None
            and fuente_config in {
                "UNIDAD",
                "EMPRESA",
            }
        ):
            resultados.append(
                {
                    **item,
                    "margen_efectivo":
                        float(
                            margen_config
                        ),
                    "fuente_margen_efectivo":
                        fuente_config,
                }
            )

            continue

        resultados.append(
            {
                **item,
                "margen_efectivo":
                    None,
                "fuente_margen_efectivo":
                    None,
            }
        )

    return resultados
