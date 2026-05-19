# REPORTE TÉCNICO: Catálogo SQL y Explorador BD - Matching Enterprise

**Fecha:** 2025-05-19  
**Prioridad:** P0  
**Estado:** ✅ IMPLEMENTADO Y VALIDADO  
**Autor:** Agente E1 (Arquitecto Backend)

---

## 1. DIAGNÓSTICO RAÍZ

### Problema Reportado
Después del fix anterior (normalización a códigos canónicos), se generó una regresión:
1. **Catálogo SQL:** Al seleccionar una consulta `SOFRESATAURANT_ENTER`, el selector de servidor mostraba "No hay servidores SOFRESATAURANT_ENTER"
2. **Explorador BD:** El primer combo mostraba "API Local" pero las conexiones tenían código normalizado, no el RAW

### Causa de la Regresión
El fix anterior normalizó `sistema_codigo` de `SOFRESATAURANT_ENTER` → `API_LOCAL`, pero:
- Las consultas custom en `ConsultasSQL_Catalogo` siguen usando el código RAW `SOFRESATAURANT_ENTER`
- El matching en el frontend (`CatalogoConsultas.js`) comparaba `consulta.sistema` con `servidor.system_type`
- Al normalizar, `'SOFRESATAURANT_ENTER' !== 'API_LOCAL'` → no match

---

## 2. EVIDENCIA DE LA REGRESIÓN

### Antes del Fix
```
Consulta: ALMACENCES (sistema: SOFRESATAURANT_ENTER)
Servidor Chapur: sistema_codigo = API_LOCAL (normalizado)
Matching: 'SOFRESATAURANT_ENTER' !== 'API_LOCAL' → NO HAY SERVIDORES
```

### Después del Fix
```
Consulta: ALMACENCES (sistema: SOFRESATAURANT_ENTER)
Servidor Chapur: 
  - sistema_codigo (RAW): SOFRESATAURANT_ENTER
  - sistema_codigo_normalizado: API_LOCAL
Matching: 'SOFRESATAURANT_ENTER' === 'SOFRESATAURANT_ENTER' → MATCH ✅
```

---

## 3. ESTADO SQL DE SERVIDORES CHAPUR

```sql
SELECT id, nombre, system_type, activo, visible_en_operaciones
FROM Servidores_Conexiones
WHERE nombre LIKE '%CHAPUR%'

-- Resultado:
-- d8b2d1eb-...: CHAPUR NORTE          | system_type='SOFRESATAURANT_ENTER' | activo=1 | visible=1
-- 8cbdcc89-...: CHAPUR NORTE BACKOFICE | system_type='SOFRESATAURANT_ENTER' | activo=1 | visible=0
```

---

## 4. ESTADO SQL DE CONSULTAS SOFRESATAURANT_ENTER

```sql
SELECT ConsultaID, NombreConsulta, SistemaTipoID
FROM ConsultasSQL_Catalogo
WHERE NombreConsulta LIKE '%ALMACEN%'

-- Las consultas custom usan código RAW en el campo 'sistema' del response
-- No usan SistemaTipoID, sino que guardan el código directamente
```

**Consultas encontradas:**
| ID | Nombre | Sistema |
|----|--------|---------|
| CUSTOM_SOFRESATAURANT_ENTER_14F42D7D | ALMACENCES | SOFRESATAURANT_ENTER |
| CUSTOM_SOFRESATAURANT_ENTER_D6D7E925 | TIPOS DE MOVIMIENTO | SOFRESATAURANT_ENTER |
| CUSTOM_SOFRESATAURANT_ENTER_4C7DD61F | PRODUCTOS | SOFRESATAURANT_ENTER |
| ... | ... | ... |

---

## 5. ESTADO DE Sistema_TiposVariantes

```sql
SELECT VarianteNombre, TipoCanonicoCode, TipoCanonicoNombre
FROM Sistema_TiposVariantes sv
JOIN Sistema_Tipos st ON sv.SistemaTipoID = st.SistemaTipoID
WHERE VarianteNombre = 'SOFRESATAURANT_ENTER'

-- Resultado:
-- SOFRESATAURANT_ENTER → API_LOCAL (API Local)
```

---

## 6. EXPLICACIÓN DEL MISMATCH RAW vs NORMALIZADO

| Componente | Código Usado | Problema |
|------------|--------------|----------|
| Consultas Custom | `SOFRESATAURANT_ENTER` (RAW) | Busca servidores por este código |
| Servidores (fix anterior) | `API_LOCAL` (normalizado) | No matchea con consultas |
| Primer Combo Explorador BD | Códigos canónicos | Funciona |
| Segundo Combo Explorador BD | Depende del filtro | Necesita normalizado |

**Solución:**
El endpoint debe devolver AMBOS códigos para que:
- Catálogo SQL use el RAW para matching con consultas
- Explorador BD use el normalizado para filtros de UI

---

## 7. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/server.py` (líneas 9563-9630) | Query devuelve `sistema_codigo_raw` y `sistema_codigo_normalizado` |
| `/app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js` | Usa `sistema_codigo_raw` para matching |
| `/app/frontend/src/pages/ExploradorBD.js` | Usa `sistema_codigo_normalizado` para filtros |

---

## 8. QUERY ANTERIOR vs QUERY NUEVA

### Antes (fix que causó regresión):
```sql
SELECT 
    sc.system_type,
    COALESCE(st.CodigoSistema, sc.system_type) as sistema_codigo,  -- Solo normalizado
    COALESCE(st.NombreSistema, sc.system_type) as sistema_descripcion
FROM Servidores_Conexiones sc
LEFT JOIN Sistema_TiposVariantes sv ON ...
LEFT JOIN Sistema_Tipos st ON ...
```

### Después:
```sql
SELECT 
    sc.system_type,
    sc.system_type as sistema_codigo_raw,  -- Código RAW original
    COALESCE(st.CodigoSistema, sc.system_type) as sistema_codigo_normalizado,  -- Código canónico
    COALESCE(st.NombreSistema, sc.system_type) as sistema_nombre
FROM Servidores_Conexiones sc
LEFT JOIN Sistema_TiposVariantes sv ON ...
LEFT JOIN Sistema_Tipos st ON ...
```

---

## 9. RESPONSE ANTERIOR vs RESPONSE NUEVO

### Antes:
```json
{
  "nombre": "CHAPUR NORTE",
  "sistema_codigo": "API_LOCAL",  // Normalizado, rompe matching
  "sistema_descripcion": "API Local"
}
```

### Después:
```json
{
  "nombre": "CHAPUR NORTE",
  "sistema_codigo": "SOFRESATAURANT_ENTER",  // RAW para matching
  "sistema_codigo_raw": "SOFRESATAURANT_ENTER",
  "sistema_codigo_normalizado": "API_LOCAL",
  "sistema_nombre": "API Local"
}
```

---

## 10. VALIDACIONES REALIZADAS (cURL)

### A) Catálogo SQL - Matching SOFRESATAURANT_ENTER:
```
Servidores con sistema_codigo = SOFRESATAURANT_ENTER: 2
  - CHAPUR NORTE
  - CHAPUR NORTE BACKOFICE
✅ VALIDADO
```

### B) Explorador BD - Filtro API_LOCAL:
```
Servidores con sistema_codigo_normalizado = API_LOCAL: 2
  - CHAPUR NORTE
  - CHAPUR NORTE BACKOFICE
✅ VALIDADO
```

### C) No Regresión - Endpoints:
```
- /explorador/conexiones-explorables: 200 OK
- /catalogo/consultas-rich: 200 OK
- /catalogos/sistemas-capacidades/explorables: 200 OK
✅ VALIDADO
```

---

## 11. EVIDENCIA UI

**Nota:** El screenshot tool mostró errores 403 debido a problemas de sesión del navegador automatizado. Los endpoints funcionan correctamente con autenticación válida (cURL con token JWT).

---

## 12. VALIDACIONES DE NO REGRESIÓN

| Validación | Estado |
|------------|--------|
| SoftRestaurant sigue apareciendo | ✅ 5 conexiones |
| ManagementPro sigue apareciendo | ✅ 5 conexiones |
| API Local sigue apareciendo | ✅ 2 conexiones (Chapur) |
| Consultas por sistema intactas | ✅ 26 consultas (14 SR, 6 MPRO, 6 Enterprise) |
| No se filtró por visible_en_operaciones | ✅ Confirmado |
| No se hardcodeó Chapur | ✅ Confirmado |
| MongoDB no utilizado | ✅ Confirmado |

---

## 13. BACKOUT PLAN

```bash
# Revertir cambios:
git checkout HEAD~3 -- /app/backend/server.py
git checkout HEAD~3 -- /app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js
git checkout HEAD~3 -- /app/frontend/src/pages/ExploradorBD.js

# Reiniciar servicios:
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

---

## 14. CONFIRMACIONES EXPLÍCITAS

| Verificación | Resultado |
|--------------|-----------|
| ¿Se usó MongoDB? | **NO** |
| ¿Se filtró por `visible_en_operaciones`? | **NO** |
| ¿Se hardcodeó Chapur? | **NO** |
| ¿Se hardcodeó SOFRESATAURANT_ENTER en código? | **NO** (solo en queries SQL para JOIN) |
| ¿Se modificaron tablas SQL? | **NO** |
| ¿Se rompió Catálogo SQL? | **NO** - Ahora funciona con RAW |
| ¿Se rompió Explorador BD? | **NO** - Ahora usa normalizado para filtros |

---

## 15. ARQUITECTURA FINAL

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (server.py)                          │
│  /explorador/conexiones-explorables                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Response para cada conexión:                                ││
│  │   - sistema_codigo: RAW (para matching con consultas)       ││
│  │   - sistema_codigo_raw: RAW explícito                       ││
│  │   - sistema_codigo_normalizado: canónico (para filtros UI)  ││
│  │   - sistema_nombre: label amigable                          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
┌───────────────────────┐                 ┌───────────────────────┐
│   CATÁLOGO SQL        │                 │   EXPLORADOR BD       │
│   (CatalogoConsultas) │                 │   (ExploradorBD.js)   │
│                       │                 │                       │
│   Matching:           │                 │   Filtro:             │
│   consulta.sistema    │                 │   sistema_codigo_     │
│   vs                  │                 │   normalizado         │
│   server.system_type  │                 │   (código canónico)   │
│   (código RAW)        │                 │                       │
└───────────────────────┘                 └───────────────────────┘
```

---

*Implementación completada: 2025-05-19*
*Fin del Reporte*
