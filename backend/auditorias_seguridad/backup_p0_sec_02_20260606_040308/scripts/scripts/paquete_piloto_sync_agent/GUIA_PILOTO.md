# ============================================================================
# GUÍA DE EJECUCIÓN: PILOTO SYNC AGENT - SOFTRESTAURANT
# ============================================================================
#
# Versión: 1.0
# Fecha: 2026-04-23
#
# ============================================================================

## RESUMEN

Este paquete permite ejecutar el piloto del Sync Agent para sincronizar
KPIs de un servidor SoftRestaurant real hacia EDARSA HUB.

**Objetivo del piloto:**
- Validar el flujo completo: Extracción SQL → Envío a HUB → UPSERT → Heartbeat
- Confirmar idempotencia (sin duplicados)
- Generar evidencia para autorizar Fase 2

---

## PREREQUISITOS

### En la máquina donde se ejecutará el piloto:

| Requisito | Detalle |
|-----------|---------|
| Python | 3.9 o superior |
| Acceso SQL | Conectividad al SQL Server de SoftRestaurant |
| Acceso Internet | Para conectar a EDARSA HUB |

### Instalar dependencias Python:

```bash
pip install pymssql requests pyyaml
```

### Verificar conectividad SQL:

```bash
# Desde la máquina donde correrá el agente
telnet <IP_SQL_SERVER> 1433
```

---

## PASO 1: REGISTRAR SERVIDOR EN HUB

**Si el servidor SoftRestaurant NO está registrado en EDARSA HUB:**

1. Acceder a EDARSA HUB como administrador
2. Ir a **Menú Servidores** (o Configuración > Servidores SQL)
3. Agregar nuevo servidor:
   - Nombre: [Nombre descriptivo, ej. "CIENFUEGOS_SR"]
   - Tipo: SoftRestaurant
   - Host: [IP o hostname del SQL Server]
   - Puerto: 1433
   - Base de datos: [Nombre de la BD]
   - Usuario: [Usuario SQL]
   - Contraseña: [Password SQL]
4. Guardar y anotar el **ID del servidor** (UUID)

---

## PASO 2: GENERAR TOKEN DE AGENTE

### Desde línea de comandos (recomendado):

```bash
# Variables (reemplazar con valores reales)
HUB_URL="https://TU_HUB_URL"
USER_EMAIL="test@example.com"
USER_PASSWORD="TU_PASSWORD"
SERVER_ID="UUID_DEL_SERVIDOR"

# 1. Obtener token de usuario
USER_TOKEN=$(curl -s -X POST "$HUB_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

echo "Token usuario obtenido: ${USER_TOKEN:0:20}..."

# 2. Generar token de agente
curl -s -X POST "$HUB_URL/api/admin/agents/generate-token" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"server_id\": \"$SERVER_ID\", \"agent_id\": \"agent-piloto-001\"}"
```

**Respuesta esperada:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "agent_id": "agent-piloto-001",
  "server_id": "uuid-del-servidor",
  "expires_at": "2027-04-23T..."
}
```

**Guardar el `token` para el siguiente paso.**

---

## PASO 3: CONFIGURAR EL AGENTE

1. Copiar el template de configuración:
```bash
cp config_template.yaml config.yaml
```

2. Editar `config.yaml` con los datos reales:
```yaml
agent_id: "agent-piloto-001"
hub_url: "https://TU_HUB_URL"
hub_token: "PEGAR_TOKEN_DEL_PASO_2"
server_id: "UUID_DEL_SERVIDOR"

sql_local:
  host: "IP_O_HOSTNAME_SQL"
  port: 1433
  database: "NOMBRE_BD_SOFTRESTAURANT"
  username: "usuario_sql"
  password: "password_sql"
```

---

## PASO 4: PROBAR AUTENTICACIÓN (test-auth)

Antes de sincronizar, verificar que el token es válido:

```bash
python sync_agent_piloto.py --config config.yaml --test-only
```

**Salida esperada:**
```
======================================================================
  EDARSA SYNC AGENT - PILOTO SOFTRESTAURANT
  Versión 1.0
======================================================================
  Log: sync_agent_piloto_20260423_120000.log
======================================================================

[1/6] Cargando configuración de config.yaml
  Agent ID: agent-piloto-001
  Server ID: uuid-del-servidor
  HUB URL: https://TU_HUB_URL

[2/6] Verificando autenticación con HUB
✅ Autenticación OK: agent_id=agent-piloto-001, server_id=uuid-del-servidor

✅ Modo test-only: Solo se verificó autenticación
```

**Si falla:**
- Verificar que `hub_url` es correcto (sin trailing slash)
- Verificar que el token no tiene espacios extra
- Verificar conectividad a internet

---

## PASO 5: EJECUTAR PRIMERA CORRIDA

```bash
python sync_agent_piloto.py --config config.yaml
```

**Salida esperada:**
```
[1/6] Cargando configuración de config.yaml
  Agent ID: agent-piloto-001
  ...

[2/6] Verificando autenticación con HUB
✅ Autenticación OK

[3/6] Conectando a SQL Server local
✅ Conectado a SQL Server: localhost:1433/CIENFUEGOS_SR

[4/6] Extrayendo KPIs para fecha 2026-04-23
✅ Datos extraídos: Ventas=$125,000.00, PAX=450, Cheques=120

[5/6] Enviando KPIs a HUB
✅ Respuesta HUB: status=OK, actions={'INSERT': 1, 'UPDATE': 0, 'SKIP': 0, 'REJECTED': 0}

[6/6] Enviando heartbeat
✅ Heartbeat registrado

======================================================================
  RESUMEN DE EJECUCIÓN
======================================================================
  Config cargada:    ✅
  Auth HUB:          ✅
  SQL conectado:     ✅
  Extracción:        ✅
  KPIs enviados:     ✅
  Heartbeat:         ✅

  Acciones UPSERT:
    INSERT: 1
    UPDATE: 0
    SKIP: 0
    REJECTED: 0
======================================================================

✅ EJECUCIÓN COMPLETADA EXITOSAMENTE
```

**Anotar:** La acción debe ser `INSERT: 1` en la primera ejecución.

---

## PASO 6: EJECUTAR SEGUNDA CORRIDA (Validar Idempotencia)

Ejecutar inmediatamente después de la primera:

```bash
python sync_agent_piloto.py --config config.yaml
```

**Salida esperada:**
```
  Acciones UPSERT:
    INSERT: 0
    UPDATE: 0
    SKIP: 1      <-- IMPORTANTE: Debe ser SKIP, no INSERT
    REJECTED: 0
```

**Esto confirma que NO se crearon duplicados.**

---

## PASO 7: COMPLETAR 5 EJECUCIONES

Para validar estabilidad, ejecutar el piloto 5 veces:

| Ejecución | Fecha | Acción Esperada | Resultado |
|-----------|-------|-----------------|-----------|
| 1 | Día actual | INSERT: 1 | ☐ |
| 2 | Día actual | SKIP: 1 | ☐ |
| 3 | Día anterior | INSERT: 1 | ☐ |
| 4 | Día anterior | SKIP: 1 | ☐ |
| 5 | Día actual (con datos nuevos si es otro día) | INSERT o UPDATE | ☐ |

**Comando para fecha específica:**
```bash
python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22
```

---

## PASO 8: CAPTURAR EVIDENCIA

El script genera automáticamente:
1. **Log**: `sync_agent_piloto_YYYYMMDD_HHMMSS.log`
2. **Reporte JSON**: `reporte_piloto_YYYYMMDD_HHMMSS.json`

**Guardar todos los archivos generados para el reporte final.**

---

## CHECKLIST DE VALIDACIÓN

Completar esta checklist para cada ejecución:

| Criterio | Ejecución 1 | Ejecución 2 | Ejecución 3 | Ejecución 4 | Ejecución 5 |
|----------|-------------|-------------|-------------|-------------|-------------|
| Config cargada | ☐ | ☐ | ☐ | ☐ | ☐ |
| Auth HUB OK | ☐ | ☐ | ☐ | ☐ | ☐ |
| SQL conectado | ☐ | ☐ | ☐ | ☐ | ☐ |
| Extracción OK | ☐ | ☐ | ☐ | ☐ | ☐ |
| KPIs enviados | ☐ | ☐ | ☐ | ☐ | ☐ |
| Heartbeat OK | ☐ | ☐ | ☐ | ☐ | ☐ |
| Sin duplicados | N/A | ☐ | N/A | ☐ | ☐ |

---

## FORMATO DEL REPORTE FINAL

Al completar las 5 ejecuciones, enviar al equipo de desarrollo:

```
REPORTE PILOTO SYNC AGENT - SOFTRESTAURANT
==========================================

SERVIDOR PILOTO:
- Nombre: [Nombre del servidor]
- ID: [UUID]
- Host: [IP:Puerto]
- Base de datos: [Nombre BD]

EJECUCIONES:
| # | Fecha/Hora | Fecha Datos | Acción | Ventas | PAX | Cheques | Status |
|---|------------|-------------|--------|--------|-----|---------|--------|
| 1 | YYYY-MM-DD HH:MM | YYYY-MM-DD | INSERT | $X | X | X | OK/ERROR |
| 2 | ... | ... | SKIP | ... | ... | ... | ... |
| 3 | ... | ... | INSERT | ... | ... | ... | ... |
| 4 | ... | ... | SKIP | ... | ... | ... | ... |
| 5 | ... | ... | ... | ... | ... | ... | ... |

VALIDACIÓN DE IDEMPOTENCIA:
- Ejecución 2 después de 1: ☐ SKIP (sin duplicados)
- Ejecución 4 después de 3: ☐ SKIP (sin duplicados)

ARCHIVOS ADJUNTOS:
- [ ] Logs de las 5 ejecuciones
- [ ] Reportes JSON de las 5 ejecuciones
- [ ] Screenshot de datos en HUB (opcional)

OBSERVACIONES:
[Cualquier problema o nota relevante]

DICTAMEN:
☐ PILOTO EXITOSO - Autorizar Fase 2
☐ PILOTO CON OBSERVACIONES - [Detalle]
☐ PILOTO FALLIDO - [Motivo]
```

---

## SOLUCIÓN DE PROBLEMAS

### Error: "No se puede conectar a SQL Server"
- Verificar que SQL Server está corriendo
- Verificar que el puerto 1433 está abierto
- Verificar usuario/contraseña
- Probar conexión con SSMS u otra herramienta

### Error: "Token inválido o expirado"
- Regenerar token desde HUB
- Verificar que el token no tiene espacios

### Error: "server_id en token no coincide"
- El token fue generado para otro servidor
- Regenerar token con el server_id correcto

### Error: "Timeout conectando a HUB"
- Verificar conectividad a internet
- Verificar que la URL es correcta
- Probar abrir la URL en navegador

### Sin datos para la fecha
- Verificar que hay cheques en esa fecha en SoftRestaurant
- Probar con otra fecha: `--fecha YYYY-MM-DD`

---

## CONTACTO

Para problemas no resueltos, contactar al equipo de desarrollo con:
1. Logs completos
2. Reportes JSON generados
3. Descripción del error
4. Pasos para reproducir

---

**FIN DE LA GUÍA**
