# EDARSAHUB - Active Architecture Decisions

- SQL First.
- No MongoDB runtime nuevo.
- No hardcodes funcionales.
- Backend authoritative.
- RBAC contextual.
- Una sola fuente de verdad.
- Workspace compartido preservado.
- Desarrollo primero en Edarsahub_Desarrollo.
- Audit-first.
- Memoria persistente dentro del repo.
- No workflows paralelos.
- No acciones RBAC nuevas sin auditar catálogo.
- Domain-first; evitar crecer backend/core.
- Finanzas_CxP_DecisionesPago conserva ownership de la decisión financiera.
- EJECUTAR se reutiliza cuando represente ejecucion posterior a autorizacion.
- Excepcion unica EDARSAHUB_MCP_RECOVERY, aprobada el 2026-11-02 por @rbalam (identidad GitHub verificada; rol repository admin): auditoria READ_ONLY y preparacion de gobernanza por el Universal Worker existente; checkpoint MCP independiente; CURRENT.md y NEXT de CxP intactos; CxP pausado; ejecucion secuencial con un solo writer. No autoriza implementacion MCP, JOB MCP tecnico, EDARSAHUB_MCP_INPROCESS=1 ni Produccion. La autoridad de la excepcion proviene de AGENT_POLICY.md, no de esta entrada por si sola.
- Autorizacion acotada EDARSAHUB BOS Gate 3I (2026-11-15, GO explicito de autoridad humana sobre Edarsahub_Desarrollo, conforme a AGENT_POLICY.md): remediacion de menor privilegio de scopes OAuth/MCP (integracion selectiva de oauth_security.py, require_tool_scope por herramienta MCP e ingreso Worker, y pruebas positivas/negativas en el workflow canonico worker-mcp-gate2b.yml sin crear workflows paralelos). Preserva CURRENT.md y NEXT de CxP intactos, RBAC_ADMIN, worker_requester_rbac, PKCE S256, dbo.Sesiones, compatibilidad Emergent, worktree protegido r38-oauth-reconcile intacto, EDARSAHUB_MCP_INPROCESS=0 y Edarsahub_Produccion intacta; al concluir Gate 3I, IMPLEMENTATION_AUTHORIZED retorna a NO.
- Autorizacion acotada EDARSAHUB BOS Gate 3L (2026-11-15, GO explicito de autoridad humana sobre Edarsahub_Desarrollo y Preview, conforme a AGENT_POLICY.md): OAuth Step-Up Challenge & Runtime Sync a partir de Gate 3K READ_ONLY (anuncio de scopes disponibles en negociacion OAuth sin concesion automatica, respuesta HTTP 403 insufficient_scope con WWW-Authenticate en la frontera MCP preservando HTTP 200 para operaciones validas y get_job_status con worker:status, diferenciacion explicita de errores HTTP 403 vs HTTP 422, sincronizacion de reinicio controlado exclusivamente de edarsahub-worker-mcp en Preview y pruebas positivas/negativas en worker-mcp-gate2b.yml). Preserva CURRENT.md y NEXT de CxP intactos, OAuth 2.1, PKCE S256, RBAC, dbo.Sesiones, fail-closed, compatibilidad Emergent, EDARSAHUB_MCP_INPROCESS=0 y Edarsahub_Produccion intacta; al concluir Gate 3L, IMPLEMENTATION_AUTHORIZED retorna a NO.
