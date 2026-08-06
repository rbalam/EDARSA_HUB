# EKS-0001 — Fuente Primaria Hospitality

- Ref auditada: `origin/feature/hospitality-core-20260625_184401`
- Estado: **FUENTE PRIMARIA HISTÓRICA**

## Activos

### EKS-SRC-08029 — EDARSAHUB Hospitality Architecture Book

- Ruta: `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md`
- Autoridad propuesta: `9/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `cb9ed4556f32465b713bbf015cfbb4637d3b2b47321df10542b6686520e04983`
- Temas: `filosofia_bos, hospitality, constitucion_maximas, arquitectura_global, conectores_universales, sql_datos, rbac_seguridad, ia_agentes, finanzas, roadmap_aceptacion`

> # EDARSAHUB Hospitality Architecture Book ## Objetivo Diseñar EDARSAHUB Hospitality como satélite nativo del ERP EDARSAHUB: global, configurable, multiconector, SQL-first, sin MongoDB, sin LIVE operativo y sin duplicar lógica existente. ## Tomos 1. Visión Estratégica 2. Máximas de Arquitectura 3. Arquitectura Empresarial 4. Arquitectura Funcional 5. Arquitectura Backend 6. Arquitectura Frontend / 

### EKS-SRC-08184 — FASE 0.5 - VALIDACIÓN ARQUITECTÓNICA: MENÚS GOBERNADOS Y COMERCIAL/VENTAS

- Ruta: `docs/reports/FASE_0_5_VALIDACION_ARQUITECTURA_MENUS_Y_COMERCIAL.md`
- Autoridad propuesta: `9/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `9b88029466133b8cdd30d23d42ee021a432b4165bd0e11b78065d71352dccd7d`
- Temas: `hospitality, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # FASE 0.5 - VALIDACIÓN ARQUITECTÓNICA: MENÚS GOBERNADOS Y COMERCIAL/VENTAS **Fecha:** 24 Mayo 2026 **Autor:** Arquitecto ERP EDARSAHUB **Estado:** VALIDACIÓN COMPLETADA --- ## 1. RESUMEN EJECUTIVO La FASE 0 (Sistema de Menús Gobernados) fue implementada correctamente. Se crearon las tablas necesarias, los 27 módulos según el manifiesto ERP están registrados y el endpoint funciona. Sin embargo, se

### EKS-SRC-07548 — hospitality_rules.py

- Ruta: `backend/modules/hospitality/services/hospitality_rules.py`
- Autoridad propuesta: `8/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `f6dd677933ffa57256491548176f4225527610c6a49f3befd64519b0bfaeb5c9`
- Temas: `hospitality`

> """ Reglas base EDARSAHUB Hospitality. No contiene lógica operativa todavía. """ HOSPITALITY_MAXIMAS = [ "NO_ROMPER", "NO_MONGO", "NO_LIVE_OPERATIVO", "SQL_FIRST", "NO_DUPLICAR", "UNIDAD_NEGOCIO_PK", "RBAC_EXISTENTE", "FILTROS_CORPORATIVOS", "SCHEDULER_EXISTENTE", "NOTIFICACIONES_EXISTENTES", "COMANDERO_EXISTENTE", "MULTIDIOMA_GLOBAL", "MULTICONECTIVIDAD", "AUTOMATIZACION_SEGURA", ]

### EKS-SRC-08194 — FASE 1C-0: Diagnóstico Comercial/Ventas para Subfases

- Ruta: `docs/reports/FASE_1C_0_DIAGNOSTICO_COMERCIAL_VENTAS_SUBFASES.md`
- Autoridad propuesta: `8/10`
- Estado propuesto: `BORRADOR_CANDIDATO`
- SHA-256: `555e5cea693acab136a462f509cbb9438ecdad319978e48b24c24d933329386b`
- Temas: `hospitality, sql_datos, rbac_seguridad, comercial`

> # FASE 1C-0: Diagnóstico Comercial/Ventas para Subfases **Fecha**: 2026-05-24 **Hora México**: 12:30 - 13:15 **Ejecutado por**: Agente EDARSA HUB **Estado**: ✅ DIAGNÓSTICO COMPLETADO --- ## 1. Rutas Revisadas ### 1.1 Rutas Frontend (App.js) | Ruta | Estado | Destino/Componente | Clasificación | |------|--------|-------------------|---------------| | `/comercial` | ✓ Existe | `Comercial.js` (Dashbo

### EKS-SRC-08308 — MATRIZ DEFINITIVA — VENTAS DEL DÍA

- Ruta: `docs/reports/MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md`
- Autoridad propuesta: `8/10`
- Estado propuesto: `BORRADOR_CANDIDATO`
- SHA-256: `8145e81fc6bc2abaecb2560d5a208a09d07f16b2dde9c397016b14abc0396b71`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial, roadmap_aceptacion`

> # MATRIZ DEFINITIVA — VENTAS DEL DÍA ## SoftRestaurant / MPRO / Turnos / FechaOperacion / EDARSAHUB **Documento**: MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md **Fecha**: 2026-05-20 **Versión**: 1.0 **Estado**: DISEÑO APROBADO — PENDIENTE IMPLEMENTACIÓN POR FASES --- ## 1. DEFINICIÓN OFICIAL DE VENTAS DEL DÍA ### 1.1 Concepto Operativo **Ventas del Día** NO significa ventas de 00:00 

### EKS-SRC-07458 — comandero_terminal_ui.ts

- Ruta: `backend/modules/edge/comandero_terminal_ui.ts`
- Autoridad propuesta: `7/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `de3e0a97d1adf8ab8e880c9b87a6889a06404878eb77cf4bde8df317c28cf508`
- Temas: `hospitality`

> // backend/modules/edge/comandero_terminal_ui.ts import { TicketFinanciero, ProductoUniversal, UnidadNegocio } from "../contract/edarsa_contracts"; export interface MesaEstadoUI { id_mesa: string; estado: 'VERDE' | 'AMARILLO' | 'ROJO'; minutos_inactividad: number; tipo_comensal: 'PUBLICO' | 'SOCIO_CAVA' | 'INVERSIONISTA' | 'PERSONAL' | null; } export class ComanderoAlphaTerminalUI { private dispos

### EKS-SRC-07738 — patch_menu_sql_missing_safe.py

- Ruta: `backend/tools/patch_menu_sql_missing_safe.py`
- Autoridad propuesta: `7/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `93cc5816ca079e9f64b9e85a4b65480209f87ec12bd7462e029592cc0584c8c9`
- Temas: `hospitality, comercial, finanzas`

> from core.config.edarsahub_sql import get_edarsahub_connection from datetime import datetime APPLY = True # cambia a True después de revisar DRY_RUN CANDIDATES = [ ("SISTEMA", "sistema.centro_excepciones", "Centro de Excepciones", "Excepciones y alertas operativas", "ShieldAlert", "/admin/centro-excepciones", "centro_excepciones"), ("COMERCIAL", "comercial.pricing_ia", "Pricing IA", "Pricing e int

### EKS-SRC-08319 — MENU_ROUTE_INTEGRITY_20260623_114539.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_114539.json`
- Autoridad propuesta: `7/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `4e0ccf0c3170853c71b032f59c3a4ed8d67c1b181f7b4197461fbc7ae3a596da`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_114539", "frontend_routes_count": 58, "sql_menus_count": 64, "frontend_without_sql_menu_actionable": [], "frontend_without_sql_menu_classified": [ { "ruta": "/admin", "componente": "AdminHub", "classification": "hub_internal", "decision": "no_menu_sql", "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente." }, { "ruta": "/admin/da

### EKS-SRC-08321 — MENU_ROUTE_INTEGRITY_20260623_120032.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_120032.json`
- Autoridad propuesta: `7/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `21706d471644f1ad4e0e37a9b80c568c9b0873830428b9ad7c75a3159e73e221`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_120032", "frontend_routes_count": 58, "sql_menus_count": 64, "frontend_without_sql_menu_actionable": [], "frontend_without_sql_menu_classified": [ { "ruta": "/admin", "componente": "AdminHub", "classification": "hub_internal", "decision": "no_menu_sql", "reason": "Hub interno de administracion; no debe contarse como menu operativo independiente." }, { "ruta": "/admin/da

### EKS-SRC-08025 — DIAGNÓSTICO ARQUITECTÓNICO - FASE 1A

- Ruta: `docs/diagnosticos/FASE_1A_DIAGNOSTICO_COMERCIAL_VENTAS.md`
- Autoridad propuesta: `6/10`
- Estado propuesto: `BORRADOR_CANDIDATO`
- SHA-256: `5b905afdcaea99a7f57c2980cd5ce6f5848543e081b747d53234950c71141294`
- Temas: `hospitality, sql_datos, rbac_seguridad, comercial`

> # DIAGNÓSTICO ARQUITECTÓNICO - FASE 1A ## Módulo: Comercial / Ventas **Fecha:** 2026-05-24 **Arquitecto:** E1 (Agente Senior ERP) **Estado:** DIAGNÓSTICO PASIVO COMPLETADO --- ## 1. DIAGNÓSTICO PASIVO ### 1.1 Módulos Frontend Existentes | Ruta | Componente | Estado | |------|------------|--------| | `/comercial` | `Comercial.js` | **BLINDADO** - No modificar | | `/crm/dashboard` | `CRMDashboard.js

### EKS-SRC-08068 — Auditoría de Dependencias MongoDB

- Ruta: `docs/reports/AUDITORIA_DEPENDENCIAS_MONGODB.md`
- Autoridad propuesta: `4/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `a4008142cfa70d6e4e77ca032b95100f3d3d26310f5c58f474554afc1d13eff2`
- Temas: `hospitality, conectores_universales, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # Auditoría de Dependencias MongoDB Generado: 2026-06-02T09:33:47+00:00 ## Coincidencias en backend/frontend/docs ```text /app/backend/init_queries.py:4:from motor.motor_asyncio import AsyncIOMotorClient /app/backend/init_queries.py:10:mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017') /app/backend/init_queries.py:266: client = AsyncIOMotorClient(mongo_url) /app/backend/init_quer

### EKS-SRC-06826 — auditoria_rbac_enterprise_resultado.json

- Ruta: `backend/auditoria_rbac_enterprise_resultado.json`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `7864c0b76e12bd87e1b2b4ebeee93eca3af14ab66eb69322a77a9295a1b529ac`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial, finanzas`

> { "fecha": "2026-06-22T00:28:25.561358", "checks": { "01_ROLES_SIN_PERMISOS": [ { "RolID": 14, "CodigoRol": "CRM_ADMIN", "NombreRol": "CRM_Administrador", "NivelJerarquia": 90, "Activo": true }, { "RolID": 16, "CodigoRol": "CRM_AUDIT", "NombreRol": "CRM_Auditor", "NivelJerarquia": 70, "Activo": true }, { "RolID": 22, "CodigoRol": "GERENTE", "NombreRol": "Gerente", "NivelJerarquia": 70, "Activo": t

### EKS-SRC-07195 — Layout.js

- Ruta: `backend/auditorias_p5/backup_p5_10b_menu_sin_hardcodes_20260606_071843/frontend/src/pages/Layout.js`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `017f53d274fde3027a8f7a7e0ea3b3257e0daf8fd43cd4dff8869ecb1772835c`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial, finanzas`

> import { Outlet, useLocation, Link } from 'react-router-dom'; import { useAuth } from '@/contexts/AuthContext'; import logger from '@/services/logger'; import { Button } from '@/components/ui/button'; import { LayoutDashboard, Server, Package, Bell, Users, LogOut, Menu, X, ShoppingCart, TrendingUp, Database, TableProperties, PieChart, Warehouse, DollarSign, Factory, UserCircle, BarChart3, Clipboar

### EKS-SRC-07964 — AUDITORÍA MONGO LEGACY — EDARSAHUB

- Ruta: `docs/auditorias/AUDITORIA_MONGO_LEGACY_20260604.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `cf60e4eb76b2d6c4c20974b2f01b71662d80a07213f35a16785394f741a01e43`
- Temas: `hospitality, conectores_universales, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUDITORÍA MONGO LEGACY — EDARSAHUB Fecha: 2026-06-04 23:55:46 Objetivo: localizar referencias MongoDB/pymongo/motor y clasificarlas para eliminación o justificación temporal. ## Resumen - Hallazgos totales: **1254** - Riesgo alto: **1069** - Revisar permitido temporal: **185** ## Hallazgos RIESGO_ALTO | Archivo | Línea | Código | |---|---:|---| | `backend/init_queries.py` | 4 | `from motor.motor

### EKS-SRC-08017 — auditoria_live_sql_first_por_modulo.json

- Ruta: `docs/audits/auditoria_live_sql_first_por_modulo.json`
- Autoridad propuesta: `3/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `153d742f202e287d5c0680b60990f9f5c8fd99ae774787d5e83a5207ccd34b9e`
- Temas: `hospitality, conectores_universales, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> { "generated_at": "2026-06-04T19:38:48.583211Z", "total_findings": 4217, "findings": [ { "module": "Comercial", "classification": "PROHIBIDO_POSIBLE_LIVE_VISUAL", "severity": "ALTA", "pattern": "remote POS names", "file": "/app/backend/modules/comercial/adapters.py", "line": 170, "code": "Consulta una API MPRO local y retorna los resultados." }, { "module": "Comercial", "classification": "PROHIBID

### EKS-SRC-08062 — Auditoría de Conexiones Live

- Ruta: `docs/reports/AUDITORIA_CONEXIONES_LIVE.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `d53f57a463fb261940e0f21e5dbad39be60636265a31c735071992d96b7ad836`
- Temas: `hospitality, conectores_universales, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas, roadmap_aceptacion`

> # Auditoría de Conexiones Live Generado: 2026-06-02T09:33:51+00:00 ## Posibles conexiones live ```text /app/backend/init_queries.py:10:mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017') /app/backend/init_queries.py:13:# Consultas MPRO /app/backend/init_queries.py:14:MPRO_QUERIES = { /app/backend/init_queries.py:276: # Insert MPRO queries /app/backend/init_queries.py:277: for quer

### EKS-SRC-08064 — AUDITORIA DE CONEXIONES LIVE

- Ruta: `docs/reports/AUDITORIA_CONEXIONES_LIVE_20260604_042819.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `BORRADOR_CANDIDATO`
- SHA-256: `5ae96e3ce3dc6ad489a2a270500d71c528ba199836e45eb3306248d9bc3b7195`
- Temas: `hospitality, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # AUDITORIA DE CONEXIONES LIVE Fecha: Thu Jun 4 04:28:19 UTC 2026 ## RESUMEN - Total referencias encontradas: 3935 ## DETALLE DE HALLAZGOS ```text /app/backend/modules/comercial/service.py:36:from core.db import execute_sql_query, check_column_exists, get_propina_safe_column, get_propina_safe_column_tempcheques /app/backend/modules/comercial/service.py:105: - por_server_id: {server_id: {codigo, no

### EKS-SRC-08076 — AUDITORÍA JOBS SYNC COMPRAS / INVENTARIOS

- Ruta: `docs/reports/AUDITORIA_JOBS_SYNC_COMPRAS_20260604_053312.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `1966a8b6706474e87dd7cc8a3a1ac6755b03ca674daa4fbac093403475d6260e`
- Temas: `hospitality, conectores_universales, sql_datos, rbac_seguridad, ia_agentes, comercial`

> # AUDITORÍA JOBS SYNC COMPRAS / INVENTARIOS Fecha: Thu Jun 4 05:33:12 UTC 2026 ## 1. Ubicación de archivos sync ```text /app/backend/core/scheduler/jobs/inventarios_detector_job.py /app/backend/core/scheduler/jobs/pedidos_detector_job.py /app/backend/core/scheduler/jobs/sync_compras_job.py /app/backend/modules/compras/sync_service.py /app/backend/modules/tablajeria/sync_service.py ``` ## 2. Conten

### EKS-SRC-08136 — DIAGNÓSTICO MAPEO RBAC MongoDB → Usuario_* SQL

- Ruta: `docs/reports/DIAGNOSTICO_MAPEO_RBAC_MONGO_A_SQL.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `c677719ac62a2eed82894c6c2ea8509d6b1463b52c55c69b46a6eb2b632b131c`
- Temas: `hospitality, conectores_universales, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # DIAGNÓSTICO MAPEO RBAC MongoDB → Usuario_* SQL Generado: 2026-06-02T20:07:06+00:00 ## Objetivo Diagnosticar dependencias de RBAC MongoDB antes de migrar usuarios hacia Usuario_* SQL. ## Regla - No migrar usuarios todavía. - No borrar MongoDB todavía. - No modificar asignaciones de usuarios todavía. - Usuario_* es RBAC SQL canónico. - Sistema_RBAC_* queda como transicional / NO_USAR_NUEVO. ## Col

### EKS-SRC-08185 — FASE 0.6 - REPORTE TÉCNICO

- Ruta: `docs/reports/FASE_0_6_MIGRACION_LAYOUT_MENUS_SQL.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `2c318cd54c89b2d8a755100d1ffd2584305f7c5638e290c049e9749ad3a58e3e`
- Temas: `hospitality, sql_datos, rbac_seguridad, comercial, finanzas`

> # FASE 0.6 - REPORTE TÉCNICO ## Migración de Layout.js a Menús Dinámicos desde SQL Server **Fecha:** 2026-05-24 **Versión:** 1.0 **Estado:** COMPLETADO CON OBSERVACIONES --- ## 1. RESUMEN EJECUTIVO La FASE 0.6 implementó la migración del componente `Layout.js` para consumir menús dinámicos desde SQL Server mediante el endpoint `/api/sistema/menus/usuario`, reemplazando progresivamente los menús ha

### EKS-SRC-08186 — FASE 1A - REPORTE TÉCNICO

- Ruta: `docs/reports/FASE_1A_COMERCIAL_VENTAS_MENU_GOBERNADO.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `5a52c0cb58096d7eaa0368fb3f9d1d29aad5637cf4a803e24f59595a56f2a634`
- Temas: `hospitality, sql_datos, rbac_seguridad, comercial, finanzas`

> # FASE 1A - REPORTE TÉCNICO ## Comercial/Ventas Integrado al Menú Gobernado **Fecha:** 2026-05-24 **Versión:** 1.0 **Estado:** COMPLETADO --- ## 1. OBJETIVO Validar e integrar el acceso al módulo Comercial/Ventas desde el sistema de menús SQL, sin rediseñar pantallas, sin modificar lógica de negocio, sin tocar satélites y sin romper módulos existentes. --- ## 2. RUTAS REVISADAS ### 2.1 Rutas Comer

### EKS-SRC-08188 — FASE 1B - REPORTE TÉCNICO (ACTUALIZADO TRAS FASE 1B-R1)

- Ruta: `docs/reports/FASE_1B_DASHBOARD_COMERCIAL_EDARSAHUB_SQL.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `00c70d59e8366af642a6d7556a347968ef521c14876cc53bd7ff4cfd9365fe97`
- Temas: `hospitality, sql_datos, rbac_seguridad, comercial`

> # FASE 1B - REPORTE TÉCNICO (ACTUALIZADO TRAS FASE 1B-R1) ## Dashboard Comercial usando Fuentes EDARSAHUB SQL **Fecha:** 2026-05-24 **Versión:** 2.0 (Actualizado tras corrección NO-LIVE) **Estado:** COMPLETADO - EDARSAHUB-ONLY IMPLEMENTADO --- ## 1. RESUMEN EJECUTIVO ### Estado Inicial (v1.0): El Dashboard Comercial usaba estrategia EDARSAHUB-FIRST con fallback a servidores remotos. ### Estado Cor

### EKS-SRC-08213 — FASE 1C-3I-A: Modelo de Datos para Motor de Precios Sugeridos con IA y Benchmark

- Ruta: `docs/reports/FASE_1C_3I_A_MODELO_DATOS_PRICING_IA_BENCHMARK.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `beaf809e45e87d738e02840fdf318f937f9a5d9b9b81bfe3d61e15ac804a4f33`
- Temas: `hospitality, sql_datos, rbac_seguridad, ia_agentes, comercial`

> # FASE 1C-3I-A: Modelo de Datos para Motor de Precios Sugeridos con IA y Benchmark **Fecha:** 2026-05-25 **Estado:** COMPLETADO --- ## 1. RESUMEN EJECUTIVO Se creó el modelo de datos base en EDARSAHUB SQL para soportar el motor de precios sugeridos con IA, benchmark competitivo y perfil digital de unidad de negocio. ### Resultados Principales: - **4 tablas nuevas** creadas - **1 tabla existente** 

### EKS-SRC-08288 — GREP_MPRO_API_LOCAL_130QRO_ORIGEN.txt

- Ruta: `docs/reports/GREP_MPRO_API_LOCAL_130QRO_ORIGEN.txt`
- Autoridad propuesta: `3/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `646bed641f1ffe00c2fa91df3f7e1c15c9cb66e11372034b9e189b56e7177d1a`
- Temas: `hospitality, conectores_universales, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> backend/init_queries.py:13:# Consultas MPRO backend/init_queries.py:14:MPRO_QUERIES = { backend/init_queries.py:183: AND Conversion_Unidad.Cu_Unidad_Origen = producto.Pr_Unidad_Compra AND Conversion_Unidad.Cu_Unidad_Destino = producto.Pr_Unidad_Control_1 backend/init_queries.py:212: AND Conversion_Unidad.Cu_Unidad_Origen = producto.Pr_Unidad_Compra AND Conversion_Unidad.Cu_Unidad_Destino = product

### EKS-SRC-08309 — MATRIZ NO-LIVE DASHBOARD EDARSAHUB

- Ruta: `docs/reports/MATRIZ_NO_LIVE_DASHBOARD_EDARSAHUB.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `b1c326101461bd732efff599244df56ac9bc9acd203bfcc82d4cecd78a42e0f8`
- Temas: `hospitality, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # MATRIZ NO-LIVE DASHBOARD EDARSAHUB Generado: 2026-06-02T16:25:16+00:00 ## Criterios | Prioridad | Criterio | Accion | |---|---|---| | P0 | Endpoints/dashboard/reportes con live/Mongo/API externa | Remediar primero | | P1 | Repositorios/servicios de modulos con live fuera de scheduler | Migrar a SQL sincronizado | | P2 | Helpers/documentacion/configuracion no productiva | Documentar | | PERMITIDO

### EKS-SRC-08314 — Auditoría de Integridad Menú ↔ Route ↔ RBAC

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_105301.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `ab1c599e6bb1c46a6556eb018305e10cdce5c493f78fe78c085e28b76b5f189e`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> # Auditoría de Integridad Menú ↔ Route ↔ RBAC Generado: `20260623_105301` - Rutas frontend auditadas: **58** - Menús SQL activos auditados: **54** - Rutas frontend sin menú SQL: **20** - Menús SQL sin route frontend: **16** - Módulos RBAC con permisos pero sin menú SQL: **46** ## Rutas frontend sin menú SQL - `/admin` → `AdminHub` - `/admin/centro-excepciones` → `CentroExcepciones` - `/admin/dashb

### EKS-SRC-08316 — Auditoría de Integridad Menú ↔ Route ↔ RBAC

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_110603.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `d98849758e2c247129db1c44c7b90cf80557fb2384209fd496d5b4f1d0cddbd6`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> # Auditoría de Integridad Menú ↔ Route ↔ RBAC Generado: `20260623_110603` - Rutas frontend auditadas: **58** - Menús SQL activos auditados: **63** - Rutas frontend sin menú SQL: **11** - Menús SQL sin route frontend: **16** - Módulos RBAC con permisos pero sin menú SQL: **44** ## Rutas frontend sin menú SQL - `/admin` → `AdminHub` - `/admin/dashboard-ejecutivo` → `DashboardEjecutivo` - `/proveedor

### EKS-SRC-08318 — Auditoría de Integridad Menú ↔ Route ↔ RBAC

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_113441.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `80caf34c6e8df98ce701726f1324eac3def9dea39b87ec041ce5928012d333e0`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> # Auditoría de Integridad Menú ↔ Route ↔ RBAC Generado: `20260623_113441` - Rutas frontend auditadas: **58** - Menús SQL activos auditados: **64** - Rutas frontend sin menú SQL: **10** - Menús SQL sin route frontend: **16** - Módulos RBAC con permisos pero sin menú SQL: **44** ## Rutas frontend sin menú SQL - `/admin` → `AdminHub` - `/admin/dashboard-ejecutivo` → `DashboardEjecutivo` - `/produccio

### EKS-SRC-08320 — Auditoría de Integridad Menú ↔ Route ↔ RBAC

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_114539.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `96ddf8d86d6872ef1d4ffd76921c9c2794f75c358c1a30a2c817e34e4b6813e2`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> # Auditoría de Integridad Menú ↔ Route ↔ RBAC Generado: `20260623_114539` - Rutas frontend auditadas: **58** - Menús SQL activos auditados: **64** - Rutas frontend sin menú SQL bruto: **10** - Rutas frontend sin menú SQL accionables: **0** - Rutas frontend técnicas/alias/formularios/sensibles: **10** - Menús SQL sin route frontend: **16** - Módulos RBAC con permisos pero sin menú SQL: **44** ## Ru

### EKS-SRC-08322 — Auditoría de Integridad Menú ↔ Route ↔ RBAC

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_120032.md`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `1763988e34eb4fc0ea46654290e115fefbce05f95c21942a8baeacd37dead63f`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> # Auditoría de Integridad Menú ↔ Route ↔ RBAC Generado: `20260623_120032` - Rutas frontend auditadas: **58** - Menús SQL activos auditados: **64** - Rutas frontend sin menú SQL bruto: **10** - Rutas frontend sin menú SQL accionables: **0** - Rutas frontend técnicas/alias/formularios/sensibles: **10** - Menús SQL sin route frontend: **16** - Módulos RBAC con permisos pero sin menú SQL: **43** ## Ru

### EKS-SRC-08646 — App.js

- Ruta: `frontend/src/App.js`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `3f9f53d58bde9f638cc3605592bac53135303813a7d11e26541e26fb89958dd8`
- Temas: `hospitality, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'; import { Toaster } from 'sonner'; import { AuthProvider } from '@/contexts/AuthContext'; import ProtectedRoute from '@/components/ProtectedRoute'; import Login from '@/pages/Login'; import ForgotPassword from '@/pages/ForgotPassword'; import ResetPassword from '@/pages/ResetPassword'; import Layout from '@/pages/Layout'; im

### EKS-SRC-08695 — EnterpriseSidebarMenu.jsx

- Ruta: `frontend/src/components/navigation/EnterpriseSidebarMenu.jsx`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `c05592762f423be26ba858a314be016bd80b3f25987a750e14113cdfed4bdf72`
- Temas: `hospitality, comercial, finanzas`

> import React, { useMemo, useState } from "react"; import { useNavigate, useLocation } from "react-router-dom"; import { Activity, BarChart3, Bell, Brain, Building, Building2, Calculator, CalendarCheck, ChevronDown, ChevronRight, ClipboardList, Clock, Contact, Database, DollarSign, Grid3X3, LayoutDashboard, Megaphone, Package, Percent, PieChart, Plug, RefreshCw, Search, Server, Settings, ShieldChec

### EKS-SRC-08703 — enterpriseMenuConfig.js

- Ruta: `frontend/src/config/enterpriseMenuConfig.js`
- Autoridad propuesta: `3/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `038267a5d8ad25d9f4fccbaf2e7dcebac48b8b5e8193e12740f18b15927a4dfd`
- Temas: `hospitality, toast_netpay, rbac_seguridad, ia_agentes, comercial, finanzas`

> /** * EDARSAHUB ENTERPRISE MENU CONFIG * * MÁXIMAS OBLIGATORIAS: * 1. Ningún módulo/tablero nuevo debe agregarse como menú suelto de primer nivel. * 2. Todo nuevo módulo debe pertenecer a un grupo Enterprise. * 3. Todo nuevo tablero debe vivir dentro de Inteligencia, Operación, Finanzas, * Administración/Sistema o Satélites, según corresponda. * 4. No duplicar rutas. * 5. No hardcodear permisos en

### EKS-SRC-07457 — 1. Réplica Local del Catálogo (Sincronizada en background desde EdarasHub)

- Ruta: `backend/modules/edge/comandero_local_core.py`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `8dcab84b912eaa8de8a844feb40e43c4f55b3999f253dc69ecd1ede4987f24e9`
- Temas: `hospitality`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService import sqlite3 import json import uuid import time from typing import Dict, List, Any class ComanderoLocalCore: def __init__(self, db_path: str = "edarsa_edge_device.db"): self.db_path = db_path self._inicializar_base_datos_local() def _inicializar_base_datos_local(self) -> None: """

### EKS-SRC-07461 — backend/modules/edge/sincronizador_catalogos_edge.py

- Ruta: `backend/modules/edge/sincronizador_catalogos_edge.py`
- Autoridad propuesta: `2/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `631f93ff75bf68a88b4d451c0c82d8a423ea8c9bd599e865ade29c02b4559002`
- Temas: `hospitality, comercial`

> from core.unidades_service import UnidadesService from core.corporate_filters.service import CorporateFilterService # backend/modules/edge/sincronizador_catalogos_edge.py import sqlite3 import httpx import json from typing import Dict, List, Any class SincronizadorCatalogosEdge: def __init__(self, local_db_path: str = "edarsa_edge_device.db", hub_url: str = "http://api.edarashub.internal"): self.l

### EKS-SRC-07547 — health.py

- Ruta: `backend/modules/hospitality/routes/health.py`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `de5f543a023a36afc72ee73daa75afcb014aa1837fe540335afa6c5486c78628`
- Temas: `hospitality`

> """ EDARSAHUB Hospitality - Health Stub Fase 1: stub seguro, sin lógica operativa, sin tablas nuevas, sin conexión externa. """ from fastapi import APIRouter router = APIRouter(prefix="/api/hospitality", tags=["Hospitality"]) @router.get("/health") async def hospitality_health(): return { "module": "hospitality", "status": "stub_ready", "phase": "fase_1_preparacion", "sql_first": True, "mongo": Fa

### EKS-SRC-08028 — BLUEPRINT EDARSAHUB HOSPITALITY V1

- Ruta: `docs/hospitality/BLUEPRINT_EDARSAHUB_HOSPITALITY_V1.md`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `eb34ac706499398308d26ca46fa5d4f61dc7fab3f30cc347a5e40872619ca216`
- Temas: `hospitality, rbac_seguridad, comercial, finanzas`

> # BLUEPRINT EDARSAHUB HOSPITALITY V1 ## Principio EDARSAHUB Hospitality es un satélite nativo del ERP EDARSAHUB. No es sistema separado. ## Máximas - No romper producción. - No MongoDB. - No conexión LIVE operativa. - SQL Server como fuente única. - No duplicar usuarios, RBAC, catálogos, conexiones, endpoints ni lógica. - Usar unidad_negocio_pk. - Reutilizar filtros corporativos. - Reutilizar sche

### EKS-SRC-08118 — COSTOS-ALERTAS-001-D: UI para Reglas de Margen

- Ruta: `docs/reports/COSTOS_ALERTAS_001D_UI_REGLAS_MARGEN_DESTINATARIOS.md`
- Autoridad propuesta: `2/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `e12ef404d9f97bb8f8cb20669f721afb98614ddd933d4530860d5dae9ef1c786`
- Temas: `hospitality, rbac_seguridad, comercial`

> # COSTOS-ALERTAS-001-D: UI para Reglas de Margen ## Fecha: 25 Mayo 2026 ## Estado: ✅ COMPLETADO ## Autor: Agente E1 --- ## 1. OBJETIVO Crear interfaz de usuario (UI) dentro del módulo `/comercial/costos-margenes` para configurar reglas de margen esperado con jerarquía: - **Producto > Subfamilia > Familia > Grupo** --- ## 2. UBICACIÓN - **Módulo**: Comercial → Costos y Márgenes - **Tab**: "Reglas d

### EKS-SRC-08133 — Diagnóstico de filtros actuales EDARSAHUB

- Ruta: `docs/reports/DIAGNOSTICO_FILTROS_ACTUALES_EDARSAHUB.md`
- Autoridad propuesta: `2/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `809aec4e1166d1d46cc18ddae8dc90862d578bb9dfe0d6b7ec2aed7592d6c95a`
- Temas: `hospitality, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # Diagnóstico de filtros actuales EDARSAHUB Fecha: Wed Jun 3 07:03:00 UTC 2026 ## 1. Endpoints backend relacionados con filtros ```text /app/backend/server.py:1548:@api_router.post("/servers") /app/backend/server.py:1605:@api_router.get("/servers", response_model=List[Server]) /app/backend/server.py:1632:@api_router.get("/servers/{server_id}") /app/backend/server.py:1659:@api_router.put("/servers/

### EKS-SRC-08146 — DIAGNÓSTICO RUNTIME SYNC COMPRAS

- Ruta: `docs/reports/DIAGNOSTICO_RUNTIME_SYNC_COMPRAS_20260604_053534.md`
- Autoridad propuesta: `2/10`
- Estado propuesto: `BORRADOR_CANDIDATO`
- SHA-256: `e0ae7287ae9be3f41676e15aeebb4782c3dbf16600ccf5311ccce3099b4b03f3`
- Temas: `filosofia_bos, hospitality, conectores_universales, toast_netpay, rbac_seguridad, ia_agentes, comercial, finanzas`

> # DIAGNÓSTICO RUNTIME SYNC COMPRAS Fecha: Thu Jun 4 05:35:34 UTC 2026 ## 1. Scheduler / configuración del job ```text /app/backend/modules/comercial/rentabilidad.py:38: FROM dbo.Compras_Inventarios_Fisicos_Sync /app/backend/modules/fase2_operativo/repositories/sql_base_repository.py:57: "inventarios_fisicos_procesados": "Compras_Inventarios_Fisicos_Sync", /app/backend/modules/inventarios/repositor

### EKS-SRC-08287 — Auditoría Graphify EDARSAHUB

- Ruta: `docs/reports/GRAPHIFY_AUDIT_20260623_013052.md`
- Autoridad propuesta: `2/10`
- Estado propuesto: `BORRADOR_CANDIDATO`
- SHA-256: `9aedbda8ff8b98b1693fce320726991665bc882108144da925c617497d8a16de`
- Temas: `hospitality, conectores_universales, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # Auditoría Graphify EDARSAHUB Fecha: 20260623_013052 ## 1. Estado Git ``` ?? docs/reports/GRAPHIFY_AUDIT_20260623_013052.md ``` ## 2. Archivos Graphify ``` ./graphify-out ./graphify-out/cache ./graphify-out/cache/stat-index.json ./graphify-out/cache/ast ./graphify-out/cache/ast/v0.8.39 ./frontend/src/graphify-out ./frontend/src/graphify-out/.graphify_labels.json ./frontend/src/graphify-out/.graph

### EKS-SRC-08291 — GREP_SYNC_COMERCIAL_CONEXIONES.txt

- Ruta: `docs/reports/GREP_SYNC_COMERCIAL_CONEXIONES.txt`
- Autoridad propuesta: `2/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `a58c7a09fced4c1f93239e9e041cc458c447ead0b96deb966ad856dda3fc8c1e`
- Temas: `hospitality, conectores_universales, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> backend/init_queries.py:13:# Consultas MPRO backend/init_queries.py:14:MPRO_QUERIES = { backend/init_queries.py:276: # Insert MPRO queries backend/init_queries.py:277: for query_type, sql_query in MPRO_QUERIES.items(): backend/init_queries.py:280: "name": f"MPRO - {query_type.capitalize()}", backend/init_queries.py:281: "system_type": "MPRO", backend/migrar_a_sql.py:3:# Lista de archivos a elimina

### EKS-SRC-08311 — MENU_ROUTE_INTEGRITY_20260623_104636.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_104636.json`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `6806763a3a34ba786c1e5c94aa5984607f6476fff742a18ef42a74d1ed63f9a7`
- Temas: `hospitality, comercial`

> { "fecha_utc": "2026-06-23T10:46:36.177370", "frontend_routes_count": 58, "sql_menu_routes_count": 54, "frontend_sin_menu_sql": [ { "ruta": "/admin", "componente": "AdminHub" }, { "ruta": "/admin/centro-excepciones", "componente": "CentroExcepciones" }, { "ruta": "/admin/dashboard-ejecutivo", "componente": "DashboardEjecutivo" }, { "ruta": "/comercial/pricing-ia", "componente": "PricingIA" }, { "r

### EKS-SRC-08312 — Auditoría Menú SQL vs Rutas Frontend

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_104636.md`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `a1e747bea5011edebad3136c56aa260a4fb0c847a2b78f4d6f83ffaeb22c0e6b`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> # Auditoría Menú SQL vs Rutas Frontend - Fecha UTC: 2026-06-23T10:46:36.177370 - Rutas frontend auditadas: 58 - Rutas menú SQL activas: 54 ## Frontend sin menú SQL - `/admin` → `AdminHub` - `/admin/centro-excepciones` → `CentroExcepciones` - `/admin/dashboard-ejecutivo` → `DashboardEjecutivo` - `/comercial/pricing-ia` → `PricingIA` - `/crm/actividades` → `ActividadesPage` - `/crm/operaciones` → `O

### EKS-SRC-08313 — MENU_ROUTE_INTEGRITY_20260623_105301.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_105301.json`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `6b73dc34b90233a2a6b8c6733bf3e4c7cbd933168da4a92682cabc2e9d6fe7c6`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_105301", "frontend_routes_count": 58, "sql_menus_count": 54, "frontend_without_sql_menu": [ { "ruta": "/admin", "componente": "AdminHub" }, { "ruta": "/admin/centro-excepciones", "componente": "CentroExcepciones" }, { "ruta": "/admin/dashboard-ejecutivo", "componente": "DashboardEjecutivo" }, { "ruta": "/comercial/pricing-ia", "componente": "PricingIA" }, { "ruta": "/cr

### EKS-SRC-08315 — MENU_ROUTE_INTEGRITY_20260623_110603.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_110603.json`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `eed65ad4773c51aa5032d6cde81e90e45ec06d790c95518ab0d868a179b130f0`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_110603", "frontend_routes_count": 58, "sql_menus_count": 63, "frontend_without_sql_menu": [ { "ruta": "/admin", "componente": "AdminHub" }, { "ruta": "/admin/dashboard-ejecutivo", "componente": "DashboardEjecutivo" }, { "ruta": "/proveedores", "componente": "Proveedores" }, { "ruta": "/produccion", "componente": "Produccion" }, { "ruta": "/produccion/tablajeria", "compo

### EKS-SRC-08317 — MENU_ROUTE_INTEGRITY_20260623_113441.json

- Ruta: `docs/reports/MENU_ROUTE_INTEGRITY_20260623_113441.json`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `f948070fde40b765e14bf346262cf4a8bef9bc61c8ab6b4422acea013fbeb05c`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> { "generated_at": "20260623_113441", "frontend_routes_count": 58, "sql_menus_count": 64, "frontend_without_sql_menu": [ { "ruta": "/admin", "componente": "AdminHub" }, { "ruta": "/admin/dashboard-ejecutivo", "componente": "DashboardEjecutivo" }, { "ruta": "/produccion", "componente": "Produccion" }, { "ruta": "/produccion/tablajeria", "componente": "TablajeriaDashboard" }, { "ruta": "/produccion/t

### EKS-SRC-08507 — RBAC_GAP_ANALYSIS.json

- Ruta: `docs/reports/mongo_rbac_gap_analysis_20260607_192658/RBAC_GAP_ANALYSIS.json`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `193a0e8d16ddbcf31856dec6f3a335d3ac1868bd83ebd8f4b00f3d3f5094634c`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial, finanzas`

> { "generated_at": "2026-06-07T19:27:00", "mode": "READ_ONLY_RBAC_GAP_ANALYSIS", "rules": [ "No se borró/modificó Mongo ni SQL.", "No se insertaron datos.", "No se migró RBAC en bloque.", "No se usó pyodbc." ], "mongo_sources": { "roles": [ { "source": "edarsa_hub.rbac_roles", "docs": 6 }, { "source": "edarsa_hub.roles", "docs": 4 }, { "source": "edarsa_hub.sec_roles", "docs": 5 } ], "permisos": [ 

### EKS-SRC-08579 — ejemplo_uso_resilient_ws.js

- Ruta: `docs/snippets/ejemplo_uso_resilient_ws.js`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `6fb147f968510ff58fbc1e94ab3dc6a9e0c7f732c864c8024a257c887e8bcd82`
- Temas: `hospitality`

> import { ResilientWebSocket } from '../lib/ResilientWebSocket'; // Reemplaza tu vieja conexión: const ws = new WebSocket(...) con esto: const conexionEnVivo = new ResilientWebSocket('wss://' + window.location.host + '/api/centro-control/ws', { onMessage: (datos) => { // Aquí actualizas tu tablero o comandero con los datos frescos console.log("Datos en tiempo real:", datos); }, onConnect: () => con

### EKS-SRC-08620 — RENOMBRAR_COMEDERO_A_COMANDERO.sql

- Ruta: `docs/sql/RENOMBRAR_COMEDERO_A_COMANDERO.sql`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `2bbb9da108668cf5b1e00ed652f7ded07aea7c2e22cb639cd7846d25b19845b5`
- Temas: `hospitality`

> -- ============================================================================= -- SCRIPT: RENOMBRAR MÓDULO COMEDERO -> COMANDERO -- OBJETIVO: Actualizar el nombre del módulo satélite en tablas maestras -- ============================================================================= -- Actualizar el nombre del módulo en la tabla maestra UPDATE modulos_hub SET nombre = 'Comandero' WHERE nombre = '

### EKS-SRC-08626 — SINCRONIZACION_COMPLETA_5_UNIDADES.sql

- Ruta: `docs/sql/SINCRONIZACION_COMPLETA_5_UNIDADES.sql`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `ea006693115306592f2e2733bae1f566a64637bfc401f81be32140bc1b81f146`
- Temas: `hospitality, comercial`

> -- ============================================================================= -- SCRIPT: SINCRONIZACIÓN COMPLETA + VERIFICACIÓN MÓDULOS SATÉLITE -- OBJETIVO: Actualizar todas las unidades y asegurar módulos Comandero/Super Caja -- ============================================================================= -- 1. Actualizar estados de sincronización para todas las unidades UPDATE control_sincro

### EKS-SRC-08631 — SYNC_MASIVA_SATELITES_5_UNIDADES.sql

- Ruta: `docs/sql/SYNC_MASIVA_SATELITES_5_UNIDADES.sql`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `5eda6b516f6b09b7782fc9f12e6ca99ab3e3d503d7a061b740dee966ae49e31b`
- Temas: `hospitality`

> -- ============================================================================= -- SCRIPT: SINCRONIZACIÓN MASIVA - MÓDULOS SATÉLITES EN 5 UNIDADES -- OBJETIVO: Asegurar que 'comandero' y 'super-caja' estén activos y vinculados -- ============================================================================= INSERT INTO unidad_modulos (unidad_id, modulo_id) VALUES (130, 'comandero'), (130, 'super-c

### EKS-SRC-08681 — mapa_mesas_live3d.ts

- Ruta: `frontend/src/components/edge/mapa_mesas_live3d.ts`
- Autoridad propuesta: `2/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `6507663ba04ebe81d6a842203009e933d2dd85aaf598e1cfdfbf49a967e7cefb`
- Temas: `hospitality`

> // frontend/components/mapa_mesas_live3d.ts import { MesaEstadoUI } from "../../backend/modules/edge/comandero_terminal_ui"; import { MotorInventarioParametrico } from "../../backend/modules/edge/motor_inventario_parametrico"; export class MapaMesasLive3D { private contenedorPiso: HTMLElement; private motorInventario: MotorInventarioParametrico; constructor(idContenedor: string) { this.contenedorP

### EKS-SRC-08704 — menuFallback.js

- Ruta: `frontend/src/config/menuFallback.js`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `d4704c6b95a1815cdbcdd8419191dff1e0553ccf5d32a5a95d5cb4e467230b74`
- Temas: `hospitality, comercial`

> // /app/frontend/src/config/menuFallback.js // Configuración de menús de respaldo para cuando la API no responde export const menuFallback = [ { id: 'crm', label: 'CRM', path: '/crm', isSatelite: false }, { id: 'comercial', label: 'Comercial', path: '/comercial', isSatelite: false }, { id: 'admin', label: 'Administración', path: '/admin', isSatelite: false }, { id: 'comandero', label: 'Comandero',

### EKS-SRC-08715 — sincronizacionEnVivo.js

- Ruta: `frontend/src/lib/sincronizacionEnVivo.js`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `65fcadaf74baf15f126bfe216047e836ee6040735f5c2d2406ec59ff937faec7`
- Temas: `hospitality, comercial`

> // 1. Asegúrate de importar la nueva clase en la parte superior de tu archivo import { ResilientWebSocket } from '../lib/ResilientWebSocket'; // 2. Reemplaza tu inicialización vieja por esta función blindada export const iniciarSincronizacionEnVivo = () => { // Definimos la ruta correcta hacia el cerebro de EDARSA HUB const wsUrl = `wss://${window.location.host}/api/centro-control/ws`; // Instanci

### EKS-SRC-08716 — HospitalityDashboard.jsx

- Ruta: `frontend/src/modules/hospitality/pages/HospitalityDashboard.jsx`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `fbe3ad737f27ef7619018a41096031ec78a4f37e6ad2a0c85bddfaa4d7315002`
- Temas: `hospitality, sql_datos, rbac_seguridad, finanzas`

> import React from "react"; export default function HospitalityDashboard() { return ( <div className="p-6 space-y-4"> <div> <h1 className="text-2xl font-bold">EDARSAHUB Hospitality</h1> <p className="text-gray-500"> Módulo satélite en preparación. SQL-first, sin MongoDB, sin LIVE operativo. </p> </div> <div className="grid grid-cols-1 md:grid-cols-3 gap-4"> <div className="rounded-2xl border p-4 sh

### EKS-SRC-08734 — Layout.js

- Ruta: `frontend/src/pages/Layout.js`
- Autoridad propuesta: `2/10`
- Estado propuesto: `OFICIALIDAD_POR_VALIDAR`
- SHA-256: `6ed8bab64081095d89ed1793bd31b4995f632873e3df8e241dd1e99e978ae0d7`
- Temas: `hospitality, constitucion_maximas, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> import { Outlet, useLocation, Link, useNavigate } from 'react-router-dom'; import { useAuth } from '@/contexts/AuthContext'; import logger from '@/services/logger'; import { Button } from '@/components/ui/button'; import EnterpriseSidebarMenu from '@/components/navigation/EnterpriseSidebarMenu'; import { LayoutDashboard, Server, Package, Bell, Users, LogOut, Menu, X, ShoppingCart, TrendingUp, Data

### EKS-SRC-08766 — ComanderoPage.jsx

- Ruta: `frontend/src/pages/satelites/ComanderoPage.jsx`
- Autoridad propuesta: `2/10`
- Estado propuesto: `CANDIDATO`
- SHA-256: `7a604d217dca9201ab7512ffb927856dbf369982f979f8284f295db837a556ab`
- Temas: `hospitality`

> import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'; import { ChefHat, RefreshCw, Utensils, Clock, Users } from 'lucide-react'; const ComanderoPage = () => { return ( <div className="space-y-6"> <div className="flex items-center justify-between"> <div> <h1 className="text-2xl font-bold text-zinc-900">Comandero</h1> <p className="text-zinc-500">Módulo Satélite - Sistema 

### EKS-SRC-08868 — EDARSA HUB - CRM COMERCIAL ENTERPRISE

- Ruta: `memory/PRD.md`
- Autoridad propuesta: `2/10`
- Estado propuesto: `DEPRECADO_CANDIDATO`
- SHA-256: `d8af7440a5b3efcfc9c27bde791e8470c78e819101551eb26237caa493ac4a49`
- Temas: `hospitality, constitucion_maximas, contratos_canonicos, toast_netpay, sql_datos, rbac_seguridad, ia_agentes, comercial, finanzas`

> # EDARSA HUB - CRM COMERCIAL ENTERPRISE ## Product Requirements Document ### Original Problem Statement Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB. ### Core Requirements - **ESTRICTA PROHIBICIÓN**: Uso del subagente `testing_agent_v3_fork` totalmente prohibido - **MÁXIMA ARQUITECTÓNICA (NO-LIVE)**: EDARSAHUB SQL es la ÚNICA fuente de verdad product

### EKS-SRC-07735 — audit_menu_recommendations.py

- Ruta: `backend/tools/audit_menu_recommendations.py`
- Autoridad propuesta: `0/10`
- Estado propuesto: `BORRADOR_CANDIDATO`
- SHA-256: `291f291912f3ff1cd56b60faff33fcec4190b76204610c26d2fb56eee645a83b`
- Temas: `hospitality, comercial`

> from core.config.edarsahub_sql import get_edarsahub_connection from pathlib import Path from datetime import datetime OUT = Path("/app/docs/reports") OUT.mkdir(parents=True, exist_ok=True) FRONT_MISSING_SQL = [ ("/admin/centro-excepciones","CentroExcepciones"), ("/admin/dashboard-ejecutivo","DashboardEjecutivo"), ("/comercial/pricing-ia","PricingIA"), ("/crm/actividades","ActividadesPage"), ("/crm

### EKS-SRC-08335 — PROPUESTA MENU SQL

- Ruta: `docs/reports/MENU_SQL_RECOMMENDATIONS_20260623_105623.md`
- Autoridad propuesta: `0/10`
- Estado propuesto: `BORRADOR_CANDIDATO`
- SHA-256: `7253d47546adb9a3baebfe944109d143341db101d41da5a5693ac486b59feed2`
- Temas: `hospitality, rbac_seguridad, ia_agentes, comercial`

> # PROPUESTA MENU SQL ## /admin/centro-excepciones Frontend: CentroExcepciones Posibles módulos: - 13 | ACTIVOS_FIJOS | Activos Fijos - 27 | SISTEMA | Administración Sistema - 21 | CALIDAD | Calidad / Auditoría - 26 | CATALOGOS | Catálogos Maestros - 7 | CAVA_SOCIOS | Cava de Socios - 19 | CHEF_IA | Chef IA / Calidad - 3 | COMANDERO_RESTAURANTERO | Comandero Restaurantero - 2 | COMERCIAL | Comercia

