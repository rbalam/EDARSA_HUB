# EDARSA HUB - Módulo Consultas SQL (SQL-First)

## FASE 3: Repository SQL-First para Consultas

### Descripción

Este módulo implementa la capa de acceso a datos para el catálogo de consultas SQL
almacenado en las tablas `ConsultasSQL_*` de EDARSAHUB.

### Propósito

- Leer consultas desde EDARSAHUB SQL (no desde código hardcodeado o MongoDB)
- Validar seguridad de consultas SQL antes de devolverlas para ejecución
- Preparar contexto de ejecución para endpoints futuros
- Mantener el sistema legacy funcionando sin cambios

### Tablas SQL Origen

| Tabla | Descripción |
|-------|-------------|
| `ConsultasSQL_Catalogo` | Catálogo principal de consultas |
| `ConsultasSQL_Parametros` | Parámetros por consulta |
| `ConsultasSQL_Versiones` | Historial de versiones |
| `ConsultasSQL_Servidores` | Asociaciones consulta-servidor |
| `ConsultasSQL_EjecucionesLog` | Log de ejecuciones (futuro) |
| `ConsultasSQL_Permisos` | Permisos RBAC (futuro) |

### Estructura del Módulo

```
modules/consultas_sql/
├── __init__.py          # Exports públicos
├── models.py            # Modelos Pydantic/dataclass
├── validator.py         # Validador SQL estricto
├── repository.py        # Acceso a datos SQL
├── service.py           # Lógica de negocio
└── README.md            # Esta documentación
```

### Componentes

#### models.py

Modelos de datos:

- `ConsultaSQLCatalogo`: Modelo principal de consulta
- `ConsultaSQLParametro`: Parámetro de consulta
- `ConsultaSQLVersion`: Versión histórica
- `ConsultaSQLServidor`: Asociación con servidor
- `ConsultaSQLFilter`: Filtros de búsqueda
- `ConsultaSQLValidationResult`: Resultado de validación

#### validator.py

Validador estricto SQL:

**Reglas implementadas:**
1. Solo SELECT o WITH (CTEs) permitidos
2. Bloqueo de palabras peligrosas:
   - DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE
   - EXEC, EXECUTE, CREATE, MERGE
   - GRANT, REVOKE, DENY, BACKUP, RESTORE, DBCC
3. Bloqueo de prefijos peligrosos: `xp_`, `sp_`
4. Bloqueo de múltiples statements (`;`)
5. Detección de comentarios sospechosos (`--`, `/*`, `*/`)
6. Validación de placeholders `{param}` vs parámetros registrados

#### repository.py

Métodos disponibles:

```python
# Listados
list_consultas(filters: ConsultaSQLFilter) -> List[ConsultaSQLCatalogo]
get_by_id(consulta_id: int) -> Optional[ConsultaSQLCatalogo]
get_by_uuid(public_uuid: str) -> Optional[ConsultaSQLCatalogo]
get_by_codigo(codigo_consulta: str) -> Optional[ConsultaSQLCatalogo]

# Relaciones
get_parametros(consulta_id: int) -> List[ConsultaSQLParametro]
get_versiones(consulta_id: int) -> List[ConsultaSQLVersion]
get_servidores_asociados(consulta_id: int) -> List[ConsultaSQLServidor]

# Validación
validate_catalog_query(consulta_id: int) -> ConsultaSQLValidationResult
validate_sql_text(sql_text: str, parametros=None) -> ConsultaSQLValidationResult

# Contexto
build_execution_context(consulta_id, parametros, usuario_contexto) -> dict
register_execution_log_prepare(...) -> dict  # Solo preparación

# Estadísticas
get_counts() -> Dict[str, int]
get_modulos() -> List[str]
```

#### service.py

Métodos de negocio:

```python
# Listados con lógica
listar_consultas(sistema, modulo, solo_activas, solo_manuales, buscar, limit)
listar_consultas_por_modulo() -> Dict[str, List[Dict]]

# Obtener con validaciones
obtener_consulta(consulta_id, codigo, uuid, include_sql)
obtener_consulta_con_parametros(consulta_id, codigo)

# Validación
validar_consulta(consulta_id, codigo, sql_text)
validar_todas_las_consultas() -> Dict

# Contexto
preparar_contexto_ejecucion(consulta_id, codigo, parametros, usuario_contexto)

# Información
obtener_estadisticas() -> Dict
verificar_integridad() -> Dict
```

### Uso

```python
from modules.consultas_sql import (
    ConsultasSQLRepository,
    ConsultasSQLService,
    SQLValidator,
)

# Opción 1: Usar repository directamente
repo = ConsultasSQLRepository()
consultas = repo.list_consultas()

# Opción 2: Usar service (recomendado)
service = ConsultasSQLService()
resultado = service.validar_todas_las_consultas()

# Opción 3: Usar singletons
from modules.consultas_sql.repository import get_repository
from modules.consultas_sql.service import get_service

repo = get_repository()
service = get_service()
```

### Seguridad

**NO expone:**
- Connection strings
- Passwords
- API keys
- Datos sensibles en serialización

**Validaciones:**
- Solo SELECT/WITH permitidos
- Palabras peligrosas bloqueadas
- Múltiples statements bloqueados
- Comentarios detectados como sospechosos

### Restricciones FASE 3

1. **NO ejecuta consultas contra servidores LIVE**
2. **NO modifica datos del catálogo**
3. **NO crea endpoints públicos nuevos**
4. **NO modifica frontend**
5. **NO modifica endpoints legacy**

### Próximas Fases

- **FASE 4**: Crear endpoints `/api/consultas-sql/*`
- **FASE 5**: Integrar con ejecución real contra servidores
- **FASE 6**: RBAC y permisos
- **FASE 7**: Deprecar legacy

### Conexión SQL

Usa el patrón existente del proyecto:

```python
from core.server_registry import EDARSAHUB_CONFIG
from core.db import execute_sql_query
```

### Autor

E1 Agent - FASE 3 - Mayo 2026
