"""
Economía - dominio económico canónico de EDARSAHUB.

Contrato BOS:
- importar ``modules.economia`` no ejecuta SQL;
- no inicializa RBAC ni seguridad;
- no registra jobs;
- no importa rutas de forma eager.

El router debe importarse explícitamente desde
``modules.economia.routes`` por la capa de composición/runtime.
"""

__all__ = []
