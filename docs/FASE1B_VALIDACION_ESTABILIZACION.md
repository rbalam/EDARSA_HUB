# FASE 1B - VALIDACIÓN Y ESTABILIZACIÓN
# Módulo Propinas TPV - Solo SoftRestaurant

**Fecha:** 15 de Abril de 2026  
**Estado:** IMPLEMENTACIÓN DE CAPA DEFENSIVA COMPLETADA  
**Alcance:** La Estelar, Cienfuegos, 130 Mérida

---

## 1. MATRIZ REAL POR SERVIDOR SOFTRESTAURANT

### 1.1 Servidores Detectados

El endpoint `/api/finanzas/propinas/detectar-esquema-todos` detectó **6 servidores SoftRestaurant** en la configuración:

| # | Servidor | Host | Database | Sistema |
|---|----------|------|----------|---------|
| 1 | CIENFUEGOS | servercienfuegos.ddns.net:6669 | softrestaurant95pro | SoftRestaurant |
| 2 | LA ESTELAR (1) | serverestelar.ddns.net:6669 | softrestaurant12 | SoftRestaurant |
| 3 | LA ESTELAR (2) | serverestelar.ddns.net:6969 | softrestaurant12 | SoftRestaurant |
| 4 | 130° MERIDA (1) | 130mid.ddns.net:1433 | softrestaurant10 | SoftRestaurant |
| 5 | 130° MERIDA (2) | 130mid.ddns.net:1433 | softrestaurant10 | SoftRestaurant |
| 6 | CIENFUEGOS TABLAJERIA | servercienfuegos.ddns.net:6669 | Tablajeria | SoftRestaurant |

### 1.2 Estado de Conectividad desde Preview

| Servidor | Estado Conexión | Motivo |
|----------|----------------|--------|
| Todos | ❌ TIMEOUT | Servidores on-premise no accesibles desde Preview |

**Nota:** La validación real requiere acceso VPN o ambiente interno.

### 1.3 Datos de Esquema Parcialmente Obtenidos

En intentos previos donde hubo conexión momentánea, se detectó:

**CIENFUEGOS (softrestaurant95pro):**
```
Tablas detectadas: [estaciones, movtoscaja, movtoscajadetalles]
Columnas mapeadas:
  - tipo_movimiento: "tipo"
  - importe: "importe"
  - folio: "folio"
  - fecha: "fecha"
Problema: No se encontró columna de concepto en detalle
```

**130° MERIDA (softrestaurant10):**
```
Tablas detectadas: [estaciones, movtoscaja, movtoscajadetalles]
Columnas mapeadas:
  - tipo_movimiento: "tipo"
  - importe: "importe"
  - folio: "folio"
  - fecha: "fecha"
Problema: No se encontró columna de concepto en detalle
```

**LA ESTELAR (softrestaurant12):**
```
Tablas detectadas: [] (timeout antes de completar)
```

### 1.4 Hallazgo Crítico

**La columna `idconcepto` no fue encontrada** en las tablas de detalle. Esto indica que:

1. La columna tiene otro nombre (ej: `concepto`, `idtipo`, `tipodetalle`)
2. O la estructura de SoftRestaurant v10/v12/v95 difiere significativamente

---

## 2. QUERY DEFENSIVA IMPLEMENTADA

### 2.1 Estrategia Elegida: Opción A - Query Adaptable por Detección

**Implementación completada:**

| Archivo | Descripción |
|---------|-------------|
| `/app/backend/modules/finanzas/propinas_tpv/schema_detector.py` | Detector de esquema con mapeo de alternativas |
| `/app/backend/modules/finanzas/propinas_tpv/repository.py` | Método `get_propinas_cortes_defensivo()` |
| `/app/backend/modules/finanzas/propinas_tpv/routes.py` | Endpoints de diagnóstico |

### 2.2 Flujo de Query Defensiva

```
1. Detectar esquema (INFORMATION_SCHEMA.COLUMNS)
   ↓
2. Mapear columnas encontradas a nombres estándar
   ↓
3. Verificar compatibilidad mínima
   ↓
4. Construir query adaptada dinámicamente
   ↓
5. Ejecutar y procesar resultados
```

### 2.3 Alternativas de Columnas Configuradas

```python
COLUMN_ALTERNATIVES = {
    'concepto_id': [
        'idconcepto', 'concepto_id', 'conceptoid', 
        'id_concepto', 'concepto', 'idtipo', 'tipo_concepto'
    ],
    'tipo_movimiento': [
        'idtipomovtocaja', 'idtipomovto', 
        'tipo_movimiento', 'tipo'
    ],
    # ... más alternativas
}
```

### 2.4 Endpoints de Diagnóstico Disponibles

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/finanzas/propinas/detectar-esquema/{server_id}` | Detecta esquema de un servidor específico |
| `GET /api/finanzas/propinas/detectar-esquema-todos` | Detecta esquema de todos los servidores |
| `GET /api/finanzas/propinas/preview` | Preview de propinas sin guardar |

---

## 3. VALIDACIÓN PENDIENTE CON DATOS REALES

### 3.1 Requisito Bloqueante

**⚠️ NO ES POSIBLE VALIDAR DESDE PREVIEW**

Los servidores SoftRestaurant están en red privada/VPN y no son accesibles desde el entorno de desarrollo Preview.

### 3.2 Checklist para Validación (A ejecutar desde ambiente con VPN)

| # | Validación | Comando | Estado |
|---|------------|---------|--------|
| 1 | Detectar esquema CIENFUEGOS | `GET /detectar-esquema/{id}` | ⏳ PENDIENTE |
| 2 | Detectar esquema LA ESTELAR | `GET /detectar-esquema/{id}` | ⏳ PENDIENTE |
| 3 | Detectar esquema 130° MERIDA | `GET /detectar-esquema/{id}` | ⏳ PENDIENTE |
| 4 | Preview propinas CIENFUEGOS | `GET /preview?server_id=X` | ⏳ PENDIENTE |
| 5 | Preview propinas LA ESTELAR | `GET /preview?server_id=X` | ⏳ PENDIENTE |
| 6 | Preview propinas 130° MERIDA | `GET /preview?server_id=X` | ⏳ PENDIENTE |
| 7 | Sincronización de prueba | `POST /sincronizar` | ⏳ PENDIENTE |
| 8 | Verificar cálculo 2% | Manual | ⏳ PENDIENTE |
| 9 | Verificar no duplicidad | Re-sincronizar | ⏳ PENDIENTE |

---

## 4. RIESGOS REMANENTES

| # | Riesgo | Prob. | Impacto | Mitigación | Estado |
|---|--------|-------|---------|------------|--------|
| R1 | Columna `idconcepto` no existe | **CONFIRMADO** | Alto | Buscar alternativa en esquema real | ❌ ABIERTO |
| R2 | Diferentes versiones de SoftRest | Confirmado | Alto | Query adaptable implementada | ✅ MITIGADO |
| R3 | Timeout en servidores lentos | Alta | Bajo | Timeout configurable | ✅ MITIGADO |
| R4 | Sin acceso VPN desde Preview | 100% | Bloqueante | Requiere ambiente interno | ❌ BLOQUEANTE |
| R5 | Concepto 9 no existe | Media | Alto | Hacer configurable | ⚠️ PENDIENTE |

---

## 5. DICTAMEN GO / NO GO POR SUCURSAL

### Estado Actual: BLOQUEADO

| Sucursal | Dictamen | Justificación |
|----------|----------|---------------|
| La Estelar | ⛔ BLOQUEADO | Sin conectividad para validar esquema |
| Cienfuegos | ⛔ BLOQUEADO | Sin conectividad para validar esquema |
| 130° Mérida | ⛔ BLOQUEADO | Sin conectividad para validar esquema |

### Condiciones para Desbloquear:

1. **Ejecutar validación desde ambiente con VPN** o red interna
2. **Identificar nombre correcto de columna de concepto** en cada servidor
3. **Confirmar que concepto 9 = Propinas Pagadas** en todos los servidores
4. **Ejecutar al menos 1 sincronización exitosa** con datos reales

---

## 6. PRÓXIMOS PASOS REQUERIDOS

### Acción del Usuario (Con acceso a red interna):

1. **Conectarse a un servidor SoftRestaurant** con SQL Server Management Studio
2. **Ejecutar query de diagnóstico:**

```sql
-- Diagnóstico de estructura para propinas
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'movtoscajadetalles'
ORDER BY ORDINAL_POSITION;

-- Verificar conceptos disponibles
SELECT DISTINCT idconcepto, descripcion
FROM conceptos
ORDER BY idconcepto;

-- O si no existe tabla conceptos, buscar en detalle:
SELECT TOP 10 * FROM movtoscajadetalles;
```

3. **Reportar resultados** para ajustar el detector de esquema
4. **Probar endpoint** `/api/finanzas/propinas/detectar-esquema-todos` desde red interna

### Acción del Desarrollador (Post-diagnóstico):

1. Ajustar `COLUMN_ALTERNATIVES` según hallazgos
2. Ajustar ID de concepto de propinas si es diferente a 9
3. Re-ejecutar pruebas de sincronización
4. Documentar configuración final por servidor

---

## 7. ARCHIVOS IMPLEMENTADOS EN FASE 1B

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `schema_detector.py` | ~200 | Detector de esquema con mapeo automático |
| `repository.py` (actualizado) | +100 | Método `get_propinas_cortes_defensivo()` |
| `routes.py` (actualizado) | +150 | Endpoints de diagnóstico |

**Total cambios FASE 1B:** ~450 líneas de código

---

**FIN DEL DOCUMENTO FASE 1B**

*Requiere validación desde ambiente con acceso VPN antes de continuar.*
