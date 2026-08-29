from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
FASE 1C-3I-G: Servicio de Listas Manuales de Competidores

Este módulo permite crear y gestionar listas manuales de competidores
para facilitar comparaciones por ciudad, segmento, tipo de restaurante,
unidad de negocio o estrategia comercial.

REGLAS:
- EDARSAHUB SQL es el cerebro
- CERO MongoDB
- No modificar precios oficiales
- Un competidor puede pertenecer a varias listas
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import logging
import uuid

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

logger = logging.getLogger(__name__)


def _get_conn() -> Tuple:
    """Retorna parámetros de conexión a EDARSAHUB."""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


def _ensure_tablas_listas_existen():
    """
    Verifica y crea las tablas de listas de competidores si no existen.
    """
    conn = _get_conn()
    
    # DDL para tabla principal de listas
    ddl_listas = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_CompetidoresListas')
    BEGIN
        CREATE TABLE Comercial_CompetidoresListas (
            ListaCompetidoresID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            NombreLista NVARCHAR(200) NOT NULL,
            Descripcion NVARCHAR(500) NULL,
            EmpresaID INT NULL,
            UnidadNegocioID INT NULL,
            Segmento NVARCHAR(100) NULL,
            Categoria NVARCHAR(100) NULL,
            ColorIdentificador NVARCHAR(20) NULL,
            Activo BIT DEFAULT 1,
            FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE(),
            FechaModificacion DATETIME2 NULL,
            CreadoPor NVARCHAR(100) NOT NULL,
            ModificadoPor NVARCHAR(100) NULL
        );
        
        CREATE INDEX IX_CompetidoresListas_Empresa ON Comercial_CompetidoresListas(EmpresaID);
        CREATE INDEX IX_CompetidoresListas_Unidad ON Comercial_CompetidoresListas(UnidadNegocioID);
        CREATE INDEX IX_CompetidoresListas_Activo ON Comercial_CompetidoresListas(Activo);
    END
    """
    
    # DDL para tabla detalle (relación lista-competidor)
    ddl_detalle = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_CompetidoresListasDetalle')
    BEGIN
        CREATE TABLE Comercial_CompetidoresListasDetalle (
            ListaDetalleID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            ListaCompetidoresID UNIQUEIDENTIFIER NOT NULL,
            CompetidorID UNIQUEIDENTIFIER NOT NULL,
            Orden INT DEFAULT 0,
            Notas NVARCHAR(500) NULL,
            Activo BIT DEFAULT 1,
            FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE(),
            FechaModificacion DATETIME2 NULL,
            CreadoPor NVARCHAR(100) NOT NULL,
            ModificadoPor NVARCHAR(100) NULL,
            
            CONSTRAINT FK_ListaDetalle_Lista FOREIGN KEY (ListaCompetidoresID)
                REFERENCES Comercial_CompetidoresListas(ListaCompetidoresID),
            CONSTRAINT FK_ListaDetalle_Competidor FOREIGN KEY (CompetidorID)
                REFERENCES Comercial_Competidores(CompetidorID)
        );
        
        CREATE INDEX IX_ListasDetalle_Lista ON Comercial_CompetidoresListasDetalle(ListaCompetidoresID);
        CREATE INDEX IX_ListasDetalle_Competidor ON Comercial_CompetidoresListasDetalle(CompetidorID);
        CREATE INDEX IX_ListasDetalle_Activo ON Comercial_CompetidoresListasDetalle(Activo);
        
        -- Constraint único: no duplicar competidor activo en la misma lista
        CREATE UNIQUE INDEX UQ_ListaCompetidor_Activo 
            ON Comercial_CompetidoresListasDetalle(ListaCompetidoresID, CompetidorID) 
            WHERE Activo = 1;
    END
    """
    
    try:
        execute_sql_query(*conn, ddl_listas)
        execute_sql_query(*conn, ddl_detalle)
        logger.info("[LISTAS-COMP] Tablas de listas de competidores verificadas/creadas")
        return True
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error creando tablas: {e}")
        return False


# Inicializar tablas al importar el módulo
_ensure_tablas_listas_existen()


# =============================================================================
# CRUD LISTAS DE COMPETIDORES
# =============================================================================

def listar_listas_competidores(
    empresa_id: int = None,
    unidad_negocio_pk: int = None,
    solo_activas: bool = True,
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    """
    Lista todas las listas de competidores con conteo de miembros.
    """
    conn = _get_conn()
    
    filtros = []
    if empresa_id:
        filtros.append(f"l.EmpresaID = {empresa_id}")
    if unidad_negocio_pk:
        filtros.append(f"l.UnidadNegocioID = {unidad_negocio_pk}")
    if solo_activas:
        filtros.append("l.Activo = 1")
    
    where_clause = " AND ".join(filtros) if filtros else "1=1"
    offset = (page - 1) * page_size
    
    # Query con conteo de competidores
    query = f"""
    SELECT 
        l.ListaCompetidoresID,
        l.NombreLista,
        l.Descripcion,
        l.EmpresaID,
        l.UnidadNegocioID,
        l.Segmento,
        l.Categoria,
        l.ColorIdentificador,
        l.Activo,
        l.FechaCreacion,
        l.FechaModificacion,
        l.CreadoPor,
        l.ModificadoPor,
        (SELECT COUNT(*) FROM Comercial_CompetidoresListasDetalle d 
         WHERE d.ListaCompetidoresID = l.ListaCompetidoresID AND d.Activo = 1) as TotalCompetidores
    FROM Comercial_CompetidoresListas l
    WHERE {where_clause}
    ORDER BY l.NombreLista
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    # Query de conteo total
    count_query = f"""
    SELECT COUNT(*) as total
    FROM Comercial_CompetidoresListas l
    WHERE {where_clause}
    """
    
    try:
        result = execute_sql_query(*conn, query)
        count_result = execute_sql_query(*conn, count_query)
        total = count_result[0]['total'] if count_result else 0
        
        listas = []
        for row in result:
            # Manejar fechas que pueden ser datetime o string
            fecha_creacion = row.get('FechaCreacion')
            if fecha_creacion and hasattr(fecha_creacion, 'isoformat'):
                fecha_creacion = fecha_creacion.isoformat()
            
            fecha_modificacion = row.get('FechaModificacion')
            if fecha_modificacion and hasattr(fecha_modificacion, 'isoformat'):
                fecha_modificacion = fecha_modificacion.isoformat()
            
            listas.append({
                'lista_id': str(row['ListaCompetidoresID']),
                'nombre_lista': row['NombreLista'],
                'descripcion': row['Descripcion'],
                'empresa_id': row['EmpresaID'],
                'unidad_negocio_pk': row['UnidadNegocioID'],
                'segmento': row['Segmento'],
                'categoria': row['Categoria'],
                'color': row['ColorIdentificador'],
                'activo': bool(row['Activo']),
                'total_competidores': row['TotalCompetidores'],
                'fecha_creacion': fecha_creacion,
                'fecha_modificacion': fecha_modificacion,
                'creado_por': row['CreadoPor'],
                'modificado_por': row['ModificadoPor']
            })
        
        return {
            'listas': listas,
            'total': total,
            'page': page,
            'page_size': page_size
        }
        
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error listando listas: {e}")
        raise


def crear_lista_competidores(
    nombre_lista: str,
    descripcion: str = None,
    empresa_id: int = None,
    unidad_negocio_pk: int = None,
    segmento: str = None,
    categoria: str = None,
    color: str = None,
    usuario: str = "sistema"
) -> Dict[str, Any]:
    """
    Crea una nueva lista de competidores.
    """
    conn = _get_conn()
    lista_id = str(uuid.uuid4()).upper()
    
    query = f"""
    INSERT INTO Comercial_CompetidoresListas (
        ListaCompetidoresID, NombreLista, Descripcion, EmpresaID, 
        UnidadNegocioID, Segmento, Categoria, ColorIdentificador,
        Activo, FechaCreacion, CreadoPor
    ) VALUES (
        '{lista_id}',
        N'{nombre_lista.replace("'", "''")}',
        {f"N'{descripcion.replace(chr(39), chr(39)+chr(39))}'" if descripcion else 'NULL'},
        {empresa_id if empresa_id else 'NULL'},
        {unidad_negocio_pk if unidad_negocio_pk else 'NULL'},
        {f"N'{segmento}'" if segmento else 'NULL'},
        {f"N'{categoria}'" if categoria else 'NULL'},
        {f"N'{color}'" if color else 'NULL'},
        1,
        GETDATE(),
        N'{usuario}'
    )
    """
    
    try:
        execute_sql_query(*conn, query)
        logger.info(f"[LISTAS-COMP] Lista creada: {nombre_lista} ({lista_id})")
        
        return {
            'lista_id': lista_id,
            'nombre_lista': nombre_lista,
            'descripcion': descripcion,
            'empresa_id': empresa_id,
            'unidad_negocio_pk': unidad_negocio_pk,
            'segmento': segmento,
            'categoria': categoria,
            'color': color,
            'activo': True,
            'total_competidores': 0,
            'creado_por': usuario
        }
        
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error creando lista: {e}")
        raise


def actualizar_lista_competidores(
    lista_id: str,
    nombre_lista: str = None,
    descripcion: str = None,
    segmento: str = None,
    categoria: str = None,
    color: str = None,
    usuario: str = "sistema"
) -> Dict[str, Any]:
    """
    Actualiza una lista de competidores existente.
    """
    conn = _get_conn()
    
    updates = []
    if nombre_lista:
        updates.append(f"NombreLista = N'{nombre_lista.replace(chr(39), chr(39)+chr(39))}'")
    if descripcion is not None:
        updates.append(f"Descripcion = N'{descripcion.replace(chr(39), chr(39)+chr(39))}'")
    if segmento is not None:
        updates.append(f"Segmento = {f'N{chr(39)}{segmento}{chr(39)}' if segmento else 'NULL'}")
    if categoria is not None:
        updates.append(f"Categoria = {f'N{chr(39)}{categoria}{chr(39)}' if categoria else 'NULL'}")
    if color is not None:
        updates.append(f"ColorIdentificador = {f'N{chr(39)}{color}{chr(39)}' if color else 'NULL'}")
    
    updates.append(f"FechaModificacion = GETDATE()")
    updates.append(f"ModificadoPor = N'{usuario}'")
    
    query = f"""
    UPDATE Comercial_CompetidoresListas
    SET {', '.join(updates)}
    WHERE ListaCompetidoresID = '{lista_id}'
    """
    
    try:
        execute_sql_query(*conn, query)
        logger.info(f"[LISTAS-COMP] Lista actualizada: {lista_id}")
        return obtener_lista_competidores(lista_id)
        
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error actualizando lista: {e}")
        raise


def desactivar_lista_competidores(lista_id: str, usuario: str = "sistema") -> bool:
    """
    Desactiva (soft delete) una lista de competidores.
    """
    conn = _get_conn()
    
    query = f"""
    UPDATE Comercial_CompetidoresListas
    SET Activo = 0, FechaModificacion = GETDATE(), ModificadoPor = N'{usuario}'
    WHERE ListaCompetidoresID = '{lista_id}'
    """
    
    try:
        execute_sql_query(*conn, query)
        logger.info(f"[LISTAS-COMP] Lista desactivada: {lista_id}")
        return True
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error desactivando lista: {e}")
        return False


def obtener_lista_competidores(lista_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una lista de competidores por ID.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        l.ListaCompetidoresID,
        l.NombreLista,
        l.Descripcion,
        l.EmpresaID,
        l.UnidadNegocioID,
        l.Segmento,
        l.Categoria,
        l.ColorIdentificador,
        l.Activo,
        l.FechaCreacion,
        l.FechaModificacion,
        l.CreadoPor,
        l.ModificadoPor,
        (SELECT COUNT(*) FROM Comercial_CompetidoresListasDetalle d 
         WHERE d.ListaCompetidoresID = l.ListaCompetidoresID AND d.Activo = 1) as TotalCompetidores
    FROM Comercial_CompetidoresListas l
    WHERE l.ListaCompetidoresID = '{lista_id}'
    """
    
    try:
        result = execute_sql_query(*conn, query)
        if not result:
            return None
        
        row = result[0]
        
        # Manejar fechas que pueden ser datetime o string
        fecha_creacion = row.get('FechaCreacion')
        if fecha_creacion and hasattr(fecha_creacion, 'isoformat'):
            fecha_creacion = fecha_creacion.isoformat()
        
        fecha_modificacion = row.get('FechaModificacion')
        if fecha_modificacion and hasattr(fecha_modificacion, 'isoformat'):
            fecha_modificacion = fecha_modificacion.isoformat()
        
        return {
            'lista_id': str(row['ListaCompetidoresID']),
            'nombre_lista': row['NombreLista'],
            'descripcion': row['Descripcion'],
            'empresa_id': row['EmpresaID'],
            'unidad_negocio_pk': row['UnidadNegocioID'],
            'segmento': row['Segmento'],
            'categoria': row['Categoria'],
            'color': row['ColorIdentificador'],
            'activo': bool(row['Activo']),
            'total_competidores': row['TotalCompetidores'],
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'creado_por': row['CreadoPor'],
            'modificado_por': row['ModificadoPor']
        }
        
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error obteniendo lista: {e}")
        raise


# =============================================================================
# CRUD DETALLE (COMPETIDORES EN LISTA)
# =============================================================================

def listar_competidores_de_lista(lista_id: str, solo_activos: bool = True) -> List[Dict[str, Any]]:
    """
    Lista todos los competidores de una lista específica.
    """
    conn = _get_conn()
    
    filtro_activo = "AND d.Activo = 1" if solo_activos else ""
    
    query = f"""
    SELECT 
        d.ListaDetalleID,
        d.ListaCompetidoresID,
        d.CompetidorID,
        d.Orden,
        d.Notas,
        d.Activo,
        d.FechaCreacion,
        c.NombreCompetidor,
        c.TipoNegocio,
        c.NivelPrecioPercibido,
        c.EsCompetenciaDirecta,
        c.EsBenchmarkAspiracional,
        c.UbicacionReferencia
    FROM Comercial_CompetidoresListasDetalle d
    INNER JOIN Comercial_Competidores c ON d.CompetidorID = c.CompetidorID
    WHERE d.ListaCompetidoresID = '{lista_id}'
    {filtro_activo}
    AND c.Activo = 1
    ORDER BY d.Orden, c.NombreCompetidor
    """
    
    try:
        result = execute_sql_query(*conn, query)
        
        competidores = []
        for row in result:
            # Manejar fecha que puede ser datetime o string
            fecha_agregado = row.get('FechaCreacion')
            if fecha_agregado and hasattr(fecha_agregado, 'isoformat'):
                fecha_agregado = fecha_agregado.isoformat()
            
            competidores.append({
                'detalle_id': str(row['ListaDetalleID']),
                'lista_id': str(row['ListaCompetidoresID']),
                'competidor_id': str(row['CompetidorID']),
                'orden': row['Orden'],
                'notas': row['Notas'],
                'activo': bool(row['Activo']),
                'fecha_agregado': fecha_agregado,
                'nombre_competidor': row['NombreCompetidor'],
                'tipo_negocio': row['TipoNegocio'],
                'nivel_precio': row['NivelPrecioPercibido'],
                'es_competencia_directa': bool(row['EsCompetenciaDirecta']),
                'es_benchmark_aspiracional': bool(row['EsBenchmarkAspiracional']),
                'ubicacion': row['UbicacionReferencia']
            })
        
        return competidores
        
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error listando competidores de lista: {e}")
        raise


def agregar_competidor_a_lista(
    lista_id: str,
    competidor_id: str,
    orden: int = 0,
    notas: str = None,
    usuario: str = "sistema"
) -> Dict[str, Any]:
    """
    Agrega un competidor a una lista.
    """
    conn = _get_conn()
    detalle_id = str(uuid.uuid4()).upper()
    
    # Verificar si ya existe (activo o inactivo)
    check_query = f"""
    SELECT ListaDetalleID, Activo 
    FROM Comercial_CompetidoresListasDetalle
    WHERE ListaCompetidoresID = '{lista_id}' AND CompetidorID = '{competidor_id}'
    """
    
    try:
        existing = execute_sql_query(*conn, check_query)
        
        if existing:
            # Si ya existe y está activo, error
            if existing[0]['Activo']:
                raise ValueError("El competidor ya está en esta lista")
            
            # Si existe pero está inactivo, reactivar
            reactivate_query = f"""
            UPDATE Comercial_CompetidoresListasDetalle
            SET Activo = 1, Orden = {orden}, 
                Notas = {f"N'{notas.replace(chr(39), chr(39)+chr(39))}'" if notas else 'NULL'},
                FechaModificacion = GETDATE(), ModificadoPor = N'{usuario}'
            WHERE ListaDetalleID = '{existing[0]['ListaDetalleID']}'
            """
            execute_sql_query(*conn, reactivate_query)
            detalle_id = str(existing[0]['ListaDetalleID'])
            logger.info(f"[LISTAS-COMP] Competidor reactivado en lista: {competidor_id} -> {lista_id}")
        else:
            # Insertar nuevo
            insert_query = f"""
            INSERT INTO Comercial_CompetidoresListasDetalle (
                ListaDetalleID, ListaCompetidoresID, CompetidorID,
                Orden, Notas, Activo, FechaCreacion, CreadoPor
            ) VALUES (
                '{detalle_id}',
                '{lista_id}',
                '{competidor_id}',
                {orden},
                {f"N'{notas.replace(chr(39), chr(39)+chr(39))}'" if notas else 'NULL'},
                1,
                GETDATE(),
                N'{usuario}'
            )
            """
            execute_sql_query(*conn, insert_query)
            logger.info(f"[LISTAS-COMP] Competidor agregado a lista: {competidor_id} -> {lista_id}")
        
        return {
            'detalle_id': detalle_id,
            'lista_id': lista_id,
            'competidor_id': competidor_id,
            'orden': orden,
            'notas': notas,
            'activo': True
        }
        
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error agregando competidor a lista: {e}")
        raise


def quitar_competidor_de_lista(lista_id: str, competidor_id: str, usuario: str = "sistema") -> bool:
    """
    Quita (desactiva) un competidor de una lista.
    """
    conn = _get_conn()
    
    query = f"""
    UPDATE Comercial_CompetidoresListasDetalle
    SET Activo = 0, FechaModificacion = GETDATE(), ModificadoPor = N'{usuario}'
    WHERE ListaCompetidoresID = '{lista_id}' AND CompetidorID = '{competidor_id}'
    """
    
    try:
        execute_sql_query(*conn, query)
        logger.info(f"[LISTAS-COMP] Competidor quitado de lista: {competidor_id} <- {lista_id}")
        return True
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error quitando competidor de lista: {e}")
        return False


def obtener_ids_competidores_de_lista(lista_id: str) -> List[str]:
    """
    Obtiene solo los IDs de competidores de una lista (para filtros).
    """
    conn = _get_conn()
    
    query = f"""
    SELECT CompetidorID
    FROM Comercial_CompetidoresListasDetalle
    WHERE ListaCompetidoresID = '{lista_id}' AND Activo = 1
    """
    
    try:
        result = execute_sql_query(*conn, query)
        return [str(row['CompetidorID']) for row in result]
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error obteniendo IDs de lista: {e}")
        return []


def obtener_listas_de_competidor(competidor_id: str) -> List[Dict[str, Any]]:
    """
    Obtiene todas las listas a las que pertenece un competidor.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        l.ListaCompetidoresID,
        l.NombreLista,
        l.ColorIdentificador,
        d.FechaCreacion as FechaAgregado
    FROM Comercial_CompetidoresListasDetalle d
    INNER JOIN Comercial_CompetidoresListas l ON d.ListaCompetidoresID = l.ListaCompetidoresID
    WHERE d.CompetidorID = '{competidor_id}'
    AND d.Activo = 1
    AND l.Activo = 1
    ORDER BY l.NombreLista
    """
    
    try:
        result = execute_sql_query(*conn, query)
        listas = []
        for row in result:
            fecha_agregado = row.get('FechaAgregado')
            if fecha_agregado and hasattr(fecha_agregado, 'isoformat'):
                fecha_agregado = fecha_agregado.isoformat()
            
            listas.append({
                'lista_id': str(row['ListaCompetidoresID']),
                'nombre_lista': row['NombreLista'],
                'color': row['ColorIdentificador'],
                'fecha_agregado': fecha_agregado
            })
        return listas
    except Exception as e:
        logger.error(f"[LISTAS-COMP] Error obteniendo listas de competidor: {e}")
        return []
