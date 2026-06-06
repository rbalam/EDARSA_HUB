# ANÁLISIS DE AUDITORÍA FUNCIONAL - EDARSA HUB
## Estado Actual y Propuesta de Implementación

**Fecha:** Diciembre 2025  
**Alcance:** Tesorería, CxP, Propinas TPV

---

## 1. ESTADO ACTUAL DE AUDITORÍA

### 1.1 ¿Existe tabla formal de auditoría en EDARSA HUB?

| Ubicación | Estado | Observación |
|-----------|--------|-------------|
| **MongoDB (edarsa_hub)** | ❌ NO existe tabla centralizada | Solo `bitacora_tecnica` (1 registro de refactorización) |
| **SQL Server (Propinas TPV)** | ✅ PARCIAL | Existe `propinas_tpv_historial` con estructura completa |
| **Tesorería / Cuadre Z** | ❌ NO existe | Sin auditoría |
| **CxP** | ❌ NO existe | Sin auditoría |

### 1.2 ¿Qué acciones se están registrando actualmente?

| Módulo | Acción | ¿Se registra? | Dónde |
|--------|--------|---------------|-------|
| **Propinas TPV - Config** | Crear/Editar % | ✅ SÍ | MongoDB `propinas_config` (campos `created_by`, `updated_by`, `motivo_cambio`) |
| **Propinas TPV - Control** | Cambio de estado | ✅ SÍ (diseñado) | SQL Server `propinas_tpv_historial` |
| **Tesorería - Cuadre Z** | Guardar cuadre | ❌ NO | - |
| **Tesorería - Cuadre Z** | Ajustar cuadre | ❌ NO | - |
| **CxP** | Marcar para pago | ❌ NO | - |
| **CxP** | Autorizar pago | ❌ NO | - |

### 1.3 ¿Se guarda valor anterior y valor nuevo?

| Módulo | valor_anterior | valor_nuevo |
|--------|----------------|-------------|
| Propinas Config (MongoDB) | ❌ NO | ❌ NO |
| Propinas Control (SQL) | ✅ SÍ | ✅ SÍ |
| Tesorería | ❌ NO | ❌ NO |
| CxP | ❌ NO | ❌ NO |

### 1.4 ¿Se registra usuario, fecha y módulo?

| Módulo | Usuario | Fecha | Módulo | IP |
|--------|---------|-------|--------|-----|
| Propinas Config | ✅ `created_by`, `updated_by` | ✅ `created_at`, `updated_at` | ❌ implícito | ❌ NO |
| Propinas Control | ✅ `usuario_id`, `usuario_email` | ✅ `fecha` | ❌ implícito | ✅ `ip_origen` |
| Tesorería | ❌ NO | ❌ NO | ❌ NO | ❌ NO |
| CxP | ❌ NO | ❌ NO | ❌ NO | ❌ NO |

### 1.5 ¿Las acciones están clasificadas (EDIT, CONFIRM, AUTHORIZE)?

| Módulo | Clasificación de acciones |
|--------|---------------------------|
| Propinas Control | ⚠️ PARCIAL - usa `accion` como VARCHAR libre |
| Resto | ❌ NO existe clasificación |

---

## 2. DIAGNÓSTICO

### 🔴 CRÍTICO: No existe auditoría funcional centralizada

- **Tesorería (Cuadre Z):** Las operaciones financieras más sensibles NO tienen rastro
- **CxP:** Las decisiones de pago NO quedan registradas
- **Propinas Config:** Solo se guarda quién cambió, pero NO el valor anterior

### 🟡 PARCIAL: Propinas TPV tiene diseño de auditoría

- La tabla `propinas_tpv_historial` en SQL Server tiene la estructura correcta
- Falta estandarizar los tipos de acción (EDIT/CONFIRM/AUTHORIZE)

---

## 3. PROPUESTA DE IMPLEMENTACIÓN

### 3.1 Tabla Centralizada de Auditoría (SQL Server - EDARSA HUB)

```sql
-- ============================================================================
-- TABLA: auditoria_financiera
-- Propósito: Log estructurado de auditoría funcional y financiera
-- Ubicación: Base de datos EDARSA HUB (SQL Server)
-- ============================================================================

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'auditoria_financiera')
BEGIN
    CREATE TABLE auditoria_financiera (
        -- ============================================
        -- IDENTIFICADORES
        -- ============================================
        id                  BIGINT IDENTITY(1,1)    PRIMARY KEY,
        
        -- ============================================
        -- CONTEXTO DE LA ACCIÓN
        -- ============================================
        fecha               DATETIME                NOT NULL DEFAULT GETDATE(),
        usuario_id          NVARCHAR(50)            NOT NULL,
        usuario_email       NVARCHAR(100)           NOT NULL,
        ip_origen           NVARCHAR(50)            NULL,
        
        -- ============================================
        -- CLASIFICACIÓN
        -- ============================================
        modulo              NVARCHAR(50)            NOT NULL,  -- TESORERIA, CXP, PROPINAS
        entidad             NVARCHAR(50)            NOT NULL,  -- cuadre_z, factura, config_propinas
        accion              NVARCHAR(20)            NOT NULL,  -- VIEW, EDIT, CONFIRM, AUTHORIZE
        
        -- ============================================
        -- REFERENCIA AL REGISTRO
        -- ============================================
        registro_id         NVARCHAR(100)           NOT NULL,  -- ID del registro afectado
        registro_folio      NVARCHAR(50)            NULL,      -- Folio legible (ej: CORTE-2025-001)
        sucursal_id         NVARCHAR(50)            NULL,      -- Sucursal afectada
        
        -- ============================================
        -- CAMBIOS
        -- ============================================
        campo_modificado    NVARCHAR(100)           NULL,      -- Campo específico
        valor_anterior      NVARCHAR(MAX)           NULL,      -- JSON si es complejo
        valor_nuevo         NVARCHAR(MAX)           NULL,      -- JSON si es complejo
        
        -- ============================================
        -- CONTEXTO ADICIONAL
        -- ============================================
        motivo              NVARCHAR(500)           NULL,      -- Motivo del cambio
        observaciones       NVARCHAR(MAX)           NULL,      -- Notas adicionales
        nivel_riesgo        NVARCHAR(20)            NULL,      -- BAJO, MEDIO, ALTO, CRITICO
        
        -- ============================================
        -- ÍNDICES
        -- ============================================
        INDEX IX_auditoria_fecha (fecha DESC),
        INDEX IX_auditoria_usuario (usuario_id, fecha DESC),
        INDEX IX_auditoria_modulo (modulo, entidad, fecha DESC),
        INDEX IX_auditoria_registro (registro_id, fecha DESC)
    );

    PRINT 'Tabla auditoria_financiera creada exitosamente';
END
GO

-- ============================================
-- RESTRICCIONES DE VALORES
-- ============================================
ALTER TABLE auditoria_financiera
ADD CONSTRAINT CK_auditoria_accion 
    CHECK (accion IN ('VIEW', 'EDIT', 'CONFIRM', 'AUTHORIZE'));

ALTER TABLE auditoria_financiera
ADD CONSTRAINT CK_auditoria_modulo 
    CHECK (modulo IN ('TESORERIA', 'CXP', 'PROPINAS', 'PRESUPUESTOS', 'INGRESOS'));

ALTER TABLE auditoria_financiera
ADD CONSTRAINT CK_auditoria_riesgo 
    CHECK (nivel_riesgo IS NULL OR nivel_riesgo IN ('BAJO', 'MEDIO', 'ALTO', 'CRITICO'));
GO
```

### 3.2 Acciones a Auditar por Módulo

#### TESORERÍA (Cuadre Z)

| Acción | Tipo | Nivel Riesgo | Datos a capturar |
|--------|------|--------------|------------------|
| Ver corte pendiente | VIEW | BAJO | corte_id, sucursal |
| Iniciar cuadre | EDIT | MEDIO | corte_id, sucursal, efectivo_sistema |
| Capturar conteo efectivo | EDIT | MEDIO | denominaciones antes/después |
| Guardar cuadre | CONFIRM | ALTO | totales, diferencia, ficha_deposito |
| Ajustar cuadre existente | EDIT | ALTO | campo_modificado, valor_anterior, valor_nuevo |
| Autorizar descuadre | AUTHORIZE | CRÍTICO | diferencia, motivo_autorizacion |
| Reabrir cuadre cerrado | AUTHORIZE | CRÍTICO | motivo |

#### CxP (Cuentas por Pagar)

| Acción | Tipo | Nivel Riesgo | Datos a capturar |
|--------|------|--------------|------------------|
| Ver facturas | VIEW | BAJO | filtros_aplicados |
| Marcar para pago | EDIT | MEDIO | factura_id, monto |
| Desmarcar factura | EDIT | MEDIO | factura_id, monto |
| Pago masivo | EDIT | ALTO | cantidad_facturas, monto_total |
| Autorizar pago | AUTHORIZE | CRÍTICO | factura_ids, monto_total, autorizador |
| Confirmar pago ejecutado | CONFIRM | ALTO | factura_id, referencia_bancaria |

#### PROPINAS TPV

| Acción | Tipo | Nivel Riesgo | Datos a capturar |
|--------|------|--------------|------------------|
| Ver configuración | VIEW | BAJO | - |
| Crear config % | EDIT | ALTO | porcentaje, alcance |
| Editar config % | EDIT | ALTO | porcentaje_anterior, porcentaje_nuevo |
| Activar/desactivar config | AUTHORIZE | ALTO | config_id, estado |
| Ver cuadre propinas | VIEW | BAJO | filtros |
| Registrar pago propinas | CONFIRM | ALTO | propina_id, monto, empleado |

### 3.3 Servicio de Auditoría (Backend)

```python
# /app/backend/core/auditoria.py

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class AccionAuditoria(Enum):
    VIEW = "VIEW"
    EDIT = "EDIT"
    CONFIRM = "CONFIRM"
    AUTHORIZE = "AUTHORIZE"

class ModuloAuditoria(Enum):
    TESORERIA = "TESORERIA"
    CXP = "CXP"
    PROPINAS = "PROPINAS"
    PRESUPUESTOS = "PRESUPUESTOS"
    INGRESOS = "INGRESOS"

class NivelRiesgo(Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"

class ServicioAuditoria:
    """
    Servicio centralizado de auditoría financiera.
    Registra todas las acciones en la tabla auditoria_financiera (SQL Server).
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def registrar(
        self,
        # Contexto del usuario
        usuario_id: str,
        usuario_email: str,
        ip_origen: Optional[str] = None,
        
        # Clasificación
        modulo: ModuloAuditoria,
        entidad: str,
        accion: AccionAuditoria,
        
        # Referencia
        registro_id: str,
        registro_folio: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        
        # Cambios
        campo_modificado: Optional[str] = None,
        valor_anterior: Optional[Any] = None,
        valor_nuevo: Optional[Any] = None,
        
        # Contexto
        motivo: Optional[str] = None,
        observaciones: Optional[str] = None,
        nivel_riesgo: Optional[NivelRiesgo] = None
    ) -> bool:
        """
        Registra un evento de auditoría.
        
        Returns:
            bool: True si se registró correctamente
        """
        try:
            # Serializar valores complejos a JSON
            val_ant = json.dumps(valor_anterior) if isinstance(valor_anterior, (dict, list)) else str(valor_anterior) if valor_anterior else None
            val_new = json.dumps(valor_nuevo) if isinstance(valor_nuevo, (dict, list)) else str(valor_nuevo) if valor_nuevo else None
            
            query = """
            INSERT INTO auditoria_financiera (
                usuario_id, usuario_email, ip_origen,
                modulo, entidad, accion,
                registro_id, registro_folio, sucursal_id,
                campo_modificado, valor_anterior, valor_nuevo,
                motivo, observaciones, nivel_riesgo
            ) VALUES (
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?
            )
            """
            
            await self.db.execute(query, [
                usuario_id, usuario_email, ip_origen,
                modulo.value, entidad, accion.value,
                registro_id, registro_folio, sucursal_id,
                campo_modificado, val_ant, val_new,
                motivo, observaciones, nivel_riesgo.value if nivel_riesgo else None
            ])
            
            return True
            
        except Exception as e:
            logger.error(f"Error registrando auditoría: {e}")
            # La auditoría NO debe bloquear la operación principal
            return False
    
    async def consultar_por_registro(
        self,
        registro_id: str,
        limite: int = 100
    ) -> list:
        """Obtiene historial de auditoría de un registro específico."""
        query = """
        SELECT TOP (?) *
        FROM auditoria_financiera
        WHERE registro_id = ?
        ORDER BY fecha DESC
        """
        return await self.db.fetch_all(query, [limite, registro_id])
    
    async def consultar_por_usuario(
        self,
        usuario_id: str,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        limite: int = 100
    ) -> list:
        """Obtiene historial de auditoría de un usuario."""
        query = """
        SELECT TOP (?) *
        FROM auditoria_financiera
        WHERE usuario_id = ?
        """
        params = [limite, usuario_id]
        
        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)
        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)
        
        query += " ORDER BY fecha DESC"
        
        return await self.db.fetch_all(query, params)
```

### 3.4 Ejemplo de Uso en Tesorería

```python
# En tesoreria.py - guardar_cuadre()

async def guardar_cuadre(
    cuadre_data: dict,
    current_user: dict,
    request: Request,
    auditoria: ServicioAuditoria
):
    # ... lógica de guardado ...
    
    # Registrar auditoría
    await auditoria.registrar(
        usuario_id=current_user['user_id'],
        usuario_email=current_user['email'],
        ip_origen=request.client.host,
        
        modulo=ModuloAuditoria.TESORERIA,
        entidad="cuadre_z",
        accion=AccionAuditoria.CONFIRM,
        
        registro_id=str(cuadre_data['corte_id']),
        registro_folio=cuadre_data.get('folio_corte'),
        sucursal_id=cuadre_data.get('sucursal_id'),
        
        valor_nuevo={
            'efectivo_contado': cuadre_data['efectivo_contado'],
            'diferencia': cuadre_data['diferencia'],
            'ficha_deposito': cuadre_data.get('ficha_deposito')
        },
        
        nivel_riesgo=NivelRiesgo.ALTO if cuadre_data.get('diferencia', 0) != 0 else NivelRiesgo.MEDIO
    )
```

---

## 4. PLAN DE IMPLEMENTACIÓN

### Fase 1: Crear tabla (1 día)
- [ ] Crear tabla `auditoria_financiera` en SQL Server EDARSA HUB
- [ ] Crear índices
- [ ] Verificar permisos de escritura

### Fase 2: Servicio backend (2 días)
- [ ] Crear `/app/backend/core/auditoria.py`
- [ ] Integrar con conexión SQL Server existente
- [ ] Pruebas unitarias

### Fase 3: Integrar en módulos (3 días)
- [ ] Tesorería: `guardar_cuadre`, `ajustar_cuadre`
- [ ] CxP: `marcar_pago`, `autorizar_pago`
- [ ] Propinas: Ya tiene `propinas_tpv_historial` → Migrar a tabla centralizada

### Fase 4: Consulta de auditoría (1 día)
- [ ] Endpoint `/api/auditoria/consultar`
- [ ] UI de consulta (opcional, puede ser solo backend)

---

## 5. RESUMEN

| Pregunta | Respuesta |
|----------|-----------|
| ¿Existe tabla formal? | ❌ NO (solo parcial en Propinas SQL) |
| ¿Qué se registra? | Solo cambios en `propinas_config` (parcial) |
| ¿valor_anterior / valor_nuevo? | Solo en `propinas_tpv_historial` (SQL) |
| ¿usuario, fecha, módulo? | Parcial en Propinas, NO en Tesorería/CxP |
| ¿Clasificación EDIT/CONFIRM/AUTHORIZE? | ❌ NO existe |

**RECOMENDACIÓN:** Implementar tabla centralizada `auditoria_financiera` en SQL Server con el esquema propuesto.

---

## 6. APROBACIÓN REQUERIDA

- [ ] Aprobar esquema de tabla `auditoria_financiera`
- [ ] Aprobar clasificación de acciones (VIEW/EDIT/CONFIRM/AUTHORIZE)
- [ ] Aprobar niveles de riesgo (BAJO/MEDIO/ALTO/CRÍTICO)
- [ ] Confirmar que SQL Server EDARSA HUB es la ubicación correcta
- [ ] Priorizar fase de implementación

---

**¿Apruebas esta propuesta para proceder con la implementación?**
