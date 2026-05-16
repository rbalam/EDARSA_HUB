# REPORTE: Corrección Explorador BD - Conexiones Enterprise (API_LOCAL)

## Fecha: 2026-05-16
## Estado: ✅ COMPLETADO Y VALIDADO

---

## RESUMEN EJECUTIVO

Se completó la corrección del Explorador de Base de Datos para soportar conexiones Enterprise (`API_LOCAL`) en los endpoints de **tablas**, **columnas** y **preview**.

---

## PROBLEMAS IDENTIFICADOS Y RESUELTOS

### Problema 1: Endpoints `/columnas` y `/preview` no soportaban `API_LOCAL`
- **Síntoma**: Error 500 al intentar ver columnas o preview de tablas de CHAPUR NORTE
- **Causa raíz**: Los endpoints estaban hardcodeados para conexiones SQL directas
- **Solución**: Implementada lógica dual que detecta el tipo de conexión y usa:
  - `DATA_SOURCE`: Conexión SQL directa vía `execute_sql_query_params`
  - `API_LOCAL`: Delegación via `execute_test_query` al endpoint remoto

### Problema 2: Limitación de 20 filas en `execute_test_query`
- **Síntoma**: La lista de tablas de CHAPUR NORTE estaba truncada
- **Causa raíz**: Parámetro `limit` hardcodeado a 20 en repository.py
- **Solución**: Agregado parámetro `limit` configurable con default 20, pero `limit=None` para metadata

---

## VALIDACIÓN DE LOS 8 PUNTOS CRÍTICOS

| # | Punto | Estado | Detalle |
|---|-------|--------|---------|
| 1 | PRUEBAS SOFTRESTAURANT devuelve tablas | ⚠️ | Error DBA: Usuario 'HRLectura' sin acceso (no es bug del código) |
| 2 | CHAPUR NORTE devuelve tablas | ✅ | 356 tablas listadas correctamente |
| 3 | CHAPUR NORTE BACKOFICE devuelve tablas | ✅ | 186 tablas listadas correctamente |
| 4 | Columnas funcionan (API_LOCAL) | ✅ | 6 columnas para 'almacen', 19 para 'Accounting' |
| 5 | Preview TOP 100 funciona (API_LOCAL) | ✅ | Registros obtenidos de 'areas' y 'AccountsPayable' |
| 6 | Enterprise usa API Local vigente | ✅ | `tipo_conexion: API_LOCAL` confirmado |
| 7 | No se exponen secrets | ✅ | Respuestas sin api_key, password, secrets |
| 8 | No se rompe SoftRestaurant ni MPRO | ✅ | 130° MERIDA: 365 tablas, MPRO: 1076 tablas |

---

## ARCHIVOS MODIFICADOS

### Backend
1. `/app/backend/modules/api_connections/repository.py`
   - Línea 730: Agregado parámetro `limit: Optional[int] = 20`
   - Líneas 819-834: Lógica de límite configurable

2. `/app/backend/server.py`
   - Líneas 9887-9998: Endpoint `/columnas` reescrito con soporte dual
   - Líneas 10070-10175: Endpoint `/preview` reescrito con soporte dual
   - Línea 9733: `limit=None` para cargar todas las tablas de metadata

---

## COMANDOS DE VALIDACIÓN

```bash
# 1. Listar conexiones explorables
curl -s "$API_URL/api/explorador/conexiones-explorables" -H "Authorization: Bearer $TOKEN"

# 2. Tablas CHAPUR NORTE (API_LOCAL)
curl -s "$API_URL/api/explorador/tablas/d8b2d1eb-2e1f-4e43-b7d9-822bf671e315" -H "Authorization: Bearer $TOKEN"

# 3. Columnas CHAPUR NORTE
curl -s "$API_URL/api/explorador/columnas/d8b2d1eb-2e1f-4e43-b7d9-822bf671e315/almacen" -H "Authorization: Bearer $TOKEN"

# 4. Preview CHAPUR NORTE
curl -s "$API_URL/api/explorador/preview/d8b2d1eb-2e1f-4e43-b7d9-822bf671e315/areas?limite=10" -H "Authorization: Bearer $TOKEN"

# 5. Regresión - SoftRestaurant (DATA_SOURCE)
curl -s "$API_URL/api/explorador/tablas/a5547321-1139-4d2b-9d53-182ca737b6b6" -H "Authorization: Bearer $TOKEN"
```

---

## NOTA SOBRE PRUEBAS SOFTRESTAURANT

El servidor "PRUEBAS SOFTRESTAURANT" retorna error:
```
"Error de autenticación: El usuario no tiene acceso a la base de datos 'softrestaurant12'"
```

**Esto NO es un defecto del código**. Es una restricción de permisos del usuario `HRLectura` en el servidor SQL remoto. El DBA debe otorgar permisos de lectura sobre esa base de datos.

---

## COMPATIBILIDAD

- ✅ SoftRestaurant (DATA_SOURCE): Funcionando
- ✅ MPRO (DATA_SOURCE): Funcionando
- ✅ Enterprise/CHAPUR (API_LOCAL): Funcionando
- ✅ Sin regresiones detectadas
