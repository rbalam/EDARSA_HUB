# INCIDENTE CRÍTICO: Ventas del Día - Doble Ruta, FechaOperacion y Anti-$0

**Fecha:** 2026-05-20  
**Prioridad:** P0  
**Estado:** EN PROGRESO - CAUSA RAÍZ IDENTIFICADA

---

## 1. Causa Raíz Real: Hot-Reload + APScheduler

### Problema Confirmado

El backend se ejecuta con `--reload` (hot-reload de uvicorn). Esto causa que:

1. Cuando hay cambios de código, uvicorn crea un **nuevo proceso**
2. El nuevo proceso registra el scheduler APScheduler
3. Durante la transición, el proceso anterior puede seguir ejecutando brevemente
4. Resultado: **Dos schedulers** ejecutan el mismo job con **código diferente**

### Evidencia

| RunID | Hora (segundos) | FechaInicio | Tiene Log DIAG |
|-------|-----------------|-------------|----------------|
| `014705-09c3` | **:00** | 2026-05-20 ❌ | **NO** |
| `013834-8fc3` | :34 | 2026-05-19 ✅ | **SÍ** |
| `012830-8faa` | :30 | 2026-05-19 ✅ | **SÍ** |

**Los jobs del segundo :00 (scheduler antiguo) NO ejecutan el código nuevo con logging DIAG.**
**Los jobs del segundo :30-:34 (scheduler nuevo) SÍ ejecutan el código correcto.**

---

## 2. Correcciones Implementadas

### A) Anti-$0 Falso ✅
- Si existe snapshot con venta > 0, no sobrescribir con $0
- Si la fecha_operacion cambia, SIEMPRE actualizar (permite corregir datos)

### B) Logging Diagnóstico ✅
- Cada ejecución registra run_id, PID, UTC, México, fecha_hoy

### C) SERVER_SECRET_KEY ✅
- Ya está configurada en `/app/backend/.env`
- El descifrado de API keys funciona correctamente

---

## 3. Estado Actual de Conexiones

| Servidor | Tipo | Estado |
|----------|------|--------|
| 130° QRO LOCAL | API_LOCAL | ⚠️ Error 500 - Timeout SQL interno |
| ORIGEN LOCAL | API_LOCAL | ⚠️ Error 500 - Timeout SQL interno |
| CIENFUEGOS | SQL | ❌ Timeout |
| LA ESTELAR | SQL | ❌ Error de login |
| 130° MÉRIDA | SQL | ⚠️ Sin respuesta |

**Nota:** Las APIs MPRO responden (HTTP 422/500) pero sus conexiones SQL internas fallan.

---

## 4. Solución Propuesta (REQUIERE AUTORIZACIÓN)

### Opción A: Modificar supervisor.conf para quitar --reload

**Archivo:** `/etc/supervisor/conf.d/supervisord.conf`

**Antes:**
```
command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload
```

**Después:**
```
command=/root/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1
```

**Riesgo:** Cambios de código no se recargarán automáticamente (requiere restart manual)

### Opción B: Agregar singleton lock al scheduler

Implementar un lock distribuido (en MongoDB o EDARSAHUB) que prevenga que múltiples instancias del scheduler ejecuten el mismo job.

---

## 5. Verificaciones Pendientes

- [ ] Conexiones SoftRestaurant realmente restablecidas
- [ ] APIs MPRO pueden conectar a sus SQL internos
- [ ] Un solo scheduler activo
- [ ] Todos los datos con FechaOperacion=2026-05-19

---

*Reporte actualizado: 2026-05-20 01:50 UTC*
