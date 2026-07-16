# EDARSAHUB Dependency Knowledge

- Branch: `Edarsahub_Desarrollo`
- HEAD: `5c8e9c4a2f0b284ea0892c943a93fe90c48fa88d`
- Fingerprint: `acda5b42d5debb39eb621c8d0091d6944086fb2a3d84bf026b740145a041096b`
- Python: `3.11.15 (main, Jul 14 2026, 02:16:14) [GCC 12.2.0]`
- Python executable: `/usr/local/bin/python`

## Alcance corregido

- Se excluyeron de los datasets activos los virtualenvs, `site-packages`, `.vendor`, `node_modules`, caches, respaldos y auditorías históricas.
- Se conservaron los inventarios explícitos de virtualenvs y paquetes vendorizados.
- Filas de imports excluidas: 92,607
- Imports no resueltos excluidos: 21,457
- Imports activos restantes: 6,142
- Imports activos no resueltos: 552
- Manifiestos activos restantes: 5

## Conteos

- Distribuciones Python instaladas: 37
- Dependencias Python declaradas: 157
- Dependencias backend ausentes: 143
- Diferencias de versión exacta: 4
- Imports Python no resueltos: 552
- Aplicaciones Node: 1
- Dependencias Node declaradas: 69
- Dependencias Node ausentes: 0
- Distribuciones vendorizadas aisladas: 16
- Virtualenvs detectados: 2

## Módulos críticos

- `apscheduler`: importable=`False`, versions=`[]`
- `cryptography`: importable=`False`, versions=`[]`
- `dotenv`: importable=`False`, versions=`[]`
- `fastapi`: importable=`False`, versions=`[]`
- `jwt`: importable=`False`, versions=`[]`
- `openpyxl`: importable=`False`, versions=`[]`
- `pandas`: importable=`False`, versions=`[]`
- `pydantic`: importable=`False`, versions=`[]`
- `pymssql`: importable=`False`, versions=`[]`
- `pyodbc`: importable=`False`, versions=`[]`
- `pytest`: importable=`False`, versions=`[]`
- `requests`: importable=`False`, versions=`[]`
- `sqlalchemy`: importable=`False`, versions=`[]`
- `uvicorn`: importable=`False`, versions=`[]`
- `yaml`: importable=`False`, versions=`[]`

## Bloqueadores

- `BACKEND_DECLARED_DEPENDENCIES_MISSING`: 143

## Advertencias

- `PYTHON_VERSION_DIFFERENCES`: 4
- `UNRESOLVED_PYTHON_IMPORTS`: 552

## Reglas de uso

- Esta instantánea solo es válida para el HEAD y fingerprint indicados.
- Un paquete declarado no debe considerarse instalado si no aparece en `installed_distributions`.
- Los paquetes dentro de `.vendor` están aislados del runtime principal.
- Regenerar la auditoría cuando cambie el commit, contenedor, toolchain o manifiestos.

## Seguridad

- Paquetes instalados por la auditoría: `0`
- Secretos leídos: `0`
- Conexiones SQL: `0`
- Escrituras SQL: `0`
