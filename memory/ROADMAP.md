# EDARSA HUB — ROADMAP / Backlog priorizado

## En curso (orden acordado con usuario: a → d → c → b)
- [x] (a) Precios Sugeridos: columnas $/%, fuente del %, filtro unidad canónico. (2026-06-08)
- [x] (d) SYNC estatus inactivo/baja (SoftRestaurant `productosdetalle.bloqueado`, MPRO `Es_Cve_Estado`) + re-sync. (2026-06-08)
- [x] (c) **Catálogo canónico NO-LIVE** Categoría→Familia→Subfamilia. (2026-06-09) `/servers/{id}/report-filters` migrado a NO-LIVE (backend-only, sin cambio de UI). MPRO deriva de `Sync_Productos` (re-sync completo: 7957/7957 con categoría); SoftRestaurant (jerarquía INSUMOS: clasificacionventa/gruposiclasificacion/gruposi) desde nueva tabla `Sync_Catalogo_Filtros` (sincronizada por el job de recetas). Verificado cURL E2E + 4 tests + smoke. CostosMargenes ya era NO-LIVE; PricingIA usa texto libre. PENDIENTE menor: agregar nivel Categoría al filtro de CostosMargenes (mejora).
- [x] (b) **Auto-refresh de sesión**: (2026-06-09) Arreglado el auto-logout a los 15 min. Backend `/auth/refresh` estaba roto (500): bug `.isoformat()` sobre datetime-string + columnas faltantes en `dbo.Sesiones` (FechaRevocacion/MotivoRevocacion/ReemplazadaPorSesionID/RevocadoPorUsuarioID) + `UsuarioID` guardado como hash inestable. Refresh ahora devuelve el token en el body; interceptor axios single-flight refresca silenciosamente en 401 y reintenta. Rotación + detección de replay intactas. Verificado cURL + 3 tests + smoke navegador (token corrupto → sesión mantenida).

## Backlog (agendado)
- [ ] **Exportar a Excel/PDF** del análisis de Costos y Márgenes filtrado por unidad (y reporte de Auditoría: inventarios + movimientos + consumos + delta). (Solicitado por usuario 2026-06-08)
- [ ] Receta Expandida: ordenar componentes por costo total (mayor→menor) + ordenar por cualquier columna con doble click + abrir sub-recetas (elaborados) al dar click. (Solicitado por usuario)
- [x] (2026-06-09) **Compras → contrato canónico `unidad`**: helper central `canonical_server_id(token)` en `request_resolver.py` (regla de centralización) aplicado a los 9 endpoints que resolvían el servidor directo (facturas-proveedor, detalle-factura, parametros GET/POST, productos-para-captura, auditoria-operativa, detalle-movimientos POST, detalle-consumos POST, analisis). Acepta unidad canónica (codigo/pk) y mantiene compatibilidad legacy `server_id`. NO-LIVE (solo lee catálogo). Verificado cURL E2E (codigo vs server_id idénticos) + 6 tests `test_compras_canonical_unidad.py`. `Finanzas`/`DashboardIA` ya eran canónicos.
- [ ] Migrar tableros restantes de `server_id` → `unidad` (TableroEjecutivo resolver `unidad_negocio_id`, Finanzas resto).
- [ ] Issue 2 handoff: centralizar selector inventario inicial/final + modales de detalle (movimientos/consumos) entre Análisis (Reportes.js) y Auditoría (Compras.js).
- [ ] PIC: conectar tarjetas mock "Top Productos" y "Casas/Distribuidores" (DashboardIA) a `Sync_Sales`.
- [ ] ESTELAR histórico solo desde Jun-2025 (¿fecha real de apertura o datos faltantes?).
- [ ] MongoDB sunset (espera autorización del usuario).
