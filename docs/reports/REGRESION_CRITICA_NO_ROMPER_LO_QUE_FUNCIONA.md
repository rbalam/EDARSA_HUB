# REPORTE DE REGRESIÓN CRÍTICA

**Fecha:** 2025-05-19  
**Prioridad:** CRÍTICA  
**Estado:** ✅ RESTAURADO  
**Autor:** Agente E1

---

## 1. RESUMEN DE LA REGRESIÓN

### Síntomas Reportados
1. **Catálogo SQL:** Toast "Error al cargar catálogo"
2. **Explorador BD:** Primer filtro solo mostraba "Todos los sistemas"
3. **Catálogos del Sistema:** Toast "Error cargando catálogos"

### Causa Raíz
El cambio al endpoint dinámico `/catalogos/sistemas-capacidades/explorables-dinamico` causó problemas de:
1. **Formato diferente:** Devolvía `SoftRestaurant` (mixtas) vs `SOFTRESTAURANT` (mayúsculas)
2. **Sistemas faltantes:** No incluía `EDARSAHUB_SQL` ni `API_LOCAL`
3. **Mismatch de case:** El filtro comparaba con `===` estricto

---

## 2. ARCHIVOS MODIFICADOS PARA RESTAURAR

| Archivo | Cambio |
|---------|--------|
| `/app/frontend/src/services/exploradorService.js` | Restaurado endpoint original `/explorables` |
| `/app/frontend/src/pages/ExploradorBD.js` | Filtro case-insensitive |

---

## 3. VALIDACIÓN POST-FIX

### Endpoints Verificados (todos 200 OK)

| Endpoint | Status | Descripción |
|----------|--------|-------------|
| `/catalogos/sistemas-capacidades/explorables` | 200 | 4 sistemas |
| `/explorador/conexiones-explorables` | 200 | 12 conexiones |
| `/catalogo/consultas-rich` | 200 | 26 consultas |
| `/catalogos/dominios` | 200 | Dominios cargados |

### Sistemas en el Primer Filtro (Restaurado)
- API_LOCAL: API Local
- EDARSAHUB_SQL: EDARSAHUB SQL Server
- MPRO: ManagementPro
- SOFTRESTAURANT: SoftRestaurant

---

## 4. LECCIÓN TÉCNICA

**NO modificar contratos compartidos sin validar todos los consumidores.**

El endpoint `/catalogos/sistemas-capacidades/explorables` es consumido por múltiples componentes:
- Explorador BD
- Catálogo SQL (indirectamente)
- Otros módulos

Cambiar el endpoint o su formato sin validar todos los consumidores causa regresiones en cascada.

---

## 5. BACKOUT PLAN

Si el problema persiste:
```bash
git checkout HEAD~2 -- /app/frontend/src/services/exploradorService.js
git checkout HEAD~2 -- /app/frontend/src/pages/ExploradorBD.js
sudo supervisorctl restart frontend
```

---

## 6. NOTA SOBRE CLASIFICACIÓN ENTERPRISE

La mejora de clasificación Enterprise vs API Local queda **PAUSADA** hasta:
1. Diseñar un contrato que no rompa consumidores existentes
2. Validar con todas las pantallas afectadas
3. Obtener autorización explícita

---

*Reporte: 2025-05-19*
*Estado: RESTAURADO - Funcionalidad estable*
