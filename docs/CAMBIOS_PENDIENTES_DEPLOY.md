# EDARSA HUB - Registro de Cambios para Redeploy

## 📋 Propósito
Este documento registra los cambios significativos realizados en Preview que ameritan un Redeploy a Producción.

---

## 🚀 CAMBIOS PENDIENTES DE DEPLOY

### Sesión Actual (Diciembre 2025)

| Cambio | Impacto | Prioridad |
|--------|---------|-----------|
| FASE 16: Filtrado real por alcance en GET /api/users | ALTO | 🔴 Crítico |
| Control de acceso a tabs (Usuarios, Roles, Estructura, Bitácora) | ALTO | 🔴 Crítico |
| Permisos catálogos: puede_autorizar, puede_liberar | MEDIO | 🟡 Importante |
| SuperAdmin acceso total (visual en modal) | BAJO | 🟢 Mejora UI |
| Fix: SuperAdmin puede acceder a /api/roles/modulos | MEDIO | 🟡 Importante |
| Fix: SuperAdmin puede asignar permisos catálogos | MEDIO | 🟡 Importante |
| Botón Permisos para rol Administrador | BAJO | 🟢 Mejora UI |

### Resumen
- **Cambios críticos**: 2
- **Cambios importantes**: 3
- **Mejoras UI**: 2

---

## ✅ RECOMENDACIÓN

**Estado actual: LISTO PARA REDEPLOY**

Los cambios de FASE 16 (RBAC alcance real) son significativos y estables. Se recomienda hacer redeploy para que producción tenga:
- Filtrado de usuarios por alcance organizacional
- Control de acceso correcto a todos los tabs
- Correcciones de permisos para SuperAdmin

---

## 📝 HISTORIAL DE DEPLOYS

| Fecha | Versión | Cambios Incluidos |
|-------|---------|-------------------|
| (Pendiente) | 4.9.0 | FASE 16 + fixes de permisos |

---

## 🔔 POLÍTICA DE NOTIFICACIÓN

El agente notificará al usuario cuando:
1. Se complete una FASE del RBAC
2. Se corrija un bug crítico
3. Se agregue funcionalidad nueva significativa
4. Acumulen 5+ cambios menores

---

**Última actualización**: Diciembre 2025
