# Cierre funcional — Navegación Enterprise EDARSAHUB

**Fecha:** 3 de agosto de 2026  
**Repositorio:** `rbalam/EDARSA_HUB`  
**Rama:** `Edarsahub_Desarrollo`  
**HEAD base:** `68b65124cb00198c90447120d551716bd73a42da`  
**Ambiente validado:** Preview  
**Producción tocada:** No  
**SQL DML:** No  
**Deploy:** No  

## Objetivo

Dejar funcional y verificable la navegación Enterprise, conservando
SQL y RBAC como fuentes canónicas de acceso.

## Problemas corregidos

- El control del sidebar no conservaba correctamente su estado.
- Los iconos del menú contraído no navegaban.
- El efecto de ruta activa revertía aperturas manuales.
- Grupos y subgrupos no permanecían abiertos.
- El buscador estaba mezclado con la lista desplazable.
- Mi espacio y Favoritos seguían visibles durante una búsqueda.
- La unidad activa mostraba un UUID técnico.
- Se produjo una referencia no resuelta al icono `Search`.

## Correcciones aplicadas

- Los iconos contraídos navegan al primer menú activo del grupo.
- La apertura manual de grupos y secciones ya no es revertida.
- El estado del sidebar se conserva en `localStorage`.
- El buscador queda debajo del nombre, rol y unidad activa.
- Sólo la lista de navegación tiene desplazamiento vertical.
- Durante una búsqueda sólo aparecen resultados coincidentes.
- Mi espacio, Favoritos y grupos se ocultan durante la búsqueda.
- Se muestra el número de coincidencias.
- La unidad activa se resuelve desde `unidades_permitidas`.
- El UUID dejó de mostrarse al usuario.
- El import del icono `Search` quedó restaurado.

## Auditoría canónica

Para `ricardo@edarsa.com.mx` se confirmó:

- Usuario canónico ID: `8`
- Rol: `SUPERADMIN`
- Nivel jerárquico: `100`
- Módulos entregados por endpoint: `28`
- Grupos Enterprise: `8`
- Elementos runtime: `74`
- Elementos descartados: `0`
- Menús objetivo faltantes: `0`

Usuarios, Centro de Control, Servidores, Scheduler, Automatizaciones
y Catálogo SQL existían en SQL, endpoint, registro Enterprise y rutas
React. La aparente ausencia correspondía a la nueva agrupación.

## Archivos modificados

- `frontend/src/pages/Layout.js`
- `frontend/src/components/navigation/EnterpriseNavigationMenu.jsx`

## Validación final

- Navegación contraída: PASS
- Apertura de grupos y subgrupos: PASS
- Menús administrativos visibles: PASS
- Buscador fijo bajo datos del usuario: PASS
- Búsqueda exclusiva por coincidencias: PASS
- Unidad activa legible: PASS
- Guardián Enterprise: PASS
- Error `Search`: corregido

## Guardián Enterprise

```text
ENTERPRISE_NAVIGATION_GUARDIAN=PASS
GROUPS=8
MODULE_MAPPINGS=28
MENU_MAPPINGS=66
PLANNED_ITEMS=54
REGISTERED_FUTURE_TABS=0
NEW_BADGE_DAYS=30
```

## Checksums SHA-256

```text
Layout.js=9e50fbfe73fa8f4fbfb72b0eaed6a6f95e34887e597269c1ba905edda18d842e
EnterpriseNavigationMenu.jsx=de7c66fde9439c93f52b8c4371565de776b095f267e868fef2720ee60932c4c6
enterpriseNavigationRegistry.json=f3efa6053e4febbfda31b86adf772ac86af8be70683d8cbee77196821c85a96f
```

## Controles de seguridad

- No se abrió ni copió `.env`.
- No se imprimieron secretos.
- No se ejecutó SQL DML.
- No se modificó producción.
- No se hizo deploy.
- No se debilitó RBAC.
- No se agregaron fallbacks hardcodeados.

## Estado

**Resultado funcional:** aprobado en Preview.  
**Commit:** pendiente de autorización.  
**Push:** pendiente de autorización.  
**Deploy:** no realizado.
