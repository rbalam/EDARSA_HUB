# EKS-0001 — Fuentes Rectoras

- Candidatos curados de entrada: **1490**
- Candidatos rectores antes de deduplicar: **291**
- Candidatos rectores únicos: **291**

## Decisiones preliminares por tema

| Tema | Estado | Fuente rectora propuesta | Observación |
|---|---|---|---|
| `arquitectura_global` | `FUENTE_RECTORA_PROPUESTA` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | Requiere comparación de contenido antes de oficializar. |
| `cambios_atomicos` | `FUENTE_RECTORA_PROPUESTA` | `docs/operacion/MODO_TRABAJO_CAMBIOS_ATOMICOS.md` | Requiere comparación de contenido antes de oficializar. |
| `conectores_universales` | `FUENTE_RECTORA_PROPUESTA` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | Requiere comparación de contenido antes de oficializar. |
| `constitucion_maximas` | `FUENTE_RECTORA_PROPUESTA` | `AGENTS.md` | Requiere comparación de contenido antes de oficializar. |
| `contratos_canonicos` | `CONSOLIDACION_MULTIFUENTE` | `memory/ROADMAP.md` | No debe reducirse a un único documento sin comparar arquitectura global, contratos y evidencia vigente. |
| `filosofia_bos` | `FUENTE_RECTORA_PROPUESTA` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | Requiere comparación de contenido antes de oficializar. |
| `hospitality` | `FUENTE_RECTORA_PROPUESTA` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | Requiere comparación de contenido antes de oficializar. |
| `ia_agentes` | `FUENTE_RECTORA_PROPUESTA` | `.github/copilot-instructions.md` | Requiere comparación de contenido antes de oficializar. |
| `rbac_seguridad` | `CONSOLIDACION_MULTIFUENTE` | `memory/WORKLOG.md` | No debe reducirse a un único documento sin comparar arquitectura global, contratos y evidencia vigente. |
| `roadmap_aceptacion` | `FUENTE_RECTORA_PROPUESTA` | `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md` | Requiere comparación de contenido antes de oficializar. |
| `sql_datos` | `CONSOLIDACION_MULTIFUENTE` | `memory/WORKLOG.md` | No debe reducirse a un único documento sin comparar arquitectura global, contratos y evidencia vigente. |
| `toast_netpay` | `FUENTE_PRIMARIA_INCOMPLETA` | `frontend/src/pages/Comercial.js` | El repositorio contiene evidencias parciales, pero falta la conversación o documento rector original. |

## Fuentes primarias no recuperadas

- Chat original de Hospitality.
- Chat Robots / Toast / NetPay.

Estas fuentes no serán reemplazadas por inferencias.

## Candidatos rectores

### EKS-SRC-01274 — EDARSA HUB - Work Log

- Ruta: `memory/WORKLOG.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `conectores_universales, sql_datos, rbac_seguridad, ia_agentes, comercial`

> # EDARSA HUB - Work Log ## 2026-05-29: Migración SQL-Only Completada - Eliminación definitiva de dependencias MongoDB (pymongo, motor eliminados de requirements.txt). - Archivos de conexión en vivo eliminados: - `backend/core/server_connection_manager.py` - `backend/modules/automatizacion/detection_service.py` - Tests de DNS marcados como skip (3 tests que dependen de resolución DNS externa). - Mó

### EKS-SRC-02052 — ============================================

- Ruta: `backend/utils/migration_helpers.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, comercial`

> from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - Utilidades de Migración MongoDB → SQL Server ========================================================= Funciones helper para convertir código legacy MongoDB a SQL-First. Alineado al Canonical Data Model Oficial de EDARSAHUB (Fase 2). Uso con Google AI Studio / Gemini API. """ # ======================================

### EKS-SRC-00316 — POLÍTICA OFICIAL DE FECHAS - EDARSA HUB

- Ruta: `docs/POLITICA_FECHAS_EDARSA_HUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # POLÍTICA OFICIAL DE FECHAS - EDARSA HUB ## Documento Técnico-Funcional **Versión:** 1.0 **Fecha:** Diciembre 2025 **Estado:** DIAGNÓSTICO DOCUMENTADO (Sin cambios de código) **Autor:** Arquitectura de Software --- ## 1. RESUMEN EJECUTIVO Este documento establece las definiciones, reglas y lineamientos oficiales para el manejo de fechas/horas en EDARSA HUB, con el objetivo de: - Evitar inconsiste

### EKS-SRC-02259 — ============================================================================

- Ruta: `backend/core/connection_resolver.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - Connection Resolver Central ========================================= Resolver centralizado para conexiones y fuentes de datos. PRINCIPIOS: 1. EDARSA HUB es el cerebro - Backend manda 2. Menú "Servidores SQL" es la fuente oficial de configuración 3. Toda conexión SQL

### EKS-SRC-00326 — DOCUMENTO DE MIGRACIÓN TÉCNICA

- Ruta: `docs/MIGRACION_TECNICA_PROPINAS_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> # DOCUMENTO DE MIGRACIÓN TÉCNICA # Módulo Propinas TPV: Arquitectura SQL + Cache **Versión:** 1.0 **Fecha:** 15 de Abril de 2026 **Autor:** Arquitecto EDARSA HUB **CAB Referencia:** `ARQUITECTURA_PROPINAS_TPV_v3.md` --- ## 1. RESUMEN EJECUTIVO ### Cambio Implementado Refactorización del módulo de Propinas TPV para usar SQL Server EDARSA HUB como fuente oficial de datos financieros, relegando Mongo

### EKS-SRC-01115 — AGENTE RECTOR / ORQUESTADOR SENIOR - EDARSAHUB

- Ruta: `docs/governance/AGENTE_RECTOR_PROMPT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # AGENTE RECTOR / ORQUESTADOR SENIOR - EDARSAHUB ## Función Principal Coordinar, revisar y dirigir el trabajo de otros agentes especializados dentro de Emergent para proteger la arquitectura, estabilidad, seguridad y continuidad operativa del sistema EDARSAHUB. --- ## CONTEXTO CENTRAL DEL PROYECTO EDARSAHUB es el sistema central de consolidación operativa, comercial, financiera, contable, inventar

### EKS-SRC-00444 — ARQUITECTURA DE CONEXIONES - EDARSA HUB

- Ruta: `docs/ARQUITECTURA_CONEXIONES_RESOLVER.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `comercial`

> # ARQUITECTURA DE CONEXIONES - EDARSA HUB ## Connection Resolver Central ## Fecha: 2026-04-19 --- ## PRINCIPIOS ARQUITECTÓNICOS 1. **EDARSA HUB es el cerebro** - Backend manda 2. **Menú "Servidores SQL"** es la fuente oficial de configuración 3. **Toda conexión SQL** debe resolverse desde ConnectionResolver 4. **Toda fuente de datos** se decide por tipo de sistema + tipo de métrica 5. **El fronten

### EKS-SRC-00374 — MATRIZ DE FUENTES - TABLERO EJECUTIVO EDARSA HUB

- Ruta: `docs/MATRIZ_FUENTES_TABLERO_EJECUTIVO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial`

> # MATRIZ DE FUENTES - TABLERO EJECUTIVO EDARSA HUB ## Fecha: 2026-04-19 --- ## ARQUITECTURA DE FUENTES VERIFICADA ### 1. SoftRestaurant (CIENFUEGOS, LA ESTELAR, 130° MERIDA) | KPI | Fuente Real | Método Backend | Conexión | Query/Tabla | Estado | |-----|------------|----------------|----------|-------------|--------| | Ventas Acumuladas | SQL histórico | `get_kpis_softrestaurant()` | Menú Servidor

### EKS-SRC-00871 — DICTAMEN DE NO DUPLICIDAD - CRM ENTERPRISE EDARSAHUB

- Ruta: `docs/reports/CRM_DIAGNOSTICO_NO_DUPLICIDAD.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # DICTAMEN DE NO DUPLICIDAD - CRM ENTERPRISE EDARSAHUB **Fase 1 - Gobierno y Arquitectura** Este documento establece el diagnóstico oficial de las estructuras actuales en `EDARSAHUB SQL` para garantizar la Máxima 6 (No duplicar tablas), Máxima 7 (No duplicar entidades) y Máxima 8 (No duplicar catálogos). ## 1. ENTIDADES MAESTRAS EXISTENTES (NO DUPLICAR) Las siguientes tablas ya existen en el ecosi

### EKS-SRC-00613 — 🏛️ DICTAMEN TÉCNICO DE CERTIFICACIÓN FINAL - CRM EDARSAHUB

- Ruta: `docs/reports/CRM_ENTERPRISE_CERTIFICACION_FINAL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial`

> # 🏛️ DICTAMEN TÉCNICO DE CERTIFICACIÓN FINAL - CRM EDARSAHUB ## ESTADO DE LA PLATAFORMA: CRÍTICO / PRODUCTION-READY (2026-05-29) ### 1. CERTIFICACIÓN DEL FLUJO TRANSACCIONAL CANÓNICO Se certifica que la arquitectura lógica y física del CRM Comercial Enterprise opera de extremo a extremo de manera síncrona, determinista y local sobre la infraestructura central, validando quirúrgicamente el ciclo co

### EKS-SRC-01859 — FASE T2.3: Importar server_registry para resolver servidores desde EDARSAHUB

- Ruta: `backend/modules/finanzas/propinas_tpv/routes_sql.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ API Routes SQL para el módulo de Control de Propinas TPV ======================================================== Fecha: 15 de Abril de 2026 CAB: ARQUITECTURA_PROPINAS_TPV_v3.md FASE T2.3 (Mayo 2026): Migrado a server_registry.py (elimina MongoDB db.servers) ARQUITECTURA: - SQL S

### EKS-SRC-01857 — ==============================================================================

- Ruta: `backend/modules/finanzas/propinas_tpv/sql_scripts.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - Script DDL para Módulo de Propinas TPV =================================================== Fecha: 15 de Abril de 2026 Autor: Arquitecto EDARSA HUB CAB Aprobado: ARQUITECTURA_PROPINAS_TPV_v3.md IMPORTANTE: - Ejecutar en SQL Server EDARSA HUB (edarsa_hub database) - NO

### EKS-SRC-01860 — FASE T2.1: Usar EDARSAHUB_CONFIG desde server_registry

- Ruta: `backend/modules/finanzas/propinas_tpv/sql_repository.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - SQL Repository para Propinas TPV ============================================= Fecha: 15 de Abril de 2026 CAB: ARQUITECTURA_PROPINAS_TPV_v3.md RESPONSABILIDADES: - Persistencia oficial en SQL Server EDARSA HUB - CRUD completo de propinas_tpv_control - Gestión de prop

### EKS-SRC-01112 — EDARSAHUB Hospitality Architecture Book

- Ruta: `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `filosofia_bos, hospitality, constitucion_maximas, arquitectura_global, conectores_universales, sql_datos, rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

> # EDARSAHUB Hospitality Architecture Book ## Objetivo Diseñar EDARSAHUB Hospitality como satélite nativo del ERP EDARSAHUB: global, configurable, multiconector, SQL-first, sin MongoDB, sin LIVE operativo y sin duplicar lógica existente. ## Tomos 1. Visión Estratégica 2. Máximas de Arquitectura 3. Arquitectura Empresarial 4. Arquitectura Funcional 5. Arquitectura Backend 6. Arquitectura Frontend / 

### EKS-SRC-00824 — PLAN DE IMPLEMENTACIÓN: Fase 0 Mínima - Re-sincronización CIENFUEGOS

- Ruta: `docs/reports/PLAN_IMPLEMENTACION_FASE0_RESYNC_CIENFUEGOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial, roadmap_aceptacion`

> # PLAN DE IMPLEMENTACIÓN: Fase 0 Mínima - Re-sincronización CIENFUEGOS **Fecha:** 2026-05-25 **Ticket:** P0-B RECONCILIACIÓN CIENFUEGOS **Estado:** PLAN DE IMPLEMENTACIÓN - PENDIENTE AUTORIZACIÓN --- ## 1. OBJETIVO Implementar la **Fase 0 mínima** de la Consola General de Scheduler para resolver P0-B CIENFUEGOS, construida sobre la arquitectura definitiva. **Caso a resolver:** - Unidad: CIENFUEGOS

### EKS-SRC-00680 — FASE 0.5 - VALIDACIÓN ARQUITECTÓNICA: MENÚS GOBERNADOS Y COMERCIAL/VENTAS

- Ruta: `docs/reports/FASE_0_5_VALIDACION_ARQUITECTURA_MENUS_Y_COMERCIAL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `hospitality, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # FASE 0.5 - VALIDACIÓN ARQUITECTÓNICA: MENÚS GOBERNADOS Y COMERCIAL/VENTAS **Fecha:** 24 Mayo 2026 **Autor:** Arquitecto ERP EDARSAHUB **Estado:** VALIDACIÓN COMPLETADA --- ## 1. RESUMEN EJECUTIVO La FASE 0 (Sistema de Menús Gobernados) fue implementada correctamente. Se crearon las tablas necesarias, los 27 módulos según el manifiesto ERP están registrados y el endpoint funciona. Sin embargo, se

### EKS-SRC-00864 — DISEÑO TÉCNICO: Consola General de Scheduler y Sincronizaciones EDARSAHUB

- Ruta: `docs/reports/DISENO_CONSOLA_GENERAL_SCHEDULER_SINCRONIZACIONES_EDARSAHUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # DISEÑO TÉCNICO: Consola General de Scheduler y Sincronizaciones EDARSAHUB **Fecha:** 2026-05-25 **Versión:** 1.0 **Estado:** DISEÑO TÉCNICO - NO IMPLEMENTAR SIN AUTORIZACIÓN **Autor:** E1 Agent (Ingeniero Senior Fullstack + SQL Server) --- ## 1. RESUMEN EJECUTIVO Este documento describe el diseño técnico completo de la **Consola Administrativa General del Scheduler de EDARSAHUB**, un componente 

### EKS-SRC-03177 — ESPECIFICACIÓN OFICIAL — MÓDULO DE ANÁLISIS DE VENTAS A PRECIOS CONSTANTES

- Ruta: `.agent-worktrees/compras-inventarios/docs/reports/ESPECIFICACION_OFICIAL_ANALISIS_PRECIOS_CONSTANTES.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `comercial`

> # ESPECIFICACIÓN OFICIAL — MÓDULO DE ANÁLISIS DE VENTAS A PRECIOS CONSTANTES Fecha de Certificación: 2026-07-23 Módulo: Comercial / Inteligencia Comercial Endpoint: `GET /comercial/precios-constantes/{server_id}` Fuentes Canónicas: `dbo.vw_Comercial_KPIs_Diarios_v2_Runtime` y `dbo.Sync_Precios_Historicos` --- ## 1. OBJETIVO DEL MÓDULO El módulo de **Ventas a Precios Constantes** permite evaluar el

### EKS-SRC-07515 — Módulo de Control y Cuadre de Comisión sobre Propinas TPV

- Ruta: `backend/modules/finanzas/propinas_tpv/__init__.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `9/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService # Módulo de Control y Cuadre de Comisión sobre Propinas TPV # FASE 1 MVP - Solo SoftRestaurant # # CAB Aprobado: 2026-04-14 # Arquitectura SQL: 2026-04-15 (ARQUITECTURA_PROPINAS_TPV_v3.md) # Documentos: /app/docs/CAB_MODULO_PROPINAS_TPV.md # # ARQUITECTURA: # - SQL Server EDARSA HUB 

### EKS-SRC-00001 — EDARSAHUB V1.0 — Agent Operating Protocol

- Ruta: `AGENTS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos, comercial`

> # EDARSAHUB V1.0 — Agent Operating Protocol ## Prioridad de herramientas Prioridad operativa: 1. Antigravity 2. Codex 3. VS Code custom agents 4. Claude minimizado No usar `.claude/agents` como fuente principal de configuración. Excepción permitida: únicamente `.claude/agents/edarsa-claude-haiku-auditor.md` como auditor Claude Haiku de solo lectura, uso excepcional y bajo autorización explícita. #

### EKS-SRC-01271 — EDARSA HUB — ROADMAP / Backlog priorizado

- Ruta: `memory/ROADMAP.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `contratos_canonicos, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # EDARSA HUB — ROADMAP / Backlog priorizado ## En curso (orden acordado con usuario: a → d → c → b) - [x] (a) Precios Sugeridos: columnas $/%, fuente del %, filtro unidad canónico. (2026-06-08) - [x] (d) SYNC estatus inactivo/baja (SoftRestaurant `productosdetalle.bloqueado`, MPRO `Es_Cve_Estado`) + re-sync. (2026-06-08) - [x] (c) **Catálogo canónico NO-LIVE** Categoría→Familia→Subfamilia. (2026-0

### EKS-SRC-00010 — summary.txt

- Ruta: `.emergent/summary.txt`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, sql_datos, rbac_seguridad, comercial, roadmap_aceptacion`

> <analysis><analysis> **original_problem_statement:** Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB. PRODUCT REQUIREMENTS: - ESTRICTA PROHIBICIÓN: Uso del subagente totalmente prohibido. Pruebas exclusivas vía cURL, bash, python -c y screenshots. - NUEVA REGLA ARQUITECTÓNICA (MÁXIMA INQUEBRANTABLE - NO-LIVE): EDARSAHUB SQL será la ÚNICA fuente de verda

### EKS-SRC-00448 — FASE 1 - EVIDENCIA DE EJECUCIÓN

- Ruta: `docs/FASE1_EVIDENCIA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # FASE 1 - EVIDENCIA DE EJECUCIÓN ## Arquitectura de Seguridad EDARSA HUB **Fecha:** Diciembre 2025 **Estado:** COMPLETADA **Impacto en producción:** NINGUNO (verificado) --- ## 1. COLECCIONES CREADAS | Colección | Documentos | Índices | Estado | |-----------|------------|---------|--------| | `sec_permisos_catalogo` | 89 | codigo (unique), modulo, activo | ✅ Creada | | `sec_modulos_sistema` | 10 

### EKS-SRC-00454 — FASE 2 - EVIDENCIA DE CIERRE

- Ruta: `docs/FASE2_EVIDENCIA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial, finanzas`

> # FASE 2 - EVIDENCIA DE CIERRE ## Arquitectura de Seguridad EDARSA HUB **Fecha de cierre:** Diciembre 2025 **Estado:** COMPLETADA Y VALIDADA ✅ --- ## 1. RESUMEN EJECUTIVO La FASE 2 del rediseño de arquitectura de seguridad ha sido completada exitosamente, cumpliendo todas las condiciones establecidas en el documento de alcance controlado. ### Alcance implementado: - ✅ Tab "Estructura" añadido en `

### EKS-SRC-00292 — FASE 4 - EVIDENCIA DE CIERRE

- Ruta: `docs/FASE4_EVIDENCIA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # FASE 4 - EVIDENCIA DE CIERRE ## Administración de Permisos - Piloto Controlado **Fecha de cierre:** Diciembre 2025 **Estado:** COMPLETADA Y VALIDADA ✅ **Opción ejecutada:** A - Endpoint Simple --- ## 1. RESUMEN EJECUTIVO Se implementó exitosamente el primer endpoint de administración de permisos del sistema RBAC, permitiendo asignar y retirar el permiso piloto `SISTEMA_ESTRUCTURA_VER` con audito

### EKS-SRC-00493 — FASE 5 - EVIDENCIA DE CIERRE

- Ruta: `docs/FASE5_EVIDENCIA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # FASE 5 - EVIDENCIA DE CIERRE ## Herencia de Permisos por Rol - Piloto Controlado **Fecha de cierre:** Diciembre 2025 **Estado:** COMPLETADA Y VALIDADA ✅ **Opción ejecutada:** A - Rol Piloto Aislado --- ## 1. RESUMEN EJECUTIVO Se implementó exitosamente el sistema de herencia de permisos por rol, permitiendo que un usuario herede permisos de un rol nuevo (`sec_roles`) además de sus permisos direc

### EKS-SRC-00370 — EDARSA HUB - Normas Técnicas y Reglas Arquitectónicas

- Ruta: `docs/NORMAS_TECNICAS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> # EDARSA HUB - Normas Técnicas y Reglas Arquitectónicas ## Documento Maestro de Estándares **Versión**: 2.0 **Fecha**: Abril 2026 **Estado**: VIGENTE --- ## 0. REGLA ARQUITECTÓNICA FUNDAMENTAL: CLASIFICACIÓN DE FUENTES DE DATOS ### NORMA OBLIGATORIA **Todo módulo del sistema debe clasificarse según el origen de sus datos:** | Clasificación | Descripción | Fuente de Verdad | |--------------|-------

### EKS-SRC-00495 — FASE 11 - EVIDENCIA DE CIERRE

- Ruta: `docs/FASE11_EVIDENCIA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial`

> # FASE 11 - EVIDENCIA DE CIERRE ## Arquitectura de Seguridad EDARSA HUB **Versión:** 1.0 **Fecha:** Diciembre 2025 **Estado:** COMPLETADO **Opción Implementada:** OPCIÓN B --- ## 1. RESUMEN EJECUTIVO FASE 11 implementó la protección real de endpoints POST del módulo Sistema: - Nuevo endpoint `POST /api/users` (creación administrativa) - Protección RBAC de `POST /api/users` con permiso `SISTEMA_USU

### EKS-SRC-01297 — EDARSA HUB - Mapa de Migración del Backend

- Ruta: `memory/MAPA_MIGRACION.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # EDARSA HUB - Mapa de Migración del Backend > **Documento de Auditoría Técnica** > **Fecha de Elaboración**: Diciembre 2025 > **Estado**: APROBADO PARA DOCUMENTACIÓN > **Última Actualización**: Pendiente de ejecución de fases --- ## 1. Resumen Ejecutivo ### 1.1 Objetivo Migrar el monolito `server.py` (18,082 líneas) hacia una arquitectura modular manteniendo compatibilidad total con el frontend y

### EKS-SRC-01308 — FASE 2.3 - DICTAMEN DE CARGA HISTÓRICA

- Ruta: `memory/DICTAMEN_FASE23.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `ia_agentes, comercial`

> # FASE 2.3 - DICTAMEN DE CARGA HISTÓRICA **Fecha:** 2026-04-23 **Ejecutado por:** E1 Agent **Estado:** 🟡 IMPLEMENTADA Y LISTA PARA EJECUCIÓN | EJECUCIÓN OPERATIVA REAL PENDIENTE --- ## 1. RESUMEN EJECUTIVO La infraestructura para carga histórica de 24 meses está **IMPLEMENTADA Y VALIDADA ESTRUCTURALMENTE**. La ejecución operativa real **PERMANECE PENDIENTE** hasta contar con ambiente con conectivi

### EKS-SRC-00011 — Agent-Reach Runtime

- Ruta: `infra/agent-reach/README.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `filosofia_bos, rbac_seguridad`

> # Agent-Reach Runtime Runtime aislado y reproducible para adquisición de evidencia externa de EDARSA BOS. ## Propósito Este componente proporciona las herramientas técnicas para consultar páginas web, RSS, YouTube y otras fuentes externas sin integrarlas directamente en el proceso principal del backend. ## Componentes canónicos - Agent-Reach vendorizado en `third_party/agent-reach`. - Python 3.11 

### EKS-SRC-01739 — Router con prefijo /rrhh para mantener compatibilidad

- Ruta: `backend/modules/rh/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - RH Routes ====================== Endpoints del módulo de Recursos Humanos. PROTEGIDO CON RBAC (Fase 3.1) FASE 6B DEL REFACTOR MODULAR (Diciembre 2025): Catálogos migrados desde server.py: - GET /rrhh/catalogos/puestos - POST /rrhh/catalogos/puestos - PUT /rrhh/catalo

### EKS-SRC-01740 — ============================================================================

- Ruta: `backend/modules/rh/schemas.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - RH Schemas (Catálogos) =================================== Modelos Pydantic para validación de datos del módulo de Recursos Humanos. FASE 6B DEL REFACTOR MODULAR (Diciembre 2025): - Modelos para Catálogo de Puestos (CRUD) - Modelos para Catálogo de Tipos de Incidenci

### EKS-SRC-00490 — CENTRO DE CONTROL EDARSA

- Ruta: `docs/CENTRO_CONTROL_EDARSA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

> # CENTRO DE CONTROL EDARSA ## Módulo Central de Monitoreo, Estabilidad y Control Técnico **Versión:** 2.0.0 **Fecha:** 2026-04-19 **Autor:** Arquitectura EDARSA HUB **Estado:** ACTIVO - MONITOREO CONTINUO **Tipo:** Control Directivo/Técnico (NO Operativo) --- ## 1. VISIÓN EJECUTIVA ### Objetivo Principal Pasar de **REACCIONAR** a **PREVENIR**. El Centro de Control EDARSA es el módulo central que p

### EKS-SRC-01809 — ==================== ESTADO ====================

- Ruta: `backend/modules/crm/service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ CRM Service - Servicio CRM Enterprise SQL-First Arquitectura: EDARSAHUB SQL Server (Sin dependencias externas como vTiger) """ import logging from typing import Optional, Dict, List, Any from datetime import datetime logger = logging.getLogger(__name__) class CRMService: """ Serv

### EKS-SRC-01325 — EDARSAHUB V1.0 — instrucciones globales para GitHub Copilot / VS Code

- Ruta: `.github/copilot-instructions.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

> # EDARSAHUB V1.0 — instrucciones globales para GitHub Copilot / VS Code Usar `AGENTS.md` como contrato principal del repositorio. Prioridad operativa: 1. Antigravity 2. Codex 3. GitHub Copilot / VS Code 4. Claude minimizado Agentes Copilot disponibles: - EDARSA Copilot Supervisor: coordina, no edita. - EDARSA Auditor: audita, no edita. - EDARSA Coder: implementa cambios minimos. - EDARSA Validator

### EKS-SRC-00465 — AUDITORIA-TABLEROS-KPIS-FILTROS-01 — RH y Nóminas

- Ruta: `docs/AUDITORIA_RH_NOMINAS_01.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> # AUDITORIA-TABLEROS-KPIS-FILTROS-01 — RH y Nóminas **Código:** AUDITORIA-RH-NOMINAS-01 **Fecha:** 2025-12-27 **Módulo:** Recursos Humanos / Nóminas **Estado:** ✅ CORRECCIÓN APLICADA — Conexión EDARSAHUB directa --- ## Resumen Ejecutivo El módulo RH/Nóminas estaba bloqueado por una **falla de arquitectura** que fue **corregida**. ### Corrección Aplicada: RH-NOMINAS-EDARSAHUB-CONNECTION-01 Se modif

### EKS-SRC-00162 — Comercial.js

- Ruta: `frontend/src/pages/Comercial.js`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `toast_netpay, rbac_seguridad, ia_agentes, comercial, finanzas`

> /** * ╔════════════════════════════════════════════════════════════════════════════╗ * ║ 🔒 MÓDULO BLINDADO - NO MODIFICAR 🔒 ║ * ╠════════════════════════════════════════════════════════════════════════════╣ * ║ ESTADO: FUNCIONAL Y OPERATIVO (Abril 2026) ║ * ║ ║ * ║ Este módulo ha sido validado y estabilizado. Cualquier modificación ║ * ║ debe ser aprobada por el equipo de arquitectura y probada en

### EKS-SRC-00155 — Dashboard.js

- Ruta: `frontend/src/pages/Dashboard.js`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, toast_netpay`

> import logger from '../services/logger'; import { useEffect, useState } from 'react'; import api from '@/lib/api'; import { fetchUnidadesNegocio } from '@/services/unidadesNegocioService'; import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'; import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'; import { 

### EKS-SRC-01212 — DIAGNÓSTICO TÉCNICO ARQUITECTURA EDARSA HUB

- Ruta: `memory/DIAGNOSTICO_RH_NOMINA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # DIAGNÓSTICO TÉCNICO ARQUITECTURA EDARSA HUB ## Módulo RH / Nómina **Fecha**: Diciembre 2025 **Versión**: 1.0 **Autor**: Arquitecto de Software Senior --- ## 1. ARQUITECTURA ACTUAL DEL PROYECTO ### 1.1 Estructura Frontend ``` /app/frontend/src/ ├── pages/ │ ├── RecursosHumanos.js # 3,414 líneas - Módulo RH principal │ ├── Nomina.js # Módulo de nómina │ ├── Inventario.js # Módulo de inventario │ ├

### EKS-SRC-00391 — FASE 2 - DOCUMENTO DE ALCANCE CONTROLADO

- Ruta: `docs/FASE2_ALCANCE_CONTROLADO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, comercial, finanzas`

> # FASE 2 - DOCUMENTO DE ALCANCE CONTROLADO ## Arquitectura de Seguridad EDARSA HUB **Versión:** 1.0 **Fecha:** Diciembre 2025 **Estado:** PENDIENTE APROBACIÓN **Requisito previo:** FASE 1 aprobada y cerrada ✅ --- ## ÍNDICE 1. [Alcance Propuesto](#1-alcance-propuesto) 2. [Lista Exacta de Cambios](#2-lista-exacta-de-cambios) 3. [Lista Explícita de Exclusiones](#3-lista-explícita-de-exclusiones) 4. [

### EKS-SRC-00286 — localDB.js

- Ruta: `frontend/src/services/localDB.js`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> /** * LocalDB - Wrapper para IndexedDB * Proporciona acceso rápido a datos locales para arquitectura Local-First */ import logger from './logger'; const DB_NAME = 'edarsa_hub_local'; const DB_VERSION = 1; // Stores (tablas) de la base de datos local const STORES = { KPI_TABLERO: 'kpis_tablero', INVENTARIOS: 'inventarios', AUDITORIAS: 'auditorias', CATALOGOS: 'catalogos', SYNC_LOG: 'sync_log', PREF

### EKS-SRC-01886 — access.py

- Ruta: `backend/modules/compras/access.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad`

> """Acceso canonico para el modulo Compras. Centraliza el permiso funcional RBAC (Usuario_PermisosRolModulo) para que los endpoints de /compras/* dejen de depender unicamente de un JWT valido y verifiquen tambien que el usuario tiene el permiso COMPRAS_FACT_* requerido. El alcance por servidor/unidad de negocio para Compras ya se resuelve con `validate_server_access_by_empresa` / `_compras_resolve_

### EKS-SRC-00315 — Code Quality Improvements - EDARSA HUB

- Ruta: `docs/CODE_QUALITY_IMPROVEMENTS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # Code Quality Improvements - EDARSA HUB ## Fecha: 2026-04-26 (Actualizado) ### Cambios Aplicados - FASE ACTUAL #### Backend - Tests con Credenciales Centralizadas 1. **test_auth_service.py** - Migrado a usar `TestConfig` para credenciales - Import: `from tests.test_config import TestConfig` - Passwords ahora usan `TestConfig.TEST_USER_PASSWORD` - Variable sin usar `result` eliminada en `test_upda

### EKS-SRC-01291 — EDARSA HUB - Documento de Diseño Técnico-Funcional

- Ruta: `memory/DISENO_MODULO_CATALOGOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, finanzas`

> # EDARSA HUB - Documento de Diseño Técnico-Funcional # Módulo Maestro de Catálogos del Sistema ## 1. Objetivo Implementar un módulo centralizado para la gestión de catálogos del sistema EDARSA HUB, con arquitectura reutilizable que permita: - **Acceso central** desde el menú "Catálogos" - **Acceso contextual** desde módulos nativos (RH, Compras, Finanzas, etc.) - **Sin duplicidad** de catálogos en

### EKS-SRC-01797 — Resolución canónica de la unidad -> server scope (RBAC incluido)

- Ruta: `backend/modules/catalogo/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial`

> """ CATÁLOGO CANÓNICO (CATALOGO-CANONICO-C2) ======================================== Fuente ÚNICA de la clasificación de productos para TODO el ERP (Análisis, Costos y Márgenes, Inteligencia Comercial, etc.). - 100% NO-LIVE: lee EXCLUSIVAMENTE de EDARSAHUB (Sync_Productos). NUNCA consulta los POS en vivo (a diferencia del viejo /servers/{id}/report-filters que sí lo hacía). - Jerarquía canónica u

### EKS-SRC-01281 — EDARSA HUB - Diagnóstico de Arquitectura

- Ruta: `memory/DIAGNOSTICO_ARQUITECTURA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, comercial`

> # EDARSA HUB - Diagnóstico de Arquitectura > **Documento Técnico de Evaluación** > **Fecha**: Abril 2026 > **Autor**: E1 Agent (Análisis Master) > **Estado**: DIAGNÓSTICO COMPLETO --- ## 1. Resumen Ejecutivo ### 1.1 Métricas Actuales | Componente | Valor | Evaluación | |------------|-------|------------| | **server.py (Monolito)** | 17,366 líneas | ⚠️ CRÍTICO - Muy grande | | **Endpoints totales**

### EKS-SRC-02277 — P4-07 SQL-FIRST ACCESS CONTEXT

- Ruta: `backend/core/user_access_context.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad`

> # P4-07 SQL-FIRST ACCESS CONTEXT from core.access_context.sql_context import ( build_user_access_context as build_user_access_context_sql, can_access_empresa as can_access_empresa_sql, can_access_unidad as can_access_unidad_sql, can_access_sucursal as can_access_sucursal_sql, ) from core.sql_first.connection_factory import get_edarsahub_pymssql_connection, get_external_sql_connection, get_edarsahu

### EKS-SRC-01874 — Filtro de estado: por defecto solo activos (comportamiento legacy).

- Ruta: `backend/modules/admin_sql/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Router SQL-First para Administración de Usuarios, Roles y Permisos ================================================================== ARQUITECTURA: SQL-FIRST desde EDARSAHUB_SQL TABLAS FUENTE: - Usuario_Catalogo - Usuario_Roles - Usuario_RolesAsignacion - Usuario_Modulos - Usuari

### EKS-SRC-01648 — P0: Nuevas estructuras de respuesta

- Ruta: `backend/modules/comercial/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ ╔════════════════════════════════════════════════════════════════════════════╗ ║ 🔒 MÓDULO BLINDADO - NO MODIFICAR 🔒 ║ ╠════════════════════════════════════════════════════════════════════════════╣ ║ ESTADO: FUNCIONAL Y OPERATIVO (Abril 2026) ║ ║ ║ ║ Este módulo ha sido validado y

### EKS-SRC-00426 — SQLFIRST-LEGACY-001

- Ruta: `docs/LOG_PENDIENTES_ARQUITECTURA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

> --- ## SQLFIRST-LEGACY-001 **Fecha:** 2026-06-04 **Estado:** PENDIENTE **Prioridad:** MEDIA ### Descripción Se estandarizaron los nombres de tablas sync mediante vistas de compatibilidad: | Vista Nueva | Tabla Legacy | |-------------|--------------| | `dbo.Inventario_Sync` | `dbo.Sync_Inventory` | | `dbo.Compras_Sync` | `dbo.Sync_Purchases` | ### Decisión Arquitectónica - ❌ NO eliminar tablas lega

### EKS-SRC-00121 — !/usr/bin/env python3

- Ruta: `scripts/connect_tablero_periodos.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, comercial`

> #!/usr/bin/env python3 """Conecta TableroEjecutivo con el contrato canonico de periodos. Parche determinista y de una sola ejecucion. Falla cerrado si las anclas verificadas cambiaron. No toca produccion, SQL ni archivos de entorno. """ from __future__ import annotations from pathlib import Path ROOT = Path(__file__).resolve().parents[1] TARGET = ROOT / "frontend" / "src" / "pages" / "TableroEjecu

### EKS-SRC-01338 — EDARSA Coder

- Ruta: `.github/agents/edarsa-coder.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> --- name: EDARSA Coder description: Implementador de cambios minimos en EDARSAHUB bajo evidencia previa. tools: ["search", "read", "edit", "execute"] handoffs: - label: Pasar a EDARSA Validator agent: edarsa-validator prompt: "Valida el diff, pruebas, build, DB safety, RBAC y reglas canonicas. No modifiques salvo instruccion explicita." send: false --- # EDARSA Coder Actuas como implementador cont

### EKS-SRC-01760 — ============================================================================

- Ruta: `backend/modules/catalogos/schemas.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - Catálogos Schemas ============================== Modelos Pydantic para validación de datos del módulo de catálogos. """ from pydantic import BaseModel, Field, field_validator from typing import Optional, List, Dict, Any from datetime import datetime # ===============

### EKS-SRC-01815 — ============================================================================

- Ruta: `backend/modules/crm/native_routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - CRM Enterprise Native Routes ========================================== Endpoints REST para CRM nativo (SQL Server EDARSAHUB). Prefijo: /api/crm/native Opera con arquitectura SQL-First sin dependencias externas """ from fastapi import APIRouter, HTTPException, Depend

### EKS-SRC-02338 — ============================================================================

- Ruta: `backend/core/centro_control/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `toast_netpay, sql_datos, rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService from core.sql_first.connection_factory import get_edarsahub_pymssql_connection """ CENTRO DE CONTROL EDARSA - API Routes ====================================== Módulo central de monitoreo, estabilidad, detección de regresiones y control técnico del sistema EDARSA HUB. COMPONENTES INT

### EKS-SRC-01757 — Referencia global a MongoDB (para logging/auditoría)

- Ruta: `backend/modules/catalogos/__init__.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService from typing import Any """ EDARSA HUB - Módulo de Catálogos ================================ Módulo maestro centralizado para gestión de catálogos del sistema. ARQUITECTURA: - Catálogos NO duplicados por módulo - Fuente única de verdad en EDARSA HUB (SQL Server) - Acceso central desd

### EKS-SRC-00280 — comprasUtils.js

- Ruta: `frontend/src/services/comprasUtils.js`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> /** * comprasUtils.js * * Utilidades para el módulo de Compras - ESTABILIZACIÓN MULTI-UNIDAD MULTI-TAB * * ARQUITECTURA: * - unidad_key: Identificador canónico único para aislamiento de estado * - Formato: {system_type}:{server_id}:{sucursal_origen_id}:{unidad_id} * - Control de race conditions: requestId por unidad_key y tab * * PRINCIPIOS: * - EDARSAHUB SQL es fuente primaria de configuración * 

### EKS-SRC-01216 — AUTH SECURITY MIGRATION LOG

- Ruta: `memory/auth_security_migration_log.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUTH SECURITY MIGRATION LOG ## Bitacora de Migracion - FASE AUTH-SECURITY-01 **Iniciado:** 2025-12-XX **Estado:** ARQUITECTURA DUAL IMPLEMENTADA **Ultima actualizacion:** 2025-04-27 **Responsable:** Agente de desarrollo --- ## VALIDACIÓN EN PRODUCCIÓN (2025-04-27) ### Resultados de Validación **IMPORTANTE:** La validación del 2025-04-27 demostró que las cookies httpOnly **SÍ FUNCIONAN** en el am

### EKS-SRC-01777 — Configuracion

- Ruta: `backend/modules/auth/password_reset.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> """ Password Reset Module - 100% EDARSAHUB SQL =========================================== FASE AUTH-RESET-P2: Migración completa a EDARSAHUB SQL Fecha: 2026-05-14 Autorización: Explícita ARQUITECTURA: - EDARSAHUB SQL es el cerebro del sistema - Usuario_Catalogo: usuarios, email, PasswordHashTexto - Usuario_TokensRecuperacion: tokens de reset - Usuario_RateLimitRecuperacion: rate limit por IP/emai

### EKS-SRC-02360 — Permitir importar el paquete `core` del backend

- Ruta: `backend/tools/export_edarsahub_full.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `constitucion_maximas`

> """ export_edarsahub_full.py - EDARSAHUB Exporta TODAS las tablas base de EDARSAHUB SQL a JSON y genera un ZIP descargable. Arquitectura (MÁXIMA DE ORO): - Usa la conexión canónica `core.sql_first.db` (pymssql). NO duplica conexiones ni drivers. - Solo lectura (SELECT). No modifica la base. - Escritura incremental por lotes (fetchmany) para no cargar tablas enormes en memoria. Salida: - JSON por t

### EKS-SRC-01293 — LOG: Conexiones SQL EDARSAHUB

- Ruta: `memory/conexiones_sql_edarsahub_log.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # LOG: Conexiones SQL EDARSAHUB ## CONEXIONES-SQL-EDARSAHUB-01 **Iniciado:** 2026-04-27 **Estado:** SUBFASE B COMPLETADA - DIAGNÓSTICO DE BYPASS --- ## ENTRADA 2026-04-27 15:30 UTC - DIAGNÓSTICO INICIAL ### Contexto Usuario reportó que conexiones SQL fallaban (Error 18456). Diagnóstico inicial asumió incorrectamente que credenciales en MongoDB eran inválidas. ### Corrección arquitectónica Usuario 

### EKS-SRC-01644 — P2-01 HELPER: Convierte dataclass a formato diccionario legacy

- Ruta: `backend/modules/comercial/repository.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `sql_datos, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - Comercial Module Repository ======================================== Acceso a datos para el módulo comercial. FASE 6 MIGRACIÓN SQL-FIRST (Mayo 2026): - ELIMINADA dependencia de MongoDB completamente - Todas las funciones usan EDARSAHUB SQL como única fuente - execute

### EKS-SRC-00390 — AUDITORIA_PROVEEDORES_PORTAL_01

- Ruta: `docs/AUDITORIA_PROVEEDORES_PORTAL_01.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> # AUDITORIA_PROVEEDORES_PORTAL_01 **Fecha**: 2025-12-27 **Módulo**: Portal de Proveedores **Archivo**: `/app/backend/routes/portal_proveedores.py` **Estado**: ✅ AUDITORÍA COMPLETADA - ✅ VULNERABILIDAD P0 CORREGIDA --- ## 1. ARQUITECTURA DEL PORTAL DE PROVEEDORES ### 1.1 Modelo de Autenticación Dual (CORRECTO) El Portal de Proveedores implementa **DOS sistemas de autenticación completamente separad

### EKS-SRC-00340 — DIAGNÓSTICO INTEGRAL RBAC Y MODELO UNIDAD DE NEGOCIO

- Ruta: `docs/DIAGNOSTICO_RBAC_UNIDAD_NEGOCIO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial, finanzas, roadmap_aceptacion`

> # DIAGNÓSTICO INTEGRAL RBAC Y MODELO UNIDAD DE NEGOCIO ## EDARSA HUB - Arquitectura de Contexto por Usuario **Fecha**: 2026-04-20 **Versión**: 1.0 **Autor**: Arquitecto de Software Senior --- ## 1. DIAGNÓSTICO DE RBAC Y CONTEXTO ### 1.1 MODELO ACTUAL ``` USUARIO ├── empresas_permitidas: [lista de IDs de empresas] ├── role: "Administrador" | "Usuario" | etc. ├── allowed_servers: [lista legacy - dep

### EKS-SRC-00438 — PROTOCOLO GLOBAL DE CAMBIOS - EDARSA HUB

- Ruta: `docs/PROTOCOLO_GLOBAL_CAMBIOS_EDARSA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # PROTOCOLO GLOBAL DE CAMBIOS - EDARSA HUB ## Gobernanza Técnica y Control de Regresiones ## Versión: 1.0.0 ## Fecha: 2026-04-19 --- # ⚠️ REGLA PRINCIPAL ``` ╔═══════════════════════════════════════════════════════════════════════════════╗ ║ ║ ║ "LO QUE YA FUNCIONA, NO SE ROMPE" ║ ║ ║ ║ Todo cambio en EDARSA HUB debe ser: ║ ║ - Controlado ║ ║ - Acotado ║ ║ - Probado ║ ║ - Documentado ║ ║ ║ ╚══════

### EKS-SRC-01783 — __init__.py

- Ruta: `backend/modules/comercial_v2/__init__.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial`

> """Modulo Comercial V2 conectado a la fuente canonica EDARSAHUB. Expone un router agregado para conservar las rutas existentes e incorporar el contrato dinamico de periodos sin duplicar prefijos ni fuentes de datos. Los routers se importan de forma diferida dentro de ``get_comercial_v2_router``. Esto evita que importar funciones puras del paquete durante pruebas unitarias active configuracion SQL,

### EKS-SRC-00479 — CODE QUALITY STABILIZATION AUDIT

- Ruta: `docs/CODE_QUALITY_STABILIZATION_AUDIT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # CODE QUALITY STABILIZATION AUDIT ## EDARSA HUB - Fase de Estabilización Quirúrgica **Fecha:** 2025-12-XX **Commit Base:** ac45d98 **Rama:** stabilize/code-quality-critical-fixes **Autor:** Arquitecto Senior FullStack **Estado Final:** ✅ COMPLETADO --- ## 1. RESUMEN EJECUTIVO La fase de estabilización quirúrgica ha sido **COMPLETADA EXITOSAMENTE**. La auditoría revela que la mayoría de los ítems 

### EKS-SRC-01721 — ============================================================================

- Ruta: `backend/modules/api_connections/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `conectores_universales, rbac_seguridad, ia_agentes, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Rutas de Conexiones API Locales =============================== Endpoints REST para gestionar conexiones a APIs locales. ARQUITECTURA: - Todas las operaciones CRUD van a EDARSAHUB SQL (fuente primaria) - MongoDB solo se usa como caché/log (no autoritativo) - Errores de EDARSAHUB 

### EKS-SRC-01871 — Ejecutar script de auditoría

- Ruta: `backend/modules/sqlfirst_health/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - SQL-First Health Endpoint ====================================== Audita en tiempo real el cumplimiento de la arquitectura SQL-First. """ from fastapi import APIRouter from pathlib import Path import json import subprocess import sys from typing import Dict, Any route

### EKS-SRC-00369 — ARQUITECTURA DE SEGURIDAD EDARSA HUB

- Ruta: `docs/ARQUITECTURA_SEGURIDAD_EDARSA_HUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # ARQUITECTURA DE SEGURIDAD EDARSA HUB ## Diagnóstico, Diseño y Plan de Migración **Versión:** 1.0 **Fecha:** Diciembre 2025 **Autor:** Arquitecto de Software Senior **Estado:** PENDIENTE APROBACIÓN --- ## TABLA DE CONTENIDOS 1. [Diagnóstico del Sistema Actual](#1-diagnóstico-del-sistema-actual) 2. [Gap Analysis](#2-gap-analysis) 3. [Modelo Objetivo (Diseño)](#3-modelo-objetivo-diseño) 4. [Plan de

### EKS-SRC-00308 — AUDITORÍA DE FUENTES DE DATOS EDARSAHUB

- Ruta: `docs/AUDITORIA_FUENTES_DATOS_EDARSAHUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUDITORÍA DE FUENTES DE DATOS EDARSAHUB **Fecha:** 8 de Mayo 2026 **Autor:** Arquitectura de Sistemas **Versión:** 1.0 - DIAGNÓSTICO **Estado:** SOLO LECTURA - NO SE HAN REALIZADO CAMBIOS --- ## 1. RESUMEN EJECUTIVO Se realizó una auditoría completa del sistema EDARSAHUB para mapear las fuentes de datos reales por módulo. El diagnóstico revela: | Métrica | Valor | |---------|-------| | **Tablas 

### EKS-SRC-00389 — EDARSAHUB - MÁXIMAS INQUEBRANTABLES

- Ruta: `docs/EDARSAHUB_MAXIMAS_INQUEBRANTABLES.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial`

> # EDARSAHUB - MÁXIMAS INQUEBRANTABLES ## Documento de Arquitectura y Políticas Fundamentales **Versión:** 1.0 **Fecha:** 2026-06-02 **Estado:** VIGENTE - CUMPLIMIENTO OBLIGATORIO --- ## 🏛️ ARQUITECTURA CANÓNICA (OBLIGATORIA) ``` ┌─────────────────────────────────────────────────────────────────┐ │ FUENTES EXTERNAS │ │ SoftRestaurant / MPRO / NetPay │ └──────────────────────────────────────────────

### EKS-SRC-00307 — P0-AUTH-COOKIE-FRONTEND-01 — Reporte de Diagnóstico y Corrección

- Ruta: `docs/P0_AUTH_COOKIE_FRONTEND_01_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay, rbac_seguridad, comercial`

> # P0-AUTH-COOKIE-FRONTEND-01 — Reporte de Diagnóstico y Corrección **Código:** P0-AUTH-COOKIE-FRONTEND-01 **Fecha:** 2025-12-27 **Estado:** RESUELTO CON OBSERVACIONES --- ## 1. Resumen Ejecutivo El Tablero Ejecutivo mostraba **$0** en todos los KPIs debido a un problema de autenticación. Se diagnosticó que el proxy de infraestructura (Kubernetes/Cloudflare) sobrescribe los headers CORS con `Access

### EKS-SRC-00429 — QA POST AUTH 01 - VALIDATION REPORT

- Ruta: `docs/QA_POST_AUTH_01_VALIDATION_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # QA POST AUTH 01 - VALIDATION REPORT ## Validación General Post AUTH-SECURITY-01 y P0-CENTROCONTROL-01 **Fecha:** 2025-12-27 **Última actualización:** 2025-04-27 **Estado:** ✅ COMPLETADO - HALLAZGOS RESUELTOS **Contexto:** Post AUTH-SECURITY-01 (arquitectura dual), P0-CENTROCONTROL-01 (funciones CentroControl) y P1-FETCH-MIGRATION --- ## 1. RESUMEN EJECUTIVO | Categoría | Estado | |-----------|--

### EKS-SRC-01625 — Importar db desde server.py (motor async client)

- Ruta: `backend/modules/comercial/cache_service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `sql_datos, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Servicio Central de Cache para Módulo Comercial =============================================== Implementa cache controlado con las siguientes reglas: - Cache NO es fuente de verdad - Siempre intentar primero la fuente real SQL/API - Solo usar cache como fallback si la fuente fal

### EKS-SRC-01843 — comprobaciones.py

- Ruta: `backend/modules/finanzas/comprobaciones.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, sql_datos, rbac_seguridad, finanzas`

> """ EDARSA HUB - Comprobaciones financieras ======================================= V1.0: lectura SQL-first no-live desde tablas canonicas EDARSAHUB. - CFDI vive en Compras_DocumentosFiscales / Detalle. - Comprobaciones agregan contexto financiero, no duplican facturas. - Sin MongoDB, sin SAT live y sin lectura directa de carpetas desde pantallas. """ from __future__ import annotations from typing

### EKS-SRC-00303 — CENTRO DE CONTROL EDARSA

- Ruta: `docs/CENTRO_DE_CONTROL_EDARSA_WIREFRAME.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # CENTRO DE CONTROL EDARSA ## Wireframe Funcional Completo **Versión:** 1.0.0 **Fecha:** 2026-04-19 **Autor:** Arquitectura UX/UI EDARSA HUB **Tipo:** Documento de Diseño - Wireframe Funcional **Estado:** APROBADO PARA IMPLEMENTACIÓN --- ## ÍNDICE 1. [Visión General](#1-visión-general) 2. [Principios de Diseño](#2-principios-de-diseño) 3. [Arquitectura de Navegación](#3-arquitectura-de-navegación)

### EKS-SRC-00512 — Navegación Enterprise EDARSAHUB

- Ruta: `docs/arquitectura/NAVEGACION_ENTERPRISE.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial, finanzas`

> # Navegación Enterprise EDARSAHUB ## Fuente canónica - SQL define módulos, menús, rutas y RBAC. - El registro Enterprise define su clasificación funcional. - React representa el catálogo autorizado. - La ruta canónica identifica los favoritos. - No existe fallback al menú clásico. ## Grupos 1. Dirección e Inteligencia 2. Comercial y Clientes 3. Operaciones y Abasto 4. Finanzas y Rentabilidad 5. Pe

### EKS-SRC-00753 — FASE 3-E: Migración de context_service.py a EDARSAHUB SQL

- Ruta: `docs/reports/FASE3E_CONTEXT_SERVICE_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial, finanzas`

> # FASE 3-E: Migración de context_service.py a EDARSAHUB SQL **Fecha:** 2026-05-14 **Fase:** FASE 3-E **Estado:** COMPLETADA **Autor:** Agente E1 **Régimen:** Autorización Controlada --- ## 1. Objetivo Migrar el módulo `context_service.py` para que el contexto de navegación/UI deje de depender productivamente de MongoDB y use EDARSAHUB SQL como fuente. --- ## 2. Funciones Modificadas | Función | Pr

### EKS-SRC-01294 — DIAGNÓSTICO DE ARQUITECTURA DE CONECTIVIDAD - EDARSA HUB

- Ruta: `memory/ARQUITECTURA_CONECTIVIDAD_EDARSA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial`

> # DIAGNÓSTICO DE ARQUITECTURA DE CONECTIVIDAD - EDARSA HUB **Fecha:** 2026-04-23 **Autor:** E1 Agent (Rol: Arquitecto de Soluciones) **Versión:** 1.1 **Estado:** ✅ APROBADO POR USUARIO --- ## 0. DECISIONES APROBADAS ### Arquitectura Definitiva: AGENTES PUSH (Escenario C) ``` SQL local → Agente local → Push seguro HTTPS → EDARSA HUB → KPIs/tableros ``` ### Aclaraciones Conceptuales (por usuario): -

### EKS-SRC-01270 — Diagnóstico de Catálogos - EDARSA HUB

- Ruta: `memory/DIAGNOSTICO_CATALOGOS_EDARSA_HUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> # Diagnóstico de Catálogos - EDARSA HUB ## Resumen Ejecutivo **Fecha:** Diciembre 2025 **Base de datos:** EDARSAHUB (SQL Server) **Total tablas:** 164 **Tablas de catálogos identificadas:** 47 --- ## 1. Inventario de Catálogos Existentes ### 1.1 Catálogos de RH (19 tablas) | Tabla | Registros | Estado | Clasificación | Acción Recomendada | |-------|-----------|--------|---------------|------------

### EKS-SRC-01305 — FASE T3.3 — Reporte de Migración: 2 Endpoints Compras de Riesgo ALTO

- Ruta: `memory/FASE_T3_3_REPORTE_ENDPOINTS_ALTO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> # FASE T3.3 — Reporte de Migración: 2 Endpoints Compras de Riesgo ALTO ## Eliminación de MongoDB `db.servers` en Endpoints de Riesgo Alto **Fecha:** 14-Mayo-2026 **Estado:** COMPLETADO **Autorizado por:** Usuario (AUTORIZACIÓN CONTROLADA) --- ## 1. Archivo Modificado - `/app/backend/server.py` --- ## 2. Endpoints Modificados | # | Endpoint | Línea | Función server_registry | |---|----------|------

### EKS-SRC-01210 — PLAN DE VALIDACIÓN DE PARIDAD NUMÉRICA

- Ruta: `memory/PLAN_VALIDACION_PARIDAD_NUMERICA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `comercial, roadmap_aceptacion`

> # PLAN DE VALIDACIÓN DE PARIDAD NUMÉRICA ## Riesgos R1, R3, R4 **Versión**: 1.0 **Fecha**: 2026-04-23 **Estado**: PLAN EJECUTABLE (pendiente de ambiente con conectividad) **Autor**: Arquitectura Senior --- ## 1. RESUMEN EJECUTIVO Este documento define el plan para validar que el código refactorizado produce **exactamente los mismos resultados numéricos** que el código original cuando se ejecuta co

### EKS-SRC-02292 — MACROFASE 2: Jobs de sincronización KPIs

- Ruta: `backend/core/scheduler/scheduler_manager.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay, rbac_seguridad, ia_agentes, comercial, finanzas`

> """ EDARSA HUB - Scheduler Manager ============================== Manager central para el scheduler de jobs. Responsabilidades: - Registrar jobs - Iniciar/detener scheduler - Controlar ciclo de vida con FastAPI - Evitar registros duplicados """ import asyncio from typing import Optional, Dict, Any import logging from datetime import datetime, timedelta, timezone from apscheduler.schedulers.asyncio

### EKS-SRC-01719 — __init__.py

- Ruta: `backend/modules/api_connections/__init__.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `conectores_universales, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Módulo de Conexiones API Locales ================================ Gestiona conexiones a APIs locales (MPRO, etc.) para obtener ventas del día en tiempo real desde servidores locales. ARQUITECTURA: - Fuente primaria: EDARSAHUB SQL (Servidores_Conexiones con tipo_conexion='API_LOCA

### EKS-SRC-00463 — AUTH_HTTPONLY_COOKIE_MIGRATION_PLAN

- Ruta: `docs/AUTH_HTTPONLY_COOKIE_MIGRATION_PLAN.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

> # AUTH_HTTPONLY_COOKIE_MIGRATION_PLAN ## FASE AUTH-SECURITY-01 - Migracion de Autenticacion a httpOnly Cookies **Fecha:** 2025-12-XX **Estado:** PLAN TECNICO (No implementado) **Objetivo:** Eliminar almacenamiento de JWT en sessionStorage/localStorage y mover sesion a cookies httpOnly Secure SameSite. --- ## 1. AUDITORIA DEL FLUJO ACTUAL ### 1.1 Arquitectura de Autenticacion Actual ``` ┌──────────

### EKS-SRC-00818 — FASE 3-C: Migración de context_resolver.py a EDARSAHUB SQL

- Ruta: `docs/reports/FASE3C_CONTEXT_RESOLVER_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial, finanzas`

> # FASE 3-C: Migración de context_resolver.py a EDARSAHUB SQL **Fecha:** 2026-05-14 **Fase:** FASE 3-C **Estado:** COMPLETADA **Autor:** Agente E1 **Régimen:** Autorización Controlada --- ## 1. Objetivo Migrar el módulo `context_resolver.py` para que lea empresas, sucursales, mapeos y servidores desde EDARSAHUB SQL en lugar de MongoDB. --- ## 2. Funciones Modificadas | Función | Propósito | Cambio 

### EKS-SRC-01838 — Códigos canónicos producidos por AuthRepository desde dbo.Usuario_Roles.

- Ruta: `backend/modules/finanzas/tesoreria_access.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, finanzas`

> """Alcance RBAC fail-closed para Finanzas / Tesorería / Cortes Z.""" from __future__ import annotations from dataclasses import dataclass import logging from typing import Any, Dict, Iterable, Mapping from fastapi import HTTPException, status from core.rbac_sql.service import RBACSQLService from core.sql_first.db import fetch_all_dict_readonly from core.system_type_utils import normalize_system_ty

### EKS-SRC-01799 — ============================================================================

- Ruta: `backend/modules/sync_recetas/sync_recetas.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos`

> """ Sync Recetas - Job de sincronización de productos, recetas, insumos y costos. FASE 1C-3B - Costos y Márgenes ARQUITECTURA NO-LIVE: - Este job es el ÚNICO componente autorizado para conectarse a fuentes remotas. - Los endpoints y frontend SOLO leen de EDARSAHUB SQL. - NO usar explosioninsumosdetalle como fuente (vacía en SoftRestaurant). - USAR tabla 'costos' para recetas de productos. - USAR t

### EKS-SRC-00417 — AUDITORIA-RH-NOMINAS-01 / SUBFASE A — VALIDACIÓN DE FUENTE Y BLOQUEO

- Ruta: `docs/AUDITORIA_RH_NOMINAS_FUENTE_DATOS_01.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> # AUDITORIA-RH-NOMINAS-01 / SUBFASE A — VALIDACIÓN DE FUENTE Y BLOQUEO **Código:** AUDITORIA-RH-NOMINAS-FUENTE-DATOS-01 **Fecha:** 2025-12-27 **Módulo:** RH / Nóminas **Estado:** ⚠️ FALLA DE ARQUITECTURA DETECTADA --- ## Resumen Ejecutivo El módulo RH/Nóminas está bloqueado porque depende de un registro de servidor en MongoDB (`servers`) con `active=True`, cuando debería usar la **conexión interna

### EKS-SRC-01720 — Configuración de EDARSAHUB SQL - FUENTE PRIMARIA

- Ruta: `backend/modules/api_connections/repository.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `conectores_universales, rbac_seguridad, ia_agentes, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repositorio de Conexiones API Locales ===================================== ARQUITECTURA: - Fuente primaria de verdad: EDARSAHUB SQL (tabla Servidores_Conexiones) - MongoDB: Solo caché/log/estado auxiliar (NO autoritativo) - Sincronización: EDARSAHUB SQL → MongoDB (nunca al revés

### EKS-SRC-01619 — routes.py

- Ruta: `backend/modules/dashboard_ejecutivo/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService from fastapi import APIRouter, Depends, Query from core.security import get_current_user from core.config.edarsahub_sql import get_edarsahub_connection from core.sql_first.db import get_sql_connection from core.kpis_canonicos import KPIsCanonicosService from datetime import datetime,

### EKS-SRC-00673 — FASE B-P2-B + DDL COMERCIAL: Migración Completa y Diseño Tablas Sync

- Ruta: `docs/reports/FASE_B_P2_B_DDL_COMERCIAL_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # FASE B-P2-B + DDL COMERCIAL: Migración Completa y Diseño Tablas Sync **Fecha:** 2025-05-26 **Estado:** ✅ COMPLETADO --- ## 1. FASE B-P2-B: Migración automatizacion_compras_service.py ### Objetivo Migrar el último servicio con dependencias MongoDB (`automatizacion_compras_service.py`) a SQL Server EDARSAHUB. ### Antes (MongoDB) - 5 referencias a `self.db.*` - 13 referencias a `.collection` - 3 co

### EKS-SRC-01279 — FASE T3.2 — Reporte de Migración: 4 Endpoints Compras en server.py

- Ruta: `memory/FASE_T3_2_REPORTE_ENDPOINTS_COMPRAS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # FASE T3.2 — Reporte de Migración: 4 Endpoints Compras en server.py ## Eliminación de MongoDB `db.servers` en Endpoints de Riesgo Bajo/Medio **Fecha:** 14-Mayo-2026 **Estado:** COMPLETADO **Autorizado por:** Usuario (AUTORIZACIÓN CONTROLADA) --- ## 1. Archivo Modificado - `/app/backend/server.py` --- ## 2. Endpoints Modificados | # | Endpoint | Línea | Función server_registry | |---|----------|--

### EKS-SRC-02628 — EDARSAHUB V1.0 — Agent Operating Protocol

- Ruta: `.agent-worktrees/compras-inventarios/AGENTS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # EDARSAHUB V1.0 — Agent Operating Protocol ## Prioridad de herramientas Prioridad operativa: 1. Antigravity 2. Codex 3. VS Code custom agents 4. Claude minimizado No usar `.claude/agents` como fuente principal de configuración. Excepción permitida: únicamente `.claude/agents/edarsa-claude-haiku-auditor.md` como auditor Claude Haiku de solo lectura, uso excepcional y bajo autorización explícita. #

### EKS-SRC-02031 — Comportamiento legacy preservado: aguas abajo dará 404 "Servidor no encontrado".

- Ruta: `backend/tests/test_compras_canonical_unidad.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, sql_datos`

> """ Regresión P0 (2026-06): migración de endpoints de Compras al contrato canónico `unidad`. Valida la "puerta única" `canonical_server_id(token)` que traduce una unidad canónica (codigo o pk) al server_id real del POS y preserva la compatibilidad legacy. NO-LIVE: solo lee el catálogo canónico (dbo.Unidades_Negocio vía UnidadesService), nunca conecta a POS. """ import os from dotenv import load_do

### EKS-SRC-00402 — FASE 3B.2 — Validación Real de Escritura SQL-First y Reconciliación

- Ruta: `docs/FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, comercial, roadmap_aceptacion`

> # FASE 3B.2 — Validación Real de Escritura SQL-First y Reconciliación **Fecha:** 2026-04-25 **Autor:** E1 Agent **Estado:** COMPLETADA --- ## 1. RESUMEN EJECUTIVO La FASE 3B.2 valida que los endpoints de escritura (`POST`, `PUT`, `DELETE`) de servidores funcionan correctamente con la arquitectura **SQL-first** implementada en FASE 3B.1. ### Resultados | Prueba | Resultado Esperado | Resultado Obte

### EKS-SRC-00946 — FASE 3-D: Migración de user_access_context.py a EDARSAHUB SQL

- Ruta: `docs/reports/FASE3D_USER_ACCESS_CONTEXT_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial, finanzas`

> # FASE 3-D: Migración de user_access_context.py a EDARSAHUB SQL **Fecha:** 2026-05-14 **Fase:** FASE 3-D **Estado:** COMPLETADA **Autor:** Agente E1 **Régimen:** Autorización Controlada --- ## 1. Objetivo Migrar el módulo `user_access_context.py` para que el acceso efectivo del usuario se resuelva desde EDARSAHUB SQL en lugar de MongoDB. --- ## 2. Funciones Modificadas | Función | Propósito | Camb

### EKS-SRC-01791 — periodos_routes.py

- Ruta: `backend/modules/comercial_v2/periodos_routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `contratos_canonicos, rbac_seguridad, comercial`

> """Contrato dinamico de periodos para los tableros comerciales. Conecta las reglas puras de :mod:`periodos` con la vista canonica de KPIs. El router es solo lectura, respeta RBAC y no consulta fuentes LIVE ni MongoDB. """ from __future__ import annotations from dataclasses import asdict from datetime import date, timedelta from statistics import mean from typing import Any, Iterable, Optional from

### EKS-SRC-00435 — AUTH SECURITY - COMPATIBILIDAD POR AMBIENTE

- Ruta: `docs/AUTH_SECURITY_ENVIRONMENT_COMPATIBILITY.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad`

> # AUTH SECURITY - COMPATIBILIDAD POR AMBIENTE ## FASE AUTH-SECURITY-01 - Arquitectura Dual por Ambiente **Fecha:** 2025-12-27 **Estado:** DOCUMENTADO **Propósito:** Documentar las diferencias de comportamiento de autenticación entre ambientes de Preview y Producción. --- ## 1. RESUMEN EJECUTIVO AUTH-SECURITY-01 implementa una **arquitectura dual por ambiente**: | Ambiente | Mecanismo Principal | M

### EKS-SRC-00508 — Máxima de Oro — Cambios Atómicos y Base Estable

- Ruta: `docs/operacion/MODO_TRABAJO_CAMBIOS_ATOMICOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos, comercial, finanzas`

> # Máxima de Oro — Cambios Atómicos y Base Estable **Proyecto:** EDARSAHUB **Vigencia:** permanente **Prioridad:** máxima arquitectónica y operativa ## 1. Principio central EDARSAHUB se desarrolla mediante cambios pequeños, aislados, reversibles, verificables y asociados a un único objetivo funcional. Queda prohibido mezclar en un mismo bloque de trabajo cambios de Comercial, Finanzas, Auth, Schedu

### EKS-SRC-00908 — FASE B-P0-C: Migración base_repository.py a EDARSAHUB SQL

- Ruta: `docs/reports/FASE_B_P0_C_BASE_REPOSITORY_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> # FASE B-P0-C: Migración base_repository.py a EDARSAHUB SQL **Fecha:** 26 Mayo 2026 **Módulo:** `/app/backend/modules/fase2_operativo/repositories/` **Objetivo:** Migrar el repositorio base de fase2_operativo de MongoDB a SQL Server --- ## 1. ESTADO ANTERIOR ### Archivo: `base_repository.py` (Original) - **Líneas:** 164 - **Dependencias MongoDB:** - `from bson import ObjectId` - `self.collection =

### EKS-SRC-00874 — DECISIÓN EJECUTIVA RBAC - EDARSAHUB

- Ruta: `docs/reports/DECISION_EJECUTIVA_RBAC_20260602.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # DECISIÓN EJECUTIVA RBAC - EDARSAHUB **Fecha**: 2026-06-02 **Estado**: APROBADO --- ## 1. Arquitectura RBAC Definitiva ### RBAC Canónico: `Usuario_*` | Tabla | Propósito | Registros | |-------|-----------|-----------| | `Usuario_Modulos` | Catálogo de módulos del sistema | 59 | | `Usuario_Roles` | Catálogo de roles | 16 | | `Usuario_Acciones` | Catálogo de acciones | 16 | | `Usuario_PermisosRolMo

### EKS-SRC-01259 — PLAN DE MIGRACIÓN: Conexiones de Servidores

- Ruta: `memory/PLAN_MIGRACION_CONEXIONES_MONGODB_A_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # PLAN DE MIGRACIÓN: Conexiones de Servidores ## De MongoDB a EDARSAHUB (SQL Server) **Versión**: 2.0 **Fecha**: 2026-04-23 (Actualizado: 2026-04-24) **Estado**: FASE 2/3 COMPLETADA **Prioridad**: CRÍTICA - Sistema en producción --- ## RESUMEN EJECUTIVO DE PROGRESO | Fase | Estado | Fecha | |------|--------|-------| | **FASE 0** | ✅ COMPLETADA | 2026-04-23 | | **FASE 1** | ✅ COMPLETADA | 2026-04-2

### EKS-SRC-02319 — Centinela: unidad sin acceso / no resuelta -> resultados vacíos (nunca expone datos)

- Ruta: `backend/core/corporate_filters/request_resolver.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad`

> """ Resolvedor canónico de UNIDAD para tableros (Operaciones / Inventarios). ======================================================================== P0 (2026-06): "puerta única" de resolución. CONTRATO: - El frontend envía SOLO la unidad canónica (unidad_codigo o id). - El frontend NO resuelve server_id. - Este módulo: 1. Valida el permiso del usuario reutilizando el RBAC EXISTENTE (empresas_perm

### EKS-SRC-00442 — P0 REGRESIÓN CRÍTICA - Corrección: Servidores SQL Restaurados

- Ruta: `docs/P0_REGRESION_SQL_SERVERS_CORRECCION_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `conectores_universales, comercial`

> # P0 REGRESIÓN CRÍTICA - Corrección: Servidores SQL Restaurados ## Fecha: 2026-04-29 ## Problema Reportado Los servidores SQL desaparecieron de la UI después de implementar Conexiones API flexibles. ## Causa Raíz El endpoint `/api/servers` estaba retornando TODOS los registros de `Servidores_Conexiones`, incluyendo los de tipo `API_LOCAL`. Los registros `API_LOCAL` tienen campos NULL que el modelo

### EKS-SRC-01202 — Variable de configuración para tu cadena de conexión SQL Server / Azure SQL

- Ruta: `docs/snippets/endpoint_ventas_tiempo_referencia.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, comercial`

> """ ENDPOINT VENTAS-TIEMPO CON ALTA DISPONIBILIDAD (SQL-First + Fallback Senoidal) PROYECTO: EDARSA HUB ERP """ import math import random from datetime import datetime from fastapi import APIRouter, HTTPException, Depends from typing import Dict, Any, List import pyodbc # O la librería de conexión que utilicen (SQLAlchemy / databases) router = APIRouter() # Variable de configuración para tu cadena

### EKS-SRC-01984 — Evita ejecutar modules/comercial_v2/__init__.py, que importa rutas,

- Ruta: `backend/tests/test_mpro_fecha_operacion_contract.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, comercial`

> from datetime import date, datetime, timedelta import importlib from pathlib import Path import sys import types BACKEND_ROOT = Path(__file__).resolve().parents[1] COMERCIAL_V2_ROOT = BACKEND_ROOT / "modules" / "comercial_v2" # Evita ejecutar modules/comercial_v2/__init__.py, que importa rutas, # seguridad y configuración SQL ajenas a esta prueba unitaria. package = types.ModuleType("modules.comer

### EKS-SRC-00585 — FASE B-P1-A: Migración workflow_repository.py a SQL Explícito

- Ruta: `docs/reports/FASE_B_P1_A_WORKFLOW_REPOSITORY_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> # FASE B-P1-A: Migración workflow_repository.py a SQL Explícito **Fecha:** 26 Mayo 2026 **Archivo:** `/app/backend/modules/fase2_operativo/repositories/workflow_repository.py` **Tabla SQL:** `Workflow_Inventarios` --- ## 1. ESTADO ANTERIOR ### Dependencias MongoDB: ```python from pymongo import DESCENDING ``` ### Métodos con código MongoDB: | Método | Código MongoDB | |--------|---------------| | 

### EKS-SRC-00775 — MATRIZ DE CANONICIDAD - TABLAS EDARSAHUB

- Ruta: `docs/reports/MATRIZ_CANONICIDAD_TABLAS_EDARSAHUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # MATRIZ DE CANONICIDAD - TABLAS EDARSAHUB **Generado:** 2026-06-02T10:04:26.298025 **Estado:** ANÁLISIS - NO MODIFICAR ESTRUCTURA --- ## 1. CLASIFICACIÓN GENERAL DE TABLAS ### Resumen por Clasificación | Clasificación | Tablas | Registros | Descripción | |---------------|--------|-----------|-------------| | CANONICA | 48 | 74,163 | Fuente de verdad única | | SINCRONIZADA | 31 | 42,845 | Datos de

### EKS-SRC-00708 — Backfill Opción A — COMPLETADO (detalle ticket/producto a Sync_Sales)

- Ruta: `docs/reports/BACKFILL_OPCION_A_COMPLETADO_20260608.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, comercial, finanzas`

> # Backfill Opción A — COMPLETADO (detalle ticket/producto a Sync_Sales) **Fecha:** 2026-06-08 **Autorización:** Usuario autorizó Opción A (lectura POS en vivo) + escalado por tandas + desbloqueo CIENFUEGOS/MPRO. **Regla protegida (cumplida):** NO se tocó/re-derivó `Comercial_KPIs_Diarios_v2` ni `vw_*`. Solo `Sync_Sales`. ## Resultado final — Sync_Sales (de 79 → 112,313 tickets) | Unidad | Sistema 

### EKS-SRC-01113 — EDARSAHUB V1.2 - Deuda tecnica de conexiones SQL

- Ruta: `docs/technical-debt/EDARSAHUB_V1_2_SQL_CONNECTIONS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

> # EDARSAHUB V1.2 - Deuda tecnica de conexiones SQL ## Contexto EDARSAHUB V1.0 adopta una normalizacion incremental de conexiones para mantener el sistema operativo y reducir el riesgo de regresion. La base V1.0 incluye: - configuracion SQL lazy; - variables EDARSAHUB_SQL_* canonicas; - adaptador central de drivers; - fachada SQL-first compatible; - validacion fail-closed de HRLectura; - validacion

### EKS-SRC-01708 — RBAC - Fase 3.1

- Ruta: `backend/modules/fase2_operativo/routes/tarea_routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, rbac_seguridad`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Endpoints de Tareas CAB-003 | EDARSA HUB - Fase 2A PROTEGIDO CON RBAC (Fase 3.1) Expone la funcionalidad de tareas vía HTTP. Permisos: - Todos los endpoints requieren autenticación """ from fastapi import APIRouter, HTTPException, Query, Depends from typing import Optional, Dict,

### EKS-SRC-00357 — Corrección Arquitectónica: Conexiones API

- Ruta: `docs/API_CONNECTIONS_ARCHITECTURE_CORRECTION_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `conectores_universales, rbac_seguridad, comercial`

> # Corrección Arquitectónica: Conexiones API ## Fecha: 2026-04-29 ## Resumen Se corrigió la arquitectura del módulo de conexiones API para que EDARSAHUB SQL sea la fuente primaria de verdad. ## Arquitectura Implementada ### Fuente Primaria (Autoritativa) - **EDARSAHUB SQL** (tabla `Servidores_Conexiones`) - Todas las operaciones CRUD van primero a SQL - Si SQL falla, la operación falla completament

### EKS-SRC-00728 — FASE 1C-3E - Validación Integral, RBAC, Seguridad y Exportación

- Ruta: `docs/reports/FASE_1C_3E_VALIDACION_RBAC_EXPORTACION.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, comercial`

> # FASE 1C-3E - Validación Integral, RBAC, Seguridad y Exportación ## Resumen Ejecutivo **Fecha**: 24 Mayo 2026 **Estado**: ✅ COMPLETADO Se completó la validación integral del módulo Costos y Márgenes, incluyendo implementación de RBAC, verificaciones de seguridad y funcionalidad de exportación CSV. --- ## 1. RBAC Implementado ### Permisos Configurados | Endpoint | Permiso Requerido | Roles Permiti

### EKS-SRC-02334 — edarsahub_writer_connection.py

- Ruta: `backend/core/connections/edarsahub_writer_connection.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos`

> from __future__ import annotations from dataclasses import dataclass from core.config.edarsahub_config import ( EdarsaHubSQLConfig, get_edarsahub_sql_config, ) from core.sql_first.connection_factory import ( get_edarsahub_pymssql_connection, ) CANONICAL_PROFILE = "default" EXPECTED_DATABASE = "EDARSAHUB" EXPECTED_LOGIN = "HRLectura" EXPECTED_USER = "HRLectura" @dataclass(frozen=True) class SQLWrit

### EKS-SRC-00478 — ADENDA TÉCNICA: Definiciones Críticas de Automatización

- Ruta: `docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_A.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> # ADENDA TÉCNICA: Definiciones Críticas de Automatización ## EDARSA HUB - CAB-003 - Adenda A **Versión**: 1.1 **Fecha**: Diciembre 2025 **Estado**: DEFINICIONES TÉCNICAS FINALES **Requisito**: Aprobación obligatoria antes de implementación --- ## ÍNDICE DE DEFINICIONES CRÍTICAS 1. [Core Service de Análisis de Inventarios](#1-core-service-de-análisis-de-inventarios) 2. [Clave Única del Proceso (Ide

### EKS-SRC-00423 — ADENDA TÉCNICA B: Ajustes Finales Obligatorios

- Ruta: `docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_ADENDA_B.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

> # ADENDA TÉCNICA B: Ajustes Finales Obligatorios ## EDARSA HUB - CAB-003 - Adenda B **Versión**: 1.2 **Fecha**: Diciembre 2025 **Estado**: AJUSTES FINALES APROBADOS **Referencia**: Correcciones a Adenda A por solicitud del Product Owner --- ## AJUSTES REQUERIDOS | # | Punto | Estado Anterior | Ajuste Requerido | |---|-------|-----------------|------------------| | 1 | Clave Única | Sin `sistema_or

### EKS-SRC-02302 — 1. Calcular la fecha objetivo de vencimiento en base a los días de anticipación

- Ruta: `backend/core/scheduler/jobs/renovaciones_scheduler_job.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> from datetime import datetime, timedelta from core.pool import execute_hub_query from core.communications.dispatcher import dispatch_notification def ejecutar_escaneo_renovaciones_job(dias_anticipacion: int = 30): """ COSTOS-ALERTAS-001-G: Job automático para el Workflow de Renovaciones. Busca contratos o servicios comerciales recurrentes en el CRM próximos a vencer y despacha alertas preventivas 

### EKS-SRC-01734 — hospitality_rules.py

- Ruta: `backend/modules/hospitality/services/hospitality_rules.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `hospitality`

> """ Reglas base EDARSAHUB Hospitality. No contiene lógica operativa todavía. """ HOSPITALITY_MAXIMAS = [ "NO_ROMPER", "NO_MONGO", "NO_LIVE_OPERATIVO", "SQL_FIRST", "NO_DUPLICAR", "UNIDAD_NEGOCIO_PK", "RBAC_EXISTENTE", "FILTROS_CORPORATIVOS", "SCHEDULER_EXISTENTE", "NOTIFICACIONES_EXISTENTES", "COMANDERO_EXISTENTE", "MULTIDIOMA_GLOBAL", "MULTICONECTIVIDAD", "AUTOMATIZACION_SEGURA", ]

### EKS-SRC-00403 — AUTH SECURITY PHASE 4.2 - DEPRECATED REMOVAL REPORT

- Ruta: `docs/AUTH_SECURITY_PHASE_4_2_DEPRECATED_REMOVAL_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, comercial, finanzas`

> # AUTH SECURITY PHASE 4.2 - DEPRECATED REMOVAL REPORT ## FASE AUTH-SECURITY-01 / FASE 4.2 - Eliminación de Funciones Deprecated **Fecha:** 2025-12-27 **Estado:** COMPLETADO **Responsable:** Agente de desarrollo --- ## 1. RESUMEN EJECUTIVO La **Fase 4.2** eliminó todas las funciones legacy de autenticación JWT del frontend. El código fuente queda limpio de funciones que manipulaban tokens en localS

### EKS-SRC-00411 — CLASIFICACIÓN QUIRÚRGICA DE BYPASS

- Ruta: `docs/CONEXIONES_SQL_EDARSAHUB_01_BYPASS_CLASSIFICATION.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # CLASIFICACIÓN QUIRÚRGICA DE BYPASS ## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE B.1 **Fecha:** 2025-12-19 **Estado:** COMPLETADO - CLASIFICACIÓN DE 56 BYPASSES **Última actualización:** 2025-12-19 - LOTE 4 COMPLETADO **Autor:** Agente E1 --- ## PROGRESO DE MIGRACIÓN | Lote | Estado | Bypasses Corregidos | Pendientes | |------|--------|---------------------|------------| | **Lote 1** | ✅ COMPLETADO |

### EKS-SRC-01077 — P3-BLOQUE-A: Dashboard Ejecutivo + Rentabilidad Base

- Ruta: `docs/auditorias/P3_BLOQUE_A_COMPLETADO_20260605_060840.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos`

> # P3-BLOQUE-A: Dashboard Ejecutivo + Rentabilidad Base ## Fecha: 2026-06-05 ## Estado: ✅ IMPLEMENTADO Y VALIDADO ## Endpoints Creados: ### 1. Dashboard Ejecutivo - `GET /api/dashboard-ejecutivo/resumen` - Parámetros: `fecha_inicio`, `fecha_fin` - Retorna: KPIs consolidados, ventas por unidad, estado de precios, productos, compras, sync 24h ### 2. Rentabilidad Base - `GET /api/dashboard-ejecutivo/r

### EKS-SRC-00869 — DIAGNÓSTICO: Dependencias MongoDB del Módulo Compras

- Ruta: `docs/reports/COMPRAS_MONGO_DEPENDENCIA_DIAGNOSTICO_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # DIAGNÓSTICO: Dependencias MongoDB del Módulo Compras **Fecha**: 2026-05-25 **Auditor**: E1 Agent (Arquitecto Senior ERP/SQL Server) **Versión**: 1.0 **Estado**: DIAGNÓSTICO PASIVO (Sin modificaciones de código) --- ## 1. RESUMEN EJECUTIVO ### Hallazgo Principal El módulo de **Compras** tiene **dependencias residuales de MongoDB** que fueron parcheadas con un "modo stub" silencioso en lugar de se

### EKS-SRC-00586 — MIGRACIÓN ENDPOINTS COMERCIALES A SQL-FIRST - COMPLETADO

- Ruta: `docs/reports/MIGRACION_ENDPOINTS_COMERCIALES_SQL_FIRST.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial`

> # MIGRACIÓN ENDPOINTS COMERCIALES A SQL-FIRST - COMPLETADO **Fecha:** 2025-05-26 **Estado:** ✅ COMPLETADO --- ## 1. Resumen Ejecutivo Se completó la migración de **4 endpoints comerciales** de arquitectura LIVE (MongoDB + conexiones remotas) a **SQL-First** (consultas directas a EDARSAHUB). ### Tablas DDL Creadas | Tabla | Estado | |-------|--------| | `Sync_Metas_Comerciales` | ✅ Creada | | `Sync

### EKS-SRC-00808 — AUDITORÍA - Finanzas Fase 2: Control de Ingresos / Cortes de Caja

- Ruta: `docs/reports/auditoria_finanzas_fase2_control_ingresos.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # AUDITORÍA - Finanzas Fase 2: Control de Ingresos / Cortes de Caja **Fecha:** 30 de Abril de 2026 **Autor:** E1 Agent **Status:** AUDITORÍA COMPLETA - VALIDACIÓN EDARSAHUB VS ORIGEN --- ## 🔴 HALLAZGO CRÍTICO **Los 70 registros en `Finanzas_CortesCaja` de EDARSAHUB son DATOS DEMO, NO DATOS REALES.** **Evidencia:** - Todos tienen `FechaAlta` = 2026-04-13 (mismo día) - Los montos tienen patrones uni

### EKS-SRC-01718 — RBAC - Fase 3.1

- Ruta: `backend/modules/fase2_operativo/routes/dashboard_routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Endpoints de Dashboard CAB-003 | EDARSA HUB - Fase 2A / 2B.4 PROTEGIDO CON RBAC (Fase 3.1) Expone KPIs, resúmenes y alertas vía HTTP. Incluye métricas de SLA. Permisos requeridos: - Todos los endpoints requieren autenticación y filtran por empresas_permitidas del usuario """ from

### EKS-SRC-01998 — test_inteligencia_portal_closure_contract.py

- Ruta: `backend/tests/test_inteligencia_portal_closure_contract.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, comercial`

> """Contratos de cierre Portal/Inteligencia/Comercial.""" from pathlib import Path BACKEND = Path(__file__).resolve().parents[1] MIDDLEWARE = ( BACKEND / "core/rbac/middleware.py" ).read_text(encoding="utf-8") RBAC_INIT = ( BACKEND / "core/rbac/__init__.py" ).read_text(encoding="utf-8") PORTAL = ( BACKEND / "routes/portal_inteligencia.py" ).read_text(encoding="utf-8") INTEL = ( BACKEND / "modules/i

### EKS-SRC-00373 — REPORTE SUBFASE C — LOTE 3 QUIRÚRGICO

- Ruta: `docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE3_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, comercial`

> # REPORTE SUBFASE C — LOTE 3 QUIRÚRGICO ## CONEXIONES-SQL-EDARSAHUB-01 **Fecha:** 2025-12-19 **Estado:** COMPLETADO CON OBSERVACIONES - 5/5 CAMBIOS IMPLEMENTADOS **Autor:** Agente E1 **Revisión requerida:** Usuario --- ## 1. RESUMEN EJECUTIVO Se completaron los 5 cambios del Lote 3, migrando los bypasses de `db.servers.find_one()` hacia `server_registry.get_server_connection_info()`. | # | Función

### EKS-SRC-00392 — REPORTE DE LOTE 4 — MIGRACIÓN DE BYPASSES

- Ruta: `docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE4_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad`

> # REPORTE DE LOTE 4 — MIGRACIÓN DE BYPASSES ## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C — LOTE 4 **Fecha:** 2025-12-19 **Estado:** COMPLETADO CON OBSERVACIONES **Autor:** Agente E1 **Versión:** 1.0 --- ## 1. RESUMEN EJECUTIVO ### Resultado **10 de 10 endpoints migrados exitosamente** de `db.servers.find_one()` a `server_registry.get_server_connection_info()`. ### Dictamen por Capas | Capa | Estado 

### EKS-SRC-00464 — REPORTE DE LOTE 5 — MIGRACIÓN DE BYPASSES

- Ruta: `docs/CONEXIONES_SQL_EDARSAHUB_01_SUBFASE_C_LOTE5_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad`

> # REPORTE DE LOTE 5 — MIGRACIÓN DE BYPASSES ## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C — LOTE 5 **Fecha:** 2025-12-19 **Estado:** COMPLETADO **Autor:** Agente E1 **Versión:** 1.0 --- ## 1. RESUMEN EJECUTIVO ### Resultado **5 de 5 endpoints migrados exitosamente** de `db.servers.find()` / `db.servers.find_one()` a `server_registry.list_servers()` / `server_registry.get_server_connection_info()`. ##

### EKS-SRC-00928 — FASE B-P1-C: Migración responsabilidad_repository.py a SQL Explícito

- Ruta: `docs/reports/FASE_B_P1_C_RESPONSABILIDAD_REPOSITORY_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> # FASE B-P1-C: Migración responsabilidad_repository.py a SQL Explícito **Fecha:** 26 Mayo 2026 **Archivo:** `/app/backend/modules/fase2_operativo/repositories/responsabilidad_repository.py` **Tabla SQL:** `Operativo_ResponsabilidadEconomica` --- ## 1. ESTADO ANTERIOR ### Dependencias MongoDB: ```python # Comentario referenciando MongoDB ObjectId # Use _id (MongoDB ObjectId) for update, not id (UUI

### EKS-SRC-00958 — Reporte Ejecutivo: Hallazgos ALTA - Migración SQL-First

- Ruta: `docs/reports/REPORTE_EJECUTIVO_HALLAZGOS_ALTA_SQL_FIRST.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # Reporte Ejecutivo: Hallazgos ALTA - Migración SQL-First **Fecha:** 2026-06-04 **Alcance:** Módulos prioritarios (excluyendo Finanzas y PropinasTPV ya migrados) **Total hallazgos ALTA:** 619 (excl. Finanzas/PropinasTPV: ~580) --- ## 1. Resumen Ejecutivo | Módulo | Hallazgos ALTA | Frontend | Backend | Tests (ignorar) | Prioridad | |--------|----------------|----------|---------|-----------------|

### EKS-SRC-02297 — Configuración de conexión EDARSAHUB

- Ruta: `backend/core/scheduler/jobs/sync_comercial_endpoints_job.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, comercial`

> import os """ EDARSA HUB - Sync Comercial Endpoints Job ========================================== Job para sincronizar datos de endpoints comerciales LIVE a tablas SQL. TABLAS SINCRONIZADAS: - Sync_Metas_Comerciales - Sync_Ticket_Perfecto - Sync_Mesas - Sync_Movimientos_Detalle - Sync_Precios_Historicos - Sync_PAX_Detalle ARQUITECTURA NO-LIVE: - Este job consulta servidores remotos (SoftRestauran

### EKS-SRC-01639 — =============================================================================

- Ruta: `backend/modules/comercial/routes_competidores_enterprise.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ FASE 1C-3I-B v2: Endpoints Enterprise de Competidores por Unidad de Negocio ARQUITECTURA: - /api/comercial/competidores-catalogo: CRUD del catálogo maestro - /api/comercial/competidores-unidad: Relaciones competidor-unidad - /api/comercial/competidores: Consultas por unidad (OBLI

### EKS-SRC-01070 — P0_FIX_UNIDADES_NEGOCIO_20260605_133819.txt

- Ruta: `docs/auditorias/P0_FIX_UNIDADES_NEGOCIO_20260605_133819.txt`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos`

> ================================================================================ P0 FIX REGRESIÓN /api/unidades-negocio - COMPLETADO ================================================================================ Fecha: $(date) PROBLEMA ORIGINAL: - El endpoint /api/unidades-negocio retornaba [] (array vacío) - Error SQL: "Invalid object name 'Sistema_UnidadesNegocio'" o "Invalid column name 'empr

### EKS-SRC-00886 — DIAGNÓSTICO ARQUITECTÓNICO - CORTES Z EDARSAHUB SQL-FIRST

- Ruta: `docs/reports/CORTES_Z_ARQUITECTURA_SQL_FIRST_DIAGNOSTICO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas`

> # DIAGNÓSTICO ARQUITECTÓNICO - CORTES Z EDARSAHUB SQL-FIRST **Fecha**: 2026-05-25 **Auditor**: E1 Agent (Arquitecto Senior) **Versión**: 1.1 (Con mejoras implementadas) --- ## 1. RESUMEN EJECUTIVO ### Estado Actual El endpoint de Cortes Z (`GET /api/finanzas/tesoreria/cortes-z`) **YA ESTÁ MIGRADO** a arquitectura SQL-FIRST y lee exclusivamente desde la tabla `EDARSAHUB.Finanzas_CortesCaja`. ### Ca

### EKS-SRC-00882 — COSTOS-ALERTAS-001-C: Servicios Backend para Reglas de Margen

- Ruta: `docs/reports/COSTOS_ALERTAS_001C_SERVICIOS_REGLAS_MARGEN.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial`

> # COSTOS-ALERTAS-001-C: Servicios Backend para Reglas de Margen ## Fecha: 25 Mayo 2026 ## Estado: ✅ COMPLETADO ## Autor: Agente E1 --- ## 1. OBJETIVO Implementar el backend completo para administrar reglas de margen esperado con resolución jerárquica: - **Producto > Subfamilia > Familia > Grupo** La regla más específica siempre tiene prioridad sobre la más general. --- ## 2. ARQUITECTURA IMPLEMENT

### EKS-SRC-00688 — FASE 1C-3I-B v2: Corrección Arquitectónica - Competidores por Unidad de Negocio

- Ruta: `docs/reports/FASE_1C_3I_B_COMPETIDORES_ENTERPRISE_UNIDAD.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial`

> # FASE 1C-3I-B v2: Corrección Arquitectónica - Competidores por Unidad de Negocio ## Fecha: 25 Mayo 2026 ## Estado: ✅ IMPLEMENTADO ## Autor: Agente E1 --- ## 1. PROBLEMA IDENTIFICADO EDARSAHUB es **multiempresa, multiunidad y multimarca**. Los competidores NO deben tratarse como una lista global aplicable a todas las unidades de negocio. ### Situación Anterior (Incorrecta) - Tabla única `Comercial

### EKS-SRC-00935 — RBAC-SCOPE-D: get_all_users() Lee Permisos Operativos desde SQL

- Ruta: `docs/reports/RBAC_SCOPE_D_GET_ALL_USERS_LEE_PERMISOS_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `contratos_canonicos, rbac_seguridad, ia_agentes`

> # RBAC-SCOPE-D: get_all_users() Lee Permisos Operativos desde SQL **Fecha:** 14 de Diciembre de 2025 **Estado:** ✅ COMPLETADA **Autor:** Agente E1 **Régimen:** Autorización Controlada --- ## 1. Archivos Modificados | Archivo | Función | Cambio | |---------|---------|--------| | `/app/backend/modules/auth/repository.py` | `get_all_users()` | Lectura de permisos desde SQL | --- ## 2. Flujo Anterior 

### EKS-SRC-00926 — REPORTE DE REGRESIÓN CRÍTICA

- Ruta: `docs/reports/REGRESION_CRITICA_NO_ROMPER_LO_QUE_FUNCIONA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay`

> # REPORTE DE REGRESIÓN CRÍTICA **Fecha:** 2025-05-19 **Prioridad:** CRÍTICA **Estado:** ✅ RESTAURADO **Autor:** Agente E1 --- ## 1. RESUMEN DE LA REGRESIÓN ### Síntomas Reportados 1. **Catálogo SQL:** Toast "Error al cargar catálogo" 2. **Explorador BD:** Primer filtro solo mostraba "Todos los sistemas" 3. **Catálogos del Sistema:** Toast "Error cargando catálogos" ### Causa Raíz El cambio al endp

### EKS-SRC-00541 — VALIDACIÓN ENDPOINTS INTELIGENCIA COMERCIAL

- Ruta: `docs/reports/VALIDACION_ENDPOINTS_INTELIGENCIA_COMERCIAL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay, sql_datos, comercial`

> # VALIDACIÓN ENDPOINTS INTELIGENCIA COMERCIAL **Ejecutado:** 2026-06-02T10:32:13.699280 --- ## 1. Vistas y SP Verificados en SQL Server | Objeto | Nombre Completo | Existe | |--------|-----------------|--------| | Vista | `dbo.Comercial_Inteligencia_VW_KPIsEjecutivos` | ✅ | | Vista | `dbo.Comercial_Inteligencia_VW_SyncStatus` | ✅ | | SP | `dbo.Sp_Validar_Inteligencia_Comercial_Status` | ✅ | ## 2. 

### EKS-SRC-01854 — Filtro por unidad de negocio (server_id o unidad_negocio_pk)

- Ruta: `backend/modules/finanzas/repository_cortes_caja_edarsahub.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repository EDARSAHUB SQL para Cortes de Caja (Cortes Z) FINANZAS-TESORERIA-SQL-001: Migrado de consultas en vivo a EDARSAHUB SQL - Fecha: 2026-05-25 - Lee de tabla Finanzas_CortesCaja (ya sincronizada) - NO consulta servidores origen en vivo - Cumple máxima: "EDARSAHUB SQL es el 

### EKS-SRC-00849 — AUDITORÍA PASIVA COMPLETA - EDARSAHUB

- Ruta: `docs/reports/AUDITORIA_DEPURACION_LIMPIEZA_REPO_EDARSAHUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUDITORÍA PASIVA COMPLETA - EDARSAHUB ## Depuración, Limpieza y Deuda Técnica **Fecha:** 2026-05-15 **Autor:** E1 Agent - Arquitecto Senior **Clasificación:** Auditoría Pasiva - SIN MODIFICACIONES --- ## 1. RESUMEN EJECUTIVO ### Métricas Globales del Repositorio | Métrica | Valor | Estado | |---------|-------|--------| | **server.py** | 16,408 líneas (692KB) | 🔴 CRÍTICO | | Endpoints en server.p

### EKS-SRC-00301 — EDARSA HUB - Arquitectura de Clasificación de Datos

- Ruta: `docs/ARQUITECTURA_CLASIFICACION_DATOS_LIVE_VS_CONSOLIDADOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # EDARSA HUB - Arquitectura de Clasificación de Datos ## LIVE OPERATIVO vs ANALÍTICO/CONSOLIDADO **Versión**: 1.0 **Fecha**: Abril 2026 **Autor**: Arquitectura Senior **Estado**: VIGENTE --- ## 1. DEFINICIONES FORMALES ### 1.1 TIPO A: LIVE OPERATIVO ("LIVE FIRST, PERSIST SECOND") **Definición**: Módulos que requieren información en tiempo real de los sistemas origen (SoftRestaurant, MPRO) para tom

### EKS-SRC-01078 — P3-03 — Backfill Corporativo SQL-First

- Ruta: `docs/auditorias/P3_03_BACKFILL_CORPORATIVO_20260605_051943.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, comercial`

> # P3-03 — Backfill Corporativo SQL-First ## Estado **COMPLETADO** (Base segura) ## Fecha 2026-06-05 ## Descripción Módulo de re-sincronización histórica corporativa que opera en modo DRY_RUN por defecto. ## Arquitectura - **NO** crea nuevas conexiones LIVE - **NO** usa MongoDB - **Modo DRY_RUN** por defecto (solo valida tablas/conteos) - **COMMIT** requiere flag explícito ## Endpoints ### GET /api

### EKS-SRC-00739 — DIAGNÓSTICO ARQUITECTÓNICO — Ventas del Día

- Ruta: `docs/reports/DIAGNOSTICO_ARQUITECTURA_VENTAS_DIA_14MAY2026.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `conectores_universales, comercial`

> # DIAGNÓSTICO ARQUITECTÓNICO — Ventas del Día **Fecha:** 2026-05-14 **Estado:** DIAGNÓSTICO COMPLETADO --- ## RESUMEN EJECUTIVO | Ítem | Estado | Detalle | |------|--------|---------| | Tabla de conexiones | ✅ | `Servidores_Conexiones` en EDARSAHUB SQL | | Tabla de Ventas del Día | ✅ | `Comercial_Ventas_Dia_Abiertas_v2` en EDARSAHUB SQL | | Job de sincronización | ✅ | `sync_comercial_abiertas_v2_j

### EKS-SRC-00934 — REPORTE EJECUCIÓN: Gobierno RBAC e Inteligencia Comercial

- Ruta: `docs/reports/EJECUCION_GOBIERNO_RBAC_INTELIGENCIA_20260602.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial`

> # REPORTE EJECUCIÓN: Gobierno RBAC e Inteligencia Comercial **Fecha**: 2026-06-02 **Ejecutado por**: SQL Runner (`edarsahub_sql_runner.py`) **Modo**: migrate --- ## 1. Módulo INTELIGENCIA_COMERCIAL Registrado ```sql INSERT INTO Usuario_Modulos (CodigoModulo, NombreModulo, Ruta, ...) VALUES ('INTELIGENCIA_COMERCIAL', 'Inteligencia Comercial', '/comercial/inteligencia', ...) ``` **Resultado:** | Cam

### EKS-SRC-01097 — P3-03D & P3-04: Backfill Corporativo - COMPRAS, INVENTARIOS y VENTAS_REAL

- Ruta: `docs/auditorias/P3_03D_P3_04_BACKFILL_FINAL_20260605_055522.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, comercial`

> # P3-03D & P3-04: Backfill Corporativo - COMPRAS, INVENTARIOS y VENTAS_REAL ## Fecha: 2026-06-05 ## Estado: ✅ IMPLEMENTADO Y VALIDADO ## Módulos Implementados: ### 1. COMPRAS - **DRY_RUN**: ✅ OK - **COMMIT**: ✅ OK (status WARNING indica que hay encabezados sin detalle pendientes de sync fuente) - Tablas validadas: Compras_Pedidos, Compras_PedidosDetalle, Compras_Ordenes, Compras_Recepciones ### 2.

### EKS-SRC-01059 — P3-05: Pricing IA Base SQL-First

- Ruta: `docs/auditorias/P3_05_PRICING_IA_BASE_FINAL_20260605_060157.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos`

> # P3-05: Pricing IA Base SQL-First ## Fecha: 2026-06-05 ## Estado: ✅ IMPLEMENTADO Y VALIDADO ## Endpoint Creado: - `GET /api/pricing-ai/resumen` - Parámetros: `server_id` (opcional), `limite` (1-500, default 100) - Autenticación: Bearer Token requerido ## Respuesta de ejemplo: ```json { "success": true, "source": "EDARSAHUB_SQL", "modo": "BASE_SIN_IA_EXTERNA", "resumen": { "productos_precio": 5642

### EKS-SRC-01081 — P3-02 — Sync Monitor SQL-First

- Ruta: `docs/auditorias/P3_02_SYNC_MONITOR_SQL_FIRST_20260605_051150.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, comercial`

> # P3-02 — Sync Monitor SQL-First ## Estado **COMPLETADO** ## Fecha 2026-06-05 ## Descripción Módulo de Monitor de Sincronización tipo NOC que consume EXCLUSIVAMENTE tablas existentes en EDARSAHUB SQL. ## Arquitectura - **NO** crea nuevas conexiones - **NO** crea nuevas tablas - **NO** usa MongoDB - **NO** usa conexiones LIVE para dashboards ## Tablas Consumidas 1. `Compras_Sync_Log` (383 registros

### EKS-SRC-00700 — FASE 1C-0: Diagnóstico Comercial/Ventas para Subfases

- Ruta: `docs/reports/FASE_1C_0_DIAGNOSTICO_COMERCIAL_VENTAS_SUBFASES.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `hospitality, sql_datos, rbac_seguridad, comercial`

> # FASE 1C-0: Diagnóstico Comercial/Ventas para Subfases **Fecha**: 2026-05-24 **Hora México**: 12:30 - 13:15 **Ejecutado por**: Agente EDARSA HUB **Estado**: ✅ DIAGNÓSTICO COMPLETADO --- ## 1. Rutas Revisadas ### 1.1 Rutas Frontend (App.js) | Ruta | Estado | Destino/Componente | Clasificación | |------|--------|-------------------|---------------| | `/comercial` | ✓ Existe | `Comercial.js` (Dashbo

### EKS-SRC-01683 — Constantes para ordenamiento (reemplazan pymongo.ASCENDING/DESCENDING)

- Ruta: `backend/modules/fase2_operativo/repositories/tarea_repository.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repositorio para tareas_inventario FASE B-P1-B | EDARSA HUB - Migración SQL Explícita ARQUITECTURA: - Todo acceso productivo a EDARSAHUB SQL Server - CERO MongoDB productivo - CERO conexiones LIVE Gestiona el acceso a datos de tareas de inventario. """ from typing import Optional

### EKS-SRC-00599 — FASE B-P0-A: Diagnóstico Migración fase2_operativo MongoDB → SQL

- Ruta: `docs/reports/FASE_B_P0_FASE2_OPERATIVO_MONGO_A_SQL_DIAGNOSTICO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

> # FASE B-P0-A: Diagnóstico Migración fase2_operativo MongoDB → SQL **Fecha:** 25 Mayo 2026 **Módulo:** `/app/backend/modules/fase2_operativo/` **Prefijo API:** `/api/v2/` **Arquitectura Destino:** EDARSAHUB SQL Server (CERO MongoDB) --- ## 1. RESUMEN EJECUTIVO El módulo `fase2_operativo` constituye el **núcleo de la Gestión Operativa de Inventarios (Fase 2A)** del CRM EDARSA HUB. Actualmente opera

### EKS-SRC-00772 — FIX EXPLORADOR BD ROTO POST CONEXIONES EXPLORABLES

- Ruta: `docs/reports/FIX_EXPLORADOR_BD_ROTO_POST_CONEXIONES_EXPLORABLES.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `toast_netpay`

> # FIX EXPLORADOR BD ROTO POST CONEXIONES EXPLORABLES **Fecha:** 2026-05-18 **Estado:** ✅ COMPLETADO **Prioridad:** P0 URGENTE --- ## 1. Diagnóstico Raíz ### Síntomas Reportados - Segundo filtro mostraba "Cargando..." indefinidamente - Toast rojo "Error al ejecutar consulta" ### Hallazgos del Diagnóstico Tras análisis exhaustivo: 1. **El Explorador BD ya usaba `fetchConexionesExplorables`** antes d

### EKS-SRC-00974 — INCIDENTE FILTROS UNIDAD DE NEGOCIO - DIAGNÓSTICO

- Ruta: `docs/reports/INCIDENTE_FILTROS_UNIDAD_NEGOCIO_ROTOS_DIAGNOSTICO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, comercial, finanzas`

> # INCIDENTE FILTROS UNIDAD DE NEGOCIO - DIAGNÓSTICO **Fecha:** 2026-05-26 **Severidad:** CRÍTICO (reportado) → RESUELTO **Módulos Afectados:** Finanzas, Operaciones, Comercial, Servidores, Catálogo --- ## 1. RESUMEN EJECUTIVO Los filtros de Unidad de Negocio fueron reportados como "rotos" en múltiples módulos. Después del diagnóstico exhaustivo, se confirma que: 1. **El endpoint `/api/servers` est

### EKS-SRC-00574 — AUDITORÍA ARQUITECTÓNICA: FUENTE DE DATOS DEL TABLERO EJECUTIVO COMERCIAL

- Ruta: `docs/reports/auditoria_fuente_datos_tablero_ejecutivo_comercial.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, roadmap_aceptacion`

> # AUDITORÍA ARQUITECTÓNICA: FUENTE DE DATOS DEL TABLERO EJECUTIVO COMERCIAL **Fecha de auditoría**: 01-Mayo-2026 **Auditor**: E1 Agent (READ-ONLY) **Módulo auditado**: `/app/backend/modules/comercial/` **Estado**: COMPLETADA **Código modificado**: NO --- ## 1. RESUMEN EJECUTIVO El **Tablero Ejecutivo Comercial** actualmente **NO LEE DE EDARSAHUB** para obtener KPIs de ventas. En su lugar, consulta

### EKS-SRC-01685 — ============================================================================

- Ruta: `backend/modules/fase2_operativo/repositories/sql_base_repository.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ SQL Base Repository para módulo fase2_operativo FASE B-P0-C | EDARSA HUB Este módulo proporciona la clase base para todos los repositories del módulo operativo usando EDARSAHUB SQL Server en lugar de MongoDB. ARQUITECTURA: - Todo acceso productivo va a SQL Server - CERO MongoDB p

### EKS-SRC-01682 — Constante para ordenamiento descendente (reemplaza pymongo.DESCENDING)

- Ruta: `backend/modules/fase2_operativo/repositories/workflow_repository.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repositorio para workflow_inventarios FASE B-P1-A | EDARSA HUB - Migración SQL Explícita ARQUITECTURA: - Todo acceso productivo a EDARSAHUB SQL Server - CERO MongoDB productivo - CERO conexiones LIVE Gestiona el acceso a datos de workflows de inventario. """ from typing import Op

### EKS-SRC-00372 — DOCUMENTO DE CONSOLIDACIÓN FINAL

- Ruta: `docs/ARQUITECTURA_AUTOMATIZACION_INVENTARIOS_CONSOLIDACION_FINAL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> # DOCUMENTO DE CONSOLIDACIÓN FINAL ## CAB-003: Automatización de Análisis de Inventarios - VALIDACIÓN PARA IMPLEMENTACIÓN **Versión**: 2.0 CONSOLIDADA **Fecha**: Diciembre 2025 **Estado**: VALIDACIÓN FINAL ANTES DE IMPLEMENTACIÓN **Documentos Fuente**: v1.md, ADENDA_A.md, ADENDA_B.md, ADENDA_C.md --- ## PARTE 1: VALIDACIÓN DE LO EXISTENTE ### 1.1 Core Service Reutilizable ``` ESTADO: ✅ CORRECTO - 

### EKS-SRC-01079 — AUDITORÍA P1 — ENDPOINTS VISUALES NO-LIVE

- Ruta: `docs/auditorias/AUDITORIA_P1_NO_LIVE_ENDPOINTS_VISUALES_20260604.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial`

> # AUDITORÍA P1 — ENDPOINTS VISUALES NO-LIVE Fecha: 2026-06-04 Proyecto: EDARSAHUB Criterio: Los endpoints visuales no deben consultar servidores operativos LIVE. Solo EDARSAHUB SQL. ## Resultado Ejecutivo | Módulo | Estado | Observación | |---|---|---| | comercial | CUMPLE | Modal Detalle de Ventas y Precios Constantes migrados a SQL-first | | costos_margenes | CUMPLE | Repository SQL-first contra

### EKS-SRC-00921 — Auditoria inventario La Estelar - analisis automatico

- Ruta: `docs/reports/AUDITORIA_INVENTARIO_ESTELAR_ANALISIS_AUTO_20260630.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> # Auditoria inventario La Estelar - analisis automatico - Fecha de auditoria: 2026-06-30 - Unidad: LA ESTELAR - ServerID: `a5ff0e25-f029-43db-b634-d4ac814c904f` - Base auditada: EDARSAHUB SQL - Modo: solo lectura para datos; cambios de codigo aplicados en detector. ## Resumen ejecutivo El analisis automatico no se genero porque La Estelar no estaba entrando al detector de inventarios. La causa rai

### EKS-SRC-00611 — AUDITORÍA COMPLETA: MENÚS, FUENTES DE DATOS Y CONEXIONES EDARSAHUB

- Ruta: `docs/reports/AUDITORIA_MENUS_FUENTES_DATOS_Y_CONEXIONES_EDARSAHUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUDITORÍA COMPLETA: MENÚS, FUENTES DE DATOS Y CONEXIONES EDARSAHUB **Fecha:** 2026-05-26 **Versión:** 1.0 **Estado:** AUDITORÍA INICIAL COMPLETA --- ## RESUMEN EJECUTIVO ### Hallazgos Críticos | Categoría | Cantidad | Severidad | |-----------|----------|-----------| | Menús con conexiones LIVE | 12+ | 🔴 P0-P1 | | Módulos con MongoDB activo | 5 | 🔴 P0-P1 | | Endpoints con server_id remoto | 10+ |

### EKS-SRC-01658 — =============================================================================

- Ruta: `backend/modules/comercial/services/competidores_enterprise_service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ FASE 1C-3I-B v2: Servicio Enterprise de Competidores por Unidad de Negocio ARQUITECTURA: - Comercial_CompetidoresCatalogo: Catálogo maestro (datos del competidor) - Comercial_CompetidoresUnidad: Relación competidor-unidad (prioridad, tipo) - vw_CompetidoresPorUnidad: Vista consol

### EKS-SRC-00969 — Auditoría de proyecciones e histórico comercial

- Ruta: `docs/reports/AUDITORIA_PROYECCIONES_E_HISTORICO_COMERCIAL_20260730.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # Auditoría de proyecciones e histórico comercial Fecha: 2026-07-30 Rama auditada: `Edarsahub_Desarrollo` Commit base auditado: `776269f7afe090790e0c89c6ce08ce71064e626c` ## Objetivo Recuperar el algoritmo existente de proyección de ventas y determinar si la historia comercial de las cinco unidades está certificada desde su primer día disponible de operación. Unidades: `130MID`, `130QRO`, `ORIGEN`

### EKS-SRC-00634 — Phase 3 Comercial KPI cross-menu/source audit

- Ruta: `docs/reports/PHASE3_COMERCIAL_KPI_CROSS_MENU_SOURCE_AUDIT_20260630.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # Phase 3 Comercial KPI cross-menu/source audit Fecha: 2026-06-30 Alcance: Tablero Ejecutivo, Comercial e Inteligencia Comercial. Modo: solo lectura. ## Objetivo Auditar si los KPIs visibles en los menus comerciales de EDARSAHUB salen de la misma verdad de negocio: - Tablero Ejecutivo: ventas, cheques/tickets, PAX, cheque promedio, ticket/PAX promedio. - Comercial: dashboard por unidad/servidor y 

### EKS-SRC-05716 — EDARSAHUB V1.0 — instrucciones globales para GitHub Copilot / VS Code

- Ruta: `.agent-worktrees/enterprise-navigation/.github/copilot-instructions.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> # EDARSAHUB V1.0 — instrucciones globales para GitHub Copilot / VS Code Usar `AGENTS.md` como contrato principal del repositorio. Prioridad operativa: 1. Antigravity 2. Codex 3. GitHub Copilot / VS Code 4. Claude minimizado Agentes Copilot disponibles: - EDARSA Copilot Supervisor: coordina, no edita. - EDARSA Auditor: audita, no edita. - EDARSA Coder: implementa cambios minimos. - EDARSA Validator

### EKS-SRC-01612 — En entornos sin RBAC para este server, el endpoint puede bloquear con 403.

- Ruta: `backend/tests_guardrails/test_inventory_analysis_sql_error_handling.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad`

> import asyncio import inspect import pytest from fastapi import HTTPException from server import generate_inventory_analysis from core.inventarios.sql_error_policy import ( classify_inventory_sql_error, inventory_analysis_safe_http_exception, is_inventory_transient_error, should_retry_inventory_once, ) def test_inventory_sql_error_classifier_transient_timeout_and_dead_dbprocess(): err = Exception(

### EKS-SRC-00744 — MATRIZ DEFINITIVA — VENTAS DEL DÍA

- Ruta: `docs/reports/MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial, roadmap_aceptacion`

> # MATRIZ DEFINITIVA — VENTAS DEL DÍA ## SoftRestaurant / MPRO / Turnos / FechaOperacion / EDARSAHUB **Documento**: MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md **Fecha**: 2026-05-20 **Versión**: 1.0 **Estado**: DISEÑO APROBADO — PENDIENTE IMPLEMENTACIÓN POR FASES --- ## 1. DEFINICIÓN OFICIAL DE VENTAS DEL DÍA ### 1.1 Concepto Operativo **Ventas del Día** NO significa ventas de 00:00 

### EKS-SRC-03680 — P0: Nuevas estructuras de respuesta

- Ruta: `.agent-worktrees/compras-inventarios/backend/modules/comercial/routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ ╔════════════════════════════════════════════════════════════════════════════╗ ║ 🔒 MÓDULO BLINDADO - NO MODIFICAR 🔒 ║ ╠════════════════════════════════════════════════════════════════════════════╣ ║ ESTADO: FUNCIONAL Y OPERATIVO (Abril 2026) ║ ║ ║ ║ Este módulo ha sido validado y

### EKS-SRC-00949 — ARQ CATÁLOGO MAESTRO - FASE 5 ENDPOINTS - REPORTE DE IMPLEMENTACIÓN

- Ruta: `docs/reports/ARQ_CATALOGO_SISTEMAS_CAPACIDADES_FASE5_ENDPOINTS_REPORTE.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial, finanzas`

> # ARQ CATÁLOGO MAESTRO - FASE 5 ENDPOINTS - REPORTE DE IMPLEMENTACIÓN **Fecha:** 2025-12-XX **Estado:** ✅ COMPLETADO EXITOSAMENTE **Autor:** Arquitecto Senior Backend --- ## 1. RESUMEN EJECUTIVO La implementación de **FASE 5 - Endpoints de Catálogo** fue completada exitosamente. Se crearon 10 endpoints seguros que exponen el `SystemCapabilityResolver` via API REST, usando EDARSAHUB SQL como fuente

### EKS-SRC-01684 — Constante para ordenamiento descendente

- Ruta: `backend/modules/fase2_operativo/repositories/responsabilidad_repository.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repositorio para responsabilidad_economica FASE B-P1-C | EDARSA HUB - Migración SQL Explícita ARQUITECTURA: - Todo acceso productivo a EDARSAHUB SQL Server - CERO MongoDB productivo - CERO conexiones LIVE Gestiona el acceso a datos de cálculos de impacto económico. Tabla SQL: Ope

### EKS-SRC-02614 — Auditoría de horarios operativos, fuente horaria y ventas por área

- Ruta: `.agent-worktrees/comercial-ventas-tiempo/docs/audits/20260723_auditoria_horarios_fuente_horaria_areas.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # Auditoría de horarios operativos, fuente horaria y ventas por área **Fecha:** 23 de julio de 2026 **Dominio:** Comercial **Tab:** Ventas por hora y día de la semana **SQL ejecutado:** Solo consultas SELECT **Producción modificada:** No ## Objetivo Determinar: 1. Cómo deben influir los horarios operativos. 2. Si la fuente horaria conserva la ventana aplicada. 3. Si la fuente es suficientemente re

### EKS-SRC-02619 — Auditoría de clave compuesta servidor-sucursal-unidad

- Ruta: `.agent-worktrees/comercial-ventas-tiempo/docs/audits/20260723_auditoria_clave_compuesta_servidor_sucursal_unidad.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # Auditoría de clave compuesta servidor-sucursal-unidad ## Objetivo Determinar si la atribución comercial requiere una clave compuesta. ## Contrato de la fuente - Servidor: `server_id` - Unidad: `unidad_negocio_id` - Sucursal: `sucursal_id` - Sistema: `sistema_origen` ## Mapeos detectados - `1B230A06-FFAF-4C70-BD27-B1BE3579DEA6` → `130QRO` mediante `dbo.Unidades_Negocio` - `1B230A06-FFAF-4C70-BD27

### EKS-SRC-02615 — Auditoría de contrato y conciliación de VentasDetalleProducto

- Ruta: `.agent-worktrees/comercial-ventas-tiempo/docs/audits/20260723_auditoria_contrato_conciliacion_ventas_detalle_producto.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # Auditoría de contrato y conciliación de VentasDetalleProducto **Fecha:** 23 de julio de 2026 **Objeto:** `dbo.Comercial_Inteligencia_VentasDetalleProducto` **SQL ejecutado:** Solo consultas SELECT **Producción modificada:** No ## Objetivo Determinar el contrato real, cobertura, granularidad y capacidad de conciliación del candidato transaccional con hora. ## Interpretación de la auditoría anteri

### EKS-SRC-08724 — Comercial.js

- Ruta: `frontend/src/pages/Comercial.js`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `toast_netpay, rbac_seguridad, ia_agentes, comercial, finanzas`

> /** * ╔════════════════════════════════════════════════════════════════════════════╗ * ║ 🔒 MÓDULO BLINDADO - NO MODIFICAR 🔒 ║ * ╠════════════════════════════════════════════════════════════════════════════╣ * ║ ESTADO: FUNCIONAL Y OPERATIVO (Abril 2026) ║ * ║ ║ * ║ Este módulo ha sido validado y estabilizado. Cualquier modificación ║ * ║ debe ser aprobada por el equipo de arquitectura y probada en

### EKS-SRC-07344 — Resolución canónica de la unidad -> server scope (RBAC incluido)

- Ruta: `backend/modules/catalogo/routes.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial`

> """ CATÁLOGO CANÓNICO (CATALOGO-CANONICO-C2) ======================================== Fuente ÚNICA de la clasificación de productos para TODO el ERP (Análisis, Costos y Márgenes, Inteligencia Comercial, etc.). - 100% NO-LIVE: lee EXCLUSIVAMENTE de EDARSAHUB (Sync_Productos). NUNCA consulta los POS en vivo (a diferencia del viejo /servers/{id}/report-filters que sí lo hacía). - Jerarquía canónica u

### EKS-SRC-07332 — Filtro de estado: por defecto solo activos (comportamiento legacy).

- Ruta: `backend/modules/admin_sql/routes.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Router SQL-First para Administración de Usuarios, Roles y Permisos ================================================================== ARQUITECTURA: SQL-FIRST desde EDARSAHUB_SQL TABLAS FUENTE: - Usuario_Catalogo - Usuario_Roles - Usuario_RolesAsignacion - Usuario_Modulos - Usuari

### EKS-SRC-07368 — P0: Nuevas estructuras de respuesta

- Ruta: `backend/modules/comercial/routes.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ ╔════════════════════════════════════════════════════════════════════════════╗ ║ 🔒 MÓDULO BLINDADO - NO MODIFICAR 🔒 ║ ╠════════════════════════════════════════════════════════════════════════════╣ ║ ESTADO: FUNCIONAL Y OPERATIVO (Abril 2026) ║ ║ ║ ║ Este módulo ha sido validado y

### EKS-SRC-07205 — ============================================================================

- Ruta: `backend/core/centro_control/routes.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `toast_netpay, sql_datos, rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ CENTRO DE CONTROL EDARSA - API Routes ====================================== Módulo central de monitoreo, estabilidad, detección de regresiones y control técnico del sistema EDARSA HUB. COMPONENTES INTEGRADOS: 1. Estado General del Sistema 2. Salud por Módulo 3. Alertas de Regres

### EKS-SRC-07586 — ============================================================================

- Ruta: `backend/modules/sync_recetas/sync_recetas.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos`

> """ Sync Recetas - Job de sincronización de productos, recetas, insumos y costos. FASE 1C-3B - Costos y Márgenes ARQUITECTURA NO-LIVE: - Este job es el ÚNICO componente autorizado para conectarse a fuentes remotas. - Los endpoints y frontend SOLO leen de EDARSAHUB SQL. - NO usar explosioninsumosdetalle como fuente (vacía en SoftRestaurant). - USAR tabla 'costos' para recetas de productos. - USAR t

### EKS-SRC-07222 — Centinela: unidad sin acceso / no resuelta -> resultados vacíos (nunca expone datos)

- Ruta: `backend/core/corporate_filters/request_resolver.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad`

> """ Resolvedor canónico de UNIDAD para tableros (Operaciones / Inventarios). ======================================================================== P0 (2026-06): "puerta única" de resolución. CONTRATO: - El frontend envía SOLO la unidad canónica (unidad_codigo o id). - El frontend NO resuelve server_id. - Este módulo: 1. Valida el permiso del usuario reutilizando el RBAC EXISTENTE (empresas_perm

### EKS-SRC-07264 — Configuración de conexión EDARSAHUB

- Ruta: `backend/core/scheduler/jobs/sync_comercial_endpoints_job.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, comercial`

> import os """ EDARSA HUB - Sync Comercial Endpoints Job ========================================== Job para sincronizar datos de endpoints comerciales LIVE a tablas SQL. TABLAS SINCRONIZADAS: - Sync_Metas_Comerciales - Sync_Ticket_Perfecto - Sync_Mesas - Sync_Movimientos_Detalle - Sync_Precios_Historicos - Sync_PAX_Detalle ARQUITECTURA NO-LIVE: - Este job consulta servidores remotos (SoftRestauran

### EKS-SRC-07529 — Filtro por unidad de negocio (server_id o unidad_negocio_pk)

- Ruta: `backend/modules/finanzas/repository_cortes_caja_edarsahub.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `8/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repository EDARSAHUB SQL para Cortes de Caja (Cortes Z) FINANZAS-TESORERIA-SQL-001: Migrado de consultas en vivo a EDARSAHUB SQL - Fecha: 2026-05-25 - Lee de tabla Finanzas_CortesCaja (ya sincronizada) - NO consulta servidores origen en vivo - Cumple máxima: "EDARSAHUB SQL es el 

### EKS-SRC-00002 — design_guidelines.json

- Ruta: `design_guidelines.json`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay`

> { "identity": "E1: The Anti-AI Designer", "mission": "Create a high-performance, Swiss-style inventory dashboard that prioritizes data density, clarity, and precision over decoration.", "theme": { "name": "Performance Pro / Swiss High-Contrast", "mode": "light", "description": "A utilitarian, high-contrast interface designed for rapid data scanning and decision making. Minimalist but dense.", "emo

### EKS-SRC-00331 — FASE 15 - EVIDENCIA DE CIERRE

- Ruta: `docs/FASE15_EVIDENCIA.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad`

> # FASE 15 - EVIDENCIA DE CIERRE ## Consolidación Final y Compatibilidad Legacy (DOCUMENTO RECTOR) **Versión:** 1.0 **Fecha:** Diciembre 2025 **Estado:** COMPLETADO (SOLO DOCUMENTACIÓN) **Tipo:** Documento de Gobierno y Criterio Arquitectónico --- ## 1. RESUMEN EJECUTIVO FASE 15 completada exitosamente como **documento rector** que establece: - Diagnóstico oficial del estado actual RBAC vs Legacy -

### EKS-SRC-02264 — ============================================

- Ruta: `backend/core/auditoria.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - Servicio de Auditoría Financiera ============================================== Registra todas las acciones financieras sensibles en SQL Server. NOTA: SQL Server EDARSA HUB es la fuente única para auditoría financiera. No existe fallback operativo a MongoDB. USO: fro

### EKS-SRC-00159 — Login.js

- Ruta: `frontend/src/pages/Login.js`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay`

> import { useState } from 'react'; import { useNavigate, Link } from 'react-router-dom'; import { flushSync } from 'react-dom'; import { useAuth } from '@/contexts/AuthContext'; import api from '@/lib/api'; import { Button } from '@/components/ui/button'; import { Input } from '@/components/ui/input'; import { Label } from '@/components/ui/label'; import { Card, CardContent } from '@/components/ui/

### EKS-SRC-01817 — ============================================================================

- Ruta: `backend/modules/crm/schemas.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - CRM Enterprise Schemas =================================== Modelos Pydantic para validación de datos CRM nativos. Estas estructuras mapean directamente a las tablas SQL de EDARSAHUB. """ from pydantic import BaseModel, Field, validator from typing import Optional, Li

### EKS-SRC-00151 — Reportes.js

- Ruta: `frontend/src/pages/Reportes.js`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `toast_netpay, rbac_seguridad, ia_agentes`

> import { useEffect, useState, useMemo, useRef, useCallback } from 'react'; import { useSearchParams } from 'react-router-dom'; import logger from '@/services/logger'; import api from '@/lib/api'; import { useAuth } from '@/contexts/AuthContext'; import { fetchUnidadesNegocio, getServerIdFromUnidad } from '@/services/unidadesNegocioService'; import { Button } from '@/components/ui/button'; import {

### EKS-SRC-00507 — Agent-Reach incorporado en EDARSAHUB

- Ruta: `docs/third_party/agent-reach.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `filosofia_bos, finanzas`

> # Agent-Reach incorporado en EDARSAHUB ## Procedencia - Proyecto original: Panniantong/Agent-Reach - Repositorio original: https://github.com/Panniantong/Agent-Reach - Rama externa importada: main - Commit externo importado: 71c541577238d87057af496e9588504e552f8952 - Ruta interna: third_party/agent-reach - Metodo de incorporacion: snapshot versionado mediante git fetch y git read-tree - Licencia d

### EKS-SRC-02266 — En endpoint

- Ruta: `backend/core/auditoria_helpers.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ EDARSA HUB - Helpers de Auditoría para Módulos Financieros ========================================================== Funciones helper para integrar auditoría de forma no invasiva. USO: from core.auditoria_helpers import registrar_auditoria_cxp, registrar_auditoria_tesoreria # En

### EKS-SRC-00399 — P1-FETCH-MIGRATION - REPORTE FINAL

- Ruta: `docs/P1_FETCH_MIGRATION_REPORT.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

> # P1-FETCH-MIGRATION - REPORTE FINAL ## Migración de `fetch` directo a `api.js` centralizado **Fecha Inicio:** 2025-12-27 **Fecha Cierre:** 2025-12-27 (continúa 2025-04-27) **Estado:** COMPLETADO **Responsable:** Agente E1 --- ## 1. RESUMEN EJECUTIVO La fase P1-FETCH-MIGRATION ha sido completada exitosamente. Se migraron **todas las llamadas `fetch` nativas** en los archivos detectados durante el 

### EKS-SRC-00388 — ENTREGABLES - IMPLEMENTACIÓN DE AUDITORÍA Y ANÁLISIS RBAC

- Ruta: `docs/ENTREGABLES_AUDITORIA_RBAC.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas`

> # ENTREGABLES - IMPLEMENTACIÓN DE AUDITORÍA Y ANÁLISIS RBAC **Fecha:** Diciembre 2025 **Estado:** IMPLEMENTACIÓN PARCIAL + ANÁLISIS COMPLETO --- ## 1. AUDITORÍA FINANCIERA (IMPLEMENTADO) ### 1.1 Script SQL de la Tabla Final **Archivo:** `/app/backend/sql/auditoria_financiera.sql` ```sql CREATE TABLE auditoria_financiera ( id BIGINT IDENTITY(1,1) PRIMARY KEY, created_at DATETIME NOT NULL DEFAULT GE

### EKS-SRC-00377 — PROPUESTA DE ARQUITECTURA AJUSTADA

- Ruta: `docs/ARQUITECTURA_PROPINAS_TPV_v3.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

> # PROPUESTA DE ARQUITECTURA AJUSTADA # Módulo de Control y Cuadre de Comisión de Propinas TPV **Versión:** 3.0 **Fecha:** 15 de Abril de 2026 **Autor:** Arquitectura EDARSA HUB **Estado:** PROPUESTA PARA REVISIÓN **Clasificación:** REDISEÑO ARQUITECTÓNICO - MÓDULO FINANCIERO --- ## RESUMEN EJECUTIVO ### Problema Identificado El módulo actual de Propinas TPV fue implementado usando **MongoDB como a

### EKS-SRC-01831 — FINANZAS-TESORERIA-SQL-001: Usar repositorio SQL de Cortes de Caja

- Ruta: `backend/modules/finanzas/tesoreria.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas`

> """ API Router para Tesorería - Cuadre de Cortes Z PROTEGIDO CON RBAC (Fase 3.1) FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL - Fecha: 2026-05-25 - Ya NO usa MongoDB (tesoreria_cuadres_z) como fuente productiva - Usa repository_cuadres_z_edarsahub.py para operaciones de cuadres - ServerID se resuelve desde EDARSAHUB SQL FINANZAS-TESORERIA-SQL-001: Cortes de Caja migrados a SQL - Fecha: 20

### EKS-SRC-00484 — Manuales Operativos - Modelo Cienfuegos

- Ruta: `docs/MANUALES_OPERATIVOS_CIENFUEGOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # Manuales Operativos - Modelo Cienfuegos **Fecha implementación:** 2026-04-19 **Módulo:** `modules/manuales_operativos` **Estado:** OPERATIVO ✅ ## Descripción Sistema de generación automática de documentación operativa cuando los procesos llegan a estados finales (COMPLETADA, CERRADO, APROBADO, RECHAZADO). Los manuales se generan en **formato Cienfuegos**, el estándar de EDARSA para documentación

### EKS-SRC-00356 — P1-FETCH-MIGRATION - DIAGNÓSTICO

- Ruta: `docs/P1_FETCH_MIGRATION_DIAGNOSTICO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> # P1-FETCH-MIGRATION - DIAGNÓSTICO ## Migración de Fetch Directo a api.js Centralizado **Fecha:** 2025-12-27 **Estado:** EN PROGRESO **Objetivo:** Migrar 12 archivos de `fetch` directo a `api.js` --- ## 1. RESUMEN DE ARCHIVOS | # | Archivo | Fetch Calls | Tipo Principal | |---|---------|-------------|----------------| | 1 | Catalogos.js | 6 | GET, POST | | 2 | Finanzas.js | 8 | GET, POST, PUT | | 

### EKS-SRC-00197 — PropinasTPV.jsx

- Ruta: `frontend/src/components/PropinasTPV.jsx`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, finanzas`

> /** * EDARSA HUB - Módulo de Control de Propinas TPV * =============================================== * Refactorizado: Subcomponentes en /components/finanzas/propinas/ * * SUBFASE 3.5: Migrado a endpoints EDARSAHUB v2 * Fuente de datos: EDARSAHUB.propinas_tpv_control * * Tabs: * - Cuadre: Listado y cuadre de propinas por corte * - Configuración: Gestión del % de descuento */ import React, { useSt

### EKS-SRC-00198 — BarraLateral.jsx

- Ruta: `frontend/src/components/BarraLateral.jsx`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad`

> // /app/frontend/src/components/BarraLateral.jsx // Componente de navegación lateral con lógica de Acordeón Exclusivo import React, { useState, useEffect } from 'react'; import { Link, useLocation } from 'react-router-dom'; import { ChevronDown, ChevronRight } from 'lucide-react'; import api from '@/lib/api'; import { menuFallback, subMenusFallback } from '@/config/menuFallback'; const BarraLatera

### EKS-SRC-01223 — Code Quality Stabilization Log

- Ruta: `memory/code_quality_stabilization_log.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # Code Quality Stabilization Log ## Bitácora Técnica de Estabilización **Fecha Inicio:** 2025-12-XX **Fecha Fin:** 2025-12-XX **Commit Base:** ac45d98 **Rama:** stabilize/code-quality-critical-fixes **Estado Final:** ✅ COMPLETADO --- ## Registro de Cambios ### [Fecha] - Inicio de Auditoría - **Acción:** Creación de documentos de auditoría - **Archivos creados:** - `/app/docs/CODE_QUALITY_STABILIZA

### EKS-SRC-01924 — Configuración de conexión

- Ruta: `backend/scripts/create_tablajeria_rbac.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> """ EDARSA HUB - Script RBAC para Tablajería ========================================= Crea módulos, permisos y asignaciones de roles para el módulo de Tablajería. Ejecutar una sola vez para configurar RBAC. Uso: python create_tablajeria_rbac.py """ import pymssql import os from datetime import datetime # Configuración de conexión DB_CONFIG = { 'host': os.environ.get('EDARSAHUB_HOST', os.getenv('E

### EKS-SRC-00191 — RemisionesPage.jsx

- Ruta: `frontend/src/pages/crm/RemisionesPage.jsx`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay, comercial`

> import { useState, useEffect } from 'react'; import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'; import { Button } from '@/components/ui/button'; import { Input } from '@/components/ui/input'; import { Badge } from '@/components/ui/badge'; import { Plus, Truck, Check, DollarSign, Calendar, MapPin, User } from 'lucide-react'; import api from '@/lib/api'; import { toast 

### EKS-SRC-01904 — Módulo padre

- Ruta: `backend/scripts/create_cava_socios_rbac.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> """ EDARSA HUB - Script RBAC para Cava de Socios ============================================= Crea módulos, permisos y asignaciones de roles para el módulo Cava de Socios. Ubicación ERP: 07. Cava de Socios / Socios Cava Tipo: Módulo principal (Inventario en custodia de terceros) Uso: python create_cava_socios_rbac.py """ import pymssql import os from datetime import datetime DB_CONFIG = { 'host':

### EKS-SRC-02321 — Campos técnicos que NUNCA deben salir si el usuario no es admin técnico.

- Ruta: `backend/core/confidencialidad/anonymizer.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, comercial`

> """ AnonymizerService — Enmascaramiento central de confidencialidad comercial. ========================================================================== REGLA DE ORO: el usuario solo ve nombres reales cuando tiene permiso explícito. Si no, recibe etiquetas comparativas anónimas y SIN identificadores técnicos. Decisiones del usuario aplicadas: - (1b) EDARSA = un único grupo provisional (sin entida

### EKS-SRC-02356 — audit_menu_route_integrity.py

- Ruta: `backend/tools/audit_menu_route_integrity.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> from pathlib import Path import re import json from datetime import datetime from core.config.edarsahub_sql import get_edarsahub_connection APP = Path("/app/frontend/src/App.js") OUT_DIR = Path("/app/docs/reports") OUT_DIR.mkdir(parents=True, exist_ok=True) def norm(route): if not route: return "" route = "/" + str(route).strip().strip("/") return "" if route == "/" else route.rstrip("/") def fron

### EKS-SRC-00321 — EDARSA HUB - Matriz de Clasificación Granular de Datos

- Ruta: `docs/MATRIZ_CLASIFICACION_GRANULAR_DATOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial, roadmap_aceptacion`

> # EDARSA HUB - Matriz de Clasificación Granular de Datos ## LIVE FIRST vs EDARSA HUB FIRST por Módulo/Tab/Endpoint **Versión**: 2.0 **Fecha**: 2026-04-22 **Estado**: VIGENTE --- ## NOMENCLATURA Y DEFINICIONES ### Clasificaciones de Fuente de Datos | Clasificación | Código | Descripción | Latencia Aceptable | |--------------|--------|-------------|-------------------| | **LIVE CRÍTICO** | LIVE-C | 

### EKS-SRC-00888 — Fase 1 - Validacion RBAC/Menu

- Ruta: `docs/reports/RBAC_MENU_PHASE1_VALIDATION.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, roadmap_aceptacion`

> # Fase 1 - Validacion RBAC/Menu ## Objetivo Validar que el menu operativo de EDARSAHUB 1.0 se derive de permisos RBAC SQL efectivos y no de permisos visuales inventados en frontend. La Fase 1 no cambia permisos productivos. Deja una prueba repetible para confirmar: - `/api/auth/me/effective-permissions` responde desde RBAC SQL canonico. - `/api/auth/me/menu-permissions` deriva `permisos_modulos` d

### EKS-SRC-02361 — patch_menu_sql_missing_safe.py

- Ruta: `backend/tools/patch_menu_sql_missing_safe.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `hospitality, comercial, finanzas`

> from core.config.edarsahub_sql import get_edarsahub_connection from datetime import datetime APPLY = True # cambia a True después de revisar DRY_RUN CANDIDATES = [ ("SISTEMA", "sistema.centro_excepciones", "Centro de Excepciones", "Excepciones y alertas operativas", "ShieldAlert", "/admin/centro-excepciones", "centro_excepciones"), ("COMERCIAL", "comercial.pricing_ia", "Pricing IA", "Pricing e int

### EKS-SRC-01772 — comandero_terminal_ui.ts

- Ruta: `backend/modules/edge/comandero_terminal_ui.ts`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `hospitality`

> // backend/modules/edge/comandero_terminal_ui.ts import { TicketFinanciero, ProductoUniversal, UnidadNegocio } from "../contract/edarsa_contracts"; export interface MesaEstadoUI { id_mesa: string; estado: 'VERDE' | 'AMARILLO' | 'ROJO'; minutos_inactividad: number; tipo_comensal: 'PUBLICO' | 'SOCIO_CAVA' | 'INVERSIONISTA' | 'PERSONAL' | null; } export class ComanderoAlphaTerminalUI { private dispos

### EKS-SRC-01837 — ============================================================================

- Ruta: `backend/modules/finanzas/cuentas_por_pagar.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas`

> """ EDARSA HUB - Cuentas por Pagar (Facturas Pendientes) ===================================================== Módulo para gestionar facturas pendientes de pago agrupadas por proveedor. PROTEGIDO CON RBAC (Fase 3.1) V1.0: lectura SQL-first no-live desde dbo.Finanzas_CxP_Sync - Decisiones de pago en dbo.Finanzas_CxP_DecisionesPago - Sin demo, MongoDB ni conexiones live en endpoints Datos a mostrar:

### EKS-SRC-01677 — === WORKFLOW SCHEMAS ===

- Ruta: `backend/modules/fase2_operativo/api_schemas.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Schemas de Request/Response para Endpoints Fase 2A CAB-003 | EDARSA HUB Define los modelos Pydantic para validación de entradas y salidas HTTP. """ from pydantic import BaseModel, Field from typing import Optional, List, Dict, Any from datetime import datetime from .schemas.enums

### EKS-SRC-01867 — ============================================================================

- Ruta: `backend/modules/finanzas/propinas_tpv/models.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Modelos Pydantic para el módulo de Control de Propinas TPV FASE 1 MVP - Solo SoftRestaurant CAB Aprobado: 2026-04-14 """ from pydantic import BaseModel, Field from typing import Optional, List from datetime import datetime from enum import Enum # =================================

### EKS-SRC-01052 — PROPUESTA FORMAL: Recuperar Contraseña (TEMPORAL - SOLO PREVIEW)

- Ruta: `docs/proposals/PROP-001-recuperar-contrasena.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # PROPUESTA FORMAL: Recuperar Contraseña (TEMPORAL - SOLO PREVIEW) **ID:** PROP-001 **Fecha:** 04-Mayo-2026 **Estado:** PENDIENTE APROBACIÓN **Autor:** Agente E1 **Clasificación:** SOLUCIÓN OPERATIVA TEMPORAL --- ## ⚠️ DECLARACIÓN ARQUITECTÓNICA OBLIGATORIA ``` ╔══════════════════════════════════════════════════════════════════════════════╗ ║ ACLARACIÓN DE ALCANCE Y TEMPORALIDAD ║ ╠═══════════════

### EKS-SRC-00274 — UploadInvoicePage.jsx

- Ruta: `frontend/src/portal/pages/UploadInvoicePage.jsx`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay`

> /** * Portal Proveedores - Subir Factura * FASE AUTH-SECURITY-01: Usa credentials: 'include' para cookie httpOnly */ import React, { useState, useRef } from 'react'; import { toast } from 'sonner'; import { Upload, FileText, File, X, CheckCircle, AlertCircle } from 'lucide-react'; const UPLOAD_DISABLED_MESSAGE = 'Carga CFDI pendiente de flujo SQL canónico autorizado.'; export default function Uplo

### EKS-SRC-01692 — Fase 2C.1 - Responsabilidad Económica

- Ruta: `backend/modules/fase2_operativo/schemas/enums.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Enumeraciones compartidas para el módulo operativo Fase 2A CAB-003 | EDARSA HUB Estas enumeraciones definen los estados y tipos válidos para el flujo de trabajo de inventarios. """ from enum import Enum class EstadoWorkflow(str, Enum): """Estados posibles de un workflow de invent

### EKS-SRC-01900 — Acciones requeridas que NO existen en el catalogo base

- Ruta: `backend/scripts/create_comercial_pricing_rbac.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> """ EDARSA HUB - Seed RBAC del modulo Comercial Pricing/Benchmark ============================================================= Crea (idempotente) los modulos, acciones y permisos por rol que requieren los endpoints de Pricing IA / Benchmark (`routes_pricing_ia.py`, `routes_pricing_ai.py`). Los endpoints usan permisos con formato punto/minusculas, p.ej.: comercial.benchmark.ver / .validar comercia

### EKS-SRC-01337 — EDARSA Copilot Supervisor

- Ruta: `.github/agents/edarsa-copilot-supervisor.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

> --- name: EDARSA Copilot Supervisor description: Coordinador de GitHub Copilot para EDARSAHUB. Orquesta Auditor, Coder y Validator sin modificar archivos directamente. tools: ["search", "read", "execute"] handoffs: - label: Pasar a EDARSA Auditor agent: edarsa-auditor prompt: "Audita este tema con evidencia exacta. No modifiques archivos." send: false - label: Pasar a EDARSA Coder agent: edarsa-co

### EKS-SRC-01994 — ningún turno canónico debe ser el LEGACY

- Ruta: `backend/tests/test_turnos_operativos_canonicos.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos`

> """ Regresión — Turnos Operativos Canónicos (Desayuno/Comida/Cena) NO-LIVE ====================================================================== Blinda los fixes 2026-06-10: 1. `operational_window._get_turnos_unidad` leía la columna inexistente `unidad_negocio_pk` (real: `unidad_negocio_id`) y asumía dict-cursor → SIEMPRE caía al fallback hardcodeado. Ahora lee los turnos configurados. 2. El turn

### EKS-SRC-00835 — Fase 2 - API real y roles vacios

- Ruta: `docs/reports/RBAC_MENU_PHASE2_API_AND_ROLE_GAP.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `rbac_seguridad, finanzas`

> # Fase 2 - API real y roles vacios ## Objetivo Cerrar la validacion operativa despues de la Fase 1 SQL: - Ejecutar `validate_rbac_menu_phase1.py` contra usuarios reales. - Revisar si los 8 roles activos sin permisos afectan usuarios reales. - Bloquear el paso a produccion si existe algun usuario activo cuyo acceso depende solo de roles vacios. - Preparar la decision posterior sobre el fallback vis

### EKS-SRC-00674 — P0 REGRESIÓN CRÍTICA — COMERCIAL CIENFUEGOS

- Ruta: `docs/reports/p0_regresion_comercial_cienfuegos.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, comercial, finanzas`

> # P0 REGRESIÓN CRÍTICA — COMERCIAL CIENFUEGOS > Fecha: 2026-05-01 > Estado: **✅ RESUELTO** (Guard Clause + mes_min + ventas_año corregidos) --- ## 1. Resumen del Problema El módulo Comercial para la unidad de negocio CIENFUEGOS mostraba "Sin datos" en varios tabs, aunque el backend contenía información válida. El problema se manifestaba específicamente cuando se consultaba el mes actual (Mayo 2026

### EKS-SRC-01982 — test_tesoreria_access_fail_closed.py

- Ruta: `backend/tests/test_tesoreria_access_fail_closed.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, finanzas`

> from __future__ import annotations from pathlib import Path import pytest from fastapi import HTTPException from modules.finanzas import tesoreria_access as module def _unit( *, unit_id="unit-a", code="UNIT-A", name="Unidad A", company="company-a", server="server-a", branch="branch-a", active_units=1, ): return module.TesoreriaUnit( unidad_negocio_pk=unit_id, unidad_negocio_codigo=code, unidad_neg

### EKS-SRC-00583 — AUDITORÍA TÉCNICA — FASE 4 TESORERÍA

- Ruta: `docs/reports/auditoria_finanzas_fase4_tesoreria.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # AUDITORÍA TÉCNICA — FASE 4 TESORERÍA **Fecha:** 1 Mayo 2026 **Estado:** AUDITORÍA COMPLETADA - PENDIENTE AUTORIZACIÓN PARA IMPLEMENTAR --- ## 1. RESUMEN EJECUTIVO ### Estado Actual de Tesorería El módulo actual denominado "Tesorería" en EDARSAHUB **NO es un módulo de tesorería completo**. Actualmente solo implementa: - **Cuadre de Cortes Z**: Conciliación de efectivo en caja vs. cortes de venta 

### EKS-SRC-00879 — EJECUCIÓN FINANZAS — FASE 4 TESORERÍA

- Ruta: `docs/reports/ejecucion_finanzas_fase4_tesoreria.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # EJECUCIÓN FINANZAS — FASE 4 TESORERÍA **Fecha de Inicio:** 1 Mayo 2026 **Estado:** EN PROGRESO --- # SUBFASE 4.1 — PREPARACIÓN EDARSAHUB CUADRES Z **Fecha de Ejecución:** 1 Mayo 2026 **Estado:** ✅ COMPLETADA --- ## 1. RESUMEN EJECUTIVO Se preparó EDARSAHUB para recibir Cuadres Z como fuente de verdad financiera, creando: | Componente | Descripción | Estado | |------------|-------------|--------|

### EKS-SRC-01687 — Enumeraciones

- Ruta: `backend/modules/fase2_operativo/schemas/__init__.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Schemas Pydantic para Fase 2A - Módulo Operativo CAB-003 | EDARSA HUB Exporta todos los schemas del módulo para facilitar imports. """ # Enumeraciones from .enums import ( EstadoWorkflow, TipoTarea, EstadoTarea, TipoJustificacion, DecisionAuditoria, ) # Schemas de Workflow from .

### EKS-SRC-00504 — validacion_post_migracion_finanzas.json

- Ruta: `docs/audits/validacion_post_migracion_finanzas.json`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay, sql_datos, rbac_seguridad, finanzas`

> { "file": "/app/frontend/src/pages/Finanzas.js", "lines": 1482, "corporate_filters": [ { "line": 26, "code": "import { useCorporateFilters, CorporateFiltersProvider } from '../filters/CorporateFiltersProvider';" }, { "line": 38, "code": "<CorporateFiltersProvider scope=\"finanzas\">" }, { "line": 40, "code": "</CorporateFiltersProvider>" }, { "line": 51, "code": "} = useCorporateFilters();" } ], "

### EKS-SRC-00655 — FASE B-P0-B: Validación y Creación DDL para fase2_operativo

- Ruta: `docs/reports/FASE_B_P0_B_DDL_FASE2_OPERATIVO_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # FASE B-P0-B: Validación y Creación DDL para fase2_operativo **Fecha:** 25 Mayo 2026 **Fase:** B-P0-B **Módulo:** fase2_operativo **Objetivo:** Crear tablas SQL faltantes respetando patrones EDARSAHUB --- ## 1. TABLA COMPARATIVA DE DECISIONES | # | Nombre Propuesto Original | Nombre Final Validado | Patrón/Módulo | Equivalente Existente | Decisión | Motivo | |---|---------------------------|-----

### EKS-SRC-01695 — Workflow Service

- Ruta: `backend/modules/fase2_operativo/services/__init__.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Services para Fase 2A - Módulo Operativo CAB-003 | EDARSA HUB Exporta todos los services del módulo para facilitar imports. """ from .workflow_service import ( WorkflowService, WorkflowServiceError, WorkflowNoEncontradoError, TransicionInvalidaError, WorkflowYaExisteError, ) from

### EKS-SRC-00378 — ADENDA ARQUITECTÓNICA

- Ruta: `docs/ARQUITECTURA_PROPINAS_TPV_v3_ADENDA_CORTES_Z.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

> # ADENDA ARQUITECTÓNICA # Extensión: Módulo de Cuadre de Cortes Z bajo Principio SQL Server **Versión:** 3.1 **Fecha:** 15 de Abril de 2026 **Autor:** Arquitectura EDARSA HUB **Estado:** PROPUESTA PARA REVISIÓN **Documento Padre:** `ARQUITECTURA_PROPINAS_TPV_v3.md` --- ## RESUMEN EJECUTIVO ### Objetivo de esta Adenda Extender la arquitectura definida para Propinas TPV al módulo de **Cuadre de Cort

### EKS-SRC-00562 — Auditoría Finanzas.js para migración Corporate Filters

- Ruta: `docs/reports/AUDITORIA_FINANZAS_CORPORATE_FILTERS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas`

> # Auditoría Finanzas.js para migración Corporate Filters Fecha: Thu Jun 4 19:43:06 UTC 2026 ## Objetivo Auditar `Finanzas.js` después de migración inicial a Corporate Filters. Este script no modifica código. ## Estado actual Finanzas.js ya tiene: - CorporateFiltersProvider como wrapper - useCorporateFilters() para obtener unidades - fetchUnidadesNegocio eliminado ## Métricas básicas ```text 1482 /

### EKS-SRC-00681 — AUDITORÍA TÉCNICA — FINANZAS FASE 3: PROPINAS TPV

- Ruta: `docs/reports/auditoria_finanzas_fase3_propinas_tpv.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # AUDITORÍA TÉCNICA — FINANZAS FASE 3: PROPINAS TPV **Fecha de Auditoría:** 2026-05-01 **Estado:** AUDITORÍA COMPLETADA **Versión:** 1.0 --- ## 1. RESUMEN EJECUTIVO La auditoría técnica de Propinas TPV revela que: 1. **Existen tablas en EDARSAHUB** pero están **vacías** (0 registros de control). 2. **El módulo actual usa MongoDB** como destino de datos (no EDARSAHUB). 3. **Solo soporta SoftRestaur

### EKS-SRC-00572 — FIX_PROYECCION_MENSUAL_DIAS_OPERATIVOS

- Ruta: `docs/reports/FIX_PROYECCION_MENSUAL_DIAS_OPERATIVOS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial, finanzas`

> # FIX_PROYECCION_MENSUAL_DIAS_OPERATIVOS ## Resumen Ejecutivo **FIX COMPLETADO EXITOSAMENTE** ✅ La proyección mensual del Tablero Ejecutivo ahora usa la fórmula canónica correcta con días transcurridos operativos de México, en lugar de días con datos registrados. | Unidad | Ventas | Proyección ANTES | Proyección DESPUÉS | Esperada | |--------|--------|-----------------|-------------------|--------

### EKS-SRC-00927 — MENU_ROUTE_INTEGRITY_20260623_114539.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_114539.json`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_114539", "frontend_routes_count": 58, "sql_menus_count": 64, "frontend_without_sql_menu_actionable": [], "frontend_without_sql_menu_classified": [ { "ruta": "/admin", "componente": "AdminHub", "classification": "hub_internal", "decision": "no_menu_sql", "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente." }, { "ruta": "/admin/da

### EKS-SRC-00842 — MENU_ROUTE_INTEGRITY_20260623_120032.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_120032.json`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_120032", "frontend_routes_count": 58, "sql_menus_count": 64, "frontend_without_sql_menu_actionable": [], "frontend_without_sql_menu_classified": [ { "ruta": "/admin", "componente": "AdminHub", "classification": "hub_internal", "decision": "no_menu_sql", "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente." }, { "ruta": "/admin/da

### EKS-SRC-00813 — MENU_ROUTE_INTEGRITY_20260623_120401.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_120401.json`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_120401", "frontend_routes_count": 58, "sql_menus_count": 60, "frontend_without_sql_menu_actionable": [], "frontend_without_sql_menu_classified": [ { "ruta": "/admin", "componente": "AdminHub", "classification": "hub_internal", "decision": "no_menu_sql", "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente." }, { "ruta": "/admin/da

### EKS-SRC-00853 — MENU_ROUTE_INTEGRITY_20260623_121337.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_121337.json`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_121337", "frontend_routes_count": 67, "sql_menus_count": 60, "frontend_without_sql_menu_actionable": [], "frontend_without_sql_menu_classified": [ { "ruta": "/admin", "componente": "AdminHub", "route_type": "screen", "classification": "hub_internal", "decision": "no_menu_sql", "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente."

### EKS-SRC-00883 — MENU_ROUTE_INTEGRITY_20260623_122340.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_122340.json`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_122340", "frontend_routes_count": 78, "sql_menus_count": 60, "frontend_without_sql_menu_actionable": [], "frontend_without_sql_menu_classified": [ { "ruta": "/admin", "componente": "AdminHub", "route_type": "screen", "classification": "hub_internal", "decision": "no_menu_sql", "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente."

### EKS-SRC-00661 — MENU_ROUTE_INTEGRITY_20260623_123526.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_123526.json`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_123526", "frontend_routes_count": 78, "sql_menus_count": 60, "frontend_without_sql_menu_actionable": [], "frontend_without_sql_menu_classified": [ { "ruta": "/admin", "componente": "AdminHub", "route_type": "screen", "classification": "hub_internal", "decision": "no_menu_sql", "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente."

### EKS-SRC-00973 — FIX P0: Scheduler FechaOperacion ORIGEN/130QRO

- Ruta: `docs/reports/FIX_P0_SCHEDULER_FECHA_OPERACION_ORIGEN.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, comercial, finanzas`

> # FIX P0: Scheduler FechaOperacion ORIGEN/130QRO **Fecha**: 2026-05-15 **Estado**: COMPLETADO ✅ **Prioridad**: P0 (Crítico) --- ## 1. Resumen Ejecutivo Se corrigió el job de sincronización `sync_comercial_abiertas_v2_job.py` para que las unidades MPRO (ORIGEN y 130QRO) calculen correctamente la `FechaOperacion` usando la ventana operativa del restaurante, en lugar de la fecha calendario. **Resulta

### EKS-SRC-00025 — Robot NetPay Manager Downloader para EDARSAHUB

- Ruta: `netpay_robot_edarsahub/netpay_robot_edarsahub/README.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `toast_netpay, finanzas`

> # Robot NetPay Manager Downloader para EDARSAHUB Robot base para descargar reportes de NetPay Manager y alimentar el pipeline de conciliaciones de EDARSAHUB SQL. ## Alcance incluido - Login controlado a `https://manager.netpay.com.mx`. - Detección de MFA/captcha sin intentar evadirlo. - Selección/validación de empresa esperada. - Descarga de reportes: - `DETALLE_TRANSACCIONES`: Reportes → Transacc

### EKS-SRC-01678 — SQL Base (FASE B-P0-C)

- Ruta: `backend/modules/fase2_operativo/repositories/__init__.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repositories para Fase 2A - Módulo Operativo CAB-003 | EDARSA HUB FASE B-P1-E: Todos los repositories migrados a EDARSAHUB SQL Server - CERO MongoDB productivo - CERO conexiones LIVE - SQL explícito en todos los repositories Exporta todos los repositories del módulo para facilita

### EKS-SRC-00723 — FASE B-P1-E + B-P2: Migración Completa de Repositories y Services

- Ruta: `docs/reports/FASE_B_P1_E_P2_REPOSITORIES_SERVICES_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, comercial, roadmap_aceptacion`

> # FASE B-P1-E + B-P2: Migración Completa de Repositories y Services **Fecha:** 2025-05-26 **Estado:** ✅ COMPLETADO (98% - 1 servicio pendiente) **Módulo:** `fase2_operativo` --- ## 1. Resumen Ejecutivo Se completó la migración de: - **8 repositorios** de MongoDB a SQL Server EDARSAHUB - **16 servicios** de acceso directo MongoDB a SQL-only ### Resultados FASE B-P1-E (Repositories) | Repositorio | 

### EKS-SRC-01698 — Estilos predefinidos

- Ruta: `backend/modules/fase2_operativo/services/excel_service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Servicio de Generación de Excel CAB-003 | EDARSA HUB - Fase 2B.2 Genera archivos Excel con el detalle completo de un workflow. Consume datos desde DocumentDataService (fuente única). """ from typing import Dict, Any from datetime import datetime, timezone from io import BytesIO i

### EKS-SRC-01100 — AUDITORÍA MONGO — RUTAS ACTIVAS

- Ruta: `docs/auditorias/AUDITORIA_MONGO_RUTAS_ACTIVAS_20260604.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUDITORÍA MONGO — RUTAS ACTIVAS Fecha: 2026-06-05 00:02:31 Objetivo: identificar si archivos con MongoDB son consumidos por rutas/endpoints activos. ## Archivos con MongoDB detectados Total: 45 - `backend/core/auditoria.py` - `backend/core/auth/user_repository_sql.py` - `backend/core/centro_control/recipients_manager.py` - `backend/core/communications/scripts/__init__.py` - `backend/core/connect

### EKS-SRC-00960 — AUDITORÍA TÉCNICA - MENÚ FINANZAS Y CONTROL PRESUPUESTAL

- Ruta: `docs/reports/auditoria_finanzas_filtros_datos_unidades.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUDITORÍA TÉCNICA - MENÚ FINANZAS Y CONTROL PRESUPUESTAL ## EDARSA HUB - 30 Abril 2026 --- ## 1. RESUMEN EJECUTIVO Se realizó auditoría técnica del menú Finanzas sin modificar código. Se identificaron las siguientes causas raíz de los problemas reportados: | Tab | Problema Principal | Causa Raíz | |-----|-------------------|------------| | **Dashboard** | $0 en todos los KPIs | Datos hardcodeado

### EKS-SRC-01717 — RBAC - Fase 3.1

- Ruta: `backend/modules/fase2_operativo/routes/auditoria_routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Endpoints de Auditoría CAB-003 | EDARSA HUB - Fase 2A PROTEGIDO CON RBAC (Fase 3.1) Expone la funcionalidad de auditoría vía HTTP. """ from fastapi import APIRouter, HTTPException, Query, Depends from typing import Optional, Dict, Any from ..services.auditoria_service import ( Au

### EKS-SRC-01829 — =========================================================================

- Ruta: `backend/modules/finanzas/repository_cuadres_z_edarsahub.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repository EDARSAHUB para Cuadres Z Fase 4 - Tesorería - Subfase 4.3 EDARSAHUB como fuente de verdad financiera para Cuadres Z. Tablas utilizadas: - Finanzas_CuadresZ (principal) - Finanzas_Cat_EstatusCuadreZ (catálogo) - Finanzas_Cat_EstatusTesoreria (catálogo) - Finanzas_Cuadre

### EKS-SRC-01954 — !/usr/bin/env python3

- Ruta: `backend/scripts/poblar_ventas_detalle_producto_canonico.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, comercial`

> #!/usr/bin/env python3 """ Poblar detalle canónico de ventas/productos para Inteligencia Comercial. Guardrails: - Dry-run por defecto. - --commit requerido para escribir. - No usa Sync_Sales. - No recalcula KPIs. - No toca frontend, modal ni endpoints. - Solo escribe días que cuadran contra vw_Comercial_KPIs_Diarios_v2_Runtime. - Bloquea días con ventas abiertas/runtime overlay cuando --excluir-ab

### EKS-SRC-00628 — Integración useFinanzasCorporateFilters en Finanzas.js

- Ruta: `docs/reports/INTEGRACION_USE_FINANZAS_CORPORATE_FILTERS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, finanzas`

> # Integración useFinanzasCorporateFilters en Finanzas.js Fecha: Thu Jun 4 20:04:42 UTC 2026 Backups en: /app/backups/integracion_use_finanzas_corporate_filters_20260604_200442 ## Reglas de este script - Solo modifica Finanzas.js. - No modifica componentes hijos. - No toca PropinasTPV. - No restaura fetchUnidadesNegocio. - No restaura /api/servers. - No restaura /api/sucursales. - Mantiene props co

### EKS-SRC-01665 — Estados de clasificación comercial (FASE 1C-3G-E3-R1)

- Ruta: `backend/modules/comercial/services/precios_vinos_service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `conectores_universales, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Servicio de Cálculo de Precio Sugerido para Vinos - FASE 1C-3G-E Este módulo calcula el precio sugerido para productos clasificados como vino usando la regla de precio por rango configurada en EDARSAHUB SQL. ACLARACIÓN CONCEPTUAL (Corrección FASE 1C-3G-E): La tabla de rangos NO c

### EKS-SRC-01716 — RBAC - Fase 3.1

- Ruta: `backend/modules/fase2_operativo/routes/documentos_routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Rutas de Documentos - API para generación de documentos. CAB-003 | EDARSA HUB - Fase 2B.2 / 2B.3 PROTEGIDO CON RBAC (Fase 3.1) Endpoints para generar y descargar documentos (Excel, PDF). """ from fastapi import APIRouter, HTTPException, Depends from fastapi.responses import Strea

### EKS-SRC-01688 — auditoria_schemas.py

- Ruta: `backend/modules/fase2_operativo/schemas/auditoria_schemas.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Schemas Pydantic para Auditoría CAB-003 | EDARSA HUB - Fase 2A Define los modelos de datos para las decisiones de auditoría. """ from pydantic import BaseModel, Field from typing import Optional, List from datetime import datetime from .enums import DecisionAuditoria class Decisi

### EKS-SRC-00857 — PILOTO Opción A — Backfill de detalle a Sync_Sales (ESTELAR, mayo 2026)

- Ruta: `docs/reports/PILOTO_OPCION_A_BACKFILL_SYNC_SALES_20260608.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, comercial`

> # PILOTO Opción A — Backfill de detalle a Sync_Sales (ESTELAR, mayo 2026) **Fecha:** 2026-06-08 **Autorización:** Usuario autorizó Opción A (lectura POS en vivo) + piloto controlado (1 unidad, 1 mes, solo detalle). **Regla protegida:** PROHIBIDO tocar/re-derivar `Comercial_KPIs_Diarios_v2` / `vw_*`. Solo `Sync_Sales` (staging). ## Conectividad (paso previo) Las **5 unidades POS son alcanzables** d

### EKS-SRC-00226 — FinanzasCuentasPorPagar.jsx

- Ruta: `frontend/src/components/finanzas/FinanzasCuentasPorPagar.jsx`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, finanzas`

> import React, { useMemo, useState } from 'react'; import { Card, CardContent } from '../ui/card'; import { Button } from '../ui/button'; import { Input } from '../ui/input'; import { Label } from '../ui/label'; import { Building2, RefreshCw, X, Download, CreditCard, ChevronRight, ChevronDown, ChevronUp, PieChart, CheckCircle2, XCircle, FileText, File, FileSpreadsheet } from 'lucide-react'; /** * F

### EKS-SRC-01700 — Validar longitud de comentarios

- Ruta: `backend/modules/fase2_operativo/services/auditoria_service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Servicio de Auditoría de Inventario CAB-003 | EDARSA HUB - Fase 2A Encapsula la lógica de negocio para gestión de decisiones de auditoría. """ from typing import Optional, List, Dict from datetime import datetime, timezone from ..repositories.auditoria_repository import Auditoria

### EKS-SRC-01703 — === OPERACIONES DE INICIO DE WORKFLOW ===

- Ruta: `backend/modules/fase2_operativo/services/operativo_service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Servicio Orquestador Operativo CAB-003 | EDARSA HUB - Fase 2A Coordina el flujo completo de operaciones sobre workflows, tareas, justificaciones y auditoría. Actúa como fachada para operaciones que involucran múltiples servicios. """ from typing import Optional, List, Dict, Any f

### EKS-SRC-00668 — FASE 0 — Auditoría de Cobertura PIC (SOLO LECTURA)

- Ruta: `docs/reports/FASE0_AUDITORIA_COBERTURA_SYNC_SALES_20260607.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> # FASE 0 — Auditoría de Cobertura PIC (SOLO LECTURA) Fecha: 2026-06-07 Alcance: diagnóstico de por qué `Sync_Sales` (detalle de producto) solo tiene 79 tickets, sin realizar cambios. --- ## 1. Métricas comparativas (datos reales) ### A) `dbo.Sync_Sales` (detalle con items JSON) | Métrica | Valor | |---|---| | Tickets (distintos) | **79** | | Líneas de producto (OPENJSON items) | **1,374** | | Rang

### EKS-SRC-01711 — RBAC - Fase 2D

- Ruta: `backend/modules/fase2_operativo/routes/responsabilidad_routes.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Endpoints de Responsabilidad Económica CAB-003 | EDARSA HUB - Fase 2C.1 y 2C.2 PROTEGIDOS CON RBAC (Fase 2D) Expone la funcionalidad de cálculo de impacto económico y aprobaciones vía HTTP. Permisos requeridos por endpoint: - POST /calcular - RESPONSABILIDAD_CALCULAR - GET / - RE

### EKS-SRC-00858 — AUDITORÍA CREDENCIALES HARDCODED EDARSAHUB

- Ruta: `docs/reports/AUDITORIA_CREDENCIALES_HARDCODED_20260604_080239.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUDITORÍA CREDENCIALES HARDCODED EDARSAHUB **Fecha:** 2026-06-04 **Estado:** DOCUMENTADO (Sin modificaciones) --- ## Resumen | Tipo | Cantidad | |------|----------| | Archivos .py con credenciales | 93 | | Archivos .md (documentación) | 41 | | Total ocurrencias | 445 | --- ## Archivos Python con Credenciales (Requieren Limpieza) ```text /app/backend/api/admin_data_quality.py /app/backend/api/adm

### EKS-SRC-01693 — FASE B-P2: Usar repositorio SQL

- Ruta: `backend/modules/fase2_operativo/services/document_data_service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `contratos_canonicos, rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Servicio de Datos para Documentos - Fuente Única de Verdad CAB-003 | EDARSA HUB - Fase 2B.2 Este servicio centraliza la obtención de datos para la generación de documentos (Excel, PDF). Evita duplicación de lógica. """ from typing import Optional, Dict, List, Any from datetime im

### EKS-SRC-00622 — DIAGNÓSTICO: Migración Circuit Breaker de MongoDB a EDARSAHUB SQL

- Ruta: `docs/reports/COMERCIAL_CIRCUIT_BREAKER_MONGO_A_SQL_DIAGNOSTICO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `BORRADOR_CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial, roadmap_aceptacion`

> # DIAGNÓSTICO: Migración Circuit Breaker de MongoDB a EDARSAHUB SQL **Fecha:** 2026-05-17 **Módulo:** Comercial (Tablero Ejecutivo V1) **Estado:** DIAGNÓSTICO COMPLETADO **Prioridad:** P0 - CRÍTICO --- ## 1. RESUMEN EJECUTIVO Se identificó que el módulo Comercial depende de MongoDB para: - Estado de conexión de servidores (`server_status`) - Circuit breaker (`is_server_recently_offline`) - Decisió

### EKS-SRC-00609 — Mongo Sunset Fase 2 — Verificación de Restauración

- Ruta: `docs/reports/MONGO_SUNSET_FASE2_VERIFY_RESTORE_20260607_181818.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> # Mongo Sunset Fase 2 — Verificación de Restauración - **Fecha:** 2026-06-07 18:18:18 - **BACKUP_ROOT:** `/app/backups/mongo_sunset_20260607_181350` - **Sufijo temporal:** `verify_20260607_181818` (bases restauradas y luego eliminadas) - **Log mongorestore:** `/app/backups/mongo_sunset_20260607_181350/mongorestore_verify_20260607_181818.log` - **Resultado global:** ❌ DISCREPANCIAS DETECTADAS (ver 

### EKS-SRC-01702 — Claves de configuración para responsabilidad

- Ruta: `backend/modules/fase2_operativo/services/responsabilidad_service.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Servicio de Responsabilidad Económica CAB-003 | EDARSA HUB - Fase 2C.1 y 2C.2 Lógica de negocio para el cálculo de impacto económico de diferencias de inventario y flujo de aprobaciones. """ from typing import Optional, Dict, List from datetime import datetime, timezone import uu

### EKS-SRC-01681 — Métodos de compatibilidad

- Ruta: `backend/modules/fase2_operativo/repositories/auditoria_repository.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Repositorio para decisiones_auditoria - VERSIÓN SQL CAB-003 | EDARSA HUB - Fase 2A FASE B-P1-E: Migrado a EDARSAHUB SQL Server - CERO MongoDB productivo - SQL explícito contra Workflow_DecisionesAuditoria """ from typing import Optional, List, Dict from .sql_base_repository impor

### EKS-SRC-00964 — FINANZAS-TESORERIA-MONGO-002: Migración Cuadres Z a SQL

- Ruta: `docs/reports/FINANZAS_TESORERIA_MONGO_002_MIGRACION_CUADRES_Z_SQL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial, finanzas`

> # FINANZAS-TESORERIA-MONGO-002: Migración Cuadres Z a SQL **Fase:** FINANZAS-TESORERIA-MONGO-002 **Fecha:** 2026-05-25 **Estado:** COMPLETADO --- ## 1. ESTADO ANTERIOR ### Dependencias MongoDB ```python # tesoreria.py (ANTES) from .repository_cuadres_z import get_cuadres_repository repo = await get_cuadres_repository() # MongoDB ``` ### Colección usada - `tesoreria_cuadres_z` en MongoDB - Endpoint

### EKS-SRC-00626 — Validación post migración Finanzas.js a Corporate Filters

- Ruta: `docs/reports/VALIDACION_POST_MIGRACION_FINANZAS_CORPORATE_FILTERS.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `sql_datos, rbac_seguridad, comercial, finanzas`

> # Validación post migración Finanzas.js a Corporate Filters Fecha: Thu Jun 4 19:44:52 UTC 2026 ## Objetivo Validar que la migración de `Finanzas.js` a Corporate Filters no rompió tabs financieros ni duplicó filtros. ## Reglas - No migrar otro módulo todavía. - No tocar Comercial, Compras ni Dashboard. - No tocar PropinasTPV si ya funciona. - No restaurar `/api/servers`. - No restaurar `/api/sucurs

### EKS-SRC-00107 — Usar labels visibles; evita selectores frágiles.

- Ruta: `netpay_robot_edarsahub/netpay_robot_edarsahub/netpay_robot/portal.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay`

> from __future__ import annotations import asyncio import re import shutil from datetime import date from pathlib import Path from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError from .settings import Settings from .models import ReportType, DownloadResult, ExecutionStatus from .hash_utils import sha256_file MFA_PATTERNS = [ re.compile(r'c[oó]digo.*verific

### EKS-SRC-00109 — NetPay puede traer fecha con hora: 18/06/2026 02:13

- Ruta: `netpay_robot_edarsahub/netpay_robot_edarsahub/netpay_robot/pipeline.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay, comercial`

> from __future__ import annotations from datetime import date from pathlib import Path from decimal import Decimal from .settings import Settings from .crypto import decrypt_secret from .date_ranges import split_date_range from .models import ReportType, DownloadResult from .portal import NetPayPortalRobot from .layouts import detect_layout from .importer import parse_netpay_workbook from .db impor

### EKS-SRC-00748 — DIAGNÓSTICO: Dependencia MongoDB en Tesorería Cuadres Z

- Ruta: `docs/reports/FINANZAS_TESORERIA_MONGO_DEPENDENCIA_CUADRES_DIAGNOSTICO.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, ia_agentes, finanzas`

> # DIAGNÓSTICO: Dependencia MongoDB en Tesorería Cuadres Z **Fase:** FINANZAS-TESORERIA-MONGO-001 **Fecha:** 2026-05-25 **Estado:** DIAGNÓSTICO COMPLETADO --- ## 1. DEPENDENCIAS MONGODB ENCONTRADAS ### 1.1 Archivo Principal **Archivo:** `/app/backend/modules/finanzas/repository_cuadres_z.py` ```python # Línea 18-21: Conexión MongoDB from pymongo import MongoClient mongo_url = os.environ.get('MONGO_

### EKS-SRC-00105 — Implementación recomendada en EDARSAHUB

- Ruta: `netpay_robot_edarsahub/netpay_robot_edarsahub/docs/IMPLEMENTACION_EDARSAHUB.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `toast_netpay, rbac_seguridad, comercial, finanzas`

> # Implementación recomendada en EDARSAHUB ## Ubicación del módulo Menú: ```text Finanzas → Conciliaciones ``` Tabs: ```text Dashboard General Cuadre origen NetPay / Adquirentes Efectivo Banco / Estado de Cuenta Depósitos no identificados Propinas TPV Diferencias y aclaraciones Robot NetPay Importación manual Configuración Logs ``` ## Amarre obligatorio con Cuadre de Cortes Z El robot no reemplaza 

### EKS-SRC-05728 — EDARSA Copilot Supervisor

- Ruta: `.agent-worktrees/enterprise-navigation/.github/agents/edarsa-copilot-supervisor.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> --- name: EDARSA Copilot Supervisor description: Coordinador de GitHub Copilot para EDARSAHUB. Orquesta Auditor, Coder y Validator sin modificar archivos directamente. tools: ["search", "read", "execute"] handoffs: - label: Pasar a EDARSA Auditor agent: edarsa-auditor prompt: "Audita este tema con evidencia exacta. No modifiques archivos." send: false - label: Pasar a EDARSA Coder agent: edarsa-co

### EKS-SRC-03983 — !/usr/bin/env python3

- Ruta: `.agent-worktrees/compras-inventarios/backend/scripts/poblar_ventas_detalle_producto_canonico.py`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad, comercial`

> #!/usr/bin/env python3 """ Poblar detalle canónico de ventas/productos para Inteligencia Comercial. Guardrails: - Dry-run por defecto. - --commit requerido para escribir. - No usa Sync_Sales. - No recalcula KPIs. - No toca frontend, modal ni endpoints. - Solo escribe días que cuadran contra vw_Comercial_KPIs_Diarios_v2_Runtime. - Bloquea días con ventas abiertas/runtime overlay cuando --excluir-ab

### EKS-SRC-01025 — EDARSAHUB SQL Runner Report

- Ruta: `docs/reports/sql_runner_logs/20260602_161833_migrate_017_registrar_inteligencia_comercial_y_transicionales.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial`

> # EDARSAHUB SQL Runner Report - Fecha: 2026-06-02T16:18:33.215366 - Modo: `migrate` - Servidor: `54.39.104.176` - Base de datos: `EDARSAHUB` - Script: `/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql` ## Resultado ERROR ## Detalle ```text Error ejecutando SQL. Se hizo rollback. Detalle: (207, b"Invalid column name 'fecha_registro'.DB-Lib error message 200

### EKS-SRC-00998 — EDARSAHUB SQL Runner Report

- Ruta: `docs/reports/sql_runner_logs/20260602_161912_migrate_017_registrar_inteligencia_comercial_y_transicionales.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, comercial`

> # EDARSAHUB SQL Runner Report - Fecha: 2026-06-02T16:19:12.870279 - Modo: `migrate` - Servidor: `54.39.104.176` - Base de datos: `EDARSAHUB` - Script: `/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql` ## Resultado OK ## Resumen - Batches ejecutados: 1 - Mensaje: Ejecución completada. ### Batch 1 - Tipo: SELECT - Columnas: diagnostico, total_tablas_gobiern

### EKS-SRC-08735 — Login.js

- Ruta: `frontend/src/pages/Login.js`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay`

> import { useState } from 'react'; import { useNavigate, Link } from 'react-router-dom'; import { flushSync } from 'react-dom'; import { useAuth } from '@/contexts/AuthContext'; import api from '@/lib/api'; import { Button } from '@/components/ui/button'; import { Input } from '@/components/ui/input'; import { Label } from '@/components/ui/label'; import { Card, CardContent } from '@/components/ui/

### EKS-SRC-07544 — FINANZAS-TESORERIA-SQL-001: Usar repositorio SQL de Cortes de Caja

- Ruta: `backend/modules/finanzas/tesoreria.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, rbac_seguridad, ia_agentes, finanzas`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ API Router para Tesorería - Cuadre de Cortes Z PROTEGIDO CON RBAC (Fase 3.1) FINANZAS-TESORERIA-MONGO-002: Migrado a EDARSAHUB SQL - Fecha: 2026-05-25 - Ya NO usa MongoDB (tesoreria_cuadres_z) como fuente productiva - Usa repository_cuadres_z_edarsahub.py para operaciones de cuad

### EKS-SRC-08651 — PropinasTPV.jsx

- Ruta: `frontend/src/components/PropinasTPV.jsx`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `sql_datos, finanzas`

> /** * EDARSA HUB - Módulo de Control de Propinas TPV * =============================================== * Refactorizado: Subcomponentes en /components/finanzas/propinas/ * * SUBFASE 3.5: Migrado a endpoints EDARSAHUB v2 * Fuente de datos: EDARSAHUB.propinas_tpv_control * * Tabs: * - Cuadre: Listado y cuadre de propinas por corte * - Configuración: Gestión del % de descuento */ import React, { useSt

### EKS-SRC-08787 — UploadInvoicePage.jsx

- Ruta: `frontend/src/portal/pages/UploadInvoicePage.jsx`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `toast_netpay`

> /** * Portal Proveedores - Subir Factura * FASE AUTH-SECURITY-01: Usa credentials: 'include' para cookie httpOnly */ import React, { useState, useRef } from 'react'; import { toast } from 'sonner'; import { Upload, FileText, File, X, CheckCircle, AlertCircle } from 'lucide-react'; const API_URL = process.env.REACT_APP_BACKEND_URL || ''; export default function UploadInvoicePage({ supplier, onNavig

### EKS-SRC-07484 — RBAC - Fase 2D

- Ruta: `backend/modules/fase2_operativo/routes/responsabilidad_routes.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `7/10`
- Estado previo: `CANDIDATO`
- Temas: `rbac_seguridad`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Endpoints de Responsabilidad Económica CAB-003 | EDARSA HUB - Fase 2C.1 y 2C.2 PROTEGIDOS CON RBAC (Fase 2D) Expone la funcionalidad de cálculo de impacto económico y aprobaciones vía HTTP. Permisos requeridos por endpoint: - POST /calcular - RESPONSABILIDAD_CALCULAR - GET / - RE

### EKS-SRC-07504 — Claves de configuración para responsabilidad

- Ruta: `backend/modules/fase2_operativo/services/responsabilidad_service.py`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `7/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService """ Servicio de Responsabilidad Económica CAB-003 | EDARSA HUB - Fase 2C.1 y 2C.2 Lógica de negocio para el cálculo de impacto económico de diferencias de inventario y flujo de aprobaciones. """ from typing import Optional, Dict, List from datetime import datetime, timezone import uu

### EKS-SRC-00116 — EDARSA Coder Skill

- Ruta: `.agents/skills/edarsa-coder/SKILL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `3/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos, comercial`

> --- name: edarsa-coder description: Implementador controlado de EDARSAHUB para aplicar patches minimos despues de evidencia del auditor. --- # EDARSA Coder Skill Usa esta skill solo cuando el usuario autorice implementar. ## Reglas - Cambios minimos. - No tocar produccion. - No push/deploy. - No crear tablas/columnas/migraciones sin autorizacion. - No mocks. - No hardcodes. - No MongoDB. - No live

### EKS-SRC-00118 — EDARSA Auditor Skill

- Ruta: `.agents/skills/edarsa-auditor/SKILL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `3/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

> --- name: edarsa-auditor description: Auditor de EDARSAHUB para inspeccionar codigo, SQL solo lectura, fuentes canonicas, KPIs, RBAC y riesgos sin modificar archivos. --- # EDARSA Auditor Skill Usa esta skill cuando la tarea sea auditar, investigar, comparar KPIs, revisar fuentes o detectar riesgos. ## Reglas - No modificar archivos. - No hacer patch. - No ejecutar SQL destructivo. - Solo usar `SE

### EKS-SRC-01335 — EDARSA Auditor

- Ruta: `.github/agents/edarsa-auditor.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `3/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

> --- name: EDARSA Auditor description: Auditor tecnico de EDARSAHUB. Solo lectura, evidencia exacta, sin patches. tools: [execute, read, search] handoffs: - label: Pasar a EDARSA Coder agent: edarsa-coder prompt: "Implementa solo el cambio minimo basado en la evidencia anterior. No amplíes alcance." send: false --- # EDARSA Auditor Actuas como auditor tecnico de EDARSAHUB. ## Prohibido - No modific

### EKS-SRC-01336 — EDARSA Validator

- Ruta: `.github/agents/edarsa-validator.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `3/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

> --- name: EDARSA Validator description: Validador independiente de diff, build, DB safety, RBAC y reglas canonicas. tools: ["search", "read", "execute"] handoffs: - label: Regresar a EDARSA Auditor agent: edarsa-auditor prompt: "Reaudita los riesgos detectados por Validator y determina si se corrige o revierte." send: false --- # EDARSA Validator Actuas como validador independiente. ## No debes - 

### EKS-SRC-01334 — EDARSAHUB Codex Auditor

- Ruta: `.github/agents/edarsahub-codex-auditor.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `3/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes, comercial`

> --- name: edarsahub-codex-auditor description: Auditor especializado para inspeccion y validacion controlada de EDARSAHUB V1.0. Solo lectura, evidencia exacta y SQL SELECT. No modifica archivos. argument-hint: Describe la tarea de inspeccion o validacion. Ejemplo: "inspecciona Comercial.js y detecta endpoints legacy sin modificar archivos". tools: ['read', 'search', 'execute'] --- # EDARSAHUB Code

### EKS-SRC-01241 — EDARSA HUB - CRM COMERCIAL ENTERPRISE

- Ruta: `memory/PRD.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `2/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `hospitality, constitucion_maximas, contratos_canonicos, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # EDARSA HUB - CRM COMERCIAL ENTERPRISE ## Product Requirements Document ### Original Problem Statement Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB. ### Core Requirements - **ESTRICTA PROHIBICIÓN**: Uso del subagente `testing_agent_v3_fork` totalmente prohibido - **MÁXIMA ARQUITECTÓNICA (NO-LIVE)**: EDARSAHUB SQL es la ÚNICA fuente de verdad product

### EKS-SRC-00117 — EDARSA Committer Skill

- Ruta: `.agents/skills/edarsa-committer/SKILL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `2/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> --- name: edarsa-committer description: Committer controlado de EDARSAHUB para crear commits locales despues de Validator APROBADO, sin push ni deploy. --- # EDARSA Committer Skill Usar cuando el usuario autoriza commit despues de Auditor, Coder y Validator. ## Reglas - Solo rama `Edarsahub_Desarrollo`. - No push. - No deploy. - No Produccion. - No `.env`. - No secretos. - No SQL. - No reset. - No

### EKS-SRC-00115 — EDARSA Validator Skill

- Ruta: `.agents/skills/edarsa-validator/SKILL.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `2/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `constitucion_maximas, rbac_seguridad, ia_agentes, cambios_atomicos`

> --- name: edarsa-validator description: Validador independiente de EDARSAHUB para revisar diff, build, py_compile, DB safety, RBAC y reglas canonicas. --- # EDARSA Validator Skill Usa esta skill despues de un patch. ## Validar - Rama correcta. - Working tree. - Diff. - `git diff --check`. - `py_compile` para Python modificado. - Build frontend si aplica. - No MongoDB nuevo. - No live nuevo. - No D

### EKS-SRC-01339 — EDARSA Committer

- Ruta: `.github/agents/edarsa-committer.agent.md`
- Fuente: `WORKSPACE_ACTUAL`
- Autoridad: `2/10`
- Estado previo: `OFICIALIDAD_POR_VALIDAR`
- Temas: `rbac_seguridad, ia_agentes`

> --- name: EDARSA Committer description: Committer controlado de EDARSAHUB. Solo crea commits locales despues de Validator APROBADO. No hace push ni deploy. --- # EDARSA Committer Rol: crear commits locales seguros en `Edarsahub_Desarrollo` despues de validacion completa. ## Reglas obligatorias - Solo trabajar en `/app`. - Solo trabajar en rama `Edarsahub_Desarrollo`. - No hacer push. - No hacer de

### EKS-SRC-08868 — EDARSA HUB - CRM COMERCIAL ENTERPRISE

- Ruta: `memory/PRD.md`
- Fuente: `HOSPITALITY_BRANCH`
- Autoridad: `2/10`
- Estado previo: `DEPRECADO_CANDIDATO`
- Temas: `hospitality, constitucion_maximas, contratos_canonicos, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # EDARSA HUB - CRM COMERCIAL ENTERPRISE ## Product Requirements Document ### Original Problem Statement Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB. ### Core Requirements - **ESTRICTA PROHIBICIÓN**: Uso del subagente `testing_agent_v3_fork` totalmente prohibido - **MÁXIMA ARQUITECTÓNICA (NO-LIVE)**: EDARSAHUB SQL es la ÚNICA fuente de verdad product

