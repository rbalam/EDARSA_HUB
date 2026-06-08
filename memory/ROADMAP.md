# EDARSA HUB — ROADMAP / Backlog priorizado

## En curso (orden acordado con usuario: a → d → c → b)
- [x] (a) Precios Sugeridos: columnas $/%, fuente del %, filtro unidad canónico. (2026-06-08)
- [x] (d) SYNC estatus inactivo/baja (SoftRestaurant `productosdetalle.bloqueado`, MPRO `Es_Cve_Estado`) + re-sync. (2026-06-08)
- [ ] (c) **Catálogo canónico NO-LIVE** Categoría→Familia→Subgrupo reutilizable (Análisis + Costos y Márgenes + Inteligencia Comercial). Migrar `/servers/{id}/report-filters` (hoy LIVE → viola NO-LIVE) a EDARSAHUB. Estructuras por sistema:
  - MPRO: 1 catálogo único (Categoría / Departamento / Marca / Línea / Familia / Subfamilia + Proveedor/Comprador).
  - SoftRestaurant: catálogo VENTAS (Clasificación / Grupo / Subgrupo) + catálogo INSUMOS-elaborados (Clasificación / Grupo).
- [ ] (b) **Auto-refresh de sesión**: token de 15 min sin refresco → logout al cambiar de tab. Existe cookie refresh_token 7 días sin usar. Requiere experto de integración (AUTH).

## Backlog (agendado)
- [ ] **Exportar a Excel/PDF** del análisis de Costos y Márgenes filtrado por unidad (y reporte de Auditoría: inventarios + movimientos + consumos + delta). (Solicitado por usuario 2026-06-08)
- [ ] Receta Expandida: ordenar componentes por costo total (mayor→menor) + ordenar por cualquier columna con doble click + abrir sub-recetas (elaborados) al dar click. (Solicitado por usuario)
- [ ] Migrar tableros restantes de `server_id` → `unidad` (TableroEjecutivo, DashboardIA, Compras, Finanzas resto).
- [ ] Issue 2 handoff: centralizar selector inventario inicial/final + modales de detalle (movimientos/consumos) entre Análisis (Reportes.js) y Auditoría (Compras.js).
- [ ] PIC: conectar tarjetas mock "Top Productos" y "Casas/Distribuidores" (DashboardIA) a `Sync_Sales`.
- [ ] ESTELAR histórico solo desde Jun-2025 (¿fecha real de apertura o datos faltantes?).
- [ ] MongoDB sunset (espera autorización del usuario).
