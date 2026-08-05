# ADR — EDARSAHUB V1.2: Core mínimo y modularidad

## Estado

Aprobado.

## Decisión principal

EDARSAHUB no deberá crecer más el core en la medida de lo posible.

Toda capacidad nueva deberá construirse primero dentro del dominio propietario o en una capa de plataforma y composición.

Solo podrán incorporarse al core contratos, tipos, protocolos y validaciones puras que sean mínimos, estables y verdaderamente transversales.

## V1.0

- Estabilizar lo existente.
- Corregir fallos funcionales.
- No realizar refactorizaciones transversales amplias.
- No trasladar lógica específica de dominios al core.
- Dejar puntos de extensión y deuda técnica documentada.
- Conservar RBAC, fuentes canónicas y reglas de negocio.

## V1.2

- Refactorizar preferentemente los menús y estructuras existentes.
- Implementar navegación modular.
- Separar core, platform y dominios.
- Migrar progresivamente lógica duplicada.
- Reducir o estabilizar el tamaño del core.
- Incorporar contratos temporales y KPI atómicos.

## Regla de dependencias

- core no importa modules.
- modules pueden importar contratos mínimos de core.
- platform compone módulos mediante protocolos.
- frontend presenta contratos y no calcula reglas de negocio.

## Prohibiciones

- No agregar lógica funcional de dominios al core.
- No agregar SQL específico de dominio al core.
- No crear condicionales por dominio dentro del core.
- No crear un megamotor transversal.
- No duplicar fuentes de verdad.
- No calcular KPI, comparativos o proyecciones en frontend.
- No crear fallbacks silenciosos.
- No usar core como contenedor genérico de utilidades.

## Criterios de entrada al core

Una capacidad solo podrá entrar al core cuando:

1. Sea utilizada por al menos dos dominios reales.
2. Su semántica sea idéntica.
3. No contenga reglas particulares de dominio.
4. No contenga SQL específico.
5. Pueda probarse de forma aislada.
6. Reduzca duplicación sin aumentar acoplamiento.
7. Tenga contrato estable y versionado.
8. No requiera condiciones por dominio.

Si no cumple todos los criterios, deberá permanecer en el módulo propietario o en platform.

## Menús V1.2

Cada módulo declarará su contribución de navegación.

La plataforma descubrirá contribuciones, validará códigos únicos, aplicará RBAC y alcance organizacional, ordenará los elementos y construirá el árbol final.

El core no conocerá el catálogo completo de menús.

## Máxima permanente

Toda capacidad nueva deberá construirse primero dentro del dominio propietario. Solo contratos mínimos y mecanismos realmente transversales podrán elevarse al core. La refactorización de estructuras existentes se realizará preferentemente en V1.2. V1.0 permanecerá enfocada en estabilidad, operación y funcionalidad.
