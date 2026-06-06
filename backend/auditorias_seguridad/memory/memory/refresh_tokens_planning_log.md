# REFRESH TOKENS PLANNING LOG
## Bitácora de Planificación - P1-REFRESH-TOKENS

**Iniciado:** 2025-04-27  
**Estado:** DISEÑO TÉCNICO COMPLETADO  
**Responsable:** Agente E1

---

## ENTRADA 2025-04-27 - DISEÑO TÉCNICO

### Objetivo
Diseñar el sistema de refresh tokens, rotación, revocación y sesiones seguras para EDARSA HUB sin implementar código.

### Análisis del Estado Actual

**Archivos revisados:**
- `/app/backend/core/security.py` - Funciones de auth, JWT, cookies
- `/app/backend/modules/auth/routes.py` - Endpoints login/logout/me
- `/app/backend/routes/portal_proveedores.py` - Auth del portal
- `/app/backend/core/db.py` - Conexiones SQL Server

**Configuración actual:**
- Access Token: JWT HS256, 72 horas
- Cookie interna: `edarsa_access_token`, httpOnly, path=/
- Cookie portal: `edarsa_portal_access_token`, httpOnly, path=/api/portal
- No hay refresh token
- No hay tabla de sesiones
- Logout no revoca token (solo elimina cookie)

### Decisiones de Diseño

1. **EDARSAHUB como fuente de verdad:** Sesiones en SQL Server, no MongoDB
2. **Hash de refresh tokens:** Nunca almacenar token plano
3. **Rotación de tokens:** Nuevo refresh token en cada uso
4. **Detección de replay:** FamiliaTokenID para revocar toda la familia
5. **Separación portal/interno:** Tablas y cookies completamente separadas

### Entregables Generados

1. `/app/docs/P1_REFRESH_TOKENS_TECHNICAL_PLAN.md`
   - Estado actual documentado
   - Objetivo propuesto
   - Diseño de cookies
   - Modelo de datos SQL
   - Endpoints propuestos
   - Flujos diagramados
   - Plan de seguridad
   - Plan de compatibilidad
   - Fases de implementación
   - Pruebas necesarias
   - Riesgos identificados
   - Recomendación final

2. `/app/memory/refresh_tokens_planning_log.md` (este archivo)

### Tiempos Recomendados

| Token | Duración |
|-------|----------|
| Access Token | 15 minutos |
| Refresh Token Interno | 7 días |
| Refresh Token Portal | 24 horas |

### Fases de Implementación Propuestas

- **Fase A:** Backend - Modelo + Endpoints Base
- **Fase B:** Frontend - Refresh Automático
- **Fase C:** Portal Proveedores
- **Fase D:** Revocación y Administración
- **Fase E:** Limpieza y Hardening

### Criterios de Aceptación Cumplidos

- [x] No propone MongoDB como fuente maestra
- [x] No guarda tokens planos (solo hash)
- [x] Mantiene EDARSAHUB como cerebro
- [x] Mantiene separación portal/interno
- [x] Tiene rollback
- [x] Tiene pruebas
- [x] No implementa código todavía

### Recomendación

Validar AUTH en dominio personalizado **antes** de implementar refresh tokens para asegurar que las cookies funcionan correctamente en producción real.

### Próximos Pasos

1. Usuario aprueba el plan técnico
2. Validar AUTH en dominio personalizado (si disponible)
3. Implementar Fase A (backend)
4. Continuar con fases siguientes

---

---

## ENTRADA 2025-04-27 - FASE A IMPLEMENTACIÓN

### Estado
IMPLEMENTACIÓN COMPLETA - PRUEBAS BLOQUEADAS

### Archivos creados/modificados

| Archivo | Acción | Líneas |
|---------|--------|--------|
| `/app/docs/sql/CREATE_SESIONES_REFRESH_TOKENS.sql` | CREADO | 283 |
| `/app/backend/core/refresh_tokens.py` | CREADO | 868 |
| `/app/backend/core/security.py` | MODIFICADO | +50 |
| `/app/backend/modules/auth/routes.py` | MODIFICADO | +150 |
| `/app/backend/modules/auth/service.py` | MODIFICADO | +20 |

### Verificaciones realizadas

- [x] Backend inicia sin errores de compilación
- [x] No hay auto-creación de tablas en código
- [x] Imports válidos en todos los módulos
- [x] Login legacy sigue funcionando
- [x] Endpoint `/api/auth/logout` funciona

### Bloqueo actual

El usuario NO ha ejecutado el script SQL en EDARSAHUB.

**Pruebas bloqueadas:**
- Crear sesión SQL
- Refresh token
- Rotación
- Logout-all
- Detección de replay

### Documentación generada

1. `/app/docs/P1_REFRESH_TOKENS_PHASE_A_SQL_EXECUTION_GUIDE.md`
   - Instrucciones paso a paso para SSMS
   - Queries de validación
   - Script de rollback

2. `/app/docs/P1_REFRESH_TOKENS_PHASE_A_BACKEND_REPORT.md`
   - Resumen de implementación
   - Verificaciones realizadas
   - Pruebas pendientes
   - Criterios de aceptación

### Próximos pasos

1. Usuario ejecuta script SQL
2. Usuario confirma creación de tablas
3. Agente ejecuta pruebas de integración
4. Agente cierra Fase A

---

## HISTORIAL DE CAMBIOS

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2025-04-27 | Creación del plan técnico | Agente E1 |
| 2025-04-27 | Implementación Fase A backend | Agente E1 |
| 2025-04-27 | Documentación guía SQL y reporte | Agente E1 |

---
