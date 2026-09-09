"""
EDARSA HUB - Sync Históricos: Repository
=========================================
FASE SYNC-1: Acceso a datos para sincronización histórica.

VENTANA OPERATIVA: 13:00 - 11:00 (cruza medianoche)

DDL SEGURO:
- IF NOT EXISTS
- Sin DROP, DELETE, TRUNCATE
- Sin ALTER destructivo

OPERACIONES:
- Crear tablas Sync_*
- UPSERT idempotente
- Consultar bitácora
"""

import logging
import uuid
from datetime import date, datetime, time
from typing import List, Optional, Dict, Any
from decimal import Decimal

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG
from core.utils.operational_window import (
    MEXICO_TZ,
    get_mexico_now,
    get_sync_operational_window,
    DEFAULT_VENTANA_INICIO_HORA,
    DEFAULT_VENTANA_FIN_HORA,
)

from .models import (
    SyncVentaHistorica,
    SyncVentaPorHora,
    SyncVentaPorDiaSemana,
    SyncControlEjecucion,
)

logger = logging.getLogger(__name__)


class SyncHistoricosRepository:
    """
    Repository para tablas Sync_* en EDARSAHUB.
    """
    
    def __init__(self, connection_config: Optional[Dict] = None):
        """
        Inicializa el repository.
        
        Args:
            connection_config: Configuración de conexión (default: EDARSAHUB_CONFIG)
        """
        self._config = connection_config or EDARSAHUB_CONFIG
    
    def _execute(self, query: str) -> List[Dict]:
        """Ejecuta una query SQL."""
        return execute_sql_query(
            self._config['host'],
            self._config['port'],
            self._config['database'],
            self._config['username'],
            self._config['password'],
            query
        )
    
    # =========================================================================
    # DDL - Creación de Tablas
    # =========================================================================
    
    def create_tables_if_not_exist(self) -> Dict[str, bool]:
        """
        Crea las tablas Sync_* si no existen.
        
        SEGURO:
        - Usa IF NOT EXISTS
        - No hace DROP
        - No modifica tablas existentes
        
        Returns:
            Dict con nombre de tabla y si fue creada (True) o ya existía (False)
        """
        results = {}
        
        # 1. Sync_Ventas_Historicas
        ddl_ventas_historicas = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sync_Ventas_Historicas')
        BEGIN
            CREATE TABLE Sync_Ventas_Historicas (
                -- PK compuesta para UPSERT idempotente
                SyncVentaHistoricaID INT IDENTITY(1,1) PRIMARY KEY,
                
                -- Identificadores (clave única)
                ServerID NVARCHAR(50) NOT NULL,
                EmpresaID INT NOT NULL,
                SucursalID NVARCHAR(50) NULL,
                UnidadNegocioID NVARCHAR(50) NULL,
                SystemType NVARCHAR(20) NOT NULL,
                
                -- Fecha operativa (NO calendario)
                -- FASE SYNC-1: Ventana 13:00-11:00
                FechaOperacion DATE NOT NULL,
                
                -- Ventana operativa (preparación para módulo Horarios de Operación)
                VentanaInicio TIME NOT NULL,
                VentanaFin TIME NOT NULL,
                CruzaMedianoche BIT NOT NULL DEFAULT 1,
                VentanaInicioHoraConfig INT NOT NULL DEFAULT 13,
                VentanaFinHoraConfig INT NOT NULL DEFAULT 11,
                
                -- Métricas de ventas
                VentaTotal DECIMAL(18,2) NOT NULL DEFAULT 0,
                VentaEfectivo DECIMAL(18,2) NOT NULL DEFAULT 0,
                VentaTarjeta DECIMAL(18,2) NOT NULL DEFAULT 0,
                VentaOtros DECIMAL(18,2) NOT NULL DEFAULT 0,
                NumTickets INT NOT NULL DEFAULT 0,
                TicketPromedio DECIMAL(18,2) NOT NULL DEFAULT 0,
                
                -- Control de sincronización
                SyncRunID NVARCHAR(50) NOT NULL,
                SourceStatus NVARCHAR(20) NOT NULL,
                SourceType NVARCHAR(20) NOT NULL,
                SyncedAtMexico DATETIME2 NOT NULL,
                
                -- Integridad para UPSERT
                RowHash NVARCHAR(64) NOT NULL,
                
                -- Auditoría
                CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
                UpdatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
                
                -- Índice único para UPSERT
                CONSTRAINT UQ_Sync_Ventas_Historicas_Key 
                    UNIQUE (ServerID, EmpresaID, FechaOperacion)
            );
            
            -- Índices para consultas
            CREATE INDEX IX_Sync_Ventas_Historicas_Fecha 
                ON Sync_Ventas_Historicas(FechaOperacion);
            CREATE INDEX IX_Sync_Ventas_Historicas_Server 
                ON Sync_Ventas_Historicas(ServerID, FechaOperacion);
            CREATE INDEX IX_Sync_Ventas_Historicas_SyncRun 
                ON Sync_Ventas_Historicas(SyncRunID);
        END
        """
        try:
            self._execute(ddl_ventas_historicas)
            # Verificar si fue creada
            check = self._execute(
                "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sync_Ventas_Historicas'"
            )
            results['Sync_Ventas_Historicas'] = len(check) > 0
            logger.info("[SYNC-DDL] Tabla Sync_Ventas_Historicas verificada")
        except Exception as e:
            logger.error(f"[SYNC-DDL] Error con Sync_Ventas_Historicas: {e}")
            results['Sync_Ventas_Historicas'] = False
        
        # 2. Sync_Ventas_PorHora
        ddl_ventas_por_hora = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sync_Ventas_PorHora')
        BEGIN
            CREATE TABLE Sync_Ventas_PorHora (
                SyncVentaPorHoraID INT IDENTITY(1,1) PRIMARY KEY,
                
                -- Identificadores
                ServerID NVARCHAR(50) NOT NULL,
                EmpresaID INT NOT NULL,
                SucursalID NVARCHAR(50) NULL,
                UnidadNegocioID NVARCHAR(50) NULL,
                SystemType NVARCHAR(20) NOT NULL,
                
                -- Fecha y hora operativa
                FechaOperacion DATE NOT NULL,
                Hora INT NOT NULL CHECK (Hora >= 0 AND Hora <= 23),
                
                -- Ventana operativa
                VentanaInicio TIME NOT NULL,
                VentanaFin TIME NOT NULL,
                CruzaMedianoche BIT NOT NULL DEFAULT 1,
                VentanaInicioHoraConfig INT NOT NULL DEFAULT 13,
                VentanaFinHoraConfig INT NOT NULL DEFAULT 11,
                
                -- Métricas
                VentaHora DECIMAL(18,2) NOT NULL DEFAULT 0,
                NumTicketsHora INT NOT NULL DEFAULT 0,
                
                -- Control
                SyncRunID NVARCHAR(50) NOT NULL,
                SourceStatus NVARCHAR(20) NOT NULL,
                SourceType NVARCHAR(20) NOT NULL,
                SyncedAtMexico DATETIME2 NOT NULL,
                
                -- Integridad
                RowHash NVARCHAR(64) NOT NULL,
                
                -- Auditoría
                CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
                UpdatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
                
                -- Índice único para UPSERT
                CONSTRAINT UQ_Sync_Ventas_PorHora_Key 
                    UNIQUE (ServerID, EmpresaID, FechaOperacion, Hora)
            );
            
            CREATE INDEX IX_Sync_Ventas_PorHora_Fecha 
                ON Sync_Ventas_PorHora(FechaOperacion);
        END
        """
        try:
            self._execute(ddl_ventas_por_hora)
            check = self._execute(
                "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sync_Ventas_PorHora'"
            )
            results['Sync_Ventas_PorHora'] = len(check) > 0
            logger.info("[SYNC-DDL] Tabla Sync_Ventas_PorHora verificada")
        except Exception as e:
            logger.error(f"[SYNC-DDL] Error con Sync_Ventas_PorHora: {e}")
            results['Sync_Ventas_PorHora'] = False
        
        # 3. Sync_Ventas_PorDiaSemana
        ddl_ventas_por_dia = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sync_Ventas_PorDiaSemana')
        BEGIN
            CREATE TABLE Sync_Ventas_PorDiaSemana (
                SyncVentaPorDiaSemanaID INT IDENTITY(1,1) PRIMARY KEY,
                
                -- Identificadores
                ServerID NVARCHAR(50) NOT NULL,
                EmpresaID INT NOT NULL,
                SucursalID NVARCHAR(50) NULL,
                UnidadNegocioID NVARCHAR(50) NULL,
                SystemType NVARCHAR(20) NOT NULL,
                
                -- Período
                FechaInicioPeriodo DATE NOT NULL,
                FechaFinPeriodo DATE NOT NULL,
                DiaSemana INT NOT NULL CHECK (DiaSemana >= 0 AND DiaSemana <= 6),
                DiaSemananombre NVARCHAR(20) NOT NULL,
                
                -- Ventana operativa config
                VentanaInicioHoraConfig INT NOT NULL DEFAULT 13,
                VentanaFinHoraConfig INT NOT NULL DEFAULT 11,
                
                -- Métricas agregadas
                VentaPromedio DECIMAL(18,2) NOT NULL DEFAULT 0,
                VentaMin DECIMAL(18,2) NOT NULL DEFAULT 0,
                VentaMax DECIMAL(18,2) NOT NULL DEFAULT 0,
                NumDiasConDatos INT NOT NULL DEFAULT 0,
                
                -- Control
                SyncRunID NVARCHAR(50) NOT NULL,
                SourceStatus NVARCHAR(20) NOT NULL,
                SourceType NVARCHAR(20) NOT NULL,
                SyncedAtMexico DATETIME2 NOT NULL,
                
                -- Integridad
                RowHash NVARCHAR(64) NOT NULL,
                
                -- Auditoría
                CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
                UpdatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
                
                -- Índice único para UPSERT
                CONSTRAINT UQ_Sync_Ventas_PorDiaSemana_Key 
                    UNIQUE (ServerID, EmpresaID, FechaInicioPeriodo, FechaFinPeriodo, DiaSemana)
            );
        END
        """
        try:
            self._execute(ddl_ventas_por_dia)
            check = self._execute(
                "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sync_Ventas_PorDiaSemana'"
            )
            results['Sync_Ventas_PorDiaSemana'] = len(check) > 0
            logger.info("[SYNC-DDL] Tabla Sync_Ventas_PorDiaSemana verificada")
        except Exception as e:
            logger.error(f"[SYNC-DDL] Error con Sync_Ventas_PorDiaSemana: {e}")
            results['Sync_Ventas_PorDiaSemana'] = False
        
        # 4. Sync_Control_Ejecuciones
        ddl_control = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sync_Control_Ejecuciones')
        BEGIN
            CREATE TABLE Sync_Control_Ejecuciones (
                SyncControlID INT IDENTITY(1,1) PRIMARY KEY,
                
                -- Identificación del run
                SyncRunID NVARCHAR(50) NOT NULL UNIQUE,
                SyncType NVARCHAR(50) NOT NULL,
                
                -- Scope
                ServerID NVARCHAR(50) NULL,
                EmpresaID INT NULL,
                
                -- Rango procesado
                FechaInicio DATE NOT NULL,
                FechaFin DATE NOT NULL,
                
                -- Ventana operativa usada
                VentanaInicioHoraConfig INT NOT NULL DEFAULT 13,
                VentanaFinHoraConfig INT NOT NULL DEFAULT 11,
                
                -- Modo
                IsDryRun BIT NOT NULL DEFAULT 1,
                
                -- Resultados
                RegistrosProcesados INT NOT NULL DEFAULT 0,
                RegistrosInsertados INT NOT NULL DEFAULT 0,
                RegistrosActualizados INT NOT NULL DEFAULT 0,
                RegistrosError INT NOT NULL DEFAULT 0,
                
                -- Estado
                Status NVARCHAR(20) NOT NULL DEFAULT 'RUNNING',
                ErrorMessage NVARCHAR(MAX) NULL,
                
                -- Timestamps México
                StartedAtMexico DATETIME2 NOT NULL,
                FinishedAtMexico DATETIME2 NULL,
                DurationSeconds INT NULL,
                
                -- Auditoría
                CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME()
            );
            
            CREATE INDEX IX_Sync_Control_Ejecuciones_Run 
                ON Sync_Control_Ejecuciones(SyncRunID);
            CREATE INDEX IX_Sync_Control_Ejecuciones_Status 
                ON Sync_Control_Ejecuciones(Status);
        END
        """
        try:
            self._execute(ddl_control)
            check = self._execute(
                "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sync_Control_Ejecuciones'"
            )
            results['Sync_Control_Ejecuciones'] = len(check) > 0
            logger.info("[SYNC-DDL] Tabla Sync_Control_Ejecuciones verificada")
        except Exception as e:
            logger.error(f"[SYNC-DDL] Error con Sync_Control_Ejecuciones: {e}")
            results['Sync_Control_Ejecuciones'] = False
        
        return results
    
    # =========================================================================
    # UPSERT - Ventas Históricas
    # =========================================================================
    
    def upsert_venta_historica(self, venta: SyncVentaHistorica) -> bool:
        """
        Inserta o actualiza una venta histórica.
        
        UPSERT idempotente basado en (ServerID, EmpresaID, FechaOperacion).
        Solo actualiza si el hash cambió.
        
        Returns:
            True si se insertó/actualizó, False si ya existía con mismo hash
        """
        # Verificar si existe con mismo hash
        check_query = f"""
        SELECT RowHash FROM Sync_Ventas_Historicas
        WHERE ServerID = '{venta.ServerID}'
          AND EmpresaID = {venta.EmpresaID}
          AND FechaOperacion = '{venta.fecha_operacion}'
        """
        existing = self._execute(check_query)
        
        if existing and existing[0]['RowHash'] == venta.row_hash:
            # Ya existe con mismo hash, no actualizar
            logger.debug(f"[SYNC-UPSERT] Venta ya existe con mismo hash: {venta.server_id}/{venta.fecha_operacion}")
            return False
        
        # UPSERT
        upsert_query = f"""
        MERGE Sync_Ventas_Historicas AS target
        USING (SELECT 
            '{venta.server_id}' AS ServerID,
            {venta.empresa_id} AS EmpresaID,
            '{venta.fecha_operacion}' AS FechaOperacion
        ) AS source
        ON target.ServerID = source.ServerID 
           AND target.EmpresaID = source.EmpresaID 
           AND target.FechaOperacion = source.FechaOperacion
        WHEN MATCHED THEN
            UPDATE SET
                SucursalID = {f"'{venta.sucursal_id}'" if venta.sucursal_id else 'NULL'},
                UnidadNegocioID = {f"'{venta.unidad_negocio_id}'" if venta.unidad_negocio_id else 'NULL'},
                SystemType = '{venta.system_type}',
                VentanaInicio = '{venta.ventana_inicio}',
                VentanaFin = '{venta.ventana_fin}',
                CruzaMedianoche = {1 if venta.cruza_medianoche else 0},
                VentanaInicioHoraConfig = {venta.ventana_inicio_hora_config},
                VentanaFinHoraConfig = {venta.ventana_fin_hora_config},
                VentaTotal = {venta.venta_total},
                VentaEfectivo = {venta.venta_efectivo},
                VentaTarjeta = {venta.venta_tarjeta},
                VentaOtros = {venta.venta_otros},
                NumTickets = {venta.num_tickets},
                TicketPromedio = {venta.ticket_promedio},
                SyncRunID = '{venta.sync_run_id}',
                SourceStatus = '{venta.source_status}',
                SourceType = '{venta.source_type}',
                SyncedAtMexico = '{venta.synced_at_mexico.strftime('%Y-%m-%d %H:%M:%S')}',
                RowHash = '{venta.row_hash}',
                UpdatedAt = SYSDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (
                ServerID, EmpresaID, SucursalID, UnidadNegocioID, SystemType,
                FechaOperacion, VentanaInicio, VentanaFin, CruzaMedianoche,
                VentanaInicioHoraConfig, VentanaFinHoraConfig,
                VentaTotal, VentaEfectivo, VentaTarjeta, VentaOtros,
                NumTickets, TicketPromedio,
                SyncRunID, SourceStatus, SourceType, SyncedAtMexico, RowHash
            )
            VALUES (
                '{venta.server_id}', {venta.empresa_id}, 
                {f"'{venta.sucursal_id}'" if venta.sucursal_id else 'NULL'},
                {f"'{venta.unidad_negocio_id}'" if venta.unidad_negocio_id else 'NULL'},
                '{venta.system_type}',
                '{venta.fecha_operacion}', '{venta.ventana_inicio}', '{venta.ventana_fin}',
                {1 if venta.cruza_medianoche else 0},
                {venta.ventana_inicio_hora_config}, {venta.ventana_fin_hora_config},
                {venta.venta_total}, {venta.venta_efectivo}, {venta.venta_tarjeta}, {venta.venta_otros},
                {venta.num_tickets}, {venta.ticket_promedio},
                '{venta.sync_run_id}', '{venta.source_status}', '{venta.source_type}',
                '{venta.synced_at_mexico.strftime('%Y-%m-%d %H:%M:%S')}', '{venta.row_hash}'
            );
        """
        try:
            self._execute(upsert_query)
            return True
        except Exception as e:
            logger.error(f"[SYNC-UPSERT] Error: {e}")
            raise
    
    # =========================================================================
    # Control de Ejecuciones
    # =========================================================================
    
    def registrar_inicio_ejecucion(self, ejecucion: SyncControlEjecucion) -> None:
        """Registra el inicio de una ejecución de sincronización."""
        query = f"""
        INSERT INTO Sync_Control_Ejecuciones (
            SyncRunID, SyncType, ServerID, EmpresaID,
            FechaInicio, FechaFin,
            VentanaInicioHoraConfig, VentanaFinHoraConfig,
            IsDryRun, Status, StartedAtMexico, ConexionID, StartedAtUTC, IdempotencyKey
        ) VALUES (
            '{ejecucion.sync_run_id}', '{ejecucion.sync_type}',
            {f"'{ejecucion.ServerID}'" if ejecucion.ServerID else 'NULL'},
            {ejecucion.EmpresaID if ejecucion.EmpresaID else 'NULL'},
            '{ejecucion.fecha_inicio}', '{ejecucion.fecha_fin}',
            {ejecucion.ventana_inicio_hora_config}, {ejecucion.ventana_fin_hora_config},
            {1 if ejecucion.is_dry_run else 0}, 'RUNNING',
            '{ejecucion.started_at_mexico.strftime('%Y-%m-%d %H:%M:%S')}',
            {f"(SELECT TOP 1 id FROM dbo.Servidores_Conexiones WHERE id=TRY_CONVERT(uniqueidentifier, '{ejecucion.ServerID}'))" if ejecucion.ServerID else 'NULL'},
            SYSUTCDATETIME(),
            '{ejecucion.sync_type}:{ejecucion.sync_run_id}'
        )
        """
        self._execute(query)
    
    def actualizar_fin_ejecucion(
        self,
        sync_run_id: str,
        status: str,
        registros_procesados: int,
        registros_insertados: int,
        registros_actualizados: int,
        registros_error: int,
        error_message: Optional[str] = None
    ) -> None:
        """Actualiza el registro de ejecución al finalizar."""
        now = get_mexico_now()
        error_msg_sql = f"'{error_message[:500]}'" if error_message else 'NULL'
        
        query = f"""
        UPDATE Sync_Control_Ejecuciones
        SET 
            Status = '{status}',
            RegistrosProcesados = {registros_procesados},
            RegistrosInsertados = {registros_insertados},
            RegistrosActualizados = {registros_actualizados},
            RegistrosError = {registros_error},
            ErrorMessage = {error_msg_sql},
            FinishedAtMexico = '{now.strftime('%Y-%m-%d %H:%M:%S')}',
            FinishedAtUTC = COALESCE(FinishedAtUTC, SYSUTCDATETIME()),
            DurationSeconds = DATEDIFF(SECOND, StartedAtMexico, '{now.strftime('%Y-%m-%d %H:%M:%S')}')
        WHERE SyncRunID = '{sync_run_id}'
        """
        self._execute(query)
    
    def get_ultimo_sync(self, server_id: str, sync_type: str) -> Optional[Dict]:
        """Obtiene la última ejecución de sincronización para un servidor."""
        query = f"""
        SELECT TOP 1 *
        FROM Sync_Control_Ejecuciones
        WHERE ServerID = '{server_id}'
          AND SyncType = '{sync_type}'
          AND Status = 'SUCCESS'
        ORDER BY FinishedAtMexico DESC
        """
        result = self._execute(query)
        return result[0] if result else None
    
    # =========================================================================
    # UPSERT - Ventas Por Hora
    # =========================================================================
    
    def upsert_venta_por_hora(self, venta: SyncVentaPorHora) -> bool:
        """
        Inserta o actualiza una venta por hora.
        
        UPSERT idempotente basado en (ServerID, EmpresaID, FechaOperacion, Hora).
        Solo actualiza si el hash cambió.
        
        Returns:
            True si se insertó/actualizó, False si ya existía con mismo hash
        """
        # Verificar si existe con mismo hash
        check_query = f"""
        SELECT RowHash FROM Sync_Ventas_PorHora
        WHERE ServerID = '{venta.ServerID}'
          AND EmpresaID = {venta.EmpresaID}
          AND FechaOperacion = '{venta.fecha_operacion}'
          AND Hora = {venta.Hora}
        """
        existing = self._execute(check_query)
        
        if existing and existing[0]['RowHash'] == venta.row_hash:
            logger.debug(f"[SYNC-UPSERT] VentaPorHora ya existe con mismo hash: {venta.server_id}/{venta.fecha_operacion}/{venta.hora}")
            return False
        
        # UPSERT
        upsert_query = f"""
        MERGE Sync_Ventas_PorHora AS target
        USING (SELECT 
            '{venta.server_id}' AS ServerID,
            {venta.empresa_id} AS EmpresaID,
            '{venta.fecha_operacion}' AS FechaOperacion,
            {venta.hora} AS Hora
        ) AS source
        ON target.ServerID = source.ServerID 
           AND target.EmpresaID = source.EmpresaID 
           AND target.FechaOperacion = source.FechaOperacion
           AND target.Hora = source.Hora
        WHEN MATCHED THEN
            UPDATE SET
                SucursalID = {f"'{venta.sucursal_id}'" if venta.sucursal_id else 'NULL'},
                UnidadNegocioID = {f"'{venta.unidad_negocio_id}'" if venta.unidad_negocio_id else 'NULL'},
                SystemType = '{venta.system_type}',
                VentanaInicio = '{venta.ventana_inicio}',
                VentanaFin = '{venta.ventana_fin}',
                CruzaMedianoche = {1 if venta.cruza_medianoche else 0},
                VentanaInicioHoraConfig = {venta.ventana_inicio_hora_config},
                VentanaFinHoraConfig = {venta.ventana_fin_hora_config},
                VentaHora = {venta.venta_hora},
                NumTicketsHora = {venta.num_tickets_hora},
                SyncRunID = '{venta.sync_run_id}',
                SourceStatus = '{venta.source_status}',
                SourceType = '{venta.source_type}',
                SyncedAtMexico = '{venta.synced_at_mexico.strftime('%Y-%m-%d %H:%M:%S')}',
                RowHash = '{venta.row_hash}',
                UpdatedAt = SYSDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (
                ServerID, EmpresaID, SucursalID, UnidadNegocioID, SystemType,
                FechaOperacion, Hora,
                VentanaInicio, VentanaFin, CruzaMedianoche,
                VentanaInicioHoraConfig, VentanaFinHoraConfig,
                VentaHora, NumTicketsHora,
                SyncRunID, SourceStatus, SourceType, SyncedAtMexico, RowHash
            )
            VALUES (
                '{venta.server_id}', {venta.empresa_id}, 
                {f"'{venta.sucursal_id}'" if venta.sucursal_id else 'NULL'},
                {f"'{venta.unidad_negocio_id}'" if venta.unidad_negocio_id else 'NULL'},
                '{venta.system_type}',
                '{venta.fecha_operacion}', {venta.hora},
                '{venta.ventana_inicio}', '{venta.ventana_fin}',
                {1 if venta.cruza_medianoche else 0},
                {venta.ventana_inicio_hora_config}, {venta.ventana_fin_hora_config},
                {venta.venta_hora}, {venta.num_tickets_hora},
                '{venta.sync_run_id}', '{venta.source_status}', '{venta.source_type}',
                '{venta.synced_at_mexico.strftime('%Y-%m-%d %H:%M:%S')}', '{venta.row_hash}'
            );
        """
        try:
            self._execute(upsert_query)
            return True
        except Exception as e:
            logger.error(f"[SYNC-UPSERT] Error VentaPorHora: {e}")
            raise
    
    # =========================================================================
    # UPSERT - Ventas Por Día Semana
    # =========================================================================
    
    def upsert_venta_por_dia_semana(self, venta: SyncVentaPorDiaSemana) -> bool:
        """
        Inserta o actualiza una venta por día de semana.
        
        UPSERT idempotente basado en (ServerID, EmpresaID, FechaInicioPeriodo, FechaFinPeriodo, DiaSemana).
        Solo actualiza si el hash cambió.
        
        Returns:
            True si se insertó/actualizó, False si ya existía con mismo hash
        """
        # Verificar si existe con mismo hash
        check_query = f"""
        SELECT RowHash FROM Sync_Ventas_PorDiaSemana
        WHERE ServerID = '{venta.ServerID}'
          AND EmpresaID = {venta.EmpresaID}
          AND FechaInicioPeriodo = '{venta.fecha_inicio_periodo}'
          AND FechaFinPeriodo = '{venta.fecha_fin_periodo}'
          AND DiaSemana = {venta.dia_semana}
        """
        existing = self._execute(check_query)
        
        if existing and existing[0]['RowHash'] == venta.row_hash:
            logger.debug(f"[SYNC-UPSERT] VentaPorDiaSemana ya existe con mismo hash")
            return False
        
        # UPSERT
        upsert_query = f"""
        MERGE Sync_Ventas_PorDiaSemana AS target
        USING (SELECT 
            '{venta.server_id}' AS ServerID,
            {venta.empresa_id} AS EmpresaID,
            '{venta.fecha_inicio_periodo}' AS FechaInicioPeriodo,
            '{venta.fecha_fin_periodo}' AS FechaFinPeriodo,
            {venta.dia_semana} AS DiaSemana
        ) AS source
        ON target.ServerID = source.ServerID 
           AND target.EmpresaID = source.EmpresaID 
           AND target.FechaInicioPeriodo = source.FechaInicioPeriodo
           AND target.FechaFinPeriodo = source.FechaFinPeriodo
           AND target.DiaSemana = source.DiaSemana
        WHEN MATCHED THEN
            UPDATE SET
                SucursalID = {f"'{venta.sucursal_id}'" if venta.sucursal_id else 'NULL'},
                UnidadNegocioID = {f"'{venta.unidad_negocio_id}'" if venta.unidad_negocio_id else 'NULL'},
                SystemType = '{venta.system_type}',
                DiaSemananombre = '{venta.dia_semana_nombre}',
                VentanaInicioHoraConfig = {venta.ventana_inicio_hora_config},
                VentanaFinHoraConfig = {venta.ventana_fin_hora_config},
                VentaPromedio = {venta.venta_promedio},
                VentaMin = {venta.venta_min},
                VentaMax = {venta.venta_max},
                NumDiasConDatos = {venta.num_dias_con_datos},
                SyncRunID = '{venta.sync_run_id}',
                SourceStatus = '{venta.source_status}',
                SourceType = '{venta.source_type}',
                SyncedAtMexico = '{venta.synced_at_mexico.strftime('%Y-%m-%d %H:%M:%S')}',
                RowHash = '{venta.row_hash}',
                UpdatedAt = SYSDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (
                ServerID, EmpresaID, SucursalID, UnidadNegocioID, SystemType,
                FechaInicioPeriodo, FechaFinPeriodo, DiaSemana, DiaSemananombre,
                VentanaInicioHoraConfig, VentanaFinHoraConfig,
                VentaPromedio, VentaMin, VentaMax, NumDiasConDatos,
                SyncRunID, SourceStatus, SourceType, SyncedAtMexico, RowHash
            )
            VALUES (
                '{venta.server_id}', {venta.empresa_id}, 
                {f"'{venta.sucursal_id}'" if venta.sucursal_id else 'NULL'},
                {f"'{venta.unidad_negocio_id}'" if venta.unidad_negocio_id else 'NULL'},
                '{venta.system_type}',
                '{venta.fecha_inicio_periodo}', '{venta.fecha_fin_periodo}',
                {venta.dia_semana}, '{venta.dia_semana_nombre}',
                {venta.ventana_inicio_hora_config}, {venta.ventana_fin_hora_config},
                {venta.venta_promedio}, {venta.venta_min}, {venta.venta_max}, {venta.num_dias_con_datos},
                '{venta.sync_run_id}', '{venta.source_status}', '{venta.source_type}',
                '{venta.synced_at_mexico.strftime('%Y-%m-%d %H:%M:%S')}', '{venta.row_hash}'
            );
        """
        try:
            self._execute(upsert_query)
            return True
        except Exception as e:
            logger.error(f"[SYNC-UPSERT] Error VentaPorDiaSemana: {e}")
            raise
