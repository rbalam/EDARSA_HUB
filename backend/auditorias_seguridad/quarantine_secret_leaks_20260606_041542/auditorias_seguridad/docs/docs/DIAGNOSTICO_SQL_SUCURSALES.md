# DIAGNÓSTICO: SQL Server Local para APIs de Ventas del Día
## ORIGEN y 130° QUERÉTARO

**Fecha:** Diciembre 2025  
**Estado:** REQUIERE INTERVENCIÓN EN SITIO

---

## ESTADO ACTUAL VERIFICADO

| Componente | Estado | Evidencia |
|------------|--------|-----------|
| API ORIGEN (puerto 8000) | ✅ Activa | `{"status":"API EDARSA funcionando"}` |
| API 130QRO (puerto 8001) | ✅ Activa | `{"status":"API EDARSA funcionando"}` |
| Query SQL ORIGEN | ❌ Timeout | Query tarda >10s y no responde |
| Query SQL 130QRO | ❌ Timeout | Query tarda >10s y no responde |

**Conclusión:** Las APIs intermedias funcionan, pero NO pueden conectarse a los SQL Server de las sucursales.

---

## ARQUITECTURA ACTUAL

```
┌─────────────────┐     HTTP      ┌─────────────────────────┐     SQL      ┌──────────────────┐
│  EDARSA HUB     │────────────── │  API Intermedia (Nube)  │──────────────│  SQL Server      │
│  (Este servidor)│               │  54.39.104.176          │              │  (Sucursal local)│
└─────────────────┘               └─────────────────────────┘              └──────────────────┘
      │                                    │                                       │
      │ Consulta ventas del día           │ ✅ API responde                       │ ❌ SQL NO conecta
      │                                    │                                       │
```

### APIs Intermedias Configuradas:

| Sucursal | URL API | Puerto | Estado HTTP | Estado SQL |
|----------|---------|--------|-------------|------------|
| ORIGEN | http://54.39.104.176:8000/query | 8000 | ✅ Responde | ❌ SQL timeout |
| 130QRO | http://54.39.104.176:8001/query | 8001 | ✅ Responde | ❌ SQL timeout |

---

## CAUSA RAÍZ PROBABLE

El problema NO está en EDARSA HUB ni en las APIs intermedias (ambas funcionan).  
El problema está en **la conectividad entre las APIs intermedias y el SQL Server en cada sucursal**.

### Posibles causas:

1. **SQL Server detenido** en la sucursal
2. **Firewall** bloqueando puerto SQL (1433 o el configurado)
3. **Red/VPN** entre servidor en nube y sucursales no disponible
4. **Credenciales** de SQL incorrectas en la configuración de las APIs
5. **TCP/IP deshabilitado** en SQL Server Configuration Manager
6. **Puertos dinámicos** en lugar de puerto fijo

---

## DIAGNÓSTICO A EJECUTAR EN CADA SUCURSAL

### 1. VERIFICAR SERVICIO SQL SERVER

```powershell
# En la máquina de la sucursal (Windows)
Get-Service -Name "MSSQL*" | Format-Table Name, Status, StartType

# Si está detenido:
Start-Service -Name "MSSQLSERVER"  # O el nombre de la instancia
```

### 2. VERIFICAR BASE DE DATOS

```sql
-- Conectarse localmente con SSMS y ejecutar:
SELECT name, state_desc FROM sys.databases WHERE name = 'ManagementPro'
-- Debe mostrar: ONLINE
```

### 3. VERIFICAR CONFIGURACIÓN DE RED SQL

```
1. Abrir "SQL Server Configuration Manager"
2. Ir a "SQL Server Network Configuration" > "Protocols for [INSTANCIA]"
3. Verificar que TCP/IP esté "Enabled"
4. Doble clic en TCP/IP > pestaña "IP Addresses"
5. En "IPAll":
   - TCP Dynamic Ports: VACÍO (sin valor)
   - TCP Port: 1433 (o el puerto fijo documentado)
6. Reiniciar servicio SQL Server
```

### 4. VERIFICAR FIREWALL (Windows)

```powershell
# Verificar regla existente
Get-NetFirewallRule -DisplayName "*SQL*" | Format-Table Name, Enabled, Direction

# Crear regla si no existe
New-NetFirewallRule -DisplayName "SQL Server" -Direction Inbound -Protocol TCP -LocalPort 1433 -Action Allow
```

### 5. PRUEBA DE CONECTIVIDAD DESDE SERVIDOR API

Desde el servidor donde corren las APIs (54.39.104.176):

```bash
# Para ORIGEN
Test-NetConnection -ComputerName [IP_SUCURSAL_ORIGEN] -Port 1433

# Para 130QRO
Test-NetConnection -ComputerName [IP_SUCURSAL_QRO] -Port 1433

# Debe devolver: TcpTestSucceeded = True
```

### 6. VERIFICAR CREDENCIALES SQL

```sql
-- En SQL Server de la sucursal:
-- Verificar que el usuario usado por la API existe y tiene permisos

SELECT name, is_disabled FROM sys.sql_logins WHERE name = 'usuario_api'
-- is_disabled debe ser 0

-- Verificar modo de autenticación (debe ser "Mixed")
EXEC xp_loginconfig 'login mode'
-- Debe mostrar: Mixed
```

### 7. VERIFICAR SQL SERVER BROWSER (si es instancia nombrada)

```powershell
# Si la instancia SQL tiene nombre (ej: SQLEXPRESS, MPRO)
Get-Service -Name "SQLBrowser" | Format-Table Name, Status

# Si está detenido:
Start-Service -Name "SQLBrowser"
Set-Service -Name "SQLBrowser" -StartupType Automatic
```

---

## CONNECTION STRING CORRECTO

Las APIs intermedias deben usar un connection string en este formato:

```
# Para instancia predeterminada:
Server=IP_SUCURSAL,1433;Database=ManagementPro;User Id=usuario;Password=***;

# Para instancia nombrada CON puerto fijo:
Server=IP_SUCURSAL,PUERTO;Database=ManagementPro;User Id=usuario;Password=***;

# EVITAR este formato (problemas con algunos drivers):
Server=IP_SUCURSAL\INSTANCIA,PUERTO;Database=...
```

---

## ENTREGABLES REQUERIDOS POR SUCURSAL

Para cerrar este ticket, entregar para **ORIGEN** y **130QRO**:

| # | Entregable | Valor |
|---|-----------|-------|
| 1 | IP del SQL Server | ej: 192.168.1.100 |
| 2 | Puerto configurado | ej: 1433 |
| 3 | Nombre de instancia | ej: DEFAULT o SQLEXPRESS |
| 4 | Resultado Test-NetConnection | TcpTestSucceeded = True/False |
| 5 | Estado servicio SQL Server | Running/Stopped |
| 6 | Estado SQL Server Browser | Running/Stopped/N/A |
| 7 | Causa raíz identificada | ej: "Firewall bloqueaba puerto" |
| 8 | Cambios realizados | ej: "Habilitado TCP/IP, puerto fijo 1433" |
| 9 | Evidencia de conexión OK | Screenshot o resultado de query |

---

## PRUEBA FINAL DESDE EDARSA HUB

Una vez corregido en las sucursales, ejecutar:

```bash
# Desde este servidor, probar las APIs
curl -X GET "http://54.39.104.176:8000/query?sql=SELECT%201%20as%20test" \
  -H "x-api-key: EDARSA_2026_SECURE_KEY"

curl -X GET "http://54.39.104.176:8001/query?sql=SELECT%201%20as%20test" \
  -H "x-api-key: EDARSA_2026_SECURE_KEY"
```

Respuesta esperada:
```json
{"total_registros": 1, "data": [{"test": 1}]}
```

---

## NOTA IMPORTANTE

**Este problema NO se puede resolver desde EDARSA HUB.**

Se requiere:
1. Acceso físico o remoto a las máquinas de las sucursales
2. Permisos de administrador en Windows
3. Acceso a SQL Server Management Studio
4. Posiblemente acceso al router/firewall de la sucursal

El código de EDARSA HUB está correcto y listo. Solo falta restablecer la conectividad SQL en las sucursales.
