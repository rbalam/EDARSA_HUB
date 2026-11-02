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
