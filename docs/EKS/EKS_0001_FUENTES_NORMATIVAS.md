# EKS-0001 — Fuentes Normativas

- Entrada: **291**
- Normativos antes de deduplicar: **35**
- Normativos únicos: **35**

## Dictamen por tema

| Tema | Estado | Fuente primaria | Candidatos |
|---|---|---|---:|
| `filosofia_bos` | `CONSOLIDAR_DESDE_HOSPITALITY` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | 1 |
| `hospitality` | `FUENTE_PRIMARIA_CONFIRMADA` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | 4 |
| `arquitectura_global` | `CONSOLIDAR_DESDE_HOSPITALITY` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | 1 |
| `constitucion_maximas` | `NO_EXISTE_DOCUMENTO_UNICO_CONFIRMADO` | `NO CONFIRMADA` | 12 |
| `conectores_universales` | `PARCIAL_HOSPITALITY_MAS_TOAST_NETPAY_PENDIENTE` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | 2 |
| `toast_netpay` | `FUENTE_PRIMARIA_FALTANTE` | `NO CONFIRMADA` | 3 |
| `sql_datos` | `CONSOLIDACION_MULTIFUENTE` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | 14 |
| `rbac_seguridad` | `CONSOLIDACION_MULTIFUENTE` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | 34 |
| `ia_agentes` | `POLITICA_OPERATIVA_NO_CONSTITUCION` | `.github/agents/edarsa-coder.agent.md` | 31 |
| `cambios_atomicos` | `POLITICA_OPERATIVA_PROPUESTA` | `docs/operacion/MODO_TRABAJO_CAMBIOS_ATOMICOS.md` | 9 |
| `contratos_canonicos` | `CONSOLIDAR_POR_DOMINIO` | `NO CONFIRMADA` | 3 |
| `roadmap_aceptacion` | `SEPARAR_PERMANENTE_DE_TEMPORAL` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | 5 |

## Reglas de autoridad

1. Los documentos normativos gobiernan.
2. El código solo demuestra implementación.
3. Worklogs, auditorías y reportes son evidencia histórica.
4. Un documento deprecado nunca puede ser rector.
5. Los chats faltantes no serán reconstruidos por inferencia.

## Fuentes normativas candidatas

### EKS-SRC-00444 — ARQUITECTURA DE CONEXIONES - EDARSA HUB

- Ruta: `docs/ARQUITECTURA_CONEXIONES_RESOLVER.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `9/10`
- Temas: `comercial`

### EKS-SRC-00316 — POLÍTICA OFICIAL DE FECHAS - EDARSA HUB

- Ruta: `docs/POLITICA_FECHAS_EDARSA_HUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `9/10`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

### EKS-SRC-01112 — EDARSAHUB Hospitality Architecture Book

- Ruta: `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `9/10`
- Temas: `filosofia_bos, hospitality, constitucion_maximas, arquitectura_global, conectores_universales, sql_datos, rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

### EKS-SRC-00864 — DISEÑO TÉCNICO: Consola General de Scheduler y Sincronizaciones EDARSAHUB

- Ruta: `docs/reports/DISENO_CONSOLA_GENERAL_SCHEDULER_SINCRONIZACIONES_EDARSAHUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `9/10`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

### EKS-SRC-00680 — FASE 0.5 - VALIDACIÓN ARQUITECTÓNICA: MENÚS GOBERNADOS Y COMERCIAL/VENTAS

- Ruta: `docs/reports/FASE_0_5_VALIDACION_ARQUITECTURA_MENUS_Y_COMERCIAL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `9/10`
- Temas: `hospitality, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

### EKS-SRC-01338 — EDARSA Coder

- Ruta: `.github/agents/edarsa-coder.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `rbac_seguridad, ia_agentes, comercial`

### EKS-SRC-01325 — EDARSAHUB V1.0 — instrucciones globales para GitHub Copilot / VS Code

- Ruta: `.github/copilot-instructions.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

### EKS-SRC-00001 — EDARSAHUB V1.0 — Agent Operating Protocol

- Ruta: `AGENTS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos, comercial`

### EKS-SRC-00357 — Corrección Arquitectónica: Conexiones API

- Ruta: `docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `conectores_universales, rbac_seguridad, comercial`

### EKS-SRC-00478 — ADENDA TÉCNICA: Definiciones Críticas de Automatización

- Ruta: `docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_A.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

### EKS-SRC-00423 — ADENDA TÉCNICA B: Ajustes Finales Obligatorios

- Ruta: `docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_B.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

### EKS-SRC-00372 — DOCUMENTO DE CONSOLIDACIÓN FINAL

- Ruta: `docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_CONSOLIDACION_FINAL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

### EKS-SRC-00301 — EDARSA HUB - Arquitectura de Clasificación de Datos

- Ruta: `docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

### EKS-SRC-00369 — ARQUITECTURA DE SEGURIDAD EDARSA HUB

- Ruta: `docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

### EKS-SRC-00389 — EDARSAHUB - MÁXIMAS INQUEBRANTABLES

- Ruta: `docs/EDARSAHUB_MAXIMAS_INQUEBRANTABLES.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial`

### EKS-SRC-00426 — SQLFIRST-LEGACY-001

- Ruta: `docs/LOG_PENDIENTES_ARQUITECTURA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

### EKS-SRC-00512 — Navegación Enterprise EDARSAHUB

- Ruta: `docs/arquitectura/NAVEGACION_ENTERPRISE.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `rbac_seguridad, comercial, finanzas`

### EKS-SRC-00508 — Máxima de Oro — Cambios Atómicos y Base Estable

- Ruta: `docs/operacion/MODO_TRABAJO_CAMBIOS_ATOMICOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos, comercial, finanzas`

### EKS-SRC-00874 — DECISIÓN EJECUTIVA RBAC - EDARSAHUB

- Ruta: `docs/reports/DECISION_EJECUTIVA_RBAC_20260602.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `rbac_seguridad, ia_agentes, comercial`

### EKS-SRC-01294 — DIAGNÓSTICO DE ARQUITECTURA DE CONECTIVIDAD - EDARSA HUB

- Ruta: `memory/ARQUITECTURA_CONECTIVIDAD_EDARSA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial`

### EKS-SRC-01291 — EDARSA HUB - Documento de Diseño Técnico-Funcional

- Ruta: `memory/DISENO_MODULO_CATALOGOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `sql_datos, rbac_seguridad, finanzas`

### EKS-SRC-01271 — EDARSA HUB — ROADMAP / Backlog priorizado

- Ruta: `memory/ROADMAP.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `8/10`
- Temas: `contratos_canonicos, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

### EKS-SRC-01337 — EDARSA Copilot Supervisor

- Ruta: `.github/agents/edarsa-copilot-supervisor.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `7/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

### EKS-SRC-00377 — PROPUESTA DE ARQUITECTURA AJUSTADA

- Ruta: `docs/ARQUITECTURA_PROPINAS_TPV_v3.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `7/10`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

### EKS-SRC-00378 — ADENDA ARQUITECTÓNICA

- Ruta: `docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `7/10`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

### EKS-SRC-00118 — EDARSA Auditor Skill

- Ruta: `.agents/skills/edarsa-auditor/SKILL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `3/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

### EKS-SRC-00116 — EDARSA Coder Skill

- Ruta: `.agents/skills/edarsa-coder/SKILL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `3/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos, comercial`

### EKS-SRC-01335 — EDARSA Auditor

- Ruta: `.github/agents/edarsa-auditor.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `3/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

### EKS-SRC-01336 — EDARSA Validator

- Ruta: `.github/agents/edarsa-validator.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `3/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

### EKS-SRC-01334 — EDARSAHUB Codex Auditor

- Ruta: `.github/agents/edarsahub-codex-auditor.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `3/10`
- Temas: `rbac_seguridad, ia_agentes, comercial`

### EKS-SRC-00117 — EDARSA Committer Skill

- Ruta: `.agents/skills/edarsa-committer/SKILL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `2/10`
- Temas: `rbac_seguridad, ia_agentes`

### EKS-SRC-00115 — EDARSA Validator Skill

- Ruta: `.agents/skills/edarsa-validator/SKILL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `2/10`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

### EKS-SRC-01339 — EDARSA Committer

- Ruta: `.github/agents/edarsa-committer.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `2/10`
- Temas: `rbac_seguridad, ia_agentes`

### EKS-SRC-01241 — EDARSA HUB - CRM COMERCIAL ENTERPRISE

- Ruta: `memory/PRD.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad previa: `2/10`
- Temas: `hospitality, constitucion_maximas, contratos_canonicos, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

### EKS-SRC-08868 — EDARSA HUB - CRM COMERCIAL ENTERPRISE

- Ruta: `memory/PRD.md`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad previa: `2/10`
- Temas: `hospitality, constitucion_maximas, contratos_canonicos, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

