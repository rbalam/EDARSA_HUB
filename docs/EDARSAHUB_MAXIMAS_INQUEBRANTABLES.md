# EDARSAHUB - MÁXIMAS INQUEBRANTABLES
## Documento de Arquitectura y Políticas Fundamentales

**Versión:** 1.0  
**Fecha:** 2026-06-02  
**Estado:** VIGENTE - CUMPLIMIENTO OBLIGATORIO

---

## 🏛️ ARQUITECTURA CANÓNICA (OBLIGATORIA)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FUENTES EXTERNAS                              │
│         SoftRestaurant  /  MPRO  /  NetPay                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Scheduler / Jobs]
                    Sincronizaciones controladas
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EDARSAHUB SQL SERVER                          │
│   ┌─────────────────┐    ┌─────────────────────────────────┐    │
│   │  Tablas Sync_*  │ →  │  Vistas / Agregados / SP        │    │
│   │  Comercial_*    │    │  VW_KPIsEjecutivos              │    │
│   └─────────────────┘    └─────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                         [FastAPI]
                    Endpoints REST seguros
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    REACT DASHBOARD                               │
│                    Portal Inteligencia                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚫 ANTIPATRÓN PROHIBIDO

```
┌─────────────────────────────────────────────────────────────────┐
│              ❌ ARQUITECTURA PROHIBIDA ❌                         │
│                                                                   │
│   React / FastAPI Dashboard                                       │
│            ↓                                                      │
│   MongoDB o Conexión LIVE a Soft/MPRO                            │
│                                                                   │
│   PROBLEMAS:                                                      │
│   - Latencia en dashboards                                        │
│   - Dependencia de disponibilidad POS                             │
│   - Riesgo de sobrecarga en sistemas origen                       │
│   - Datos inconsistentes entre vistas                             │
│   - Imposibilidad de auditoría                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📜 LAS 10 MÁXIMAS INQUEBRANTABLES

### MÁXIMA 1: NO-LIVE EN DASHBOARDS
> **Los dashboards y reportes ejecutivos NUNCA consultan sistemas externos en tiempo real.**

- ❌ PROHIBIDO: `pymssql.connect()` a SoftRestaurant desde endpoints de dashboard
- ❌ PROHIBIDO: `requests.get()` a APIs MPRO desde reportes
- ✅ PERMITIDO: Lectura de vistas SQL EDARSAHUB pre-sincronizadas

### MÁXIMA 2: SQL SERVER ES LA FUENTE DE VERDAD
> **Toda información operativa existe primero en EDARSAHUB SQL Server.**

- La tabla canónica siempre está en SQL Server
- MongoDB es SOLO caché temporal o legacy en migración
- Las decisiones de negocio se basan en datos SQL

### MÁXIMA 3: SINCRONIZACIÓN CONTROLADA
> **Las conexiones a sistemas externos SOLO ocurren dentro de Jobs programados.**

Paths permitidos para conexiones live:
- `/scheduler/`
- `/jobs/`
- `/sync/`
- `/sincronizacion/`
- `/adapters.py` (solo si no se importa desde endpoints)

### MÁXIMA 4: GOBIERNO DE TABLAS
> **Cada tabla tiene un propietario, estado y reglas de uso documentados.**

Tabla de gobierno: `Sistema_Gobierno_Tablas`
- Categorías: CANONICA, SINCRONIZADA, DERIVADA, LEGADO_REVISION, STAGING, LOG
- Estados: ACTIVA, NO_USAR_NUEVO, DEPRECADA

### MÁXIMA 5: VISTAS COMO CONTRATO
> **Los dashboards consumen VISTAS, no tablas directamente.**

- `Comercial_Inteligencia_VW_KPIsEjecutivos` - KPIs ejecutivos
- `Comercial_Inteligencia_VW_SyncStatus` - Estado de sincronización
- `Sistema_VW_Servidores_Conexiones_Publico` - Servidores sin credenciales

### MÁXIMA 6: CREDENCIALES NUNCA AL FRONTEND
> **El frontend JAMÁS recibe contraseñas, API keys ni queries SQL.**

Vista pública obligatoria: `Sistema_VW_Servidores_Conexiones_Publico`
Campos prohibidos en respuestas API:
- `password_encrypted`
- `api_key_encrypted`
- `username` (si no es necesario)
- `query_ventas`, `query_inventario`, `query_movimientos`

### MÁXIMA 7: RBAC SQL-NATIVE
> **Los permisos se definen y validan en SQL Server.**

Tablas canónicas:
- `Sistema_RBAC_Permisos`
- `Sistema_RBAC_Roles`
- `Sistema_RBAC_RolesPermisos`

### MÁXIMA 8: AUDITORÍA PERMANENTE
> **Toda acción crítica deja rastro en SQL Server.**

- Cambios de configuración → Log
- Ejecución de sincronizaciones → Log
- Errores de sistema → Log

### MÁXIMA 9: MIGRACIÓN DOCUMENTADA
> **Cada colección MongoDB tiene un plan de migración a SQL.**

Tabla de mapeo: `Sistema_Migracion_MongoSQL_Mapeo`
- Estado: PENDIENTE, EN_PROGRESO, COMPLETADA, DEPRECADA
- Prioridad: P0, P1, P2

### MÁXIMA 10: CERO DEPENDENCIAS EXTERNAS EN RUNTIME
> **El dashboard debe funcionar aunque SoftRestaurant/MPRO estén caídos.**

- Datos pre-sincronizados en SQL
- Fallbacks proporcionales para gráficos
- Indicadores de "última sincronización"

### MÁXIMA 11: GOBIERNO PREVIO A CREACIÓN
> **Cualquier tabla nueva debe validarse contra `Sistema_Gobierno_Tablas` antes de crearse.**

```sql
-- OBLIGATORIO antes de CREATE TABLE:
SELECT * FROM Sistema_Gobierno_Tablas
WHERE nombre_tabla LIKE '%<nombre_similar>%'
   OR modulo = '<modulo_destino>';

-- Si no existe conflicto, registrar PRIMERO:
INSERT INTO Sistema_Gobierno_Tablas 
    (nombre_tabla, modulo, categoria, estado)
VALUES 
    ('<nueva_tabla>', '<modulo>', '<categoria>', 'ACTIVA');

-- DESPUÉS crear la tabla
CREATE TABLE ...
```

Checklist obligatorio:
1. ✅ Verificar que no existe tabla similar
2. ✅ Verificar que no existe tabla LEGADO con mismo propósito
3. ✅ Definir clasificación: CANONICA, SINCRONIZADA, DERIVADA
4. ✅ Registrar en gobierno ANTES de CREATE
5. ✅ Documentar fuente de verdad

---

## 🔧 LAS TRES PIEZAS FUNDAMENTALES

### 1. Sistema_Gobierno_Tablas
```sql
-- Registra el estado y uso permitido de cada tabla
SELECT * FROM Sistema_Gobierno_Tablas WHERE estado = 'ACTIVA';
```

### 2. Auditoría MongoDB/Live
```bash
# Detecta violaciones de conexiones live
python backend/core/policies/no_live_dashboard_policy.py
bash scripts/audit_mongodb_dependencies.sh /app
bash scripts/audit_live_connections.sh /app
```

### 3. Comercial_Inteligencia_VW_KPIsEjecutivos
```sql
-- Vista única de KPIs ejecutivos (fuente de verdad para dashboards)
SELECT * FROM Comercial_Inteligencia_VW_KPIsEjecutivos;
EXEC Sp_Validar_Inteligencia_Comercial_Status;
```

---

## 📋 CHECKLIST DE CUMPLIMIENTO

Antes de cada release, verificar:

- [ ] `python backend/core/policies/no_live_dashboard_policy.py` retorna OK
- [ ] Nuevas tablas registradas en `Sistema_Gobierno_Tablas`
- [ ] Colecciones MongoDB tienen plan en `Sistema_Migracion_MongoSQL_Mapeo`
- [ ] Endpoints de dashboard usan vistas, no tablas directas
- [ ] Credenciales excluidas de respuestas API
- [ ] Jobs de sincronización tienen logs activos

---

## 🚨 VIOLACIONES Y CONSECUENCIAS

| Nivel | Descripción | Acción |
|-------|-------------|--------|
| CRÍTICO | Conexión live en endpoint de dashboard | Bloquear deploy |
| ALTO | Credenciales expuestas en API | Hotfix inmediato |
| MEDIO | Tabla sin gobierno documentado | Documentar antes de merge |
| BAJO | MongoDB usado sin plan de migración | Agregar a backlog P1 |

---

## 📚 DOCUMENTOS RELACIONADOS

- `/app/backend/core/policies/no_live_dashboard_policy.py`
- `/app/scripts/audit_mongodb_dependencies.sh`
- `/app/scripts/audit_live_connections.sh`
- `/app/backend/database/migrations/*.sql`
- `/app/docs/reports/AUDITORIA_*.md`

---

*Este documento es ley. No hay excepciones.*

**Firmado:** Arquitectura EDARSAHUB  
**Vigencia:** Permanente
