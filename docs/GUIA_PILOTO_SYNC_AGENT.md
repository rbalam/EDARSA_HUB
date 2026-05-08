# GUÍA DE PILOTO: EDARSA Sync Agent - FASE 1

**Versión**: 1.0  
**Fecha**: 2026-04-23  
**Estado**: PILOTO

---

## 1. RESUMEN

Esta guía describe cómo ejecutar el piloto del Sync Agent para sincronizar KPIs de un servidor **SoftRestaurant** hacia EDARSA HUB.

**Alcance del piloto:**
- UN servidor SoftRestaurant
- Sincronización manual (no automática)
- KPIs básicos: ventas, pax, cheques

---

## 2. REQUISITOS PREVIOS

### 2.1 En la máquina donde se ejecutará el agente

| Requisito | Versión |
|-----------|---------|
| Python | 3.9 o superior |
| pymssql o pyodbc | Última versión |
| requests | Última versión |
| pyyaml | Última versión |

**Instalar dependencias:**
```bash
pip install pymssql requests pyyaml
```

### 2.2 Conectividad

- Acceso a SQL Server local (localhost:1433 o IP local)
- Acceso a internet para conectar a EDARSA HUB

### 2.3 Credenciales necesarias

1. **Token de agente** (se genera desde HUB)
2. **server_id** del servidor SR en HUB
3. **Credenciales SQL** del servidor SoftRestaurant

---

## 3. PASO A PASO

### Paso 1: Generar token de agente en HUB

**Desde la máquina con acceso a HUB (como admin):**

```bash
# Login como admin
curl -X POST "https://TU_HUB_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@edarsa.com","password":"TU_PASSWORD"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])"

# Guardar el token de usuario
USER_TOKEN="eyJ..."

# Generar token de agente
curl -X POST "https://TU_HUB_URL/api/admin/agents/generate-token" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"server_id":"UUID_DEL_SERVIDOR_SR"}'
```

**Respuesta esperada:**
```json
{
  "token": "eyJ...(token largo)...",
  "agent_id": "agent-nombre-servidor-001",
  "server_id": "uuid-del-servidor",
  "expires_at": "2027-04-23T..."
}
```

**Guardar el `token` para el siguiente paso.**

### Paso 2: Crear archivo de configuración

1. Copiar el template:
```bash
cp sync_agent_config_template.yaml config.yaml
```

2. Editar `config.yaml` con los datos reales:
```yaml
agent_id: "agent-piloto-sr-001"
hub_url: "https://TU_HUB_URL"
hub_token: "PEGAR_TOKEN_DEL_PASO_1"
server_id: "UUID_DEL_SERVIDOR"

sql_local:
  host: "localhost"
  port: 1433
  database: "NOMBRE_BD_SOFTRESTAURANT"
  username: "usuario_sql"
  password: "password_sql"
```

### Paso 3: Verificar autenticación

```bash
python sync_agent_piloto.py --config config.yaml --test-only
```

**Salida esperada:**
```
2026-04-23 10:00:00 INFO [SYNC_AGENT_PILOTO] Cargando configuración de config.yaml
2026-04-23 10:00:00 INFO [SYNC_AGENT_PILOTO] Agent ID: agent-piloto-sr-001
2026-04-23 10:00:00 INFO [SYNC_AGENT_PILOTO] Verificando autenticación con HUB...
2026-04-23 10:00:01 INFO [SYNC_AGENT_PILOTO] Autenticación OK: agent_id=agent-piloto-sr-001
2026-04-23 10:00:01 INFO [SYNC_AGENT_PILOTO] Modo test-only: Solo se verificó autenticación
```

### Paso 4: Ejecutar sincronización

```bash
python sync_agent_piloto.py --config config.yaml
```

**Salida esperada:**
```
2026-04-23 10:00:00 INFO [SYNC_AGENT_PILOTO] Cargando configuración de config.yaml
2026-04-23 10:00:00 INFO [SYNC_AGENT_PILOTO] Agent ID: agent-piloto-sr-001
2026-04-23 10:00:00 INFO [SYNC_AGENT_PILOTO] Fecha a sincronizar: 2026-04-23
2026-04-23 10:00:00 INFO [SYNC_AGENT_PILOTO] Verificando autenticación con HUB...
2026-04-23 10:00:01 INFO [SYNC_AGENT_PILOTO] Autenticación OK: agent_id=agent-piloto-sr-001
2026-04-23 10:00:01 INFO [SYNC_AGENT_PILOTO] Conectado a SQL Server via pymssql: localhost:1433/BD
2026-04-23 10:00:02 INFO [SYNC_AGENT_PILOTO] Ejecutando query de KPIs para fecha 2026-04-23
2026-04-23 10:00:02 INFO [SYNC_AGENT_PILOTO] Extraídos 1 registros
2026-04-23 10:00:02 INFO [SYNC_AGENT_PILOTO]   Sucursal 01: Ventas=$125,000.00, PAX=450, Cheques=120
2026-04-23 10:00:02 INFO [SYNC_AGENT_PILOTO] Enviando 1 registros a https://HUB/api/sync/kpis
2026-04-23 10:00:03 INFO [SYNC_AGENT_PILOTO] Respuesta HUB: status=OK, processed=1
2026-04-23 10:00:03 INFO [SYNC_AGENT_PILOTO] ✅ Sincronización exitosa
2026-04-23 10:00:03 INFO [SYNC_AGENT_PILOTO] Enviando heartbeat a https://HUB/api/sync/heartbeat
2026-04-23 10:00:04 INFO [SYNC_AGENT_PILOTO] Heartbeat registrado: Heartbeat registrado
2026-04-23 10:00:04 INFO [SYNC_AGENT_PILOTO] ============================================================
2026-04-23 10:00:04 INFO [SYNC_AGENT_PILOTO] SYNC AGENT PILOTO - EJECUCIÓN COMPLETADA
2026-04-23 10:00:04 INFO [SYNC_AGENT_PILOTO] ============================================================
```

### Paso 5: Verificar datos en HUB

**Verificar documento en kpis_comercial:**
```bash
# Desde ambiente con acceso a MongoDB
mongosh --eval "db.kpis_comercial.find({'source.type': 'SYNC_AGENT'}).pretty()"
```

**Verificar registro en sync_agent_registry:**
```bash
mongosh --eval "db.sync_agent_registry.find({'agent_id': 'agent-piloto-sr-001'}).pretty()"
```

---

## 4. VALIDACIÓN DEL PILOTO

### 4.1 Checklist de éxito

| Criterio | Cómo verificar | ✅/❌ |
|----------|----------------|-------|
| Auth OK | `--test-only` no da error 401 | |
| SQL local OK | Conecta sin timeout | |
| Extracción OK | Muestra ventas > 0 | |
| POST OK | `status=OK` en respuesta | |
| UPSERT OK | Documento en `kpis_comercial` | |
| Heartbeat OK | Documento en `sync_agent_registry` | |
| Idempotencia | Ejecutar 2 veces, verificar 1 doc | |

### 4.2 Verificar idempotencia

Ejecutar el agente dos veces consecutivas:
```bash
python sync_agent_piloto.py --config config.yaml
python sync_agent_piloto.py --config config.yaml
```

En la segunda ejecución, la respuesta debe indicar `SKIP` (no hay cambios):
```json
{
  "status": "OK",
  "processed": 1,
  "actions": {"INSERT": 0, "UPDATE": 0, "SKIP": 1, "REJECTED": 0}
}
```

---

## 5. SOLUCIÓN DE PROBLEMAS

### Error: "Token de agente expirado"
**Causa:** El token tiene más de 1 año.  
**Solución:** Generar nuevo token desde HUB.

### Error: "server_id en token no coincide con payload"
**Causa:** El token fue generado para otro servidor.  
**Solución:** Verificar que `server_id` en config.yaml coincida con el usado al generar el token.

### Error: "No se pudo conectar a SQL Server"
**Causa:** SQL Server no accesible o credenciales incorrectas.  
**Solución:** 
1. Verificar que SQL Server esté corriendo
2. Probar conexión con otra herramienta (SSMS, sqlcmd)
3. Verificar credenciales

### Error: "No se encontraron datos para fecha X"
**Causa:** No hay ventas registradas en esa fecha.  
**Solución:** Usar `--fecha` con una fecha que tenga datos.

### Error: HTTP 401 al enviar a HUB
**Causa:** Token inválido o expirado.  
**Solución:** Ejecutar `--test-only` para verificar auth primero.

---

## 6. ARCHIVOS DEL PILOTO

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `sync_agent_piloto.py` | `/app/backend/scripts/` | Script del agente |
| `sync_agent_config_template.yaml` | `/app/backend/scripts/` | Template de config |
| `sync_receiver.py` | `/app/backend/api/` | Endpoints HUB |
| `sync_agent_piloto.log` | Directorio de ejecución | Log local |

---

## 7. IDENTIFICACIÓN DE REGISTROS DEL PILOTO

Todos los registros creados por el piloto tienen:

**En `kpis_comercial`:**
```javascript
{
  "source": {
    "type": "SYNC_AGENT",
    "is_pilot": true,
    "agent_id": "agent-piloto-sr-001"
  }
}
```

**En `sync_agent_registry`:**
```javascript
{
  "is_pilot": true
}
```

**Query para encontrar registros del piloto:**
```javascript
// KPIs del piloto
db.kpis_comercial.find({"source.is_pilot": true})

// Agentes piloto
db.sync_agent_registry.find({"is_pilot": true})
```

---

## 8. ROLLBACK DEL PILOTO

Si es necesario eliminar los datos del piloto:

```javascript
// Eliminar KPIs del piloto
db.kpis_comercial.deleteMany({"source.is_pilot": true})

// Eliminar registros de agentes piloto
db.sync_agent_registry.deleteMany({"is_pilot": true})
```

---

## 9. PRÓXIMOS PASOS (FASE 2)

Una vez validado el piloto:

1. Agregar más servidores
2. Implementar cola local con reintentos
3. Instalar como servicio Windows/Linux
4. Dashboard de monitoreo de agentes
5. Auto-actualización del agente

---

**GUÍA DE PILOTO COMPLETADA**
