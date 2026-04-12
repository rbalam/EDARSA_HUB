"""
EDARSA HUB - RH Service (Catálogos)
===================================
Lógica de negocio del módulo de Recursos Humanos.

FASE 6B DEL REFACTOR MODULAR (Diciembre 2025):
- Orquesta validaciones de negocio
- Coordina acceso a repositorio
- Maneja excepciones y respuestas

RESPONSABILIDADES:
- Validar reglas de negocio (ej: no eliminar puesto con colaboradores asignados)
- Obtener servidor EDARSA HUB
- Delegar operaciones de datos al repositorio
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
import logging

from modules.rh.repository import (
    get_edarsa_hub_server,
    query_listar_puestos,
    query_crear_puesto,
    query_actualizar_puesto,
    query_verificar_colaboradores_puesto,
    query_eliminar_puesto,
    query_listar_sucursales,
    query_listar_tipos_incidencias,
    query_crear_tipo_incidencia,
    query_actualizar_tipo_incidencia,
    query_desactivar_tipo_incidencia,
)
from modules.rh.schemas import (
    PuestoCreate,
    PuestoUpdate,
    TipoIncidenciaCreate,
    TipoIncidenciaUpdate,
)


# ============================================================================
# SCRIPT DE INICIALIZACIÓN (CONSTANTE)
# ============================================================================

SCRIPT_INICIALIZACION_SQL = """
-- ============================================
-- SCRIPT DE INICIALIZACIÓN - CATÁLOGOS RRHH
-- Compatible con: NomiPAQ, MPRO, Excel
-- Base de datos: EDARSA HUB
-- ============================================

-- ========== MODIFICAR TABLA PUESTOS ==========
-- Agregar columnas de mapeo si no existen
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Cat_Puestos' AND COLUMN_NAME = 'NomiPAQ_ID')
BEGIN
    ALTER TABLE RH_Cat_Puestos ADD NomiPAQ_ID NVARCHAR(50) NULL;
    PRINT 'Columna NomiPAQ_ID agregada a RH_Cat_Puestos';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Cat_Puestos' AND COLUMN_NAME = 'MPRO_ID')
BEGIN
    ALTER TABLE RH_Cat_Puestos ADD MPRO_ID NVARCHAR(50) NULL;
    PRINT 'Columna MPRO_ID agregada a RH_Cat_Puestos';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Cat_Puestos' AND COLUMN_NAME = 'Fecha_Creacion')
BEGIN
    ALTER TABLE RH_Cat_Puestos ADD Fecha_Creacion DATETIME DEFAULT GETDATE();
    ALTER TABLE RH_Cat_Puestos ADD Fecha_Modificacion DATETIME NULL;
    ALTER TABLE RH_Cat_Puestos ADD Creado_Por NVARCHAR(100) NULL;
    PRINT 'Columnas de auditoría agregadas a RH_Cat_Puestos';
END
GO

-- ========== TABLA TIPOS DE INCIDENCIAS ==========
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RH_Cat_Tipos_Incidencias' AND xtype='U')
BEGIN
    CREATE TABLE RH_Cat_Tipos_Incidencias (
        TipoIncidenciaID INT IDENTITY(1,1) PRIMARY KEY,
        Codigo NVARCHAR(10) NOT NULL UNIQUE,
        Descripcion NVARCHAR(100) NOT NULL,
        Categoria NVARCHAR(20) NOT NULL CHECK (Categoria IN ('Ingreso', 'Descuento')),
        Afectacion INT NOT NULL DEFAULT -1,  -- 1 = suma, -1 = resta
        Calculo_Monto NVARCHAR(20) DEFAULT 'Manual',  -- Manual, Porcentaje, Formula
        Formula NVARCHAR(500) NULL,  -- Fórmula personalizada si aplica
        Activo BIT DEFAULT 1,
        
        -- Mapeo con sistemas externos
        NomiPAQ_ID NVARCHAR(50) NULL,  -- ID en NomiPAQ
        NomiPAQ_Tipo NVARCHAR(50) NULL,  -- Tipo de concepto en NomiPAQ
        MPRO_ID NVARCHAR(50) NULL,  -- ID en MPRO
        Excel_Columna NVARCHAR(50) NULL,  -- Nombre de columna en Excel
        
        -- Auditoría
        Fecha_Creacion DATETIME DEFAULT GETDATE(),
        Fecha_Modificacion DATETIME NULL,
        Creado_Por NVARCHAR(100) NULL
    );
    
    CREATE INDEX IX_TiposIncidencias_Categoria ON RH_Cat_Tipos_Incidencias(Categoria);
    CREATE INDEX IX_TiposIncidencias_Activo ON RH_Cat_Tipos_Incidencias(Activo);
    
    PRINT 'Tabla RH_Cat_Tipos_Incidencias creada exitosamente';
END
GO

-- ========== INSERTAR TIPOS DE INCIDENCIAS POR DEFECTO ==========
IF NOT EXISTS (SELECT 1 FROM RH_Cat_Tipos_Incidencias)
BEGIN
    -- INGRESOS (+)
    INSERT INTO RH_Cat_Tipos_Incidencias (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto) VALUES
    ('BON', 'Bono', 'Ingreso', 1, 'Manual'),
    ('HEX', 'Horas Extra', 'Ingreso', 1, 'Formula'),
    ('COM', 'Comisión', 'Ingreso', 1, 'Porcentaje'),
    ('INC', 'Incentivo', 'Ingreso', 1, 'Manual'),
    ('GRA', 'Gratificación', 'Ingreso', 1, 'Manual'),
    ('AGU', 'Aguinaldo', 'Ingreso', 1, 'Formula'),
    ('PTU', 'PTU', 'Ingreso', 1, 'Formula'),
    ('PVA', 'Prima Vacacional', 'Ingreso', 1, 'Formula');
    
    -- DESCUENTOS (-)
    INSERT INTO RH_Cat_Tipos_Incidencias (Codigo, Descripcion, Categoria, Afectacion, Calculo_Monto) VALUES
    ('FAL', 'Falta', 'Descuento', -1, 'Formula'),
    ('RET', 'Retardo', 'Descuento', -1, 'Manual'),
    ('DES', 'Descuento General', 'Descuento', -1, 'Manual'),
    ('VAC', 'Vacaciones', 'Descuento', -1, 'Formula'),
    ('INA', 'Incapacidad', 'Descuento', -1, 'Formula'),
    ('PER', 'Permiso', 'Descuento', -1, 'Manual'),
    ('PRE', 'Préstamo', 'Descuento', -1, 'Manual'),
    ('INF', 'INFONAVIT', 'Descuento', -1, 'Porcentaje'),
    ('FON', 'FONACOT', 'Descuento', -1, 'Manual'),
    ('ISR', 'ISR', 'Descuento', -1, 'Formula'),
    ('IMSS', 'IMSS', 'Descuento', -1, 'Formula');
    
    PRINT 'Tipos de incidencias por defecto insertados';
END
GO

-- ========== MODIFICAR TABLA INCIDENCIAS NÓMINA ==========
-- Agregar columna para vincular con catálogo de tipos
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Incidencias_Nomina' AND COLUMN_NAME = 'TipoIncidenciaID')
BEGIN
    ALTER TABLE RH_Incidencias_Nomina ADD TipoIncidenciaID INT NULL;
    ALTER TABLE RH_Incidencias_Nomina ADD CONSTRAINT FK_Incidencia_Tipo 
        FOREIGN KEY (TipoIncidenciaID) REFERENCES RH_Cat_Tipos_Incidencias(TipoIncidenciaID);
    PRINT 'Columna TipoIncidenciaID agregada a RH_Incidencias_Nomina';
END

-- Agregar columnas de mapeo externo
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'RH_Incidencias_Nomina' AND COLUMN_NAME = 'Origen_Sistema')
BEGIN
    ALTER TABLE RH_Incidencias_Nomina ADD Origen_Sistema NVARCHAR(20) DEFAULT 'EDARSA_HUB';  -- EDARSA_HUB, NomiPAQ, MPRO, Excel
    ALTER TABLE RH_Incidencias_Nomina ADD Origen_ID NVARCHAR(50) NULL;  -- ID en sistema origen
    ALTER TABLE RH_Incidencias_Nomina ADD Fecha_Importacion DATETIME NULL;
    PRINT 'Columnas de origen agregadas a RH_Incidencias_Nomina';
END
GO

-- ========== TABLA DE MAPEO SISTEMAS EXTERNOS ==========
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='RH_Mapeo_Sistemas' AND xtype='U')
BEGIN
    CREATE TABLE RH_Mapeo_Sistemas (
        MapeoID INT IDENTITY(1,1) PRIMARY KEY,
        Sistema_Origen NVARCHAR(20) NOT NULL,  -- NomiPAQ, MPRO, Excel
        Tabla_Origen NVARCHAR(100) NOT NULL,
        Campo_Origen NVARCHAR(100) NOT NULL,
        Tabla_Destino NVARCHAR(100) NOT NULL,  -- Tabla en EDARSA HUB
        Campo_Destino NVARCHAR(100) NOT NULL,
        Transformacion NVARCHAR(500) NULL,  -- SQL o fórmula de transformación
        Activo BIT DEFAULT 1,
        Fecha_Creacion DATETIME DEFAULT GETDATE()
    );
    
    PRINT 'Tabla RH_Mapeo_Sistemas creada para configurar importaciones';
END
GO

-- ========== INSERTAR MAPEOS POR DEFECTO PARA NOMIPAQ ==========
IF NOT EXISTS (SELECT 1 FROM RH_Mapeo_Sistemas WHERE Sistema_Origen = 'NomiPAQ')
BEGIN
    INSERT INTO RH_Mapeo_Sistemas (Sistema_Origen, Tabla_Origen, Campo_Origen, Tabla_Destino, Campo_Destino) VALUES
    ('NomiPAQ', 'nom10001', 'numtrab', 'RH_Colaboradores_Expediente', 'NomiPAQ_ID'),
    ('NomiPAQ', 'nom10001', 'nombre', 'RH_Colaboradores_Expediente', 'Nombre_Completo'),
    ('NomiPAQ', 'nom10001', 'rfc', 'RH_Colaboradores_Expediente', 'RFC'),
    ('NomiPAQ', 'nom10001', 'curp', 'RH_Colaboradores_Expediente', 'CURP'),
    ('NomiPAQ', 'nom10003', 'idconcepto', 'RH_Cat_Tipos_Incidencias', 'NomiPAQ_ID'),
    ('NomiPAQ', 'nom10007', 'idmovto', 'RH_Incidencias_Nomina', 'Origen_ID');
    
    PRINT 'Mapeos NomiPAQ insertados';
END
GO

PRINT '=== Script de catálogos RRHH completado ===';
PRINT 'Las tablas están listas para importar datos de NomiPAQ, MPRO o Excel';
"""


# ============================================================================
# SERVICIOS DE CATÁLOGOS RH
# ============================================================================

class RHCatalogosService:
    """Servicio para gestionar los catálogos de Recursos Humanos."""
    
    async def _get_server(self) -> Dict:
        """Obtiene el servidor EDARSA HUB o lanza excepción."""
        server = await get_edarsa_hub_server()
        if not server:
            raise HTTPException(status_code=404, detail="Servidor EDARSA HUB no configurado")
        return server
    
    def _check_admin_role(self, current_user: Dict) -> None:
        """Verifica que el usuario tenga rol de Administrador."""
        if current_user.get('role') != 'Administrador':
            raise HTTPException(
                status_code=403, 
                detail="Solo administradores pueden realizar esta acción"
            )
    
    # ---------- PUESTOS ----------
    
    async def listar_puestos(self) -> Dict[str, Any]:
        """Lista todos los puestos del catálogo."""
        server = await self._get_server()
        result = query_listar_puestos(server)
        return {"puestos": result.get("datos", []), "total": result.get("registros", 0)}
    
    async def crear_puesto(self, data: PuestoCreate, current_user: Dict) -> Dict[str, Any]:
        """Crea un nuevo puesto (solo admin)."""
        self._check_admin_role(current_user)
        server = await self._get_server()
        
        query_crear_puesto(
            server,
            descripcion=data.descripcion,
            departamento=data.departamento,
            sueldo_base=float(data.sueldo_base),
            nomipaq_id=data.nomipaq_id,
            mpro_id=data.mpro_id,
            creado_por=current_user.get("email", "")
        )
        
        return {"success": True, "message": "Puesto creado"}
    
    async def actualizar_puesto(
        self, 
        puesto_id: int, 
        data: PuestoUpdate, 
        current_user: Dict
    ) -> Dict[str, Any]:
        """Actualiza un puesto existente (solo admin)."""
        self._check_admin_role(current_user)
        server = await self._get_server()
        
        # Convertir Pydantic model a dict excluyendo None
        updates = data.model_dump(exclude_none=True)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        result = query_actualizar_puesto(server, puesto_id, updates)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"success": True, "message": "Puesto actualizado"}
    
    async def eliminar_puesto(self, puesto_id: int, current_user: Dict) -> Dict[str, Any]:
        """Elimina un puesto (solo admin, verifica colaboradores)."""
        self._check_admin_role(current_user)
        server = await self._get_server()
        
        # Verificar si hay colaboradores con este puesto
        total_colaboradores = query_verificar_colaboradores_puesto(server, puesto_id)
        if total_colaboradores > 0:
            raise HTTPException(
                status_code=400, 
                detail="No se puede eliminar: hay colaboradores asignados a este puesto"
            )
        
        result = query_eliminar_puesto(server, puesto_id)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"success": True, "message": "Puesto eliminado"}
    
    # ---------- SUCURSALES ----------
    
    async def listar_sucursales(self) -> Dict[str, Any]:
        """Lista todas las sucursales del catálogo."""
        server = await self._get_server()
        result = query_listar_sucursales(server)
        return {"sucursales": result.get("datos", []), "total": result.get("registros", 0)}
    
    # ---------- TIPOS DE INCIDENCIAS ----------
    
    async def listar_tipos_incidencias(self) -> Dict[str, Any]:
        """Lista todos los tipos de incidencias activos."""
        server = await self._get_server()
        result = query_listar_tipos_incidencias(server)
        
        response = {
            "tipos_incidencias": result.get("datos", []),
            "total": result.get("registros", 0)
        }
        
        if result.get("nota"):
            response["nota"] = result["nota"]
        
        return response
    
    async def crear_tipo_incidencia(
        self, 
        data: TipoIncidenciaCreate, 
        current_user: Dict
    ) -> Dict[str, Any]:
        """Crea un nuevo tipo de incidencia (solo admin)."""
        self._check_admin_role(current_user)
        server = await self._get_server()
        
        query_crear_tipo_incidencia(
            server,
            codigo=data.codigo,
            descripcion=data.descripcion,
            categoria=data.categoria,
            calculo_monto=data.calculo_monto,
            nomipaq_id=data.nomipaq_id,
            mpro_id=data.mpro_id,
            creado_por=current_user.get("email", "")
        )
        
        return {"success": True, "message": "Tipo de incidencia creado"}
    
    async def actualizar_tipo_incidencia(
        self, 
        tipo_id: int, 
        data: TipoIncidenciaUpdate, 
        current_user: Dict
    ) -> Dict[str, Any]:
        """Actualiza un tipo de incidencia existente (solo admin)."""
        self._check_admin_role(current_user)
        server = await self._get_server()
        
        # Convertir Pydantic model a dict excluyendo None
        updates = data.model_dump(exclude_none=True)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        result = query_actualizar_tipo_incidencia(server, tipo_id, updates)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"success": True, "message": "Tipo de incidencia actualizado"}
    
    async def eliminar_tipo_incidencia(
        self, 
        tipo_id: int, 
        current_user: Dict
    ) -> Dict[str, Any]:
        """Desactiva un tipo de incidencia (soft delete, solo admin)."""
        self._check_admin_role(current_user)
        server = await self._get_server()
        
        result = query_desactivar_tipo_incidencia(server, tipo_id)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"success": True, "message": "Tipo de incidencia desactivado"}
    
    # ---------- SCRIPT INICIALIZACIÓN ----------
    
    def obtener_script_inicializacion(self) -> Dict[str, Any]:
        """Retorna el script SQL para crear/actualizar las tablas de catálogos RRHH."""
        return {
            "script": SCRIPT_INICIALIZACION_SQL,
            "instrucciones": [
                "1. Copia el script SQL completo",
                "2. Ve a 'Explorador BD' en el menú lateral",
                "3. Selecciona el servidor EDARSA HUB",
                "4. Ejecuta el script con credenciales de administrador",
                "5. Las tablas quedarán preparadas para:",
                "   - Gestionar catálogos de Puestos e Incidencias",
                "   - Importar datos desde NomiPAQ",
                "   - Importar datos desde MPRO",
                "   - Importar datos desde Excel",
                "   - Migrar a EDARSA HUB sin pérdida de datos"
            ],
            "compatibilidad": {
                "nomipaq": "Mapeo con nom10001 (empleados), nom10003 (conceptos), nom10007 (movimientos)",
                "mpro": "Campos MPRO_ID en todas las tablas para vincular registros",
                "excel": "Campo Excel_Columna para mapear columnas de importación"
            }
        }


# Instancia singleton del servicio
rh_catalogos_service = RHCatalogosService()
