# CORRECCIÓN: EDARSAHUB SQL Restaurado en Menú de Servidores

**Fecha**: 2026-05-20  
**Estado**: COMPLETADO  
**Severidad**: CRÍTICA → RESUELTA  

---

## RESUMEN

El servidor EDARSAHUB SQL ha sido restaurado correctamente en el menú de Servidores/Conexiones.

---

## CAMBIO REALIZADO

### Archivo Modificado
`/app/backend/server.py`

### Línea Modificada
Línea 1243

### Valor Anterior
```python
exclude_core=True,
```

### Valor Nuevo
```python
exclude_core=False,
```

### Comentario Actualizado
```python
# CORRECCIÓN 2026-05-20: Las conexiones CORE (ej. EDARSAHUB SQL) ahora aparecen
# en el listado del menú administrativo de servidores.
```

---

## EVIDENCIA DE FUNCIONAMIENTO

### EDARSAHUB SQL en GET /api/servers ✅

```
Total servidores: 9

>>> EDARSA HUB                 | EDARSA_HUB           | CORE         | pwd_cfg=True | api_cfg=False
    130° MERIDA                | SOFTRESTAURANT_PRO   | DATA_SOURCE  | pwd_cfg=True | api_cfg=False
    CIENFUEGOS                 | SOFTRESTAURANT_PRO   | DATA_SOURCE  | pwd_cfg=True | api_cfg=False
    LA ESTELAR                 | SOFTRESTAURANT_PRO   | DATA_SOURCE  | pwd_cfg=True | api_cfg=False
    ManagmentPro               | MPRO                 | DATA_SOURCE  | pwd_cfg=True | api_cfg=False
    ...
```

### Secretos NO Expuestos ✅

| Campo | Estado |
|-------|--------|
| password | ❌ NO presente en respuesta |
| api_key | ❌ NO presente en respuesta |
| password_configured | ✅ Solo indica si está configurado (True/False) |
| api_key_configured | ✅ Solo indica si está configurado (True/False) |
| secrets_encrypted | ✅ True |

---

## VALIDACIONES DE NO REGRESIÓN

| Validación | Estado |
|------------|--------|
| EDARSAHUB SQL aparece en /api/servers | ✅ |
| No se exponen passwords | ✅ |
| No se exponen api_keys | ✅ |
| SoftRestaurant (5 servidores) siguen apareciendo | ✅ |
| MPRO (3 servidores) siguen apareciendo | ✅ |
| Endpoint responde correctamente | ✅ |

---

## INFORMACIÓN SOBRE MONGODB

### ¿El endpoint GET /api/servers usa MongoDB actualmente?
**SÍ, como fallback**. La función `list_servers` tiene `allow_mongo_fallback=True`.

### ¿Existe fallback MongoDB en la ruta de servidores?
**SÍ**. Si EDARSAHUB SQL falla, consulta MongoDB como respaldo.

### ¿MongoDB contiene registros legacy de servidores?
**Posiblemente SÍ**. No se investigó en detalle para este incidente.

### ¿Esos registros MongoDB participan en la respuesta actual?
**NO activamente**. La fuente primaria es EDARSAHUB SQL (`prefer_sql=True`).

### Fuente efectiva para este endpoint
**EDARSAHUB SQL** (confirmado por `config_origin: EDARSAHUB_SQL` en la respuesta).

### ¿Se detectó dependencia activa de MongoDB?
**NO para este incidente**. MongoDB solo actúa como fallback legacy.

---

## CONFIRMACIONES

| Confirmación | Estado |
|--------------|--------|
| No se tocó MongoDB | ✅ |
| No se modificaron credenciales | ✅ |
| No se modificaron módulos blindados | ✅ |
| No se modificaron servidores SoftRestaurant | ✅ |
| No se modificaron servidores MPRO | ✅ |
| Tablero Ejecutivo intacto | ✅ |
| Módulo Comercial intacto | ✅ |
| Módulo Compras intacto | ✅ |

---

## ARCHIVOS MODIFICADOS

1. `/app/backend/server.py` (línea 1243)

---

## CONCLUSIÓN

EDARSAHUB SQL ahora aparece correctamente en el menú de Servidores como servidor CORE/CENTRAL, sin exponer secretos y sin afectar otros servidores ni módulos del sistema.

---

*Documento generado: 2026-05-20 04:15 UTC*
