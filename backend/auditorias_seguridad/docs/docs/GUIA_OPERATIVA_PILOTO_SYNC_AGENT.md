# GUÍA OPERATIVA COMPLETA: PILOTO SYNC AGENT
## Ejecución Paso a Paso desde Ambiente Local

**Versión**: 1.1  
**Fecha**: 2026-04-23  
**Actualización**: Ajustado para usar servidor existente (no crear nuevo)  
**Objetivo**: Completar 5 ejecuciones exitosas del piloto Sync Agent

---

# ANTES DE EMPEZAR

## Qué necesitas tener listo:

| Requisito | Cómo verificar |
|-----------|----------------|
| Computadora con Windows o Linux | - |
| Python 3.9 o superior | Ejecutar: `python --version` |
| Acceso a internet | Poder abrir https://stock-tracker-990.preview.emergentagent.com |
| Acceso al SQL Server de SoftRestaurant | Poder conectarte con SSMS o similar |
| Credenciales de admin en EDARSA HUB | Email y contraseña de admin |
| Credenciales SQL del servidor SR | Host, puerto, base de datos, usuario, contraseña |

## URLs que usarás:

```
HUB_URL = https://stock-tracker-990.preview.emergentagent.com
```

---

# PASO 1: SELECCIONAR SERVIDOR SR EXISTENTE EN HUB

**IMPORTANTE: NO crear un servidor nuevo. Usar uno existente.**

## 1.1 Acceder a EDARSA HUB

1. Abre tu navegador
2. Ve a: `https://stock-tracker-990.preview.emergentagent.com`
3. Inicia sesión con tu cuenta de administrador:
   - Email: `admin@edarsa.com`
   - Contraseña: `EDARSA2025`

## 1.2 Ir al menú de Servidores

1. Una vez dentro, busca en el menú lateral izquierdo la opción **"Servidores"** o **"Configuración > Servidores SQL"**
2. Haz clic para entrar

## 1.3 Localizar un servidor SoftRestaurant existente

1. En la lista de servidores, busca uno que cumpla:
   - **Tipo**: SoftRestaurant
   - **Estado**: Activo
   - **Acceso local confirmado**: Que puedas conectarte al SQL desde tu máquina

2. Verifica que el servidor tenga configuración SQL válida:

| Campo | Qué verificar |
|-------|---------------|
| **Tipo de Sistema** | Debe ser **SoftRestaurant** |
| **Host** | IP o hostname accesible desde tu máquina |
| **Puerto** | Normalmente 1433 |
| **Base de datos** | Nombre de la BD de SoftRestaurant |
| **Estado** | Debe estar **Activo** |

3. **NO crear un servidor nuevo**. Usar uno existente con datos reales.

## 1.4 Copiar el Server ID

**MUY IMPORTANTE**: Necesitas copiar el **ID del servidor existente** (UUID).

**Opción A - Desde la interfaz:**
- Haz clic en el servidor que seleccionaste
- Busca el campo ID o Server ID
- Debe tener formato tipo: `6d053c22-523e-48c0-b72b-96081e2d781b`
- Cópialo y guárdalo en un archivo de texto

**Opción B - Desde la consola del navegador (si no ves el ID en la interfaz):**
1. Presiona F12 para abrir las herramientas de desarrollador
2. Ve a la pestaña "Network" o "Red"
3. Busca la llamada que trae los servidores (normalmente `/api/comercial/servers` o similar)
4. En la respuesta verás los servidores con sus IDs

**Guarda este ID**, lo necesitarás en el paso 2.

## 1.5 Nota sobre trazabilidad del piloto

Aunque uses un `server_id` existente, los registros del piloto se distinguirán por metadata:
- `source.type = "SYNC_AGENT"`
- `source.is_pilot = true`
- `agent_id` único del agente piloto

Esto permite identificar qué datos fueron generados por el piloto sin duplicar servidores.

## 1.6 Validar antes de continuar

✅ Seleccionaste un servidor SoftRestaurant **existente** (no creaste uno nuevo)  
✅ El servidor está **activo**  
✅ Tienes **acceso local** al SQL de ese servidor  
✅ Tienes anotado el **Server ID** (UUID)  
✅ Tienes las **credenciales SQL** para conectarte

---

# PASO 2: GENERAR EL TOKEN DEL AGENTE

## 2.1 Preparar los datos

Antes de ejecutar los comandos, prepara estos valores:

```
HUB_URL=https://stock-tracker-990.preview.emergentagent.com
USER_EMAIL=admin@edarsa.com
USER_PASSWORD=EDARSA2025
SERVER_ID=<EL_UUID_QUE_COPIASTE_EN_PASO_1>
```

## 2.2 Ejecutar desde terminal/consola

Abre una terminal (CMD en Windows, Terminal en Linux/Mac) y ejecuta:

### En Linux/Mac:

```bash
# Definir variables (REEMPLAZA EL SERVER_ID CON EL TUYO)
HUB_URL="https://stock-tracker-990.preview.emergentagent.com"
USER_EMAIL="admin@edarsa.com"
USER_PASSWORD="EDARSA2025"
SERVER_ID="PEGAR_AQUI_TU_SERVER_ID"

# Paso 2.2.1: Obtener token de usuario
echo "Obteniendo token de usuario..."
USER_TOKEN=$(curl -s -X POST "$HUB_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

echo "Token de usuario obtenido: ${USER_TOKEN:0:30}..."

# Paso 2.2.2: Generar token de agente
echo ""
echo "Generando token de agente..."
curl -s -X POST "$HUB_URL/api/admin/agents/generate-token" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"server_id\": \"$SERVER_ID\", \"agent_id\": \"agent-sr-piloto-001\"}"
```

### En Windows (PowerShell):

```powershell
# Definir variables (REEMPLAZA EL SERVER_ID CON EL TUYO)
$HUB_URL = "https://stock-tracker-990.preview.emergentagent.com"
$USER_EMAIL = "admin@edarsa.com"
$USER_PASSWORD = "EDARSA2025"
$SERVER_ID = "PEGAR_AQUI_TU_SERVER_ID"

# Paso 2.2.1: Obtener token de usuario
Write-Host "Obteniendo token de usuario..."
$loginBody = @{
    email = $USER_EMAIL
    password = $USER_PASSWORD
} | ConvertTo-Json

$loginResponse = Invoke-RestMethod -Uri "$HUB_URL/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
$USER_TOKEN = $loginResponse.token
Write-Host "Token de usuario obtenido: $($USER_TOKEN.Substring(0,30))..."

# Paso 2.2.2: Generar token de agente
Write-Host ""
Write-Host "Generando token de agente..."
$agentBody = @{
    server_id = $SERVER_ID
    agent_id = "agent-sr-piloto-001"
} | ConvertTo-Json

$headers = @{
    Authorization = "Bearer $USER_TOKEN"
}

$agentResponse = Invoke-RestMethod -Uri "$HUB_URL/api/admin/agents/generate-token" -Method POST -Body $agentBody -ContentType "application/json" -Headers $headers
$agentResponse | ConvertTo-Json
```

## 2.3 Respuesta esperada (ÉXITO)

Si todo sale bien, verás algo como:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoic3luY19hZ2VudCIsInNlcnZlcl9pZCI6IjMyOWQzMzdmLWJiNGYtNGYzMy05NzRhLTQ3YjkxNmNjODMyZiIsImFnZW50X2lkIjoiYWdlbnQtc3ItcGlsb3RvLTAwMSIsImlhdCI6MTc3Njk3NjQyMiwiZXhwIjoxODA4NTEyNDIyfQ.tIvm-VG2lH2X6oNUsOOVGCfhpZQiQ3p8viWSeq4JXLI",
  "agent_id": "agent-sr-piloto-001",
  "server_id": "329d337f-bb4f-4f33-974a-47b916cc832f",
  "expires_at": "2027-04-23T20:33:42.412545+00:00"
}
```

## 2.4 GUARDAR EL TOKEN

**MUY IMPORTANTE**: Copia TODO el valor del campo `token` (el texto largo que empieza con `eyJ...`).

Guárdalo en un archivo de texto. Lo necesitarás en el paso 4.

## 2.5 Errores posibles y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `{"detail":"Token de usuario expirado"}` | El token de login expiró | Volver a ejecutar desde el paso 2.2.1 |
| `{"detail":"Servidor XXX no encontrado"}` | El SERVER_ID es incorrecto | Verificar que copiaste bien el UUID del paso 1 |
| `{"detail":"Solo administradores pueden generar tokens"}` | Tu usuario no es admin | Usar una cuenta de administrador |
| `Connection refused` o timeout | No hay conexión a internet o HUB está caído | Verificar conexión, intentar abrir HUB en navegador |

## 2.6 Validar antes de continuar

✅ Tienes el token del agente guardado (texto largo que empieza con `eyJ...`)  
✅ Tienes anotado el `agent_id` (normalmente `agent-sr-piloto-001`)  
✅ Tienes anotado el `server_id`  

---

# PASO 3: DESCARGAR Y PREPARAR EL PAQUETE

## 3.1 Crear carpeta de trabajo

```bash
# En Linux/Mac
mkdir -p ~/piloto_sync_agent
cd ~/piloto_sync_agent

# En Windows (PowerShell)
mkdir C:\piloto_sync_agent
cd C:\piloto_sync_agent
```

## 3.2 Descargar el paquete

**Opción A - Si tienes acceso al servidor donde está el paquete:**

El paquete está en: `/app/backend/scripts/paquete_piloto_sync_agent.tar.gz`

Cópialo a tu carpeta de trabajo.

**Opción B - Descargar los archivos individualmente:**

Crea los siguientes archivos manualmente (el contenido está en la siguiente sección).

## 3.3 Descomprimir el paquete

```bash
# En Linux/Mac
tar -xzvf paquete_piloto_sync_agent.tar.gz
cd paquete_piloto_sync_agent

# En Windows (con 7-Zip o similar)
# Click derecho > Extraer aquí
# Luego entrar a la carpeta
cd paquete_piloto_sync_agent
```

## 3.4 Verificar contenido

Deberías ver estos archivos:

```
paquete_piloto_sync_agent/
├── sync_agent_piloto.py      <-- Script principal
├── config_template.yaml      <-- Template de configuración
├── GUIA_PILOTO.md           <-- Guía (puedes ignorar, esta es más completa)
├── CHECKLIST_PILOTO.md      <-- Checklist para llenar
├── requirements.txt         <-- Dependencias
└── README.md                <-- Resumen
```

## 3.5 Instalar dependencias de Python

```bash
# Verificar que tienes Python
python --version
# o
python3 --version

# Debe mostrar: Python 3.9.x o superior

# Instalar dependencias
pip install pymssql requests pyyaml

# o si usas pip3
pip3 install pymssql requests pyyaml
```

## 3.6 Errores posibles y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `python: command not found` | Python no está instalado | Descargar de https://www.python.org/downloads/ |
| `pip: command not found` | pip no está en el PATH | Usar `python -m pip install ...` |
| Error instalando pymssql | Faltan dependencias del sistema | En Linux: `apt-get install freetds-dev` |

## 3.7 Validar antes de continuar

✅ Estás en la carpeta `paquete_piloto_sync_agent`  
✅ Ves el archivo `sync_agent_piloto.py`  
✅ Las dependencias se instalaron sin error  

---

# PASO 4: LLENAR EL ARCHIVO config.yaml

## 4.1 Crear el archivo de configuración

```bash
# Copiar el template
cp config_template.yaml config.yaml
```

## 4.2 Editar config.yaml

Abre `config.yaml` con un editor de texto (Notepad, VS Code, nano, vim).

## 4.3 Ejemplo COMPLETO de config.yaml

**COPIA ESTO Y REEMPLAZA LOS VALORES CON LOS TUYOS:**

```yaml
# ============================================================================
# CONFIGURACIÓN DEL PILOTO SYNC AGENT
# ============================================================================

# 1. AGENT_ID
# -----------
# Este valor viene de la respuesta del paso 2 (cuando generaste el token)
# Normalmente es: agent-sr-piloto-001
agent_id: "agent-sr-piloto-001"

# 2. HUB_URL
# ----------
# URL de EDARSA HUB (sin / al final)
# Esta es la URL del preview actual
hub_url: "https://stock-tracker-990.preview.emergentagent.com"

# 3. HUB_TOKEN
# ------------
# Este es el token LARGO que obtuviste en el paso 2
# Empieza con eyJ... y es MUY largo
# PEGA TODO EL TOKEN AQUÍ (sin comillas adicionales dentro)
hub_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.PEGAR_AQUI_TU_TOKEN_COMPLETO"

# 4. SERVER_ID
# ------------
# Este es el UUID del servidor que registraste en el paso 1
# Tiene formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
server_id: "PEGAR_AQUI_TU_SERVER_ID"

# 5. SQL_LOCAL
# ------------
# Estos son los datos de conexión al SQL Server de SoftRestaurant
# DEBEN COINCIDIR con la configuración del servidor existente en HUB
sql_local:
  # Host: puede ser localhost si el SQL está en la misma máquina
  # o una IP como 192.168.1.100
  host: "localhost"
  
  # Puerto: normalmente 1433 para SQL Server
  port: 1433
  
  # Nombre de la base de datos de SoftRestaurant
  database: "NOMBRE_DE_TU_BD"
  
  # Usuario SQL (el mismo que usaste en HUB)
  username: "TU_USUARIO_SQL"
  
  # Contraseña SQL (la misma que usaste en HUB)
  password: "TU_PASSWORD_SQL"
```

## 4.4 Explicación campo por campo

| Campo | De dónde viene | Ejemplo |
|-------|----------------|---------|
| `agent_id` | Respuesta del paso 2 | `agent-sr-piloto-001` |
| `hub_url` | URL fija del HUB | `https://stock-tracker-990.preview.emergentagent.com` |
| `hub_token` | Respuesta del paso 2 (campo `token`) | `eyJhbGciOiJIUzI1NiIs...` (muy largo) |
| `server_id` | Paso 1 (UUID del servidor) o respuesta del paso 2 | `329d337f-bb4f-4f33-974a-47b916cc832f` |
| `host` | Tu configuración SQL local | `localhost` o `192.168.1.100` |
| `port` | Tu configuración SQL local | `1433` |
| `database` | Nombre de la BD en tu SQL Server | `CIENFUEGOS` |
| `username` | Usuario SQL | `sa` |
| `password` | Contraseña SQL | `MiPassword123` |

## 4.5 Errores comunes al llenar config.yaml

| Error | Causa | Solución |
|-------|-------|----------|
| Espacios extra en el token | Copiaste mal | Asegúrate de copiar TODO el token sin espacios |
| Comillas mal cerradas | Error de sintaxis YAML | Usa comillas dobles `"valor"` |
| Indentación incorrecta | YAML requiere espacios específicos | Usa 2 espacios para indentar bajo `sql_local:` |

## 4.6 Validar antes de continuar

✅ El archivo `config.yaml` existe  
✅ Todos los campos tienen valores reales (no placeholders)  
✅ El token está completo (es muy largo)  
✅ Las credenciales SQL son las correctas  

---

# PASO 5: PROBAR AUTENTICACIÓN

## 5.1 Ejecutar el test de autenticación

```bash
python sync_agent_piloto.py --config config.yaml --test-only
```

## 5.2 Salida esperada si TODO ESTÁ BIEN

```
======================================================================
  EDARSA SYNC AGENT - PILOTO SOFTRESTAURANT
  Versión 1.0
======================================================================
  Log: sync_agent_piloto_20260423_120000.log
======================================================================

2026-04-23 12:00:00 INFO [SYNC_AGENT_PILOTO] [1/6] Cargando configuración de config.yaml
2026-04-23 12:00:00 INFO [SYNC_AGENT_PILOTO]   Agent ID: agent-sr-piloto-001
2026-04-23 12:00:00 INFO [SYNC_AGENT_PILOTO]   Server ID: 329d337f-bb4f-4f33-974a-47b916cc832f
2026-04-23 12:00:00 INFO [SYNC_AGENT_PILOTO]   HUB URL: https://stock-tracker-990.preview.emergentagent.com

2026-04-23 12:00:00 INFO [SYNC_AGENT_PILOTO] [2/6] Verificando autenticación con HUB
2026-04-23 12:00:01 INFO [SYNC_AGENT_PILOTO] ✅ Autenticación OK: agent_id=agent-sr-piloto-001, server_id=329d337f-bb4f-4f33-974a-47b916cc832f

2026-04-23 12:00:01 INFO [SYNC_AGENT_PILOTO] ✅ Modo test-only: Solo se verificó autenticación
```

**La clave es ver**: `✅ Autenticación OK`

## 5.3 Errores posibles y soluciones

### Error 401: Token inválido o expirado

```
2026-04-23 12:00:01 ERROR [SYNC_AGENT_PILOTO] ❌ Token inválido o expirado
```

**Causa**: El token que pegaste está mal o expiró.  
**Solución**: Volver al paso 2 y generar un nuevo token.

### Error 403: Token no es de tipo sync_agent

```
2026-04-23 12:00:01 ERROR [SYNC_AGENT_PILOTO] ❌ Token no es de tipo sync_agent
```

**Causa**: Pegaste el token de usuario en lugar del token de agente.  
**Solución**: El token correcto viene del endpoint `/api/admin/agents/generate-token`, no del login.

### Error: Timeout conectando a HUB

```
2026-04-23 12:00:10 ERROR [SYNC_AGENT_PILOTO] ❌ Timeout conectando a HUB
```

**Causa**: No hay conexión a internet o HUB está caído.  
**Solución**: 
1. Verificar conexión a internet
2. Probar abrir `https://stock-tracker-990.preview.emergentagent.com` en navegador
3. Si HUB está caído, esperar

### Error: No se puede conectar a HUB

```
2026-04-23 12:00:01 ERROR [SYNC_AGENT_PILOTO] ❌ No se puede conectar a HUB: ConnectionError
```

**Causa**: URL mal escrita o problema de red.  
**Solución**: Verificar que `hub_url` en config.yaml está bien escrito (sin espacios, sin / al final).

## 5.4 Validar antes de continuar

✅ El comando ejecutó sin errores  
✅ Viste el mensaje `✅ Autenticación OK`  
✅ Se creó un archivo de log `sync_agent_piloto_*.log`  

---

# PASO 6: EJECUTAR LA PRIMERA CORRIDA REAL

## 6.1 Ejecutar sincronización completa

```bash
python sync_agent_piloto.py --config config.yaml
```

**NOTA**: Esto sincronizará los datos del DÍA ACTUAL.

## 6.2 Salida esperada paso a paso

```
======================================================================
  EDARSA SYNC AGENT - PILOTO SOFTRESTAURANT
  Versión 1.0
======================================================================
  Log: sync_agent_piloto_20260423_143000.log
======================================================================

[1/6] Cargando configuración de config.yaml          <-- Carga config
  Agent ID: agent-sr-piloto-001
  Server ID: 329d337f-bb4f-4f33-974a-47b916cc832f
  HUB URL: https://stock-tracker-990.preview.emergentagent.com

[2/6] Verificando autenticación con HUB              <-- Verifica token
✅ Autenticación OK: agent_id=agent-sr-piloto-001

[3/6] Conectando a SQL Server local                  <-- Conecta a SQL
✅ Conectado a SQL Server: localhost:1433/CIENFUEGOS

[4/6] Extrayendo KPIs para fecha 2026-04-23          <-- Extrae datos
✅ Datos extraídos: Ventas=$125,000.00, PAX=450, Cheques=120

[5/6] Enviando KPIs a HUB                            <-- Envía a HUB
✅ Respuesta HUB: status=OK, actions={'INSERT': 1, 'UPDATE': 0, 'SKIP': 0, 'REJECTED': 0}

[6/6] Enviando heartbeat                             <-- Registra heartbeat
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
    INSERT: 1        <-- IMPORTANTE: Debe ser 1 en la primera ejecución
    UPDATE: 0
    SKIP: 0
    REJECTED: 0
======================================================================
📄 Reporte guardado en: reporte_piloto_20260423_143000.json

✅ EJECUCIÓN COMPLETADA EXITOSAMENTE
```

## 6.3 Cómo saber si cada paso funcionó

| Paso | Qué buscar | Significa |
|------|------------|-----------|
| Extracción SQL | `✅ Conectado a SQL Server` | La conexión SQL funcionó |
| Extracción SQL | `✅ Datos extraídos: Ventas=$X` | Encontró datos para la fecha |
| POST al HUB | `✅ Respuesta HUB: status=OK` | El envío fue exitoso |
| POST al HUB | `INSERT: 1` | El registro se creó correctamente |
| Heartbeat | `✅ Heartbeat registrado` | El estado del agente quedó registrado |

## 6.4 Errores posibles en esta etapa

### Error: No se pudo conectar a SQL Server

```
[3/6] Conectando a SQL Server local
❌ Error conectando a SQL Server: Login failed for user 'sa'
```

**Causa**: Usuario o contraseña SQL incorrectos.  
**Solución**: Verificar credenciales en `config.yaml`. Probar conectar con SSMS primero.

### Error: No se encontraron datos para la fecha

```
[4/6] Extrayendo KPIs para fecha 2026-04-23
⚠️ No se encontraron datos para fecha 2026-04-23
```

**Causa**: No hay cheques en SoftRestaurant para esa fecha.  
**Solución**: Usar otra fecha con `--fecha YYYY-MM-DD`.

### Error: Timeout al SQL Server

```
❌ Error conectando a SQL Server: Connection timed out
```

**Causa**: El SQL Server no es alcanzable desde tu máquina.  
**Solución**: 
1. Verificar que el SQL Server está corriendo
2. Verificar firewall (puerto 1433 debe estar abierto)
3. Verificar que la IP/hostname es correcto

## 6.5 Archivos generados

Después de ejecutar, tendrás:

1. **Log**: `sync_agent_piloto_20260423_143000.log`
2. **Reporte JSON**: `reporte_piloto_20260423_143000.json`

**GUARDA AMBOS ARCHIVOS**. Los necesitarás para el reporte final.

## 6.6 Validar antes de continuar

✅ Viste `✅ EJECUCIÓN COMPLETADA EXITOSAMENTE`  
✅ La acción fue `INSERT: 1`  
✅ Se generaron los archivos de log y reporte  

---

# PASO 7: VALIDAR NO DUPLICIDAD (Segunda Corrida)

## 7.1 Ejecutar inmediatamente otra vez

```bash
python sync_agent_piloto.py --config config.yaml
```

**IMPORTANTE**: Ejecuta EXACTAMENTE el mismo comando. No cambies la fecha.

## 7.2 Lo que DEBE pasar

En la sección de "Acciones UPSERT" debes ver:

```
  Acciones UPSERT:
    INSERT: 0        <-- Debe ser 0 (no insertó nuevo)
    UPDATE: 0        <-- Puede ser 0
    SKIP: 1          <-- DEBE SER 1 (detectó que ya existía)
    REJECTED: 0
```

## 7.3 Interpretación

| Resultado | Significado | ¿Está bien? |
|-----------|-------------|-------------|
| `SKIP: 1` | El sistema detectó que los datos ya existen y NO los duplicó | ✅ CORRECTO |
| `INSERT: 1` otra vez | Se creó un duplicado | ❌ ERROR - reportar |
| `UPDATE: 1` | Los datos cambiaron y se actualizaron | ✅ OK (si los datos realmente cambiaron) |

## 7.4 Validar antes de continuar

✅ La segunda ejecución mostró `SKIP: 1`  
✅ NO mostró `INSERT: 1` (eso sería un duplicado)  
✅ Guardaste el log y reporte de esta ejecución  

---

# PASO 8: COMPLETAR LAS 5 EJECUCIONES

## 8.1 Plan de 5 ejecuciones

| # | Qué hacer | Comando | Resultado esperado |
|---|-----------|---------|-------------------|
| 1 | Fecha actual, primera vez | `python sync_agent_piloto.py --config config.yaml` | `INSERT: 1` |
| 2 | Fecha actual, repetir | `python sync_agent_piloto.py --config config.yaml` | `SKIP: 1` |
| 3 | Fecha ayer, primera vez | `python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22` | `INSERT: 1` |
| 4 | Fecha ayer, repetir | `python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22` | `SKIP: 1` |
| 5 | Validación final | `python sync_agent_piloto.py --config config.yaml` | `SKIP: 1` o `UPDATE: 1` |

**NOTA**: Cambia la fecha del paso 3 y 4 por una fecha que tenga datos en tu SoftRestaurant.

## 8.2 Comandos para cada ejecución

### Ejecución 1 (ya la hiciste en el paso 6):
```bash
python sync_agent_piloto.py --config config.yaml
```

### Ejecución 2 (ya la hiciste en el paso 7):
```bash
python sync_agent_piloto.py --config config.yaml
```

### Ejecución 3 (fecha diferente):
```bash
# Cambiar la fecha por una que tenga datos (ej: ayer)
python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22
```

### Ejecución 4 (repetir fecha diferente):
```bash
# Misma fecha que ejecución 3
python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22
```

### Ejecución 5 (validación final):
```bash
python sync_agent_piloto.py --config config.yaml
```

## 8.3 Registro de cada ejecución

Llena esta tabla mientras ejecutas:

| # | Fecha/Hora | Fecha Datos | INSERT | UPDATE | SKIP | Status |
|---|------------|-------------|--------|--------|------|--------|
| 1 | __________ | __________ | ___ | ___ | ___ | OK/ERROR |
| 2 | __________ | __________ | ___ | ___ | ___ | OK/ERROR |
| 3 | __________ | __________ | ___ | ___ | ___ | OK/ERROR |
| 4 | __________ | __________ | ___ | ___ | ___ | OK/ERROR |
| 5 | __________ | __________ | ___ | ___ | ___ | OK/ERROR |

## 8.4 Validar antes de continuar

✅ Ejecutaste las 5 corridas  
✅ Ejecuciones 2 y 4 mostraron `SKIP: 1` (no duplicaron)  
✅ Guardaste todos los logs y reportes (10 archivos en total)  

---

# PASO 9: PREPARAR LA EVIDENCIA

## 9.1 Archivos que debes tener

Después de las 5 ejecuciones, deberías tener estos archivos:

```
piloto_sync_agent/
├── config.yaml                           <-- Tu configuración (NO COMPARTIR contraseñas)
├── sync_agent_piloto_20260423_143000.log <-- Log ejecución 1
├── sync_agent_piloto_20260423_143500.log <-- Log ejecución 2
├── sync_agent_piloto_20260423_144000.log <-- Log ejecución 3
├── sync_agent_piloto_20260423_144500.log <-- Log ejecución 4
├── sync_agent_piloto_20260423_145000.log <-- Log ejecución 5
├── reporte_piloto_20260423_143000.json   <-- Reporte ejecución 1
├── reporte_piloto_20260423_143500.json   <-- Reporte ejecución 2
├── reporte_piloto_20260423_144000.json   <-- Reporte ejecución 3
├── reporte_piloto_20260423_144500.json   <-- Reporte ejecución 4
└── reporte_piloto_20260423_145000.json   <-- Reporte ejecución 5
```

## 9.2 Crear carpeta de evidencia

```bash
mkdir evidencia_piloto
cp *.log evidencia_piloto/
cp *.json evidencia_piloto/
```

## 9.3 Llenar el reporte final

Copia y completa este reporte:

```
=========================================================
REPORTE PILOTO SYNC AGENT - SOFTRESTAURANT
=========================================================

FECHA DE EJECUCIÓN: ____________________

SERVIDOR PILOTO:
- Nombre: ____________________
- Server ID: ____________________
- Host: ____________________
- Base de datos: ____________________

AGENTE:
- Agent ID: ____________________

RESUMEN DE EJECUCIONES:

| # | Fecha/Hora | Fecha Datos | INSERT | SKIP | Status |
|---|------------|-------------|--------|------|--------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

VALIDACIÓN DE IDEMPOTENCIA:
- Ejecución 2 después de 1: [ ] SKIP confirmado (sin duplicados)
- Ejecución 4 después de 3: [ ] SKIP confirmado (sin duplicados)

CHECKLIST FINAL:
[ ] Config cargada correctamente en todas las ejecuciones
[ ] Auth HUB OK en todas las ejecuciones
[ ] SQL conectado en todas las ejecuciones
[ ] Extracción OK en todas las ejecuciones
[ ] KPIs enviados en todas las ejecuciones
[ ] Heartbeat OK en todas las ejecuciones
[ ] Sin duplicados confirmado

ARCHIVOS ADJUNTOS:
[ ] 5 archivos de log (.log)
[ ] 5 archivos de reporte (.json)

OBSERVACIONES:
_________________________________________________________________
_________________________________________________________________

DICTAMEN:
[ ] PILOTO EXITOSO - Listo para Fase 2
[ ] PILOTO CON OBSERVACIONES - Detalle: _________________________
[ ] PILOTO FALLIDO - Motivo: ___________________________________

Ejecutado por: _________________________
Fecha: ________________________________
=========================================================
```

## 9.4 Cómo nombrar los archivos

Para no perder orden, renombra los archivos así:

```
evidencia_piloto/
├── 01_log_ejecucion_1_INSERT.log
├── 01_reporte_ejecucion_1_INSERT.json
├── 02_log_ejecucion_2_SKIP.log
├── 02_reporte_ejecucion_2_SKIP.json
├── 03_log_ejecucion_3_INSERT.log
├── 03_reporte_ejecucion_3_INSERT.json
├── 04_log_ejecucion_4_SKIP.log
├── 04_reporte_ejecucion_4_SKIP.json
├── 05_log_ejecucion_5_SKIP.log
├── 05_reporte_ejecucion_5_SKIP.json
└── REPORTE_FINAL_PILOTO.txt
```

---

# PASO 10: CRITERIO DE ÉXITO O FALLA

## 10.1 El piloto es EXITOSO si:

✅ Las 5 ejecuciones completaron sin errores  
✅ Ejecuciones 1 y 3 mostraron `INSERT: 1` (datos nuevos)  
✅ Ejecuciones 2, 4 y 5 mostraron `SKIP: 1` (sin duplicados)  
✅ Todos los heartbeats se registraron  
✅ No hubo errores de autenticación  
✅ No hubo errores de conexión SQL persistentes  

## 10.2 El piloto tiene OBSERVACIONES si:

⚠️ Algunas ejecuciones tuvieron errores temporales pero se recuperaron  
⚠️ Los datos extraídos fueron 0 para alguna fecha (pero el proceso funcionó)  
⚠️ Hubo `UPDATE: 1` en lugar de `SKIP: 1` (significa que los datos cambiaron)  

## 10.3 El piloto FALLA si:

❌ Nunca se pudo autenticar (errores 401/403 persistentes)  
❌ Nunca se pudo conectar al SQL Server  
❌ Se detectaron duplicados (`INSERT: 1` en ejecución 2 o 4)  
❌ Errores sistemáticos en el envío a HUB  

## 10.4 Qué hacer si algo falla a mitad del proceso

| Problema | Acción |
|----------|--------|
| Error de autenticación | Volver al paso 2 y regenerar token |
| Error de SQL | Verificar credenciales, probar con SSMS |
| Error de red/timeout | Esperar y reintentar |
| Duplicados detectados | DETENER y reportar inmediatamente |
| Error desconocido | Guardar el log completo y reportar |

## 10.5 Cómo reportar el resultado

Una vez completado el piloto, reporta:

1. El **REPORTE_FINAL_PILOTO.txt** completado
2. La carpeta **evidencia_piloto/** con todos los logs y reportes
3. Tu **dictamen**: EXITOSO / CON OBSERVACIONES / FALLIDO
4. Cualquier **observación** relevante

---

# RESUMEN DE COMANDOS

```bash
# Instalar dependencias
pip install pymssql requests pyyaml

# Probar solo autenticación
python sync_agent_piloto.py --config config.yaml --test-only

# Ejecutar sincronización (fecha actual)
python sync_agent_piloto.py --config config.yaml

# Ejecutar sincronización (fecha específica)
python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22
```

---

**FIN DE LA GUÍA OPERATIVA**
