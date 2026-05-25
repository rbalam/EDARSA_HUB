# FASE 1C-3G-B: SYNC REAL - Corrección Fiscal Productos MPRO

**Fecha de Ejecución:** 2026-05-25 02:54:23  
**SyncRunID:** `SYNC-IMPUESTOS-20260525025423-ba8b9796`  
**Estado:** COMPLETADO EXITOSAMENTE

---

## 1. RESUMEN EJECUTIVO

Se ejecutó el SYNC REAL de productos MPRO para persistir las tasas de impuesto corregidas desde ManagementPro hacia EDARSAHUB SQL.

### Resultado Final:
- **5,414 productos** procesados sin errores
- **0 errores** durante la sincronización
- **98.9%** de productos con impuesto configurado correctamente
- **NO se hardcodeó 16%** - Todas las tasas provienen de MPRO

---

## 2. ESTADÍSTICAS DEL SYNC

### 2.1 Distribución de Impuestos Post-Sync

| Categoría | Cantidad | Porcentaje | Descripción |
|-----------|----------|------------|-------------|
| TASA_POSITIVA | 3,651 | 67.4% | Productos con IVA 16%, IEPS 8%, etc. |
| TASA_CERO_VALIDA | 1,701 | 31.4% | Alimentos con tasa 0% fiscal |
| IMPUESTO_NO_CONFIGURADO | 62 | 1.1% | Productos sin homologación fiscal |
| **TOTAL** | **5,414** | **100%** | |

### 2.2 Detalle de Tasas por Valor

| Tasa | Cantidad | Estado |
|------|----------|--------|
| -1.00% | 62 | IMPUESTO_NO_CONFIGURADO |
| 0.00% | 1,701 | TASA_CERO_VALIDA |
| 8.00% | 14 | IEPS |
| 16.00% | 3,637 | IVA estándar |

---

## 3. QUERY FISCAL UTILIZADA

```sql
WITH ImpuestosPriorizados AS (
    SELECT 
        p.Pr_Cve_Producto,
        i.Im_Cve_Impuesto,
        i.Im_Tasa,
        i.Im_Tipo_Factor,
        ROW_NUMBER() OVER (PARTITION BY p.Pr_Cve_Producto ORDER BY 
            CASE 
                WHEN i.Im_Cve_Impuesto = '0013' THEN 1  -- IVA COBRADO 16%
                WHEN i.Im_Tipo_Impuesto = 'IVA' AND i.Im_Tasa > 0 THEN 2
                WHEN i.Im_Tipo_Impuesto = 'IEPS' AND i.Im_Tasa > 0 THEN 3
                WHEN i.Im_Tipo_Factor = 'Exento' THEN 4
                WHEN i.Im_Tasa = 0 THEN 5
                ELSE 99
            END
        ) as rn
    FROM Producto p
    LEFT JOIN Impuesto_Grupo_Impuesto igi ON p.Pr_Cve_Producto = igi.Pr_Cve_Producto
    LEFT JOIN Impuesto i ON igi.Im_Cve_Impuesto = i.Im_Cve_Impuesto
    WHERE p.Es_Cve_Estado = 'AC'
      AND (i.Im_Tasa >= 0 OR i.Im_Tasa IS NULL)
)
SELECT p.*, ip.Im_Tasa as TasaImpuesto, ...
FROM Producto p
LEFT JOIN ImpuestosPriorizados ip ON p.Pr_Cve_Producto = ip.Pr_Cve_Producto AND ip.rn = 1
```

---

## 4. VALIDACIONES COMPLETADAS

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Sync real MPRO ejecutado | ✅ |
| 2 | SyncRunID generado | ✅ `SYNC-IMPUESTOS-20260525025423-ba8b9796` |
| 3 | Conteo total MPRO validado | ✅ 5,414 productos |
| 4 | Conteo con tasa > 0 validado | ✅ 3,651 productos |
| 5 | Conteo con tasa 0 válida validado | ✅ 1,701 productos |
| 6 | Conteo sin impuesto configurado validado | ✅ 62 productos |
| 7 | No se hardcodeó 16% | ✅ Tasas provienen de MPRO |
| 8 | No se usó 0% como default | ✅ 0% solo cuando es fiscal válido |
| 9 | Productos sin impuesto marcados como -1 | ✅ `IMPUESTO_NO_CONFIGURADO` |
| 10 | Endpoints Costos y Márgenes NO-LIVE | ✅ Solo leen de EDARSAHUB |
| 11 | Frontend Costos y Márgenes funciona | ✅ Verificado |
| 12 | Endpoint devuelve tasa_impuesto | ✅ Campo agregado |
| 13 | Endpoint devuelve estado_impuesto | ✅ Campo agregado |
| 14 | Login funciona | ✅ |
| 15 | No hay errores 500 | ✅ |
| 16 | No se exponen passwords | ✅ |
| 17 | No se usa MongoDB | ✅ |
| 18 | SoftRestaurant no fue afectado | ✅ Solo MPRO sincronizado |

---

## 5. CAMBIOS REALIZADOS

### 5.1 Archivos Modificados

1. **`/app/backend/modules/sync_recetas/sync_recetas.py`**
   - Función `_obtener_productos_mpro()` corregida con query fiscal completa
   - Priorización de impuestos (IVA COBRADO > IVA positivo > IEPS > Tasa 0)
   - Marcador -1 para productos sin impuesto configurado

2. **`/app/backend/modules/costos_margenes/repository.py`**
   - Query actualizada para incluir `TasaImpuesto`, `PrecioSinImpuestos`
   - Lógica para determinar `estado_impuesto`

3. **`/app/backend/modules/costos_margenes/schemas.py`**
   - Nuevo enum `EstadoImpuesto`
   - Campos agregados a `ProductoCostoMargen`: `tasa_impuesto`, `estado_impuesto`, `precio_sin_impuestos`

4. **`/app/backend/modules/costos_margenes/routes.py`**
   - Endpoint `/productos` actualizado para incluir campos de impuesto

---

## 6. MUESTRA DE PRODUCTOS POR CATEGORÍA

### 6.1 Productos con IVA 16%
```
(C) Aguja de Res Nacional Corte/Procesado pz   | Tasa: 16.0% | Estado: OK
(L) Aguja de Res Nacional Lonja Procesada kg   | Tasa: 16.0% | Estado: OK
(L) Arrachera Choice Lonja Procesada kg        | Tasa: 16.0% | Estado: OK
(L) Cordero Osobuco de Lonja Procesada kg      | Tasa: 16.0% | Estado: OK
```

### 6.2 Productos con Tasa 0% Válida (Alimentos)
```
(C) Arrachera Lorenza de kg                    | Tasa: 0.0% | Estado: OK
(C) Arrachera p/Parrilla kg                    | Tasa: 0.0% | Estado: OK
Atun Hamachi Lonja                             | Tasa: 0.0% | Estado: OK
$***Edicion Prod Col                           | Tasa: 0.0% | Estado: OK
```

### 6.3 Productos IMPUESTO_NO_CONFIGURADO
```
BRANDIG                                        | Tasa: None | Estado: IMPUESTO_NO_CONFIGURADO
EXTRA DE CHIMICHURRI                           | Tasa: None | Estado: IMPUESTO_NO_CONFIGURADO
ISR Retenido                                   | Tasa: None | Estado: IMPUESTO_NO_CONFIGURADO
Intereses Bancarios                            | Tasa: None | Estado: IMPUESTO_NO_CONFIGURADO
```

---

## 7. COMPORTAMIENTO DE CÁLCULOS

### 7.1 Para Productos con Tasa Válida (≥ 0)
```
precio_sugerido = costo_receta * (1 + margen) * (1 + tasa_impuesto/100)
estado = 'OK'
// Permite solicitud de cambio de precio
```

### 7.2 Para Productos con Tasa = -1 (NO_CONFIGURADO)
```
precio_sugerido = NULL
estado = 'IMPUESTO_NO_CONFIGURADO'
mensaje = "Producto MPRO sin tasa de impuesto homologada"
// NO permite cálculo de precio sugerido
// NO permite solicitud de cambio de precio
```

---

## 8. RIESGOS PENDIENTES

1. **62 productos sin impuesto**: Requieren revisión manual o configuración en MPRO
2. **Algunos productos con precio -1**: Marcador especial de MPRO (no afecta cálculos)

---

## 9. RECOMENDACIÓN PARA SIGUIENTE FASE

### FASE 1C-3G-C: Modelo Canónico de Impuestos

Se recomienda crear las siguientes tablas en EDARSAHUB SQL:

1. **`Comercial_ImpuestosCatalogo`**: Catálogo maestro de impuestos
2. **`Comercial_ImpuestosTasas`**: Tasas vigentes por período
3. **`Sync_Impuestos_Origen`**: Trazabilidad de mapeo MPRO/SR

Esto permitirá:
- Administración centralizada de impuestos
- UI para configurar los 62 productos sin impuesto
- Historial de cambios de tasas

---

## 10. CONEXIONES UTILIZADAS

| Sistema | Host | Base de Datos | Modo |
|---------|------|---------------|------|
| MPRO | 54.39.104.176:1433 | CENTRAL2020 | LECTURA |
| EDARSAHUB | 54.39.104.176:1433 | EDARSAHUB | ESCRITURA |

---

**FIN DEL REPORTE**

**Siguiente Acción**: Esperar autorización para FASE 1C-3G-C (Modelo Canónico de Impuestos)
