# EDARSAHUB V1.2 — Centro Unificado de Comunicaciones y Conexiones

**Estado:** Deuda técnica / backlog V1.2  
**Fecha de registro:** 2026-08-20  
**Alcance:** Arquitectura BOS / administración técnica / integraciones  

## 1. Objetivo

Evolucionar EDARSAHUB hacia un **Centro Unificado de Comunicaciones y Conexiones** que concentre la administración técnica de integraciones, comunicaciones y fuentes externas sin crear silos por proveedor, sin duplicar catálogos, sin introducir nuevas fuentes de verdad y sin crecer innecesariamente el core.

El Centro deberá reutilizar y consolidar la arquitectura existente antes de crear componentes nuevos.

## 2. Evidencia existente que debe reutilizarse

La implementación V1.2 debe partir de las estructuras actuales y no reemplazarlas arbitrariamente:

- `backend/core/connection_resolver.py`: resolver central de conexiones y fuentes.
- `dbo.Servidores_Conexiones`: fuente SQL canónica para configuración de conexiones.
- `docs/ARQUITECTURA_CONEXIONES_RESOLVER.md`: EDARSAHUB es el cerebro; frontend no decide conexiones ni fuentes.
- `backend/modules/api_connections/`: infraestructura existente para conexiones API.
- `backend/core/communications/`: infraestructura de comunicaciones/notificaciones.
- `docs/reports/MONGO_SUNSET_P4_COMMUNICATIONS_CIERRE_20260623.md`: communications ya migrado parcialmente a SQL-first.
- Menú/administración existente de Servidores SQL.
- RBAC, usuarios, empresas, unidades de negocio, sucursales, catálogos y filtros corporativos existentes.

## 3. Máximas obligatorias

1. **EDARSAHUB es el cerebro del sistema.**
2. **SQL EDARSAHUB es la fuente canónica de configuración y estado persistente.**
3. **No crear nuevas dependencias MongoDB.** Cualquier residual histórico de Mongo debe eliminarse o neutralizarse cuando se intervenga el componente, previa evidencia de no dependencia de plataforma.
4. **No conexiones LIVE para datos de negocio**, salvo excepciones explícitamente autorizadas por dominio. Los conectores externos deben sincronizar hacia modelos canónicos publicados.
5. **No duplicar** tablas, catálogos, secretos, resolvers, providers, unidades, empresas, sucursales, RBAC ni jobs ya existentes.
6. **No hardcodear proveedores ni unidades.**
7. **No crear un tab por proveedor.** La UI debe modelar capacidades y tipos de conexión, no marcas.
8. **Frontend sólo administra y visualiza; backend decide y resuelve.**
9. **Secretos nunca se exponen al frontend, logs ni respuestas.**
10. **RBAC y alcance corporativo son obligatorios** para visualizar, crear, editar, probar, activar, desactivar o rotar conexiones.
11. **Fail-closed** ante estado desconocido, credenciales ausentes, conflicto de configuración o fuente no autorizada.
12. **Auditoría completa** de altas, cambios, pruebas, activaciones, desactivaciones, fallos y sincronizaciones.

## 4. Modelo funcional del menú

Nombre propuesto de nivel superior:

**Configuración / Centro de Comunicaciones y Conexiones**

La navegación no debe organizarse por proveedor. Debe permitir vistas y filtros combinables por:

- Tipo de conexión: SQL, API, webhook, mensajería, email, almacenamiento, publicidad, redes sociales, reservas, OTA, pagos y otros.
- Dominio/capacidad: datos, comunicaciones, marketing, reservas, reputación, pagos, automatización, auditoría.
- Empresa.
- Unidad de negocio.
- Sucursal.
- Sistema origen/destino.
- Estado: activo, inactivo, degradado, error, pendiente de credenciales, pendiente de validación.
- Dirección: entrada, salida, bidireccional.
- Tipo de sincronización: programada, evento autorizado, manual administrativa.

## 5. Proveedores futuros que deben poder incorporarse sin crear arquitectura paralela

Ejemplos no exhaustivos:

- Meta / Facebook / Instagram
- X
- Google Ads / Google Business
- OpenTable
- Tripadvisor
- Airbnb
- Expedia
- WhatsApp / Twilio / Meta WhatsApp
- SMTP / email
- NetPay y otros proveedores de pago
- APIs propias o de terceros
- Conexiones SQL de sistemas POS/ERP

Estos nombres son **adaptadores**, no entidades arquitectónicas de primer nivel.

## 6. Arquitectura objetivo

```text
UI Centro de Conexiones
        |
        v
API administrativa canónica
        |
        +--> RBAC / alcance corporativo
        +--> catálogo canónico de conexiones
        +--> secret resolver / referencias de secretos
        +--> connection resolver
        +--> provider/adapters registry
        +--> scheduler/sync orchestration existente
        +--> auditoría
        |
        v
Conectores externos
        |
        v
Staging técnico autorizado / sincronización
        |
        v
Modelos SQL canónicos EDARSAHUB
        |
        v
Consumidores de negocio
```

Los consumidores de negocio **no deben leer directamente del proveedor externo** cuando exista una fuente canónica sincronizada.

## 7. Comunicación y conexiones deben compartir gobierno, no necesariamente implementación interna

`backend/core/communications` y la infraestructura de conexiones deben converger en gobierno administrativo común, pero no deben convertirse en un módulo monolítico.

El Centro será una **capa de administración/orquestación** sobre componentes cohesionados:

- conexiones
- providers
- secretos
- comunicaciones
- sincronizaciones
- health/status
- auditoría

No mover lógica de negocio al core para conseguir una UI unificada.

## 8. Relación con el sistema multiagente / Mirror Worker

La infraestructura de agentes, handoff de resultados y Mirror Worker es **infraestructura de desarrollo**, no una conexión de negocio y no debe introducirse en `backend/core/communications`.

Puede reutilizar patrones de outbox, auditoría y contratos, pero su autoridad permanece separada:

- agentes autorizados ejecutan trabajo y pruebas;
- Mirror Worker certifica/promueve convergencia del repositorio;
- el resultado certificado se consume por la capa de ChatGPT/agentes;
- el Centro de Comunicaciones y Conexiones administra integraciones operativas de EDARSAHUB.

## 9. Deuda técnica V1.2

Antes de implementar el nuevo menú:

- [ ] Auditar `Servidores_Conexiones`, `api_connections`, `connection_resolver`, `communications`, scheduler y menús actuales.
- [ ] Identificar y retirar cualquier residual Mongo de negocio en conexiones/communications que siga vivo.
- [ ] Consolidar SQL + API bajo un catálogo canónico de conexión existente; crear columnas/tablas nuevas sólo si la auditoría demuestra que el modelo actual no puede extenderse correctamente.
- [ ] Integrar RBAC granular y alcances por empresa/unidad/sucursal.
- [ ] Centralizar referencia de secretos sin exponer valores.
- [ ] Definir registry de capacidades/adaptadores sin `if provider == ...` dispersos.
- [ ] Unificar health/status y auditoría de conexiones.
- [ ] Permitir organización flexible por tipo, dominio y unidad de negocio también para conexiones SQL.
- [ ] Preparar conectores de redes sociales, Ads, reservas, reputación, OTA y mensajería sin tabs específicos por proveedor.
- [ ] Garantizar sincronización a SQL canónico y prohibir nuevas lecturas LIVE de negocio.
- [ ] Diseñar frontend reusable basado en metadatos/capacidades.
- [ ] Añadir pruebas de arquitectura: no Mongo, no hardcodes, no bypass del resolver, no secretos, RBAC, no duplicidad y no LIVE.

## 10. Criterios de aceptación V1.2

La deuda se considera cerrada sólo cuando:

1. existe un único punto administrativo para conexiones/comunicaciones;
2. SQL EDARSAHUB sigue siendo la única fuente de verdad de configuración;
3. todas las conexiones SQL usan el resolver/catálogo canónico;
4. las API externas usan adaptadores registrados y sincronización canónica;
5. no existen tabs ni estructuras paralelas por proveedor;
6. RBAC y alcance corporativo aplican a todas las acciones;
7. secretos están protegidos y referenciados, nunca devueltos;
8. health, auditoría y estado son trazables;
9. consumidores de negocio leen datos publicados/canónicos, no fuentes LIVE;
10. no se agregó una nueva dependencia MongoDB ni se duplicó arquitectura existente.

## 11. Nota de arquitectura

Documentación histórica de abril de 2026 aún describe Mongo como caché auxiliar en conexiones API. Esa parte no debe tratarse como diseño objetivo V1.2: la política actual es **no introducir ni conservar dependencias Mongo de negocio** cuando el componente sea intervenido. La referencia histórica sirve para rastrear evolución, no para justificar nuevas dependencias.
