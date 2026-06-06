"""
EDARSA HUB - Script para crear tablas de automatización CRM
============================================================
Ejecutar para crear las tablas necesarias para flujos avanzados de pipeline.
"""

import pymssql
import os


def create_automation_tables():
    """Crea las tablas de automatización CRM si no existen."""
    
    conn = pymssql.connect(
        server=os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
        user=os.environ.get('EDARSAHUB_USERNAME', '<REDACTED_EDARSAHUB_SQL_USER>'),
        password=os.environ.get('EDARSAHUB_PASSWORD', '<REDACTED_EDARSAHUB_SQL_PASSWORD>'),
        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        port=int(os.environ.get('EDARSAHUB_PORT', 1433))
    )
    
    cursor = conn.cursor()
    
    # ==================== TABLA DE REGLAS ====================
    print("Creando tabla CRM_Automation_Reglas...")
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CRM_Automation_Reglas')
        BEGIN
            CREATE TABLE CRM_Automation_Reglas (
                ReglaID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
                EmpresaID UNIQUEIDENTIFIER NOT NULL,
                Nombre NVARCHAR(200) NOT NULL,
                Descripcion NVARCHAR(500),
                PipelineID INT,  -- NULL = aplica a todos los pipelines
                TipoTrigger NVARCHAR(50) NOT NULL,  -- CAMBIO_ETAPA, TIEMPO_EN_ETAPA, CAMPO_MODIFICADO
                CondicionJSON NVARCHAR(MAX),  -- Condiciones en formato JSON
                AccionJSON NVARCHAR(MAX) NOT NULL,  -- Acción a ejecutar en formato JSON
                Prioridad INT DEFAULT 100,  -- Menor = mayor prioridad
                Activa BIT DEFAULT 1,
                UsuarioCreacionID UNIQUEIDENTIFIER,
                FechaCreacion DATETIME DEFAULT GETDATE(),
                UsuarioModificacionID UNIQUEIDENTIFIER,
                FechaModificacion DATETIME,
                
                INDEX IX_Reglas_Empresa (EmpresaID),
                INDEX IX_Reglas_Pipeline (PipelineID),
                INDEX IX_Reglas_Activa (Activa)
            )
            PRINT 'Tabla CRM_Automation_Reglas creada'
        END
        ELSE
            PRINT 'Tabla CRM_Automation_Reglas ya existe'
    """)
    
    # ==================== TABLA DE LOG ====================
    print("Creando tabla CRM_Automation_Log...")
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CRM_Automation_Log')
        BEGIN
            CREATE TABLE CRM_Automation_Log (
                LogID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
                EmpresaID UNIQUEIDENTIFIER NOT NULL,
                ReglaID UNIQUEIDENTIFIER NOT NULL,
                OportunidadID UNIQUEIDENTIFIER,
                TipoTrigger NVARCHAR(50),
                AccionEjecutada NVARCHAR(100),
                Exitoso BIT DEFAULT 1,
                DetalleJSON NVARCHAR(MAX),
                MensajeError NVARCHAR(500),
                FechaEjecucion DATETIME DEFAULT GETDATE(),
                
                INDEX IX_Log_Empresa (EmpresaID),
                INDEX IX_Log_Regla (ReglaID),
                INDEX IX_Log_Fecha (FechaEjecucion)
            )
            PRINT 'Tabla CRM_Automation_Log creada'
        END
        ELSE
            PRINT 'Tabla CRM_Automation_Log ya existe'
    """)
    
    # ==================== COLUMNA SLA EN ETAPAS ====================
    print("Agregando columna DiasSLAMaximo a CRM_Config_PipelineEtapas...")
    cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sys.columns 
            WHERE object_id = OBJECT_ID('CRM_Config_PipelineEtapas') 
            AND name = 'DiasSLAMaximo'
        )
        BEGIN
            ALTER TABLE CRM_Config_PipelineEtapas
            ADD DiasSLAMaximo INT NULL
            PRINT 'Columna DiasSLAMaximo agregada'
        END
        ELSE
            PRINT 'Columna DiasSLAMaximo ya existe'
    """)
    
    conn.commit()
    
    # ==================== INSERTAR REGLAS DE EJEMPLO ====================
    print("\nInsertando reglas de ejemplo...")
    
    # Verificar si ya hay reglas
    cursor.execute("SELECT COUNT(*) FROM CRM_Automation_Reglas")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute("""
            INSERT INTO CRM_Automation_Reglas (
                ReglaID, EmpresaID, Nombre, Descripcion,
                TipoTrigger, CondicionJSON, AccionJSON, Prioridad
            ) VALUES
            -- Regla 1: Crear seguimiento al entrar a Propuesta
            (
                NEWID(), '19E076FB-C6DE-4EA5-84AB-1CAA9E86082C',
                'Seguimiento en Propuesta', 
                'Crear actividad de seguimiento cuando oportunidad entra a etapa Propuesta',
                'CAMBIO_ETAPA',
                '{"etapa_destino": 3}',
                '{"tipo": "CREAR_ACTIVIDAD", "titulo": "Seguimiento de propuesta", "descripcion": "Dar seguimiento a propuesta enviada", "dias_programar": 3}',
                10
            ),
            -- Regla 2: Aumentar probabilidad en Negociación
            (
                NEWID(), '19E076FB-C6DE-4EA5-84AB-1CAA9E86082C',
                'Probabilidad en Negociación',
                'Aumentar probabilidad al 70% cuando entra a Negociación',
                'CAMBIO_ETAPA',
                '{"etapa_destino": 4}',
                '{"tipo": "ACTUALIZAR_CAMPO", "campo": "ProbabilidadCierre", "valor": 70}',
                20
            ),
            -- Regla 3: Notificar al cerrar ganado
            (
                NEWID(), '19E076FB-C6DE-4EA5-84AB-1CAA9E86082C',
                'Notificación Cierre Ganado',
                'Notificar cuando se cierra una oportunidad como ganada',
                'CAMBIO_ETAPA',
                '{"etapa_destino": 5}',
                '{"tipo": "ENVIAR_NOTIFICACION", "titulo": "Oportunidad Ganada", "mensaje": "Felicidades! Se cerró una nueva venta."}',
                30
            )
        """)
        conn.commit()
        print("3 reglas de ejemplo insertadas")
    else:
        print(f"Ya existen {count} reglas, omitiendo ejemplos")
    
    # ==================== ACTUALIZAR SLA EN ETAPAS ====================
    print("\nActualizando SLA en etapas de ejemplo...")
    cursor.execute("""
        UPDATE CRM_Config_PipelineEtapas
        SET DiasSLAMaximo = CASE 
            WHEN Orden = 1 THEN 3   -- Prospección: 3 días
            WHEN Orden = 2 THEN 5   -- Calificación: 5 días
            WHEN Orden = 3 THEN 7   -- Propuesta: 7 días
            WHEN Orden = 4 THEN 10  -- Negociación: 10 días
            ELSE NULL
        END
        WHERE DiasSLAMaximo IS NULL
    """)
    conn.commit()
    
    conn.close()
    print("\n" + "="*60)
    print("Tablas de automatización CRM creadas exitosamente")
    print("="*60)


if __name__ == "__main__":
    create_automation_tables()
