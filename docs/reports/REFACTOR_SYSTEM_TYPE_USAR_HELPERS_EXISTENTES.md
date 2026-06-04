# Refactor system_type usando helpers existentes

Fecha: Thu Jun  4 19:06:36 UTC 2026

## Helpers existentes
```text
OK: /app/backend/core/system_type_utils.py
97:def normalize_system_type(system_type: Optional[str]) -> str:
128:def is_mpro_system(system_type: Optional[str]) -> bool:
143:def is_softrestaurant_system(system_type: Optional[str]) -> bool:

OK: /app/backend/core/empresa_resolver.py
132:def normalize_alias(texto: str) -> str:
189:def resolve_empresa_by_alias(alias: str) -> Optional[EmpresaInfo]:

OK: /app/backend/core/text_normalizer.py
79:def normalize_for_comparison(text: str) -> str:
119:NOMBRES_CANONICOS = {
138:    return NOMBRES_CANONICOS.get(unidad_id.upper())

```

## Backups
```text
Backup: /app/backend/modules/finanzas/sync_propinas_softrestaurant.py
Backup: /app/backend/modules/finanzas/sync_cortes_softrestaurant.py
```

