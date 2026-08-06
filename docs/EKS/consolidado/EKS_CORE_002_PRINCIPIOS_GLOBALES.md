# EKS-CORE-002 — Principios Globales de EDARSAHUB

**Estado:** BORRADOR CONSOLIDADO  
**Versión:** 0.1  
**Fecha:** 2026-08-02T04:39:06.240932+00:00

## Principios rectores

### P-001 — Una sola fuente de verdad

Cada dato, KPI, regla, contrato y activo de conocimiento debe tener una única
versión canónica vigente.

### P-002 — No duplicar capacidades

Antes de crear una tabla, servicio, endpoint, módulo, conector, documento o
regla debe verificarse si ya existe una capacidad equivalente.

### P-003 — Recuperar antes de reinventar

Cuando una capacidad funcionaba correctamente, se recupera y compara la última
versión funcional antes de diseñar una lógica nueva.

### P-004 — El contrato precede a la implementación

El código implementa contratos aprobados. No los redefine de forma unilateral.

### P-005 — Frontend presentacional

El frontend no debe convertirse en la fuente de fórmulas, reglas financieras,
KPIs o decisiones de negocio.

### P-006 — SQL canónico

Los datos corporativos y operativos se consolidan en SQL Server bajo modelos
canónicos, auditables y gobernados.

### P-007 — No MongoDB

MongoDB no se utiliza como fuente, caché, fallback, lock ni configuración del
BOS.

### P-008 — No LIVE por defecto

Los sistemas origen alimentan procesos de sincronización. Los consumidores
operativos leen de EDARSAHUB, salvo excepciones controladas y autorizadas.

### P-009 — RBAC universal

Toda ruta, menú, dato, exportación, job, automatización y acción administrativa
respeta permisos efectivos y alcance de empresa o unidad.

### P-010 — Cambios atómicos

Cada bloque de trabajo tiene un objetivo, un alcance, archivos permitidos,
pruebas y punto de recuperación.

### P-011 — Evidencia antes del parche

No se modifica por intuición. Se identifica la causa demostrada y se aplica el
cambio mínimo.

### P-012 — Compatibilidad evolutiva

No se permiten bifurcaciones funcionales permanentes ni contratos paralelos
para resolver el mismo problema.

### P-013 — Desarrollo por dominios

Las pantallas son consumidores. La unidad de diseño es el dominio de negocio.

### P-014 — Conectores universales

Toast, NetPay, Meta, Google, Expedia, Airbnb, OpenTable y otros proveedores
deben integrarse mediante un núcleo común de conectores, no mediante
arquitecturas aisladas por proveedor.

### P-015 — IA gobernada

Los agentes consultan principios, arquitectura, contratos y ADR antes de
proponer o ejecutar cambios.

### P-016 — Conocimiento canónico

Los chats son espacios de trabajo. El conocimiento aprobado debe consolidarse
en activos versionados, trazables y gobernados.

### P-017 — Detención segura

Ante rama incorrecta, workspace inesperado, falta de evidencia, conflicto de
fuentes o necesidad de permisos no autorizados, el agente se detiene y reporta.

### P-018 — Protección de lo aprobado

Una mejora no puede sacrificar una función ya validada ni alterar otro dominio
fuera del alcance declarado.
