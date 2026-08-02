# Navegación Enterprise EDARSAHUB

## Fuente canónica

- SQL define módulos, menús, rutas y RBAC.
- El registro Enterprise define su clasificación funcional.
- React representa el catálogo autorizado.
- La ruta canónica identifica los favoritos.
- No existe fallback al menú clásico.

## Grupos

1. Dirección e Inteligencia
2. Comercial y Clientes
3. Operaciones y Abasto
4. Finanzas y Rentabilidad
5. Personas y Organización
6. Control, Calidad y Gestión
7. Plataforma e Integraciones
8. Portales y Aplicaciones Satélite

## Estados

- `active`: funcionalidad operativa.
- `comingSoon`: existe, pero todavía no está operativa.
- `planned`: arquitectura futura sin ruta.

`NEW` y `Próximamente` no pueden aparecer simultáneamente.

## Favoritos por usuario

- Se almacenan en `dbo.Usuario_MenuFavoritos`.
- Se identifican por `UsuarioID` y `Ruta`.
- La reorganización del árbol no modifica las rutas.
- Solo las rutas activas y autorizadas pueden marcarse.
- Los elementos `comingSoon` y `planned` no muestran estrella.
- Cambiar la unidad activa no borra la configuración personal.
- Un favorito sin permiso temporal deja de mostrarse, pero no cambia de dueño.

## Regla NEW

Todo menú o tab nuevo operativo debe:

1. registrarse en el catálogo Enterprise;
2. declarar grupo y subgrupo;
3. declarar `status: active`;
4. declarar `releasedAt` en formato ISO;
5. mostrar `NEW` durante 30 días;
6. conservar su ruta después de vencer la etiqueta.

Los elementos históricos actuales están marcados como `legacy`.
No se autoriza usar `legacy` para funcionalidades futuras.

## Menús nuevos

Todo menú nuevo debe declarar:

- código estable;
- grupo Enterprise;
- subgrupo;
- ruta;
- permiso RBAC;
- estado;
- fecha de liberación cuando sea operativo.

## Tabs nuevos

Los tabs existentes forman la línea base.

Todo tab nuevo debe:

- incluir `data-enterprise-tab-id`;
- registrarse en `enterpriseTabRegistry.json`;
- declarar pantalla o ruta padre;
- declarar grupo y subgrupo;
- usar `EnterpriseTabLabel`;
- declarar `releasedAt` cuando sea operativo.

## Acordeón

- Solo un grupo principal permanece abierto.
- La ruta activa abre su grupo y subgrupo.
- Un favorito navega a su ruta canónica y abre sus padres.
- La búsqueda incluye activos, próximos y planeados.
