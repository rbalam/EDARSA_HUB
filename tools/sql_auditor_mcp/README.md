# EDARSA SQL Auditor

Agente MCP independiente del Worker de EDARSAHUB. Su objetivo es permitir a ChatGPT inspeccionar esquemas, ejecutar consultas SQL de solo lectura y conciliar resultados entre bases origen y EDARSAHUB.

## Principios

- No modifica el Worker existente.
- No escribe en `Edarsahub_Desarrollo` mientras se valida el prototipo.
- Autoriza al requester contra RBAC SQL canonico (`Usuario_Catalogo`).
- Solo acepta una sentencia `SELECT` o `WITH`.
- Bloquea `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `EXEC`, `GRANT`, `REVOKE`, `DENY`, `BACKUP`, `RESTORE`, `DBCC`, `OPENROWSET`, `OPENDATASOURCE`, `SELECT ... INTO`, multiples sentencias y comentarios SQL.
- Toda conexion hace `rollback()` al finalizar.
- Las credenciales del catalogo nunca se devuelven como respuesta MCP.
- La barrera definitiva debe ser SQL Server: usar cuentas con `SELECT` y `VIEW DEFINITION`, sin permisos de escritura.

## Herramientas MCP

- `who_am_i`: valida identidad y rol contra EDARSAHUB SQL.
- `list_sql_servers`: lista servidores visibles sin secretos.
- `list_tables`: lista tablas y vistas.
- `describe_table`: describe columnas y tipos.
- `search_columns`: localiza columnas por nombre.
- `run_select`: ejecuta un `SELECT/WITH` de una sola sentencia.
- `compare_readonly_queries`: ejecuta dos consultas y compara filas, columnas, hashes y, opcionalmente, llaves de conciliacion.

## Instalacion local

Desde la raiz del repositorio:

```powershell
cd tools\sql_auditor_mcp
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

El agente reutiliza el backend de EDARSAHUB para resolver:

- RBAC SQL canonico.
- Catalogo `Servidores_Conexiones`.
- Descifrado de credenciales.
- Fabrica de conexiones SQL externas.

Por lo tanto, el entorno donde se ejecute debe tener disponible la configuracion canonica de EDARSAHUB y `SERVER_SECRET_KEY` cuando aplique.

## Identidad

Configurar la identidad que ChatGPT usara para este agente:

```powershell
$env:EDARSA_SQL_AUDITOR_REQUESTER_EMAIL="carlosruz@edarsa.com.mx"
```

El correo no se considera autorizado por estar en esta variable. En cada herramienta se consulta `Usuario_Catalogo` y se valida que el usuario este activo y tenga rol SUPERADMIN/SuperAdministrador.

## Ejecutar pruebas de politica

```powershell
cd tools\sql_auditor_mcp
pytest -q test_readonly_policy.py
```

## Canario local

Iniciar por stdio:

```powershell
$env:EDARSA_SQL_AUDITOR_TRANSPORT="stdio"
python server.py
```

Las primeras llamadas recomendadas son:

1. `who_am_i`
2. `list_sql_servers`
3. `list_tables` sobre un servidor de lectura
4. `run_select(server, "SELECT 1 AS conexion_ok")`

No ejecutar una consulta de negocio hasta que los cuatro pasos anteriores funcionen.

## Publicacion para ChatGPT

Para conectarlo como app MCP de ChatGPT, ejecutar el servidor con transporte `streamable-http` detras de HTTPS o de un tunel seguro compatible con el entorno de ChatGPT:

```powershell
$env:EDARSA_SQL_AUDITOR_TRANSPORT="streamable-http"
python server.py
```

No exponer SQL Server/1433 directamente a Internet. Solo el endpoint MCP debe ser accesible para ChatGPT; las conexiones SQL permanecen desde el host interno del agente hacia los servidores registrados.

## Ejemplo de uso final

Solicitud natural:

> Dame las ventas del 25 de agosto de 2026 de Origen, Queretaro, Cienfuegos y La Estelar. Comparalas contra EDARSAHUB y marca las sucursales con diferencias.

Flujo esperado:

1. Validar requester.
2. Localizar cada servidor origen y EDARSAHUB.
3. Inspeccionar tablas/columnas si la consulta no esta conocida.
4. Ejecutar `SELECT` de ventas por sucursal.
5. Ejecutar `SELECT` equivalente en EDARSAHUB.
6. Conciliar con `compare_readonly_queries`, idealmente usando folio/ticket como llave.
7. Reportar total origen, total HUB, diferencia y folios faltantes/diferentes.

## Restriccion operacional obligatoria

Aunque el agente tenga un validador de SQL, las cuentas de conexion de los servidores deben ser de solo lectura. El control de aplicacion no sustituye los permisos de SQL Server.
