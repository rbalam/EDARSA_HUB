# EKS-CORE-001 — Definición Global de EDARSAHUB BOS

**Estado:** BORRADOR CONSOLIDADO  
**Versión:** 0.1  
**Fecha de consolidación:** 2026-08-02T04:39:06.240932+00:00  
**Rama:** `Edarsahub_Desarrollo`  
**HEAD:** `f570aedab8692cc060d45e1a46321f024f95d427`  
**Propietario de aprobación:** Dirección de EDARSAHUB  

## 1. Definición

EDARSAHUB es un **Business Operating System (BOS)** empresarial diseñado para
integrar, gobernar, automatizar y explicar la operación de las empresas y
unidades de negocio del grupo.

No es únicamente un ERP, un conjunto de tableros ni una colección de módulos.
Es una plataforma operativa y de inteligencia que conecta datos, procesos,
personas, reglas de negocio, automatizaciones, sistemas externos e inteligencia
artificial bajo una arquitectura común.

## 2. Alcance global

Los principios arquitectónicos definidos inicialmente en EDARSAHUB Hospitality
se adoptan como principios transversales para todo EDARSAHUB cuando no sean
exclusivos del sector hotelero.

EDARSAHUB debe ser:

- global;
- configurable;
- multiempresa;
- multiunidad de negocio;
- multidominio;
- multiconector;
- gobernado por RBAC;
- auditable;
- evolutivo;
- compatible con inteligencia artificial;
- sostenible durante su crecimiento futuro.

## 3. Relación con Hospitality

EDARSAHUB Hospitality no es un sistema separado ni una arquitectura paralela.

Es un dominio o satélite nativo de EDARSAHUB que:

- reutiliza el núcleo común;
- consume servicios y contratos canónicos;
- utiliza el mismo gobierno de datos;
- utiliza el mismo RBAC;
- utiliza el mismo sistema de conectores;
- utiliza la misma auditoría;
- evita duplicar capacidades ya existentes.

Las capacidades sectoriales de Hospitality —por ejemplo Guest Success, Room
Service, operación de servicios o conectores hoteleros— pertenecen al dominio
Hospitality. Sus principios generales de arquitectura pertenecen al BOS global.

## 4. Principio de núcleo común

Toda capacidad transversal debe existir una sola vez.

Esto aplica, entre otros, a:

- identidad y autenticación;
- RBAC;
- empresas y unidades de negocio;
- catálogos;
- conexiones SQL y API;
- secretos;
- auditoría;
- notificaciones;
- automatizaciones;
- observabilidad;
- agentes de IA;
- contratos canónicos;
- filtros corporativos.

Los dominios consumen ese núcleo; no lo duplican.

## 5. Principio SQL-first

SQL Server es la plataforma canónica para los datos operativos y de negocio de
EDARSAHUB.

Quedan prohibidos como arquitectura normal:

- MongoDB como fuente;
- MongoDB como caché;
- MongoDB como fallback;
- MongoDB como lock;
- MongoDB como configuración;
- bases paralelas para el mismo dato;
- lógica de negocio duplicada entre fuentes.

Las excepciones requieren una decisión arquitectónica explícita y trazable.

## 6. Principio de datos consolidados

Los tableros, reportes e indicadores deben consumir datos sincronizados,
consolidados y gobernados desde EDARSAHUB.

Las consultas LIVE a sistemas origen no forman parte del funcionamiento normal,
salvo excepciones expresamente autorizadas, como operaciones del día que
necesiten actualización controlada.

## 7. Contratos canónicos

Cada dominio debe poseer contratos canónicos estables para sus datos, KPIs,
objetos, eventos y servicios.

Una misma definición no puede recalcularse de manera independiente en:

- frontend;
- dashboard ejecutivo;
- reportes;
- IA;
- exportaciones;
- aplicaciones externas;
- automatizaciones.

El frontend presenta. El backend y la capa canónica gobiernan la lógica.

## 8. Desarrollo por dominios

EDARSAHUB evoluciona por dominios de negocio, no por pantallas aisladas.

Cada dominio debe declarar:

1. alcance;
2. responsabilidades;
3. límites;
4. fuentes canónicas;
5. contratos;
6. servicios;
7. consumidores;
8. permisos;
9. eventos;
10. pruebas de aceptación.

## 9. Inteligencia artificial

La IA debe asistir, analizar, explicar, recomendar, automatizar y aprender de
la operación autorizada.

La IA no puede:

- redefinir reglas de negocio por sí misma;
- crear fuentes paralelas;
- omitir RBAC;
- modificar contratos canónicos sin gobierno;
- inventar datos;
- ejecutar acciones críticas sin autorización.

## 10. Evolución

EDARSAHUB debe poder evolucionar durante los próximos años sin depender de una
tecnología, proveedor o implementación específica.

La implementación puede cambiar. Los principios, límites de dominio y contratos
solo cambian mediante gobierno, versionado y trazabilidad.

## 11. Fuentes

Este activo consolida principios demostrados principalmente en:

- `docs/hospitality/architecture/EHAB_00_INDICE_MAESTRO.md`
- `docs/operacion/MODO_TRABAJO_CAMBIOS_ATOMICOS.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- configuraciones de agentes EDARSA

## 12. Brechas

Todavía deben incorporarse como fuentes primarias:

- conversación original de Hospitality;
- conversación Robots / Toast / NetPay;
- documentos derivados que contengan decisiones aprobadas no presentes en Git.

Estas brechas no invalidan el presente borrador, pero impiden considerarlo una
versión final completa.
