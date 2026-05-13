# DIAGNÓSTICO URGENTE — Modal "Configurar Filtros" No Muestra tipos_movimiento

**Fecha:** 14-Mayo-2026  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Problema:** SoftRestaurant muestra 0/0 tipos de movimiento, ManagementPro muestra 84

---

## 1. Resumen del Problema

| Servidor | Modal Muestra | Esperado | Estado |
|----------|---------------|----------|--------|
| ManagementPro | 0/84 | ✅ OK | Funciona |
| 130° MERIDA | 0/0 | 0/18 | ❌ Falla |
| CIENFUEGOS | 0/0 (probable) | 0/22 | ❌ Falla |
| LA ESTELAR | 0/0 (probable) | 0/19 | ❌ Falla |

---

## 2. Confirmación de Datos en EDARSAHUB

Los datos **SÍ EXISTEN** en `Servidores_Conexiones.tipos_movimiento`:

| Servidor | tipos_movimiento count | JSON Válido |
|----------|------------------------|-------------|
| 130° MERIDA | 18 | ✅ |
| CIENFUEGOS | 22 | ✅ |
| LA ESTELAR | 19 | ✅ |
| ManagmentPro | 35 | ✅ |

---

## 3. Endpoint del Modal

**Frontend:** `/app/frontend/src/pages/Servidores.js` (línea 512)
```javascript
api.get(`/servers/${serverId}/tipos-movimiento`)
```

**Backend:** `/app/backend/server.py` (línea 1811)
```python
@api_router.get("/servers/{server_id}/tipos-movimiento")
async def get_tipos_movimiento(server_id: str, ...):
```

---

## 4. CAUSA RAÍZ IDENTIFICADA

El endpoint `GET /servers/{server_id}/tipos-movimiento` **NO usa** el campo `tipos_movimiento` de EDARSAHUB.

En su lugar, hace una **consulta directa** a la base de datos del servidor destino:

### Para SoftRestaurant:
```sql
SELECT idconcepto as codigo, descripcion, ...
FROM conceptos
ORDER BY idconcepto
```

### Para MPRO:
```sql
SELECT Tm_Cve_Tipo_Movimiento as codigo, ...
FROM Tipo_Movimiento
WHERE Es_Cve_Estado <> 'BA'
```

---

## 5. Por Qué ManagementPro Funciona y SoftRestaurant No

### ManagementPro (MPRO):
- ✅ Conexión exitosa a su BD
- ✅ Tabla `Tipo_Movimiento` tiene datos
- ✅ Devuelve 84 tipos

### SoftRestaurant (130 MERIDA, CIENFUEGOS, ESTELAR):
- ❌ **Errores de conexión** detectados en logs:
  ```
  Error de inicio de sesión del usuario 'SCedarsa'
  Adaptive Server connection failed (189.235.116.216)
  ```
- ❌ La tabla `conceptos` no es accesible
- ❌ Devuelve `[]` (array vacío)

---

## 6. Verificación de server_registry.py

El campo `tipos_movimiento` **NO SE INCLUYE** en `_sql_row_to_server_dict()`:

```python
def _sql_row_to_server_dict(row: Dict, source: str = "EDARSAHUB_SQL") -> Dict:
    return {
        'id': str(row.get('id', '')),
        'name': row.get('nombre', ''),
        ...
        'categorias': _parse_json_field(row.get('categorias')),
        'departamentos': _parse_json_field(row.get('departamentos')),
        # ⚠️ FALTA: 'tipos_movimiento': _parse_json_field(row.get('tipos_movimiento')),
        ...
    }
```

---

## 7. Dos Problemas Separados

### PROBLEMA A: Conexión a SoftRestaurant
- Las credenciales o red de SoftRestaurant no permiten conexión
- Esto afecta la consulta directa a tabla `conceptos`
- **No es problema de EDARSAHUB**

### PROBLEMA B: `tipos_movimiento` no expuesto por server_registry.py
- El campo existe en EDARSAHUB pero no se mapea
- Esto impediría que `auditoria-operativa` lo use desde EDARSAHUB
- **Necesita corrección en FASE T3.4-B4**

---

## 8. Propuesta de Corrección

### Para el Modal (CORTO PLAZO):

El modal actualmente funciona así:
1. Llama a `GET /servers/{server_id}/tipos-movimiento`
2. El endpoint consulta la BD del servidor destino
3. Si la BD no responde, devuelve `[]`

**Opciones:**
- **A)** Corregir credenciales/conexión a servidores SoftRestaurant (problema de infraestructura)
- **B)** Modificar endpoint para usar `tipos_movimiento` de EDARSAHUB como fallback
- **C)** Modificar endpoint para usar SOLO `tipos_movimiento` de EDARSAHUB

### Para auditoria-operativa (FASE T3.4-B4):

Agregar `tipos_movimiento` a `_sql_row_to_server_dict()`:
```python
'tipos_movimiento': _parse_json_field(row.get('tipos_movimiento')),
```

---

## 9. Archivos que Habría que Modificar

| Archivo | Cambio |
|---------|--------|
| `/app/backend/core/server_registry.py` | Agregar `tipos_movimiento` a `_sql_row_to_server_dict()` |
| `/app/backend/server.py` | (Opcional) Modificar endpoint para usar EDARSAHUB como fuente |

---

## 10. Confirmación de No Modificación

- ✅ **NO se modificó** ningún archivo de código
- ✅ **NO se modificó** ninguna base de datos
- ✅ Diagnóstico 100% pasivo (solo lectura y consultas)

---

## 11. Recomendación

**FASE T3.4-B4 debe incluir:**
1. Agregar `tipos_movimiento` a `_sql_row_to_server_dict()` en `server_registry.py`
2. Considerar si el endpoint del modal debe usar EDARSAHUB como fuente alternativa

**El problema de conexión a SoftRestaurant** es un tema de infraestructura/credenciales separado que no afecta la migración de `tipos_movimiento` a EDARSAHUB.

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1 (Diagnóstico Pasivo)
