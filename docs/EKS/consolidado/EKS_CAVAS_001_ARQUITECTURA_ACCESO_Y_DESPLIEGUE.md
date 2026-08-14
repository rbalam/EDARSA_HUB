# EKS-CAVAS-001 — Arquitectura de Acceso, Identidad y Despliegue de Cavas

**Estado:** DECISIÓN ARQUITECTÓNICA APROBADA  
**Versión:** 1.0  
**Fecha:** 2026-08-14  
**Rama:** `Edarsahub_Desarrollo`  
**Marco rector:** EDARSAHUB BOS / EKS  

## 1. Objetivo

Definir la arquitectura obligatoria de acceso, identidad, despliegue e integración del dominio **Cavas** dentro de EDARSAHUB BOS y en modalidad standalone/satélite.

Cavas es un dominio nativo del BOS, pero debe conservar independencia operativa suficiente para poder desplegarse como sistema satélite autónomo sin depender en runtime de EDARSAHUB, POS u otros sistemas externos.

## 2. Modos de operación

Cavas debe soportar dos modos usando la misma lógica de dominio:

### 2.1 Modo integrado EDARSAHUB

- Cavas vive bajo `Satélites > Cavas`.
- Reutiliza autenticación interna, RBAC, scopes, empresas, unidades de negocio, filtros corporativos, clientes, productos, auditoría, notificaciones, configuración y servicios canónicos existentes.
- Los usuarios internos de EDARSAHUB con permisos efectivos para Cavas deben acceder sin realizar un segundo login.
- El acceso interno debe utilizar la sesión/autenticación canónica existente de EDARSAHUB y autorización backend-authoritative.

### 2.2 Modo standalone / satélite

- Cavas puede operar con su propia URL y su propia base SQL canónica local.
- Cavas debe poder seguir operando aunque EDARSAHUB, POS, CRM u otros sistemas externos estén temporalmente no disponibles.
- Las integraciones externas se realizarán mediante conectores, adaptadores, sincronizaciones, jobs o eventos autorizados.
- No se permitirán consultas LIVE a sistemas externos como dependencia normal de la operación del usuario.
- La lógica de dominio debe ser compartida con el modo integrado; no se mantendrán dos implementaciones funcionales divergentes.

## 3. URL propia del portal Cavas

Cavas debe contar con una dirección web propia para usuarios externos.

El dominio/subdominio concreto se definirá mediante configuración y despliegue; no debe hardcodearse en la lógica de negocio.

Ejemplo conceptual no vinculante:

`https://cavas.<dominio-corporativo>`

La URL pública deberá servir como portal de los **Socios Cavas** y mantenerse separada de la navegación interna de EDARSAHUB.

## 4. Tipos de identidad

Cavas debe distinguir como mínimo dos clases de actores:

### 4.1 Usuario interno EDARSAHUB

- Empleado, colaborador o usuario corporativo autenticado por EDARSAHUB.
- No necesita credenciales adicionales de Cavas.
- Accede desde `Satélites > Cavas`.
- Su autorización se resuelve mediante RBAC canónico y scopes efectivos.
- El frontend no es autoridad de acceso; todo endpoint sensible debe validar permisos y alcance en backend.

### 4.2 Usuario externo — Socio Cavas

- Persona externa con acceso al portal Cavas.
- Utiliza credenciales propias del portal externo.
- Su identidad de acceso no debe convertirse en un segundo catálogo maestro de clientes.
- Debe estar vinculada, cuando aplique, con el cliente/persona canónica correspondiente.
- Su autorización debe limitarse a sus propios recursos y relaciones autorizadas.

## 5. Principio de identidad única sin duplicidad

La existencia de una identidad de login del portal no autoriza crear un segundo maestro de clientes.

Cuando Cavas opere integrado:

- el socio debe reutilizar el cliente/persona canónica existente cuando corresponda;
- el perfil de Cavas será una relación/extensión del cliente canónico;
- las credenciales del portal constituyen identidad de acceso, no una nueva fuente maestra de datos personales;
- cualquier tabla nueva de relación deberá justificarse mediante auditoría previa del esquema real.

No se permite duplicar nombre, teléfono, correo, RFC, preferencias u otros atributos si ya existe una fuente canónica reutilizable.

## 6. Autenticación interna sin segundo login

Un usuario interno autenticado en EDARSAHUB y con permisos efectivos para Cavas debe poder navegar a:

`EDARSAHUB > Satélites > Cavas`

sin ser redirigido a un segundo formulario de autenticación.

La implementación debe reutilizar la autenticación canónica y mecanismos actuales de sesión/token/cookie autorizados por EDARSAHUB.

No se crearán contraseñas Cavas separadas para usuarios internos.

## 7. Autenticación externa

El portal público Cavas debe tener autenticación propia para Socios Cavas.

La implementación deberá auditar y reutilizar, cuando sea técnicamente correcto, patrones ya existentes en satélites externos como Portal de Proveedores y Portal Inteligencia Comercial.

Antes de implementar se debe verificar en código real:

- autenticación dual existente;
- cookies/tokens;
- expiración;
- logout;
- recuperación de acceso;
- rate limiting;
- bloqueo por intentos;
- auditoría de sesiones;
- autorización por ownership;
- SSO interno si ya existe patrón reutilizable.

No se debe copiar automáticamente deuda técnica o mecanismos legacy encontrados en otros portales.

## 8. Autorización: RBAC + scope + ownership

La autorización de Cavas no puede resolverse exclusivamente mediante roles ni exclusivamente mediante frontend.

### Usuarios internos

Deben utilizar:

- RBAC efectivo;
- permisos explícitos;
- scopes de empresa/unidad/cava cuando correspondan;
- validación backend-authoritative.

### Socios externos

Además de autenticación válida, deben estar limitados mediante ownership/relación a sus propios recursos autorizados:

- inventario propio;
- botellas propias;
- movimientos propios;
- visitas propias;
- consumos propios;
- solicitudes propias;
- personas autorizadas;
- documentos y notificaciones permitidos.

Un socio externo no debe recibir acceso general a inventario de Cavas por el simple hecho de estar autenticado.

## 9. Un solo dominio, dos experiencias

No se crearán dos sistemas funcionales independientes del tipo `cavas-interno` y `cavas-externo` con reglas duplicadas.

Debe existir un único dominio Cavas con contratos, servicios y reglas comunes.

Las experiencias de usuario podrán ser diferentes:

- UI interna EDARSAHUB para personal autorizado;
- Portal Cavas para Socios Cavas.

Ambas deben consumir la misma lógica de dominio y las mismas fuentes canónicas correspondientes.

## 10. Menú y navegación

Cuando Cavas opere integrado, su ubicación canónica es:

`Satélites > Cavas`

La entrada legacy existente de `Cava de Socios` bajo `Personas` deberá ser auditada antes de cualquier cambio para decidir si se reutiliza, migra, redirige o retira.

No se debe crear una segunda ruta funcional duplicada sin cerrar primero esa auditoría.

Cavas debe quedar preparado para tabs internos gobernados por permisos, sin hardcodear navegación o roles.

## 11. Arquitectura modular

La lógica propia de Cavas debe vivir en el dominio/módulo correspondiente y no seguir creciendo `backend/core`.

El `core` solo debe contener capacidades verdaderamente transversales del BOS.

Cavas debe consumir, cuando corresponda, servicios canónicos existentes como:

- autenticación/identidad;
- RBAC;
- empresas/unidades;
- filtros corporativos;
- clientes;
- productos;
- auditoría;
- notificaciones;
- conexiones;
- configuración;
- observabilidad.

Antes de crear cualquier nuevo helper o servicio se debe demostrar que no existe uno canónico reutilizable.

## 12. Autonomía y sincronización

Cavas standalone no puede depender de sistemas externos para completar operaciones básicas del dominio.

Los datos externos requeridos para operar offline/degradado deberán existir localmente como réplica o copia sincronizada gobernada.

Cada entidad sincronizada debe tener reglas claras de:

- ownership de la fuente;
- identificador estable;
- origen;
- versión/fecha de modificación;
- precedencia;
- idempotencia;
- reconciliación;
- resolución de conflictos;
- baja/tombstone cuando aplique.

Replicar para operar no equivale a crear una nueva fuente de verdad competidora.

## 13. Datos y fuentes prohibidas

Aplican íntegramente las políticas BOS:

- no MongoDB runtime;
- no MongoDB como caché, fallback, lock o configuración;
- no mocks/stubs productivos;
- no hardcodes funcionales;
- no fuentes paralelas;
- no duplicación de tablas/columnas/catálogos;
- no consultas LIVE como dependencia normal de usuario;
- no LocalStorage/JSON/archivos como fuente operativa canónica.

SQL Server es la plataforma canónica para los datos operativos y de negocio de Cavas, respetando el modo de despliegue integrado o standalone.

## 14. Productos y botellas propiedad de socios

Cavas debe permitir controlar botellas/productos propiedad de socios aunque la unidad de negocio no los compre ni venda.

Eso no debe alterar automáticamente:

- compras;
- ventas;
- inventario comercial;
- recetas;
- costo de ventas;
- márgenes;
- operación orgánica de la unidad.

Si el producto ya existe en el catálogo canónico, debe reutilizarse.

Si no existe, la arquitectura deberá permitir su identificación/control dentro del contexto Cavas sin convertirlo automáticamente en producto comprable o vendible.

La implementación física de este punto queda condicionada a auditoría previa del catálogo de productos existente.

## 15. Gobierno de IA durante la implementación

La auditoría arquitectónica inicial y las decisiones base deben ser cerradas por el responsable del proyecto antes de delegar generación de código.

Una vez iniciada la implementación, la IA de código puede operar autónomamente para:

- revisar código;
- auditar implementación;
- ejecutar pruebas;
- detectar inconsistencias;
- corregir bugs dentro del diseño autorizado;
- validar cumplimiento de máximas BOS.

La IA debe solicitar autorización antes de ejecutar cambios que impliquen:

- modificar diseño o arquitectura aprobada;
- crear tablas o columnas no autorizadas;
- crear nuevas fuentes canónicas;
- cambiar contratos canónicos;
- alterar estrategia RBAC;
- mover responsabilidades entre dominios/core;
- introducir nueva infraestructura transversal;
- realizar refactorizaciones estructurales fuera del alcance aprobado.

La IA puede proponer estos cambios y explicar su impacto, pero no ejecutarlos sin autorización.

## 16. Relación con EDARSAHUB BOS

Cavas está subordinado a la definición global de EDARSAHUB BOS contenida en:

`docs/EKS/consolidado/EKS_CORE_001_DEFINICION_EDARSAHUB_BOS.md`

Por tanto, Cavas debe declararse y evolucionar como dominio de negocio con:

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

## 17. Decisiones fijadas

Quedan aprobadas y documentadas las siguientes decisiones:

1. Cavas es dominio/satélite nativo del BOS.
2. Integrado, vive en `Satélites > Cavas`.
3. Cavas tendrá URL propia para Socios Cavas.
4. Socios externos tendrán autenticación propia del portal.
5. Usuarios internos autorizados no volverán a autenticarse al entrar desde EDARSAHUB.
6. No habrá dos dominios Cavas distintos para acceso interno y externo.
7. Autorización interna = RBAC + scope.
8. Autorización externa = autenticación + ownership/relación + políticas aplicables.
9. Cavas debe poder desplegarse standalone sin dependencia runtime de EDARSAHUB.
10. Integraciones externas serán desacopladas y sincronizadas, no LIVE como dependencia operativa.
11. No se duplicarán clientes, productos, permisos, roles, filtros, conexiones, catálogos ni lógica de negocio.
12. Cualquier cambio de arquitectura propuesto durante generación de código requiere autorización previa.

## 18. Pendientes de auditoría antes de implementación de autenticación

Antes de escribir código de acceso/identidad se debe auditar directamente:

- Portal de Proveedores;
- Portal Inteligencia Comercial;
- autenticación dual actual;
- mecanismo SSO/session interno;
- modelos de usuario externo existentes;
- tablas y relaciones de clientes;
- scopes empresa/unidad;
- RBAC SQL actual;
- routing externo y configuración de dominios;
- política de recuperación de contraseña y seguridad de sesiones.

La auditoría debe determinar qué se reutiliza, qué se extiende, qué se canoniza y qué realmente falta antes de crear nuevas estructuras.
