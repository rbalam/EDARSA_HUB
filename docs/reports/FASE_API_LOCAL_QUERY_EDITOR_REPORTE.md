# FASE API_LOCAL_QUERY_EDITOR - Reporte de Implementación
## Editor de Consultas SQL en Modal de Conexiones API

**Fecha:** 2026-05-15  
**Ejecutado por:** E1 Agent  
**Estado:** COMPLETADO

---

## 1. RESUMEN EJECUTIVO

Se implementó una nueva sección dentro del modal de Alta/Edición de Conexiones API que permite:

- Configurar y probar consultas SELECT asociadas a cada conexión
- Ejecutar pruebas sin repetir credenciales (usa API key cifrada guardada)
- Validar SQL con bloqueo estricto de operaciones peligrosas
- Ver resultados en preview de tabla con columnas detectadas

---

## 2. PROBLEMA UX CORREGIDO

**Antes:**
- Usuario tenía que ir al Test Universal para probar consultas
- Debía repetir URL, API Key y headers manualmente
- Confusión entre herramienta de diagnóstico y configuración operativa

**Después:**
- Sección integrada en el modal de edición de conexión
- Usa credenciales ya guardadas automáticamente
- No requiere repetir API key ni URL
- Test Universal queda como herramienta avanzada de diagnóstico

---

## 3. ARCHIVOS MODIFICADOS

### Backend

| Archivo | Cambios |
|---------|---------|
| `/app/backend/modules/api_connections/repository.py` | +`get_api_connection_with_decrypted_key()`, +`execute_test_query()` |
| `/app/backend/modules/api_connections/routes.py` | +Schemas `TestQueryRequest`, `TestQueryDraftRequest`, +Endpoints `/{id}/test-query`, `/test-query-draft` |

### Frontend

| Archivo | Cambios |
|---------|---------|
| `/app/frontend/src/pages/Servidores.js` | +Estados `queryTestData`, `testingQuery`, `queryTestResult`, +Función `executeTestQuery()`, +Sección JSX "Consulta de prueba" |

---

## 4. ENDPOINTS CREADOS

### POST `/api/api-connections/{connection_id}/test-query`

Prueba consulta SQL contra conexión existente.

**Request:**
```json
{
  "sql_query": "SELECT TOP 10 * FROM cheques",
  "tipo_uso": "Ventas del día",
  "nombre_consulta": "Cheques del día",
  "timeout": 30
}
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "status_code": 200,
  "response_time_ms": 245.5,
  "rows_count": 10,
  "columns": ["folio", "fecha", "total"],
  "preview_data": [...],
  "connection_id": "uuid...",
  "tipo_uso": "Ventas del día"
}
```

### POST `/api/api-connections/test-query-draft`

Prueba consulta sin conexión guardada (alta nueva).

**Request:**
```json
{
  "url": "http://api.local:8001/query",
  "api_key": "opcional",
  "sql_query": "SELECT 1 as test",
  "timeout": 30
}
```

---

## 5. VALIDACIONES SQL APLICADAS

El validador (`SQLValidator`) bloquea:

| Keyword/Patrón | Bloqueado |
|----------------|-----------|
| DELETE | ✅ |
| UPDATE | ✅ |
| INSERT | ✅ |
| DROP | ✅ |
| ALTER | ✅ |
| TRUNCATE | ✅ |
| EXEC / EXECUTE | ✅ |
| CREATE | ✅ |
| MERGE | ✅ |
| GRANT / REVOKE / DENY | ✅ |
| BACKUP / RESTORE | ✅ |
| DBCC | ✅ |
| KILL / SHUTDOWN | ✅ |
| WAITFOR | ✅ |
| xp_* | ✅ |
| sp_* | ✅ |
| fn_* | ✅ |
| Comentarios (-- / /* */) | ✅ |
| Múltiples statements (;) | ✅ |
| SQL vacío | ✅ |

**Permitidos:**
- SELECT
- WITH (CTEs) que terminen en SELECT

---

## 6. PERMISOS APLICADOS

| Acción | Permiso |
|--------|---------|
| Probar consulta en conexión existente | Usuario autenticado |
| Probar consulta draft (nueva) | Usuario autenticado |
| Ver preview de datos | Usuario autenticado |
| Editar conexión | Admin/SuperAdmin |

**Auditoría:**
- Cada ejecución se registra en `Servidores_Conexiones_Log`
- Se guarda: usuario, connection_id, resultado, duración
- NO se guarda: API key, SQL completo, datos sensibles

---

## 7. CÓMO SE GUARDAN LAS CONSULTAS

En esta fase, las consultas de prueba NO se persisten automáticamente con la conexión.

**Para persistir consultas:**
- Usar el Catálogo SQL existente (`ConsultasSQL_Catalogo`)
- Asociar mediante `ConsultasSQL_Servidores` (relación consulta-servidor)

**Futuro (FASE 3+):**
- Agregar campo `consulta_default_id` en `Servidores_Conexiones`
- O crear tabla `Servidores_Conexiones_Consultas` para múltiples consultas por conexión

---

## 8. PRUEBAS EJECUTADAS

### Validación SQL

| Test | Resultado |
|------|-----------|
| SELECT válido | ✅ Permitido |
| DELETE | ✅ Bloqueado |
| UPDATE | ✅ Bloqueado |
| INSERT | ✅ Bloqueado |
| DROP | ✅ Bloqueado |
| xp_cmdshell | ✅ Bloqueado |
| Múltiples statements | ✅ Bloqueado |

### Endpoints

| Test | Resultado |
|------|-----------|
| `/test-query-draft` con SELECT | ✅ OK |
| `/test-query-draft` con DELETE | ✅ Rechazado |
| `/{id}/test-query` con conexión existente | ✅ OK |
| Login después de cambios | ✅ OK |
| Build frontend | ✅ OK |

---

## 9. PAYLOADS RECHAZADOS

```json
// DELETE
{"sql_query": "DELETE FROM users"}
// Respuesta: {"sql_blocked": true, "validation_errors": ["Consulta debe iniciar con SELECT", "Palabra peligrosa: DELETE"]}

// UPDATE
{"sql_query": "UPDATE users SET name='x'"}
// Respuesta: {"sql_blocked": true}

// INSERT
{"sql_query": "INSERT INTO users VALUES (1)"}
// Respuesta: {"sql_blocked": true}

// DROP
{"sql_query": "DROP TABLE users"}
// Respuesta: {"sql_blocked": true}

// Múltiples statements
{"sql_query": "SELECT 1; DROP TABLE x"}
// Respuesta: {"sql_blocked": true, "validation_errors": ["Múltiples statements detectados"]}

// xp_ prefix
{"sql_query": "SELECT xp_cmdshell('dir')"}
// Respuesta: {"sql_blocked": true}
```

---

## 10. NO REGRESIÓN

| Componente | Estado |
|------------|--------|
| Login | ✅ OK |
| Listado conexiones API | ✅ OK |
| Probar Conexión (test health) | ✅ OK |
| Test Universal | ✅ OK (no eliminado) |
| Edición de conexión | ✅ OK |
| `/api/consultas-sql/*` | ✅ Sin cambios |
| Auth/RBAC | ✅ Sin cambios |
| Comercial | ✅ Sin cambios |
| Tablero Ejecutivo | ✅ Sin cambios |
| Compras | ✅ Sin cambios |
| Finanzas | ✅ Sin cambios |
| Operaciones/Inventarios | ✅ Sin cambios |

---

## 11. PENDIENTES

| Pendiente | Prioridad | Descripción |
|-----------|-----------|-------------|
| Persistir consulta con conexión | P2 | Guardar `tipo_uso`, `nombre_consulta`, `sql_query` en BD |
| Cargar consulta al editar | P2 | Si hay consulta guardada, pre-poblar el form |
| Checkbox "solo_ventas_dia" condicional | P3 | Aplicar solo cuando tipo_uso = "Ventas del día" |
| Limitar por permisos granulares | P3 | Solo admin puede crear consultas, otros solo probar |
| Histórico de pruebas | P3 | Mostrar últimas N ejecuciones de prueba |

---

## 12. COMPONENTES UI AGREGADOS

```jsx
// Sección en modal de conexión API
<div className="border-t border-zinc-200 pt-4 mt-4">
  <h4>Consulta de prueba / Consulta operativa</h4>
  
  {/* Tipo de uso */}
  <Select value={queryTestData.tipo_uso} ...>
    <SelectItem value="Ventas del día" />
    <SelectItem value="Inventario" />
    <SelectItem value="Cortes" />
    <SelectItem value="Compras" />
    <SelectItem value="Otro" />
  </Select>
  
  {/* Nombre de consulta */}
  <Input value={queryTestData.nombre_consulta} ... />
  
  {/* SQL */}
  <Textarea value={queryTestData.sql_query} ... />
  
  {/* Timeout + Botón */}
  <Select value={queryTestData.timeout} ... />
  <Button onClick={executeTestQuery}>Probar consulta</Button>
  
  {/* Resultado */}
  {queryTestResult && (
    <div className={success ? 'bg-green-50' : 'bg-red-50'}>
      {/* Estado, tiempo, filas, columnas */}
      {/* Preview de tabla con max 5 filas */}
    </div>
  )}
</div>
```

---

## 13. SEGURIDAD IMPLEMENTADA

1. **SQL Injection:** Validador estricto rechaza todo excepto SELECT/WITH
2. **API Key:** Nunca expuesta en frontend ni logs
3. **Auditoría:** Toda ejecución registrada sin datos sensibles
4. **Timeout:** Configurable 15-90s para evitar DoS
5. **Preview limitado:** Max 20 filas, 5 visibles en UI

---

*Documento generado por E1 Agent*  
*Fecha: 2026-05-15*
