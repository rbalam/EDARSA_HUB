# Script 3 - Migración PropinasTPV a Corporate Filters

Fecha: Thu Jun  4 16:25:48 UTC 2026

Backup creado: /app/frontend/src/components/PropinasTPV.jsx.backup_script_3_20260604_162548
## Fetch directos prohibidos
```text
107:      const res = await fetch(`${API_URL}/api/servers`, {
130:      const resSuc = await fetch(`${API_URL}/api/sucursales`, {
138:      const resServers = await fetch(`${API_URL}/api/servers`, {
```
