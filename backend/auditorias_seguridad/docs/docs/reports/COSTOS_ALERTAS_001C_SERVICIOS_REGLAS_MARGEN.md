# COSTOS-ALERTAS-001-C: Servicios Backend para Reglas de Margen

## Fecha: 25 Mayo 2026
## Estado: ✅ COMPLETADO
## Autor: Agente E1

---

## 1. OBJETIVO

Implementar el backend completo para administrar reglas de margen esperado con resolución jerárquica:
- **Producto > Subfamilia > Familia > Grupo**

La regla más específica siempre tiene prioridad sobre la más general.

---

## 2. ARQUITECTURA IMPLEMENTADA

### 2.1 Archivos Creados/Modificados

| Archivo | Función |
|---------|---------|
| `/app/backend/modules/comercial/alertas_margen_repository.py` | CRUD SQL + Lógica jerárquica |
| `/app/backend/modules/comercial/alertas_margen_service.py` | Validaciones de negocio |
| `/app/backend/modules/comercial/routes_alertas_margen.py` | Endpoints REST |
| `/app/backend/server.py` | Registro del router |

### 2.2 Tablas SQL Utilizadas (creadas en FASE B)

- `Comercial_AlertasMargenReglas` - Reglas de margen por nivel
- `Comercial_AlertasUmbralesSeveridad` - Configuración de severidades

---

## 3. ENDPOINTS IMPLEMENTADOS

Base URL: `/api/comercial/alertas-margen`

### CRUD de Reglas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/reglas` | Listar reglas con filtros |
| POST | `/reglas` | Crear nueva regla |
| GET | `/reglas/{regla_id}` | Obtener regla por ID |
| PUT | `/reglas/{regla_id}` | Actualizar regla |
| DELETE | `/reglas/{regla_id}` | Desactivar regla (soft delete) |

### Resolución y Evaluación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/resolver-regla` | Resolver regla aplicable por jerarquía |
| POST | `/evaluar` | Evaluar margen de producto contra regla |

### Configuración

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/umbrales` | Obtener umbrales de severidad |
| GET | `/estadisticas` | Estadísticas de reglas configuradas |

---

## 4. LÓGICA DE RESOLUCIÓN JERÁRQUICA

La función `resolver_regla_aplicable()` busca la regla aplicable en el siguiente orden de prioridad:

1. **PRODUCTO** - Busca regla específica para el producto
2. **SUBFAMILIA** - Si no hay regla de producto, busca por subfamilia
3. **FAMILIA** - Si no hay regla de subfamilia, busca por familia
4. **GRUPO** - Si no hay regla de familia, busca por grupo
5. **SIN_REGLA** - Si no hay ninguna regla aplicable

### Ejemplo de Resolución

```
Reglas configuradas:
  - GRUPO=ALIMENTOS: 65%
  - FAMILIA=CARNES: 55%
  - PRODUCTO=RIBEYE-500: 40%

Consulta para RIBEYE-500:
  → Resultado: PRODUCTO, 40% (regla más específica)

Consulta para ARRACHERA (familia CARNES):
  → Resultado: FAMILIA, 55% (no hay regla de producto)

Consulta para COCA-COLA (familia BEBIDAS, grupo ALIMENTOS):
  → Resultado: GRUPO, 65% (no hay regla de familia ni producto)
```

---

## 5. MODELO DE DATOS DE REGLA

```json
{
  "regla_id": "UUID",
  "nivel_aplicacion": "GRUPO|FAMILIA|SUBFAMILIA|PRODUCTO",
  "entidad_codigo": "código de la entidad",
  "margen_esperado": 65.0,
  "costo_maximo": null,
  "utilidad_minima": null,
  "severidad_base": "INFORMATIVA|MEDIA|ALTA|CRITICA",
  "descripcion": "texto opcional",
  "empresa_id": null,
  "sucursal_id": null,
  "activo": true,
  "fecha_inicio": "2026-05-25T00:00:00",
  "fecha_fin": null
}
```

---

## 6. EVALUACIÓN DE MARGEN

El endpoint `/evaluar` compara el margen actual de un producto contra el margen esperado según su regla jerárquica:

### Request
```json
{
  "margen_actual": 35,
  "producto_clave": "RIBEYE-500",
  "familia_codigo": "CARNES",
  "grupo_codigo": "ALIMENTOS",
  "precio_venta": 450,
  "costo_receta": 292.5
}
```

### Response
```json
{
  "tiene_alerta": true,
  "estado": "ALERTA_MARGEN_BAJO",
  "margen_actual": 35.0,
  "margen_esperado": 40.0,
  "diferencia_puntos": 5.0,
  "severidad": "ALTA",
  "utilidad_negativa": false,
  "costo_mayor_precio": false,
  "perdida_por_unidad": 22.5,
  "fuente_regla": "PRODUCTO",
  "mensaje": "Margen actual (35.0%) está 5.0 puntos debajo del esperado (40.0%)"
}
```

---

## 7. UMBRALES DE SEVERIDAD

| Severidad | Rango (puntos) | Color | Condiciones especiales |
|-----------|----------------|-------|------------------------|
| INFORMATIVA | 0 - 1.99 | #3B82F6 (azul) | - |
| MEDIA | 2 - 4.99 | #F59E0B (amarillo) | - |
| ALTA | 5 - 9.99 | #F97316 (naranja) | - |
| CRITICA | 10+ | #EF4444 (rojo) | Utilidad negativa, Costo > Precio |

---

## 8. VALIDACIONES IMPLEMENTADAS

1. **Nivel de aplicación** debe ser: GRUPO, FAMILIA, SUBFAMILIA, PRODUCTO
2. **Severidad** debe ser: INFORMATIVA, MEDIA, ALTA, CRITICA
3. **Margen esperado** entre 0% y 100%
4. **Costo máximo** entre 0% y 100% (opcional)
5. **Utilidad mínima** entre -100% y 100% (opcional)
6. **No duplicados activos** para la misma entidad/nivel
7. **Fecha fin** debe ser posterior a fecha inicio

---

## 9. PRUEBAS REALIZADAS (curl)

### Crear reglas
```bash
# Regla GRUPO
POST /api/comercial/alertas-margen/reglas
{"nivel_aplicacion": "GRUPO", "entidad_codigo": "ALIMENTOS", "margen_esperado": 65}
→ 201 OK

# Regla FAMILIA
POST /api/comercial/alertas-margen/reglas
{"nivel_aplicacion": "FAMILIA", "entidad_codigo": "CARNES", "margen_esperado": 55}
→ 201 OK

# Regla PRODUCTO
POST /api/comercial/alertas-margen/reglas
{"nivel_aplicacion": "PRODUCTO", "entidad_codigo": "RIBEYE-500", "margen_esperado": 40}
→ 201 OK
```

### Resolver jerarquía
```bash
GET /api/comercial/alertas-margen/resolver-regla?producto_clave=RIBEYE-500&familia_codigo=CARNES&grupo_codigo=ALIMENTOS
→ {"fuente": "PRODUCTO", "margen_esperado": 40}

GET /api/comercial/alertas-margen/resolver-regla?producto_clave=OTRO&familia_codigo=CARNES&grupo_codigo=ALIMENTOS
→ {"fuente": "FAMILIA", "margen_esperado": 55}

GET /api/comercial/alertas-margen/resolver-regla?producto_clave=COCA&familia_codigo=BEBIDAS&grupo_codigo=ALIMENTOS
→ {"fuente": "GRUPO", "margen_esperado": 65}
```

### Evaluar margen
```bash
POST /api/comercial/alertas-margen/evaluar
{"margen_actual": 35, "producto_clave": "RIBEYE-500", ...}
→ {"tiene_alerta": true, "severidad": "ALTA", "diferencia_puntos": 5}
```

---

## 10. PRÓXIMOS PASOS

| Fase | Descripción | Estado |
|------|-------------|--------|
| COSTOS-ALERTAS-001-D | UI para configurar reglas/destinatarios | PENDIENTE |
| COSTOS-ALERTAS-001-E | Motor de evaluación masiva de margen | PENDIENTE |
| COSTOS-ALERTAS-001-F | Job/scheduler y envío Email/WhatsApp | PENDIENTE |

---

## 11. MÁXIMAS RESPETADAS

- ✅ EDARSAHUB SQL Server es el cerebro
- ✅ CERO MongoDB
- ✅ Backend-first (toda la lógica en Python/SQL)
- ✅ Auditoría completa (creado_por, modificado_por, fechas)
- ✅ Soft delete (Activo = 0, no DELETE físico)
- ✅ Validaciones en service layer
