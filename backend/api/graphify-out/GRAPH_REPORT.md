# Graph Report - /app/backend/api  (2026-06-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 260 nodes · 412 edges · 9 communities
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 26 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ded4bc56`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]

## God Nodes (most connected - your core abstractions)
1. `success_response()` - 14 edges
2. `ejecutar_resync()` - 11 edges
3. `_execute_edarsahub_query()` - 8 edges
4. `validar_resync()` - 8 edges
5. `get_current_user_from_request()` - 8 edges
6. `register_dba_credential()` - 8 edges
7. `SyncKPIsPayload` - 8 edges
8. `GenerateTokenResponse` - 8 edges
9. `SyncResponse` - 8 edges
10. `clear_preview_cache()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `KPIRecord` --uses--> `GenerateTokenRequest`  [INFERRED]
  sync_receiver.py → sync_schemas.py
- `KPIRecord` --uses--> `GenerateTokenResponse`  [INFERRED]
  sync_receiver.py → sync_schemas.py
- `KPIRecord` --uses--> `HeartbeatPayload`  [INFERRED]
  sync_receiver.py → sync_schemas.py
- `KPIRecord` --uses--> `KPIRecord`  [INFERRED]
  sync_receiver.py → sync_schemas.py
- `KPIRecord` --uses--> `SyncKPIsPayload`  [INFERRED]
  sync_receiver.py → sync_schemas.py

## Import Cycles
- 1-file cycle: `configuracion_operativa_unidades.py -> configuracion_operativa_unidades.py`

## Communities (9 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (49): ConsolidationPreviewResponse, Vista previa de consolidación., BaseModel, GenerateTokenRequest, HeartbeatPayload, KPIRecord, create_agent_token(), determine_agent_status() (+41 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (50): actualizar_tipo_sync(), crear_tipo_sync(), _ejecutar_dry_run(), ejecutar_resync(), _ejecutar_sync_real(), _execute_edarsahub_query(), _get_edarsahub_config(), _get_tipo_sync_config() (+42 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (35): check_catalogo_permission(), diagnostico_sistema(), error_response(), get_current_user_from_token(), listar_capacidades_disponibles(), listar_capacidades_sistema(), listar_modulos_disponibles(), listar_sistemas() (+27 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (32): calcular_fecha_operacion_por_unidad(), ConfiguracionOperativaSchema, get_configuracion_operativa(), get_connection(), get_fecha_operacion_para_unidad(), get_todas_configuraciones(), get_turnos_por_unidad(), _one_dict() (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.10
Nodes (26): audit_core_action(), _classify_sql_error(), format_core_connection(), get_core_audit_log(), get_core_connection_by_id(), get_core_connection_detail(), get_core_connections_from_sql(), list_core_connections() (+18 more)

### Community 5 - "Community 5"
Cohesion: 0.16
Nodes (23): audit_dba_action(), clear_dba_credential(), DBACredentialRequest, DBACredentialResponse, DBAQueryRequest, execute_dba_diagnostic(), get_current_user_from_request(), get_dba_credential_status() (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (22): check_cache_admin_permission(), clear_context_resolver_cache(), clear_db_pool_cache(), clear_lru_caches(), clear_preview_cache(), clear_server_registry_cache(), get_cache_status(), get_registered_caches() (+14 more)

### Community 7 - "Community 7"
Cohesion: 0.20
Nodes (13): audit_generic_duplicates(), audit_merida_duplicates(), DuplicateAuditResponse, _execute_readonly_query(), _get_edarsahub_config(), EDARSA HUB - API Administrativa: Calidad de Datos ==============================, Audita los duplicados de Mérida por variantes de acento.          Issue: DATA-QU, Auditoría genérica para encontrar duplicados por variantes de texto.     Útil pa (+5 more)

## Knowledge Gaps
- **5 isolated node(s):** `Any`, `HTTPAuthorizationCredentials`, `Any`, `Any`, `date`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `datetime` connect `Community 3` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.348) - this node is a cross-community bridge._
- **What connects `Any`, `EDARSA HUB - Endpoint de Limpieza de Caché para Modo Preview ===================`, `Detecta si el backend está corriendo en modo preview.          Criterios:     1.` to the rest of the system?**
  _125 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07137254901960784 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06588235294117648 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.07301587301587302 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.08522727272727272 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.10256410256410256 - nodes in this community are weakly interconnected._