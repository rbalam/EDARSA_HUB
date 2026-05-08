# BACKEND COMPLEXITY REFACTOR PLAN
## EDARSA HUB - Plan de Refactorización de Funciones Complejas

**Fecha:** 2025-12-XX  
**Estado:** DOCUMENTACIÓN PARA FASES FUTURAS  
**Prioridad:** BAJA (funciones estables, no causan errores)

---

## 1. RESUMEN

Este documento describe el plan de refactorización de funciones complejas identificadas en el reporte de calidad. **NO SE EJECUTARÁ EN LA FASE DE ESTABILIZACIÓN** porque las funciones están funcionando correctamente.

---

## 2. FUNCIONES ANALIZADAS

### 2.1 `core/cache_key_builder.py` - `build_context_cache_key()`
**Líneas:** 369 total (función ~123 líneas)  
**Complejidad reportada:** 24  
**Argumentos:** 18

**Responsabilidad actual:**
- Construye claves de cache únicas basadas en contexto
- Soporta múltiples tipos de entidad
- Maneja filtros complejos por servidor/sucursal/empresa

**Estado:** ✅ FUNCIONAL - No causa errores

**Riesgo de tocarla:** ALTO
- Afecta performance de todo el sistema
- Cache mal generado = datos incorrectos
- Múltiples módulos dependen de esta función

**Propuesta futura (NO URGENTE):**
```python
# Dividir en funciones especializadas:
def build_user_context_key(user_id, empresa_id, sucursal_id) -> str
def build_date_context_key(fecha_inicio, fecha_fin) -> str
def build_filter_context_key(filters: dict) -> str
def build_entity_context_key(entity_type, entity_id) -> str

# Usar clase de configuración:
@dataclass
class CacheKeyConfig:
    user_id: str
    empresa_id: Optional[str]
    # ...
```

**Pruebas necesarias antes de refactor:**
- Unit tests para cada tipo de cache key
- Integration tests con Redis/memoria
- Performance benchmarks

**Contrato que NO debe romperse:**
- Mismas claves para mismos parámetros (determinístico)
- Claves únicas para contextos diferentes
- Formato compatible con Redis

---

### 2.2 `core/centro_control/email_notifications.py` - `generate_alert_html()`
**Líneas:** 431 total (función ~120 líneas)  
**Complejidad reportada:** MEDIA

**Responsabilidad actual:**
- Genera HTML para emails de alertas
- Template inline con string concatenation

**Estado:** ✅ FUNCIONAL - Emails se envían correctamente

**Riesgo de tocarla:** MEDIO
- Si el HTML se rompe, emails no se ven bien
- Notificaciones críticas afectadas

**Propuesta futura (NO URGENTE):**
```python
# Opción 1: Templates Jinja2
from jinja2 import Template

ALERT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>...</head>
<body>
    <h1>{{ alert.title }}</h1>
    ...
</body>
</html>
"""

def generate_alert_html(alert: AlertData) -> str:
    template = Template(ALERT_TEMPLATE)
    return template.render(alert=alert)

# Opción 2: Archivos de template externos
# /templates/email/alert.html
```

**Dependencia adicional requerida:** Jinja2 (ya instalado en FastAPI)

**Pruebas necesarias antes de refactor:**
- Renderizar emails de prueba
- Verificar en diferentes clientes de email
- Validar HTML con W3C validator

---

### 2.3 `core/auditoria.py` - `_crear_evento()` y `registrar()`
**Líneas:** 611 total  
**Argumentos reportados:** 23 cada una

**Estado actual:** ✅ YA REFACTORIZADO

**Cambios aplicados:**
- Creada `AuditoriaParams` dataclass (línea 90)
- Agregado `registrar_params()` para nuevo código
- Agregado `_crear_evento_from_params()`
- Métodos legacy mantienen compatibilidad hacia atrás

**Código existente:**
```python
@dataclass
class AuditoriaParams:
    """
    Parámetros de entrada para registrar auditoría.
    Agrupa los 23 parámetros en una estructura reutilizable.
    """
    usuario: Optional[Dict] = None
    usuario_id: Optional[str] = None
    # ... (47 líneas de definición)
```

**Acción futura:** NINGUNA URGENTE
- La refactorización ya fue aplicada
- Código legacy mantiene compatibilidad
- Nuevo código puede usar `registrar_params()`

---

### 2.4 `core/auditoria_helpers.py` - `registrar_auditoria_tesoreria()`
**Líneas:** 284 total (función ~52 líneas)  
**Argumentos:** 12

**Responsabilidad actual:**
- Helper específico para auditoría de tesorería
- Envuelve llamadas a `registrar()` con contexto de tesorería

**Estado:** ✅ FUNCIONAL - Ya usa patrón DRY interno

**Riesgo de tocarla:** BAJO
- Es un helper wrapper
- Cambios no afectan la función principal

**Propuesta futura (OPCIONAL):**
```python
# Usar AuditoriaParams en lugar de argumentos individuales
async def registrar_auditoria_tesoreria(params: AuditoriaTesoreriaParams) -> bool:
    audit_params = AuditoriaParams(
        modulo=ModuloAuditoria.TESORERIA,
        **params.to_dict()
    )
    return await servicio_auditoria.registrar_params(audit_params)
```

---

## 3. ORDEN DE PRIORIDAD PARA REFACTORS FUTUROS

| Prioridad | Función | Riesgo | Esfuerzo | Ya Hecho |
|-----------|---------|--------|----------|----------|
| ✅ | auditoria.py | ALTO | 1 día | **SÍ** |
| 2 | email_notifications.py | MEDIO | 1 día | NO |
| 3 | cache_key_builder.py | ALTO | 2 días | NO |
| 4 | auditoria_helpers.py | BAJO | 0.5 días | NO |

---

## 4. CONTRATOS QUE NO DEBEN ROMPERSE

### auditoria.py
- `registrar()` debe seguir aceptando 23 argumentos individuales
- `auditar()` decorator debe funcionar igual
- Eventos deben guardarse en SQL y/o MongoDB

### cache_key_builder.py
- Misma clave para mismos parámetros
- Claves válidas para Redis (sin caracteres especiales)
- Performance < 1ms por generación

### email_notifications.py
- HTML válido y responsive
- Estilos inline (no CSS externo)
- Compatible con Outlook, Gmail, Apple Mail

### auditoria_helpers.py
- Firma de funciones públicas
- Comportamiento de logging

---

## 5. CONCLUSIÓN

**Estado de esta fase:** ✅ DOCUMENTADO

De las 5 funciones complejas identificadas:
- 1 ya fue refactorizada (auditoria.py con AuditoriaParams)
- 4 están funcionando correctamente y no requieren cambios urgentes

**NO SE REQUIEREN CAMBIOS EN ESTA FASE DE ESTABILIZACIÓN.**

Los refactors futuros deben ejecutarse en fases dedicadas con:
- Testing exhaustivo
- Benchmarks de performance
- Rollback plan
