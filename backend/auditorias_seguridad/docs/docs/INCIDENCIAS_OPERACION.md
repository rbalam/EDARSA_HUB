# EDARSA HUB - Incidencias de Operación Real

**Sistema:** EDARSA HUB  
**Fase:** Operación Real Controlada  
**Inicio de operación real:** 15 de Abril de 2026

---

## Registro de Incidencias

> Este documento registra incidencias detectadas durante la operación real del sistema.
> Cada incidencia se clasifica por severidad y módulo afectado.

### Clasificación de Severidad

| Nivel | Descripción | Acción |
|-------|-------------|--------|
| **CRÍTICA** | Sistema inoperante o pérdida de datos | Corrección inmediata |
| **ALTA** | Funcionalidad principal afectada | Corrección en 24h |
| **MEDIA** | Funcionalidad secundaria afectada | Corrección planificada |
| **BAJA** | Inconveniencia menor | Backlog |

---

## Incidencias Activas

_Ninguna incidencia activa al momento de iniciar operación real._

---

## Incidencias Resueltas

### INC-001: Expiración rápida de sesión JWT
- **Fecha detectada:** 15 de Abril de 2026
- **Severidad:** MEDIA
- **Módulo:** Autenticación
- **Síntoma:** La sesión expiraba en menos de 1 minuto durante pruebas
- **Causa raíz:** Token configurado a 24h pero comportamiento errático
- **Solución:** 
  - Expiración aumentada a 72 horas
  - JWT_SECRET fijado en .env sin fallback
  - Variable `JWT_EXPIRATION_HOURS` configurable
- **Archivos modificados:**
  - `/app/backend/core/security.py`
  - `/app/backend/.env`
- **Fecha resolución:** 15 de Abril de 2026
- **Estado:** ✅ RESUELTO

---

## Observaciones Operativas

### Módulos en Operación Real

| Módulo | Estado | Observaciones |
|--------|--------|---------------|
| Autenticación | ✅ Operativo | JWT 72h, secret fijo |
| CxP | ✅ Operativo | Datos reales (use_demo=False) |
| Tesorería | ✅ Operativo | Pendiente: Precarga de declaración cajera |
| Propinas TPV | ✅ Operativo | Config % descuento funcional |
| Control de Ingresos | ✅ Operativo | Datos reales |
| Portal Proveedores | ✅ Operativo | - |

### Módulos Pendientes de Validación VPN

| Módulo | Dependencia |
|--------|-------------|
| Sincronización Propinas | Conexión VPN a SoftRestaurant |
| Cortes Z reales | Conexión VPN a SoftRestaurant |

---

## Decisiones Arquitectónicas en Operación

1. **Tesorería solo valida, no recaptura** - La cajera declara en SoftRestaurant, Tesorería confirma.
2. **Propinas contenidas en Corte Z** - El descuento del 2% está dentro del efectivo declarado.
3. **EDARSA HUB es fuente de verdad** - SoftRestaurant y MPRO son solo lectura.
4. **MongoDB solo para cache** - Persistencia oficial en SQL Server.

---

## Histórico de Cambios en Producción

| Fecha | Cambio | Impacto |
|-------|--------|---------|
| 2026-04-15 | JWT 72h + Secret fijo | Sesiones estables |
| 2026-04-15 | use_demo=False default | Datos reales activos |
| 2026-04-15 | Tab Propinas TPV | Nuevo módulo operativo |

---

_Última actualización: 15 de Abril de 2026_
