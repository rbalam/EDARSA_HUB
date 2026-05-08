# PLAN DE MIGRACIÓN: Conexiones de Servidores
## De MongoDB a EDARSAHUB (SQL Server)

**Versión**: 2.0  
**Fecha**: 2026-04-23 (Actualizado: 2026-04-24)  
**Estado**: FASE 2/3 COMPLETADA  
**Prioridad**: CRÍTICA - Sistema en producción

---

## RESUMEN EJECUTIVO DE PROGRESO

| Fase | Estado | Fecha |
|------|--------|-------|
| **FASE 0** | ✅ COMPLETADA | 2026-04-23 |
| **FASE 1** | ✅ COMPLETADA | 2026-04-23 |
| **FASE 2/3** | ✅ COMPLETADA | 2026-04-24 |
| **FASE 4** | ⬜ PENDIENTE | - |

### LOGROS FASE 2/3 (24-Abril-2026)
- ✅ `get_servers_for_tablero()` ahora lee de EDARSAHUB SQL como fuente primaria
- ✅ `get_server_by_id()` ahora lee de EDARSAHUB SQL como fuente primaria
- ✅ Fallback automático a MongoDB si SQL falla (migración sin ruptura)
- ✅ Paridad estructural mantenida (diccionarios idénticos al esquema original)
- ✅ Variable de entorno `USE_SQL_FOR_SERVERS` para rollback inmediato

### ROLLBACK INMEDIATO
Para revertir a MongoDB:
```bash
# En backend/.env agregar:
USE_SQL_FOR_SERVERS=false
# Reiniciar backend
sudo supervisorctl restart backend
```

---

## 1. OBJETIVO

Migrar la configuración de conexiones de servidores desde MongoDB (colección `servers`) hacia la base de datos SQL `EDARSAHUB`, estableciendo EDARSAHUB SQL como el **cerebro único** del sistema.

---

## 2. PRINCIPIOS OBLIGATORIOS

| Principio | Descripción |
|-----------|-------------|
| **NO ROMPER NADA** | El sistema debe seguir operando durante toda la migración |
| **ROLLBACK INMEDIATO** | Cada fase debe poder revertirse en < 5 minutos |
| **CERO DOWNTIME** | Sin interrupción de servicio |
| **VALIDACIÓN ANTES DE CORTE** | Verificar paridad antes de cambiar fuente |

---

## 3. ESTADO ACTUAL

### 3.1 Fuente actual (MongoDB)

```
Colección: servers
Documentos: 10 servidores
Campos: id, name, host, port, database, username, password, 
        system_type, active, tipo_conexion, etc.
```

### 3.2 Destino (EDARSAHUB SQL)

```
Servidor: 54.39.104.176:1433
Base de datos: EDARSAHUB
Tablas actuales: 180 (ninguna específica para conexiones de servidores)
Conectividad: ✅ Verificada desde preview
```

---

## 4. FASES DE MIGRACIÓN

### FASE 0: PREPARACIÓN (Sin cambios en producción)
**Duración estimada**: 1 día  
**Riesgo**: NINGUNO

| Paso | Acción | Validación |
|------|--------|------------|
| 0.1 | Crear tabla `Servidores_Conexiones` en EDARSAHUB SQL | Query exitosa |
| 0.2 | Crear tabla `Servidores_Conexiones_Log` para auditoría | Query exitosa |
| 0.3 | Documentar estructura de datos actual en MongoDB | Documento generado |
| 0.4 | Crear script de migración de datos | Script probado en ambiente aislado |

**Rollback**: No aplica (no hay cambios en producción)

---

### FASE 1: DUPLICACIÓN (Escritura dual)
**Duración estimada**: 3-5 días de observación  
**Riesgo**: BAJO

| Paso | Acción | Validación |
|------|--------|------------|
| 1.1 | Migrar datos existentes de MongoDB → EDARSAHUB SQL | Conteo igual |
| 1.2 | Modificar código para escribir en AMBAS fuentes | Logs sin errores |
| 1.3 | Leer sigue siendo de MongoDB (sin cambio) | Funcionalidad intacta |
| 1.4 | Monitorear paridad diaria | Diff = 0 |

**Arquitectura Fase 1:**
```
                    ┌─────────────────┐
                    │   Aplicación    │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │    MongoDB      │           │  EDARSAHUB SQL  │
    │   (LECTURA)     │           │  (ESCRITURA)    │
    │   (ESCRITURA)   │           │                 │
    └─────────────────┘           └─────────────────┘
```

**Rollback**: Quitar escritura dual, volver a solo MongoDB

---

### FASE 2: VALIDACIÓN DE PARIDAD
**Duración estimada**: 2-3 días  
**Riesgo**: BAJO

| Paso | Acción | Validación |
|------|--------|------------|
| 2.1 | Comparar todos los registros MongoDB vs SQL | Diff = 0 |
| 2.2 | Verificar que cambios en UI se reflejan en ambos | Tests manuales OK |
| 2.3 | Verificar timestamps y auditoría | Logs consistentes |
| 2.4 | Aprobación del usuario para continuar | Autorización explícita |

**Criterio de éxito:**
- 100% de registros idénticos
- 0 errores de sincronización en 48 horas
- Aprobación del usuario

**Rollback**: Volver a Fase 1 si hay discrepancias

---

### FASE 3: CAMBIO DE LECTURA (SQL como primario)
**Duración estimada**: 1 día + 3-5 días observación  
**Riesgo**: MEDIO

| Paso | Acción | Validación |
|------|--------|------------|
| 3.1 | Cambiar lectura de MongoDB → EDARSAHUB SQL | Funcionalidad OK |
| 3.2 | Mantener escritura en AMBAS fuentes (backup) | Paridad OK |
| 3.3 | Monitorear rendimiento | Sin degradación |
| 3.4 | Validar todos los módulos que usan servidores | Tests OK |

**Arquitectura Fase 3:**
```
                    ┌─────────────────┐
                    │   Aplicación    │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │    MongoDB      │           │  EDARSAHUB SQL  │
    │   (ESCRITURA)   │◄─────────▶│   (LECTURA)     │
    │   (BACKUP)      │           │   (ESCRITURA)   │
    └─────────────────┘           └─────────────────┘
```

**Rollback**: Cambiar lectura de vuelta a MongoDB (1 línea de config)

---

### FASE 4: CONSOLIDACIÓN (SQL como único)
**Duración estimada**: 1 día  
**Riesgo**: BAJO (si Fase 3 fue exitosa)

| Paso | Acción | Validación |
|------|--------|------------|
| 4.1 | Quitar escritura a MongoDB | Solo SQL escribe |
| 4.2 | Marcar colección MongoDB como deprecated | Documentado |
| 4.3 | Mantener datos en MongoDB como backup histórico | Sin eliminar |
| 4.4 | Documentar nueva arquitectura | Doc actualizado |

**Arquitectura Final:**
```
                    ┌─────────────────┐
                    │   Aplicación    │
                    └────────┬────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   EDARSAHUB SQL     │
                  │   (CEREBRO ÚNICO)   │
                  │                     │
                  │   - Conexiones      │
                  │   - Configuración   │
                  │   - Auditoría       │
                  └─────────────────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │    MongoDB          │
                  │  (BACKUP/HISTÓRICO) │
                  └─────────────────────┘
```

**Rollback**: Reactivar escritura dual, volver a Fase 3

---

## 5. ESTRUCTURA DE TABLA PROPUESTA EN SQL

```sql
-- Tabla principal de conexiones
CREATE TABLE Servidores_Conexiones (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    nombre NVARCHAR(100) NOT NULL,
    system_type NVARCHAR(50) NOT NULL,  -- SoftRestaurant, MPRO, EDARSA_HUB, Otro
    tipo_conexion NVARCHAR(20) NOT NULL, -- DATA_SOURCE, CORE, API
    
    -- Conexión SQL
    host NVARCHAR(255),
    port INT DEFAULT 1433,
    database_name NVARCHAR(100),
    username NVARCHAR(100),
    password_encrypted NVARCHAR(500),  -- Encriptado
    
    -- Conexión API (si aplica)
    api_url NVARCHAR(500),
    api_key_encrypted NVARCHAR(500),
    
    -- Estado
    activo BIT DEFAULT 1,
    visible_en_operaciones BIT DEFAULT 1,
    visible_en_listado BIT DEFAULT 1,
    es_editable_ui BIT DEFAULT 1,
    es_eliminable_ui BIT DEFAULT 1,
    
    -- Metadata
    empresa_id NVARCHAR(100),
    sucursales NVARCHAR(MAX),  -- JSON array
    
    -- Auditoría
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    created_by NVARCHAR(100),
    updated_by NVARCHAR(100)
);

-- Índices
CREATE INDEX IX_Servidores_Tipo ON Servidores_Conexiones(tipo_conexion);
CREATE INDEX IX_Servidores_Activo ON Servidores_Conexiones(activo);
CREATE INDEX IX_Servidores_SystemType ON Servidores_Conexiones(system_type);

-- Tabla de auditoría
CREATE TABLE Servidores_Conexiones_Log (
    log_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    servidor_id UNIQUEIDENTIFIER,
    accion NVARCHAR(20),  -- INSERT, UPDATE, DELETE
    datos_anteriores NVARCHAR(MAX),  -- JSON
    datos_nuevos NVARCHAR(MAX),  -- JSON
    usuario NVARCHAR(100),
    fecha DATETIME DEFAULT GETDATE(),
    ip_origen NVARCHAR(50)
);
```

---

## 6. ARCHIVOS A MODIFICAR

| Archivo | Fase | Cambio |
|---------|------|--------|
| `/app/backend/modules/comercial/repository.py` | 1, 3 | Agregar funciones para SQL |
| `/app/backend/core/db.py` | 1 | Agregar conexión a EDARSAHUB SQL |
| `/app/backend/modules/comercial/routes.py` | 3 | Cambiar fuente de lectura |
| `/app/backend/server.py` | 1 | Inicializar conexión SQL |

---

## 7. VALIDACIONES POR MÓDULO

| Módulo | Usa `servers` | Prioridad |
|--------|---------------|-----------|
| Tablero Ejecutivo | ✅ | ALTA |
| Dashboard por servidor | ✅ | ALTA |
| Menú Servidores | ✅ | ALTA |
| Compras | ✅ | ALTA |
| Sync Agent | ✅ | MEDIA |
| KPIs consolidados | ✅ | MEDIA |

---

## 8. PLAN DE ROLLBACK

| Fase | Acción de Rollback | Tiempo |
|------|-------------------|--------|
| 1 | Quitar escritura dual | 5 min |
| 2 | N/A (solo validación) | - |
| 3 | Cambiar lectura a MongoDB | 1 min |
| 4 | Reactivar escritura dual | 5 min |

---

## 9. CHECKLIST PRE-MIGRACIÓN

- [ ] Backup completo de MongoDB (`servers`)
- [ ] Backup de EDARSAHUB SQL (si hay datos)
- [ ] Script de migración probado en ambiente de test
- [ ] Script de rollback probado
- [ ] Monitoreo configurado
- [ ] Horario de baja carga identificado
- [ ] Usuario informado y disponible para validar

---

## 10. CRITERIOS DE ÉXITO FINAL

| Criterio | Validación |
|----------|------------|
| Todas las conexiones en EDARSAHUB SQL | COUNT = igual que MongoDB |
| Sistema operativo sin errores | 0 errores en 48h |
| Rendimiento sin degradación | Response time <= actual |
| Todos los módulos funcionando | Tests manuales OK |
| Auditoría funcionando | Logs en tabla SQL |

---

## APROBACIÓN REQUERIDA

Para iniciar la **FASE 0** (preparación), necesito:

1. ✅ Confirmación de que EDARSAHUB SQL es el destino correcto
2. ⬜ Aprobación del usuario para crear las tablas en EDARSAHUB
3. ⬜ Confirmación de permisos de escritura en EDARSAHUB (usuario actual es `HRLectura`)

---

**¿Autoriza proceder con la FASE 0 (Preparación)?**
