# CIERRE PROP-002 - Corrección de 130° MÉRIDA en Dashboard V2

| Campo | Valor |
|-------|-------|
| **ID** | PROP-002 |
| **Fecha de implementación** | 2026-05-05 |
| **Estado** | COMPLETADO |
| **Resultado** | ÉXITO |

---

## EVIDENCIA DE IMPLEMENTACIÓN

### 1. Diff Exacto de comercial_v2/routes.py

```diff
diff --git a/backend/modules/comercial_v2/routes.py b/backend/modules/comercial_v2/routes.py
index 60581fb..6c2521f 100644
--- a/backend/modules/comercial_v2/routes.py
+++ b/backend/modules/comercial_v2/routes.py
@@ -81,7 +81,7 @@ async def get_unidades_permitidas_v2(current_user: dict) -> List[str]:
                 unidades_v2.append('CIENFUEGOS')
             elif 'ESTELAR' in nombre:
                 unidades_v2.append('LA-ESTELAR')
-            elif 'MERIDA' in nombre or 'MER' in codigo:
+            elif 'MERIDA' in nombre or 'MER' in codigo or 'MID' in codigo:
                 unidades_v2.append('130-MER')
             elif 'QUERETARO' in nombre or 'QRO' in codigo:
                 unidades_v2.append('130-QRO')
@@ -89,7 +89,7 @@ async def get_unidades_permitidas_v2(current_user: dict) -> List[str]:
                 unidades_v2.append('ORIGEN')
         
         # Si es SuperAdmin, dar acceso a todas
-        if current_user.get('rol') in ['SuperAdministrador', 'Director']:
+        if current_user.get('role') in ['SuperAdministrador', 'Director']:
             return ['CIENFUEGOS', 'LA-ESTELAR', '130-MER', '130-QRO', 'ORIGEN']
         
         return list(set(unidades_v2)) if unidades_v2 else []
```

### 2. Verificación de eliminación del bug 'rol'

```bash
$ grep -rn "\.get('rol')" /app/backend/ --include="*.py"
# (sin resultados - código de salida 1)
```

**Confirmado**: No hay más ocurrencias de `current_user.get('rol')` en el backend.

### 3. Respuesta JSON con 130-MER

```json
{
  "filtros_aplicados": {
    "unidades": ["CIENFUEGOS", "LA-ESTELAR", "130-MER", "130-QRO", "ORIGEN"]
  }
}
```

**Total unidades**: 5 (antes: 4)

### 4. Ventas reales de 130° MÉRIDA

| Campo | Valor |
|-------|-------|
| unidad_negocio_id | 130-MER |
| unidad_negocio_nombre | 130° MÉRIDA |
| ventas_total | **$409,213.00** |
| dias | 4 |
| fecha_min | 2026-05-01 |
| fecha_max | 2026-05-04 |
| _v2_fuente | EDARSAHUB |
| _status_v2 | ACTUALIZADO |

### 5. Regresión - Todas las unidades funcionando

| Unidad | ID | Ventas | Status |
|--------|-----|--------|--------|
| ✓ 130° MÉRIDA | 130-MER | $409,213.00 | ACTUALIZADO |
| ✓ 130° QUERETARO | 130-QRO | $407,073.00 | ACTUALIZADO |
| ✓ CIENFUEGOS | CIENFUEGOS | $559,865.00 | ACTUALIZADO |
| ✓ LA ESTELAR | LA-ESTELAR | $462,031.00 | ACTUALIZADO |
| ✓ ORIGEN | ORIGEN | $223,447.70 | ACTUALIZADO |

**Total ventas Mayo 2026**: $2,061,629.70

### 6. Confirmación de módulos NO modificados

```bash
$ git status --short
 M backend/modules/comercial_v2/routes.py
```

**Único archivo modificado**: `backend/modules/comercial_v2/routes.py`

**Módulos verificados como NO tocados**:
- ✓ Comercial V1 (`/app/backend/modules/comercial/`)
- ✓ Compras (`/app/backend/modules/compras/`)
- ✓ Auth (`/app/backend/modules/auth/`)
- ✓ Tablero Ejecutivo
- ✓ Finanzas
- ✓ MongoDB (catálogos)
- ✓ EDARSAHUB (estructura)

---

## RESUMEN

| Elemento | Estado |
|----------|--------|
| Bug #1 (role/rol) | CORREGIDO |
| Bug #2 (MER/MID) | CORREGIDO |
| 130° MÉRIDA visible | SÍ |
| Ventas de MÉRIDA | $409,213.00 |
| Regresión otras unidades | NINGUNA |
| Módulos no autorizados tocados | NINGUNO |

---

**PROP-002 CERRADA EXITOSAMENTE**

*Fecha de cierre: 2026-05-05*
