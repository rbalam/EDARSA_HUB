# Tableros con filtros duplicados pendientes de migrar

Fecha: Wed Jun  3 07:14:29 UTC 2026

## Fetch directos a catálogos/filtros desde frontend
```text
/app/frontend/src/portal-inteligencia/pages/VentasFamiliaPage.jsx:70:      const response = await fetch(
/app/frontend/src/portal-inteligencia/pages/VentasPax.jsx:8:        fetch('/api/inteligencia/pax')
/app/frontend/src/portal-inteligencia/pages/DashboardIA.jsx:50:      const response = await fetch(
/app/frontend/src/portal-inteligencia/pages/VentasHorarioPage.jsx:69:      const response = await fetch(
/app/frontend/src/portal-inteligencia/pages/VentasProductoPage.jsx:23:  const [productos, setProductos] = useState(FALLBACK_PRODUCTOS);
/app/frontend/src/portal-inteligencia/pages/VentasProductoPage.jsx:37:      const response = await fetch(
/app/frontend/src/portal-inteligencia/pages/VentasProductoPage.jsx:43:        if (data.length > 0) setProductos(data);
/app/frontend/src/portal-inteligencia/pages/VentasCasaPage.jsx:95:      const response = await fetch(
/app/frontend/src/portal-inteligencia/pages/VentasCasas.jsx:8:        fetch('/api/inteligencia/casas')
/app/frontend/src/portal-inteligencia/pages/AnalisisPAXPage.jsx:47:      const response = await fetch(
/app/frontend/src/pages/Compras.js:125:      const response = await api.get(`/compras/dashboard/${selectedServer}?sucursal=${encodeURIComponent(selectedSucursal)}&meses=${selectedMeses.join(',')}&anios=${selectedAnios.join(',')}`);
/app/frontend/src/pages/Compras.js:529:  const [almacenes, setAlmacenes] = useState([]);
/app/frontend/src/pages/Compras.js:558:      const response = await api.get(`/servers/${serverId}/almacenes?sucursal=${encodeURIComponent(sucursal)}`);
/app/frontend/src/pages/Compras.js:560:      setAlmacenes(unique);
/app/frontend/src/pages/Compras.js:568:      const response = await api.get(`/compras/inventarios-fisicos/${serverId}?sucursal=${encodeURIComponent(sucursal)}`);
/app/frontend/src/pages/Compras.js:581:      const response = await api.get(`/compras/pedidos-vigentes/${serverId}?sucursal=${encodeURIComponent(sucursal)}`);
/app/frontend/src/pages/Compras.js:994:      const response = await api.get(`/compras/facturas-proveedor/${selectedServer}`, {
/app/frontend/src/pages/Compras.js:1023:      const response = await api.get(`/compras/detalle-factura/${selectedServer}/${encodeURIComponent(factura.folio)}`);
/app/frontend/src/pages/Compras.js:1487:  const [almacenes, setAlmacenes] = useState([]);
/app/frontend/src/pages/Compras.js:1683:      const response = await api.get(`/servers/${selectedServer}/almacenes?sucursal=${encodeURIComponent(parentSucursal)}`);
/app/frontend/src/pages/Compras.js:1684:      setAlmacenes(response.data);
/app/frontend/src/pages/Compras.js:1694:      const response = await api.get(`/compras/inventarios-fisicos/${selectedServer}?sucursal=${encodeURIComponent(parentSucursal)}`, {
/app/frontend/src/pages/Compras.js:1718:      const response = await api.get(`/compras/pedidos-vigentes/${selectedServer}?sucursal=${encodeURIComponent(parentSucursal)}`, {
/app/frontend/src/pages/Compras.js:3390:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/pages/Compras.js:3493:          const response = await api.get(`/servers/${selectedServer}/sucursales`);
/app/frontend/src/pages/Compras.js:3495:          setSucursales(sucursalesData);
/app/frontend/src/pages/Compras.js:3524:          setSucursales([]);
/app/frontend/src/pages/Compras.js:3529:      setSucursales([]);
/app/frontend/src/pages/Nominas.js:45:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/pages/Nominas.js:107:    const response = await api.get(url);
/app/frontend/src/pages/Nominas.js:123:      setSucursales(sucursalesData.sucursales || []);
/app/frontend/src/pages/ResetPassword.js:16:import axios from 'axios';
/app/frontend/src/pages/ResetPassword.js:23:  const token = searchParams.get('token');
/app/frontend/src/pages/ResetPassword.js:60:      await axios.post(`${API_URL}/api/auth/reset-password`, {
/app/frontend/src/pages/comercial/TabReglasMargen.jsx:373:      const response = await api.get(`/comercial/alertas-margen/resolver-regla?${params.toString()}`);
/app/frontend/src/pages/comercial/TabReglasMargen.jsx:707:        api.get('/comercial/alertas-margen/reglas?page_size=100'),
/app/frontend/src/pages/comercial/TabReglasMargen.jsx:708:        api.get('/comercial/alertas-margen/estadisticas'),
/app/frontend/src/pages/comercial/TabReglasMargen.jsx:709:        api.get('/comercial/alertas-margen/umbrales')
/app/frontend/src/pages/comercial/PricingIA.jsx:684:    api.get('/servidores/list')
/app/frontend/src/pages/comercial/PricingIA.jsx:690:    api.get('/comercial/pricing/listas-competidores?activo=true')
/app/frontend/src/pages/comercial/PricingIA.jsx:1026:      api.get('/comercial/pricing/listas-competidores?activo=true')
/app/frontend/src/pages/comercial/PricingIA.jsx:1148:      const res = await api.get(`/comercial/competidores?${params}`);
/app/frontend/src/pages/comercial/PricingIA.jsx:1359:        const res = await api.get(`/comercial/competidores?${params}`);
/app/frontend/src/pages/comercial/PricingIA.jsx:1384:        const res = await api.get(`/comercial/competidores/${selectedCompetidor.competidor_id}/menu-items?page_size=200`);
/app/frontend/src/pages/comercial/PricingIA.jsx:1409:      const res = await api.get(`/comercial/competidores/${selectedCompetidor.competidor_id}/menu-items?page_size=200`);
/app/frontend/src/pages/comercial/PricingIA.jsx:1831:      const res = await api.get(`/comercial/pricing-ai/analisis/${id}`);
/app/frontend/src/pages/comercial/PricingIA.jsx:1939:        api.get(`/comercial/pricing-ai/dashboard/metricas?${params}`),
/app/frontend/src/pages/comercial/PricingIA.jsx:1940:        api.get(`/comercial/pricing-ai/dashboard/estadisticas-competidores?${params}`)
/app/frontend/src/pages/comercial/PricingIA.jsx:2414:        const res = await api.get(`/comercial/benchmark/resumen/${unidadId}?empresa_id=${empresaId}`);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:152:      const res = await api.get(url);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:485:      api.get(`/costos-margenes/productos/${productoId}/insumos`)
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1011:        api.get(`/costos-margenes/solicitudes-precio/${solicitudId}`),
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1012:        api.get(`/costos-margenes/solicitudes-precio/${solicitudId}/historial`)
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1334:  const [productos, setProductos] = useState([]);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1407:    api.get('/costos-margenes/unidades-negocio')
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1418:        const res = await api.get(`/costos-margenes/familias${params}`);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1438:      api.get(`/costos-margenes/subfamilias?${params}`)
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1449:      const res = await api.get('/costos-margenes/resumen');
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1458:      const res = await api.get('/costos-margenes/sync-status');
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1489:      const res = await api.get(`/costos-margenes/productos?${params}`);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:1491:      setProductos(res.data.productos || []);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2196:  const [productos, setProductos] = useState([]);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2234:      const res = await api.get(`/comercial/pricing/precios-sugeridos?${params}`);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2235:      setProductos(res.data.productos || []);
/app/frontend/src/pages/comercial/CostosMargenes.jsx:2734:      const res = await api.get('/comercial/pricing/reglas/vinos/rangos');
/app/frontend/src/pages/comercial/CostosMargenes.jsx:3063:      const res = await api.get(`/costos-margenes/solicitudes-precio?${params}`);
/app/frontend/src/pages/comercial/PricingIACharts.jsx:657:      const res = await api.get(`/comercial/pricing/listas-competidores?${params}`);
/app/frontend/src/pages/comercial/PricingIACharts.jsx:713:        api.get(`/comercial/competidores?page_size=200&empresa_id=${empresaId || 1}`),
/app/frontend/src/pages/comercial/PricingIACharts.jsx:714:        api.get(`/comercial/pricing/listas-competidores/${lista.lista_id}/competidores`)
/app/frontend/src/pages/Finanzas.js:43:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/pages/Finanzas.js:310:    const response = await api.get(endpoint);
/app/frontend/src/pages/Finanzas.js:354:      setSucursales(data.sucursales || []);
/app/frontend/src/pages/ConfigAsignaciones.jsx:96:  const [almacenesPorUnidad, setAlmacenesPorUnidad] = useState({}); // {unidad_id: [{id, nombre}]}
/app/frontend/src/pages/ConfigAsignaciones.jsx:160:      const response = await api.get(`/config-asignaciones?${params.toString()}`);
/app/frontend/src/pages/ConfigAsignaciones.jsx:177:      const response = await api.get('/config-asignaciones/unidades-negocio');
/app/frontend/src/pages/ConfigAsignaciones.jsx:187:      const response = await api.get(`/config-asignaciones/almacenes/${unidadId}`);
/app/frontend/src/pages/ConfigAsignaciones.jsx:199:      setAlmacenesPorUnidad({});
/app/frontend/src/pages/ConfigAsignaciones.jsx:215:    setAlmacenesPorUnidad(nuevoAlmacenes);
/app/frontend/src/pages/ConfigAsignaciones.jsx:223:    setAlmacenesPorUnidad({ [unidadId]: almacenes });
/app/frontend/src/pages/ConfigAsignaciones.jsx:228:      const response = await api.get('/users');
/app/frontend/src/pages/ConfigAsignaciones.jsx:240:      const response = await api.get(`/config-asignaciones/almacenes/${unidadId}/sync-info`);
/app/frontend/src/pages/ConfigAsignaciones.jsx:280:      setAlmacenesPorUnidad(prev => ({ ...prev, [unidadId]: almacenes }));
/app/frontend/src/pages/ConfigAsignaciones.jsx:341:    setAlmacenesPorUnidad({});
/app/frontend/src/pages/ConfigAsignaciones.jsx:370:      setAlmacenesPorUnidad(prev => ({ ...prev, [asignacion.unidad_negocio_id]: almacenes }));
/app/frontend/src/pages/ConfigAsignaciones.jsx:438:        setAlmacenesPorUnidad(prev => ({ ...prev, [unidadId]: almacenes }));
/app/frontend/src/pages/ExploradorBD.js:6:// AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado de axios directo a api centralizado
/app/frontend/src/pages/ExploradorBD.js:58:      const response = await api.get(
/app/frontend/src/pages/ExploradorBD.js:645:      const response = await api.get(
/app/frontend/src/pages/ExploradorBD.js:924:      const response = await api.get(`/explorador/tablas/${serverId}`);
/app/frontend/src/pages/ExploradorBD.js:958:        api.get(`/explorador/columnas/${serverSeleccionado}/${tabla}`),
/app/frontend/src/pages/ExploradorBD.js:959:        api.get(`/explorador/relaciones/${serverSeleccionado}/${tabla}`)
/app/frontend/src/pages/ExploradorBD.js:975:      const response = await api.get(
/app/frontend/src/pages/Servidores.js:101:  const [sucursalesConfigOpen, setSucursalesConfigOpen] = useState(false);
/app/frontend/src/pages/Servidores.js:102:  const [sucursalesConfig, setSucursalesConfig] = useState([]);
/app/frontend/src/pages/Servidores.js:195:      const response = await api.get('/catalogos/sistemas-capacidades');
/app/frontend/src/pages/Servidores.js:218:      const response = await api.get('/catalogos/sistemas/activos');
/app/frontend/src/pages/Servidores.js:308:      const response = await api.get('/api-connections');
/app/frontend/src/pages/Servidores.js:359:      const response = await api.get('/vtiger/connections');
/app/frontend/src/pages/Servidores.js:843:      const response = await api.get('/servers');
/app/frontend/src/pages/Servidores.js:860:      const response = await api.get(`/servers/${serverId}/ping`, { timeout: 10000 }); // 10s timeout
/app/frontend/src/pages/Servidores.js:894:      const response = await api.get(`/servers/${serverId}/ping`);
/app/frontend/src/pages/Servidores.js:1001:        api.get(`/servers/${serverId}/tipos-movimiento`),
/app/frontend/src/pages/Servidores.js:1002:        api.get(`/servers/${serverId}/categorias`),
/app/frontend/src/pages/Servidores.js:1003:        api.get(`/servers/${serverId}/departamentos`)
/app/frontend/src/pages/Servidores.js:1032:    setSucursalesConfigOpen(true);
/app/frontend/src/pages/Servidores.js:1039:      const response = await api.get(`/servers/${serverId}/sucursales-config`);
/app/frontend/src/pages/Servidores.js:1040:      setSucursalesConfig(response.data.sucursales || []);
/app/frontend/src/pages/Servidores.js:1044:      setSucursalesConfig([]);
/app/frontend/src/pages/Servidores.js:1057:      setSucursalesConfig(response.data.sucursales || []);
/app/frontend/src/pages/Servidores.js:1075:      setSucursalesConfig(prev => prev.map(s => 
/app/frontend/src/pages/Servidores.js:3312:      <Dialog open={sucursalesConfigOpen} onOpenChange={setSucursalesConfigOpen}>
/app/frontend/src/pages/Servidores.js:3431:              <Button variant="outline" onClick={() => setSucursalesConfigOpen(false)}>
/app/frontend/src/pages/Catalogos.js:109:      const response = await api.get('/catalogos/dominios');
/app/frontend/src/pages/Catalogos.js:136:      const response = await api.get(`/catalogos/tabla/${catalogoActivo.tabla}?${params}`);
/app/frontend/src/pages/Catalogos.js:212:      const response = await api.get('/catalogos/admin/verificar-tablas');
/app/frontend/src/pages/cava-socios/SocioForm.jsx:72:      const response = await api.get(`/cava-socios/socios/${id}`);
/app/frontend/src/pages/cava-socios/SociosList.jsx:59:      const response = await api.get(`/cava-socios/socios?${params}`);
/app/frontend/src/pages/cava-socios/CavaSociosDashboard.jsx:42:        api.get(`/cava-socios/dashboard?empresa_id=${EMPRESA_ID}`),
/app/frontend/src/pages/cava-socios/CavaSociosDashboard.jsx:43:        api.get(`/cava-socios/socios?empresa_id=${EMPRESA_ID}&limit=10`)
/app/frontend/src/pages/cava-socios/SocioDetail.jsx:106:      const response = await api.get(`/cava-socios/socios/${id}`);
/app/frontend/src/pages/cava-socios/SocioDetail.jsx:212:      const response = await api.get(`/cava-socios/reportes/socio/${id}/${tipo}`, {
/app/frontend/src/pages/RecursosHumanos.js:55:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/pages/RecursosHumanos.js:234:    const response = await api.get(url);
/app/frontend/src/pages/RecursosHumanos.js:258:      setSucursales(sucData.sucursales || []);
/app/frontend/src/pages/RecursosHumanos.js:496:        const response = await api.get(url);
/app/frontend/src/pages/RecursosHumanos.js:1083:      const response = await api.get('/rrhh/incidencias/plantilla-excel', {
/app/frontend/src/pages/Reportes.js:57:  const initialTab = searchParams.get('tab') || 'analisis';
/app/frontend/src/pages/Reportes.js:77:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/pages/Reportes.js:78:  const [almacenes, setAlmacenes] = useState([]);
/app/frontend/src/pages/Reportes.js:103:  const [almacenesPendientesSeleccionados, setAlmacenesPendientesSeleccionados] = useState([]);
/app/frontend/src/pages/Reportes.js:260:      const response = await api.get('/auditoria/informes');
/app/frontend/src/pages/Reportes.js:414:      const response = await api.get(`/auditoria/informes/${informeId}`);
/app/frontend/src/pages/Reportes.js:426:      const response = await api.get(`/auditoria/informes/${informeId}/pdf`, {
/app/frontend/src/pages/Reportes.js:523:        setAlmacenes([]);
/app/frontend/src/pages/Reportes.js:524:        setSucursales([]);
/app/frontend/src/pages/Reportes.js:552:      const response = await api.get(url);
/app/frontend/src/pages/Reportes.js:553:      setAlmacenes(response.data);
/app/frontend/src/pages/Reportes.js:562:      setAlmacenes([]);
/app/frontend/src/pages/Reportes.js:572:      const response = await api.get(`/servers/${filters.server_id}/report-filters`);
/app/frontend/src/pages/Reportes.js:644:          const response = await api.get(`/compras/inventarios-fisicos/${filters.server_id}`, { params });
/app/frontend/src/pages/Reportes.js:807:      const response = await api.get(`/servers/${filters.server_id}/sucursales`);
/app/frontend/src/pages/Reportes.js:810:      setSucursales(data);
/app/frontend/src/pages/Reportes.js:813:      setSucursales([]);
/app/frontend/src/pages/Reportes.js:820:      const response = await api.get(`/servers/${filters.server_id}/almacenes`, {
/app/frontend/src/pages/Reportes.js:824:      setAlmacenes(response.data);
/app/frontend/src/pages/Reportes.js:827:      setAlmacenes([]);
/app/frontend/src/pages/Reportes.js:833:      const response = await api.get(`/servers/${filters.server_id}/inventarios`, {
/app/frontend/src/pages/Reportes.js:865:      const response = await api.get(url);
/app/frontend/src/pages/Reportes.js:1008:    setAlmacenes([]);
/app/frontend/src/pages/Reportes.js:2540:                      onClick={() => setAlmacenesPendientesSeleccionados([])}
/app/frontend/src/pages/Reportes.js:2551:                            setAlmacenesPendientesSeleccionados(prev => prev.filter(a => a !== alm));
/app/frontend/src/pages/Reportes.js:2553:                            setAlmacenesPendientesSeleccionados([alm]);
/app/frontend/src/pages/Scheduler.jsx:227:      const response = await api.get('/v2/scheduler/status');
/app/frontend/src/pages/Scheduler.jsx:237:      const response = await api.get('/v2/scheduler/config');
/app/frontend/src/pages/Scheduler.jsx:254:      const response = await api.get(`/v2/scheduler/logs?${params}`);
/app/frontend/src/pages/Scheduler.jsx:264:      const response = await api.get('/v2/scheduler/logs/stats?hours=24');
/app/frontend/src/pages/DBACredentialManager.jsx:80:      const response = await fetch(`${API_URL}/api/admin/dba-credential/status`, {
/app/frontend/src/pages/DBACredentialManager.jsx:118:      const response = await fetch(`${API_URL}/api/admin/dba-credential/register`, {
/app/frontend/src/pages/DBACredentialManager.jsx:156:      const response = await fetch(`${API_URL}/api/admin/dba-credential/test-connection`, {
/app/frontend/src/pages/DBACredentialManager.jsx:184:      const response = await fetch(`${API_URL}/api/admin/dba-credential/execute-diagnostic`, {
/app/frontend/src/pages/DBACredentialManager.jsx:217:      const response = await fetch(`${API_URL}/api/admin/dba-credential/clear`, {
/app/frontend/src/pages/Dashboard.js:95:  const [almacenesPendientesSeleccionados, setAlmacenesPendientesSeleccionados] = useState([]);
/app/frontend/src/pages/Dashboard.js:134:      const response = await api.get(`/dashboard/inventory-summary?server_id=${serverId}`);
/app/frontend/src/pages/Dashboard.js:152:    setAlmacenesPendientesSeleccionados([]);
/app/frontend/src/pages/Dashboard.js:154:      const response = await api.get(`/inventarios/pendientes/${serverId}`);
/app/frontend/src/pages/Dashboard.js:661:                      onClick={() => setAlmacenesPendientesSeleccionados([])}
/app/frontend/src/pages/Dashboard.js:671:                            setAlmacenesPendientesSeleccionados(prev => prev.filter(a => a !== alm));
/app/frontend/src/pages/Dashboard.js:673:                            setAlmacenesPendientesSeleccionados([alm]);
/app/frontend/src/pages/ImportadorRH.js:49:      const resp = await api.get('/rrhh/importar/staging/estadisticas');
/app/frontend/src/pages/ImportadorRH.js:60:      const resp = await api.get(`/rrhh/importar/staging/pendientes?limite=200${empresaParam}`);
/app/frontend/src/pages/ImportadorRH.js:73:      const resp = await api.get('/rrhh/importar/staging/incompletos?limite=200');
/app/frontend/src/pages/ImportadorRH.js:85:      const resp = await api.get('/rrhh/importar/staging/excluidos?limite=200');
/app/frontend/src/pages/ImportadorRH.js:110:      const resp = await api.get('/rrhh/importar/homologacion/estadisticas');
/app/frontend/src/pages/ImportadorRH.js:120:      const resp = await api.get('/rrhh/importar/homologacion/equivalencias');
/app/frontend/src/pages/TableroEjecutivo.js:5:// AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado de axios directo a api centralizado
/app/frontend/src/pages/TableroEjecutivo.js:545:            const histResponse = await api.get(`/v2/comercial/kpis-diarios/${unidad.unidad_negocio_id || unidad.id}`, {
/app/frontend/src/pages/TableroEjecutivo.js:611:            api.get(`/comercial/dashboard/${unidad.server_id}${periodParams}`),
/app/frontend/src/pages/TableroEjecutivo.js:612:            api.get(`/comercial/ventas-tiempo/${unidad.server_id}${params}`),
/app/frontend/src/pages/TableroEjecutivo.js:613:            api.get(`/comercial/mesas/${unidad.server_id}${params}`)
/app/frontend/src/pages/TableroEjecutivo.js:984:            const v2VentasDia = await api.get(`/v2/comercial/ventas-dia`, { timeout: 30000 });
/app/frontend/src/pages/TableroEjecutivo.js:1079:            const v2Response = await api.get(`/v2/comercial/dashboard`, {
/app/frontend/src/pages/TableroEjecutivo.js:1113:        const response = await api.get(`/comercial/tablero-ejecutivo`, {
/app/frontend/src/pages/ForgotPassword.js:16:import axios from 'axios';
/app/frontend/src/pages/ForgotPassword.js:32:      await axios.post(`${API_URL}/api/auth/forgot-password`, { email });
/app/frontend/src/pages/CatalogoConsultas.js:2:// AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado de axios directo a api centralizado
/app/frontend/src/pages/Finanzas.js.backup:33:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/pages/Finanzas.js.backup:271:          const response = await fetch(`${API_URL}/api/users`, {
/app/frontend/src/pages/Finanzas.js.backup:328:    const response = await fetch(`${API_URL}${endpoint}`, {
/app/frontend/src/pages/Finanzas.js.backup:375:      setSucursales(data.sucursales || []);
/app/frontend/src/pages/Finanzas.js.backup:505:      const response = await fetch(`${API_URL}/api/finanzas/cuentas-por-pagar/${facturaId}/decision-pago`, {
/app/frontend/src/pages/Finanzas.js.backup:613:      const response = await fetch(`${API_URL}/api/finanzas/cuentas-por-pagar/decision-pago-masivo`, {
/app/frontend/src/pages/Finanzas.js.backup:655:      const response = await fetch(`${API_URL}/api/finanzas/cuentas-por-pagar/decision-pago-masivo`, {
/app/frontend/src/pages/Finanzas.js.backup:739:      const response = await fetch(`${API_URL}/api/finanzas/ingresos/cortes-caja/${corteId}/deposito-efectivo`, {
/app/frontend/src/pages/Finanzas.js.backup:763:      const response = await fetch(`${API_URL}/api/finanzas/ingresos/cortes-caja/${corteId}/deposito-tarjetas?referencia_netpay=${referencia}`, {
/app/frontend/src/pages/Finanzas.js.backup:849:      const response = await fetch(url, {
/app/frontend/src/pages/Finanzas.js.backup:876:      const response = await fetch(`${API_URL}/api/finanzas/presupuestos/${pres.PresupuestoID}`, {
/app/frontend/src/pages/tablajeria/OrdenesPage.jsx:69:      const response = await api.get(`/tablajeria/ordenes?${params}`);
/app/frontend/src/pages/tablajeria/OrdenesPage.jsx:82:      const response = await api.get('/tablajeria/plantillas?estatus=PUBLICADA&limit=100');
/app/frontend/src/pages/tablajeria/OrdenesPage.jsx:84:      const response2 = await api.get('/tablajeria/plantillas?estatus=SINCRONIZADA&limit=100');
/app/frontend/src/pages/tablajeria/OrdenesPage.jsx:85:      const response3 = await api.get('/tablajeria/plantillas?estatus=VALIDADA&limit=100');
/app/frontend/src/pages/tablajeria/OrdenesPage.jsx:99:      const response = await api.get(`/tablajeria/ordenes/${ordenId}`);
/app/frontend/src/pages/tablajeria/TablajeriaDashboard.jsx:35:        api.get('/tablajeria/dashboard/kpis'),
/app/frontend/src/pages/tablajeria/TablajeriaDashboard.jsx:36:        api.get('/tablajeria/dashboard/alertas?umbral=5'),
/app/frontend/src/pages/tablajeria/TablajeriaDashboard.jsx:37:        api.get('/tablajeria/dashboard/rendimientos-plantilla?limit=5'),
/app/frontend/src/pages/tablajeria/TablajeriaDashboard.jsx:38:        api.get('/tablajeria/dashboard/top-mermas?limit=5'),
/app/frontend/src/pages/tablajeria/TablajeriaDashboard.jsx:39:        api.get('/tablajeria/dashboard/resumen-costeo')
/app/frontend/src/pages/tablajeria/PlantillasPage.jsx:39:      const response = await api.get(`/tablajeria/plantillas?${params}`);
/app/frontend/src/pages/tablajeria/PlantillasPage.jsx:52:      const response = await api.get(`/tablajeria/plantillas/${plantillaId}`);
/app/frontend/src/pages/tablajeria/CapturaDirectaPage.jsx:35:  const [empresas, setEmpresas] = useState([]);
/app/frontend/src/pages/tablajeria/CapturaDirectaPage.jsx:65:      const response = await api.get('/empresas');
/app/frontend/src/pages/tablajeria/CapturaDirectaPage.jsx:66:      setEmpresas(response.data.empresas || response.data || []);
/app/frontend/src/pages/AutorizacionCompras.js:4:// AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado de axios directo a api centralizado
/app/frontend/src/pages/AutorizacionCompras.js:195:      const response = await api.get(`/compras/detalle-pedido-manual/${selectedServer}?folio=${encodeURIComponent(folioManual)}`);
/app/frontend/src/pages/AutorizacionCompras.js:281:      const response = await api.get(`/compras/detalle-movimientos/${selectedServer}?codigo_producto=${codigo}&almacenes=${infoInventario.almacenCodigos.join(',')}&fecha_ini=${fechaInvFisico}&fecha_fin=${fechaFinPeriodo}`);
/app/frontend/src/pages/AutorizacionCompras.js:293:      const response = await api.get(`/compras/detalle-consumos/${selectedServer}?codigo_producto=${codigo}&sucursal_codigo=${infoInventario.sucursalCodigo}&fecha_ini=${fechaInvFisico}&fecha_fin=${fechaFinPeriodo}`);
/app/frontend/src/pages/Dashboard.js.backup:85:  const [almacenesPendientesSeleccionados, setAlmacenesPendientesSeleccionados] = useState([]);
/app/frontend/src/pages/Dashboard.js.backup:104:      const response = await api.get('/dashboard/servers-configured');
/app/frontend/src/pages/Dashboard.js.backup:124:      const response = await api.get(`/dashboard/inventory-summary?server_id=${serverId}`);
/app/frontend/src/pages/Dashboard.js.backup:142:    setAlmacenesPendientesSeleccionados([]);
/app/frontend/src/pages/Dashboard.js.backup:144:      const response = await api.get(`/inventarios/pendientes/${serverId}`);
/app/frontend/src/pages/Dashboard.js.backup:659:                      onClick={() => setAlmacenesPendientesSeleccionados([])}
/app/frontend/src/pages/Dashboard.js.backup:669:                            setAlmacenesPendientesSeleccionados(prev => prev.filter(a => a !== alm));
/app/frontend/src/pages/Dashboard.js.backup:671:                            setAlmacenesPendientesSeleccionados([alm]);
/app/frontend/src/pages/Comercial.js:24:// AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado de axios directo a api centralizado
/app/frontend/src/pages/Comercial.js:182:      const response = await api.get(`/comercial/detalle-movimientos/${serverId}`, {
/app/frontend/src/pages/Comercial.js:382:      const response = await api.get(`/comercial/dashboard/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:979:      const response = await api.get(`/comercial/ticket-perfecto/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:1168:      const response = await api.get(`/comercial/metas/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:1309:      const response = await api.get(`/comercial/ventas-tiempo/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:1461:      const response = await api.get(`/comercial/mesas/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:1631:      const response = await api.get(`/comercial/reporte-pax/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2103:      const response = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2126:        const responseAnterior = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2167:          const res = await api.get(`/comercial/precios-constantes/${selectedServer}`, {
/app/frontend/src/pages/Comercial.js:2721:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/pages/Comercial.js:2807:  // NO hacer llamada adicional a /api/servers/.../sucursales que no respeta RBAC
/app/frontend/src/pages/Comercial.js:2815:        setSucursales([]);
/app/frontend/src/pages/Comercial.js:2829:      setSucursales(sucursalesRBAC);
/app/frontend/src/pages/Comercial.js:2870:      setSucursales([]);
/app/frontend/src/pages/MisTareas.js:52:  const [sucursalesProveedor, setSucursalesProveedor] = useState([]);
/app/frontend/src/pages/MisTareas.js:102:    const response = await api.get(url);
/app/frontend/src/pages/MisTareas.js:182:      const response = await api.get('/portal/admin/all-suppliers');
/app/frontend/src/pages/MisTareas.js:192:      const response = await api.get('/servers');
/app/frontend/src/pages/MisTareas.js:611:      setSucursalesProveedor([]);
/app/frontend/src/pages/MisTareas.js:641:    setSucursalesProveedor(supplier.sucursales_asignadas || []);
/app/frontend/src/pages/MisTareas.js:1273:                                    setSucursalesProveedor([...sucursalesProveedor, suc.codigo]);
/app/frontend/src/pages/MisTareas.js:1275:                                    setSucursalesProveedor(sucursalesProveedor.filter(s => s !== suc.codigo));
/app/frontend/src/pages/AutorizacionCompras.js.backup:2:import axios from 'axios';
/app/frontend/src/pages/AutorizacionCompras.js.backup:45:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/pages/AutorizacionCompras.js.backup:46:  const [almacenes, setAlmacenes] = useState([]);
/app/frontend/src/pages/AutorizacionCompras.js.backup:87:        const response = await axios.get(`${API_URL}/api/servers`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:218:      const response = await axios.get(`${API_URL}/api/servers/${serverId}/sucursales`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:221:      setSucursales(response.data);
/app/frontend/src/pages/AutorizacionCompras.js.backup:230:      const response = await axios.get(`${API_URL}/api/servers/${serverId}/almacenes?sucursal=${encodeURIComponent(sucursal)}`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:234:      setAlmacenes(unique);
/app/frontend/src/pages/AutorizacionCompras.js.backup:247:      const response = await axios.get(url, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:263:      const response = await axios.get(`${API_URL}/api/compras/pedidos-vigentes/${serverId}?sucursal=${encodeURIComponent(sucursal)}`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:301:      const response = await axios.get(`${API_URL}/api/compras/detalle-pedido-manual/${selectedServer}?folio=${encodeURIComponent(folioManual)}`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:335:      const response = await axios.post(`${API_URL}/api/compras/calculo-pedido`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:393:      const response = await axios.get(`${API_URL}/api/compras/detalle-movimientos/${selectedServer}?codigo_producto=${codigo}&almacenes=${infoInventario.almacenCodigos.join(',')}&fecha_ini=${fechaInvFisico}&fecha_fin=${fechaFinPeriodo}`, {
/app/frontend/src/pages/AutorizacionCompras.js.backup:408:      const response = await axios.get(`${API_URL}/api/compras/detalle-consumos/${selectedServer}?codigo_producto=${codigo}&sucursal_codigo=${infoInventario.sucursalCodigo}&fecha_ini=${fechaInvFisico}&fecha_fin=${fechaFinPeriodo}`, {
/app/frontend/src/pages/ConfiguracionOperativaUnidades.jsx:54:      const response = await fetch(
/app/frontend/src/pages/ConfiguracionOperativaUnidades.jsx:72:      const response = await fetch(
/app/frontend/src/pages/crm/OportunidadesPage.jsx:49:      const response = await api.get(`/crm/native/oportunidades?${params}`);
/app/frontend/src/pages/crm/CRMDashboard.jsx:20:      const response = await api.get(`/crm/native/dashboard?empresa_id=${EMPRESA_ID}`);
/app/frontend/src/pages/crm/CuentasPage.jsx:34:      const response = await api.get('/crm/cuentas', { 
/app/frontend/src/pages/crm/ImplementacionesPage.jsx:18:      const response = await api.get('/crm/implementaciones');
/app/frontend/src/pages/crm/PedidosPage.jsx:33:      const response = await api.get('/crm/pedidos-venta', { params: { limit: 100 } });
/app/frontend/src/pages/crm/PedidosPage.jsx:44:      const response = await api.get('/crm/clientes', { params: { limit: 500 } });
/app/frontend/src/pages/crm/CerrarOportunidadModal.jsx:30:      const response = await api.get('/crm/native/catalogos');
/app/frontend/src/pages/crm/CotizacionesPage.jsx:33:      const response = await api.get('/crm/cotizaciones', { params: { limit: 100 } });
/app/frontend/src/pages/crm/CotizacionesPage.jsx:44:      const response = await api.get('/crm/clientes', { params: { limit: 500 } });
/app/frontend/src/pages/crm/RemisionesPage.jsx:32:      const response = await api.get('/crm/remisiones-venta', { params: { limit: 100 } });
/app/frontend/src/pages/crm/RemisionesPage.jsx:43:      const response = await api.get('/crm/clientes', { params: { limit: 500 } });
/app/frontend/src/pages/crm/LeadForm.jsx:56:      const response = await api.get('/crm/native/catalogos');
/app/frontend/src/pages/crm/PostventaPage.jsx:18:      const response = await api.get('/crm/postventa/tickets');
/app/frontend/src/pages/crm/SolicitudesAltaPage.jsx:40:      const response = await api.get('/crm/clientes/solicitudes', { params: { limit: 100 } });
/app/frontend/src/pages/crm/ConvertirLeadModal.jsx:32:      const response = await api.get('/crm/native/pipelines');
/app/frontend/src/pages/crm/PipelinePage.jsx:25:      const response = await api.get(
/app/frontend/src/pages/crm/OportunidadForm.jsx:49:      const response = await api.get('/crm/native/pipelines');
/app/frontend/src/pages/crm/LeadsPage.jsx:48:      const response = await api.get(`/crm/native/leads?${params}`);
/app/frontend/src/pages/Layout.js:128:        const response = await api.get('/sistema/menus/usuario');
/app/frontend/src/pages/Layout.js:153:        const response = await api.get('/auth/me/menu-permissions');
/app/frontend/src/pages/Alertas.js:31:      const response = await api.get('/alerts');
/app/frontend/src/pages/CentroControl.jsx:172:      const response = await api.get('/centro-control/destinatarios');
/app/frontend/src/pages/CentroControl.jsx:183:      const response = await api.get('/notificaciones/config');
/app/frontend/src/pages/Usuarios.js:35:  const [sucursalesMap, setSucursalesMap] = useState({});
/app/frontend/src/pages/Usuarios.js:86:  const [sucursalesProveedor, setSucursalesProveedor] = useState([]);
/app/frontend/src/pages/Usuarios.js:109:      const response = await api.get('/users');
/app/frontend/src/pages/Usuarios.js:121:      const response = await api.get('/servers');
/app/frontend/src/pages/Usuarios.js:135:        api.get('/sistema/estructura-organizacional'),
/app/frontend/src/pages/Usuarios.js:136:        api.get('/sistema/mapeo-servidores')
/app/frontend/src/pages/Usuarios.js:163:      const response = await api.get('/portal/admin/all-suppliers');
/app/frontend/src/pages/Usuarios.js:196:      setSucursalesProveedor([]);
/app/frontend/src/pages/Usuarios.js:224:    setSucursalesProveedor(supplier.sucursales_asignadas || []);
/app/frontend/src/pages/Usuarios.js:251:      const response = await api.get('/sistema/usuarios-asignables');
/app/frontend/src/pages/Usuarios.js:260:      const response = await api.get('/sistema/catalogos-disponibles');
/app/frontend/src/pages/Usuarios.js:311:      const response = await api.get('/roles');
/app/frontend/src/pages/Usuarios.js:323:      const response = await api.get('/roles/modulos');
/app/frontend/src/pages/Usuarios.js:393:      const response = await api.get(`/servers/${serverId}/sucursales`);
/app/frontend/src/pages/Usuarios.js:395:      setSucursalesMap(prev => ({ ...prev, [serverId]: data }));
/app/frontend/src/pages/Usuarios.js:398:      setSucursalesMap(prev => ({ ...prev, [serverId]: [] }));
/app/frontend/src/pages/Usuarios.js:405:      const response = await api.get(`/servers/${serverId}/departamentos`);
/app/frontend/src/pages/Proveedores.js:41:      const response = await api.get('/portal/admin/all-suppliers');
/app/frontend/src/pages/Proveedores.js:53:      const response = await api.get('/servers');
/app/frontend/src/components/PropinasTPV.jsx:59:  const [sucursales, setSucursales] = useState([]);
/app/frontend/src/components/PropinasTPV.jsx:60:  const [empresas, setEmpresas] = useState([]);
/app/frontend/src/components/PropinasTPV.jsx:83:      const resV2 = await fetch(`${API_URL}/api/finanzas/propinas/v2/unidades`, {
/app/frontend/src/components/PropinasTPV.jsx:107:      const res = await fetch(`${API_URL}/api/servers`, {
/app/frontend/src/components/PropinasTPV.jsx:130:      const resSuc = await fetch(`${API_URL}/api/sucursales`, {
/app/frontend/src/components/PropinasTPV.jsx:135:        setSucursales(data.sucursales || data || []);
/app/frontend/src/components/PropinasTPV.jsx:138:      const resServers = await fetch(`${API_URL}/api/servers`, {
/app/frontend/src/components/PropinasTPV.jsx:145:        setEmpresas(Array.from(empresasSet));
/app/frontend/src/components/PropinasTPV.jsx:155:      const res = await fetch(`${API_URL}/api/finanzas/propinas/config/all`, {
/app/frontend/src/components/PropinasTPV.jsx:187:      const res = await fetch(`${API_URL}/api/finanzas/propinas/v2/detalle?${params.toString()}`, {
/app/frontend/src/components/PropinasTPV.jsx:256:      const res = await fetch(url, {
/app/frontend/src/components/BarraLateral.jsx:34:          api.get('/sistema/menus/usuario'),
/app/frontend/src/components/fase2_operativo/ResponsabilidadPendientesPanel.jsx:171:        const res = await fetch(`${API_BASE}/api/v2/responsabilidad/${responsabilidadId}/historial`);
/app/frontend/src/components/fase2_operativo/ResponsabilidadPendientesPanel.jsx:247:        fetch(`${API_BASE}/api/v2/responsabilidad/pendientes-aprobacion`),
/app/frontend/src/components/fase2_operativo/ResponsabilidadPendientesPanel.jsx:248:        fetch(`${API_BASE}/api/v2/responsabilidad/en-disputa`)
/app/frontend/src/components/fase2_operativo/ResponsabilidadCard.jsx:137:      const response = await fetch(`${API_BASE}/api/v2/responsabilidad/metricas`, {
/app/frontend/src/components/fase2_operativo/ResponsabilidadAccionesModal.jsx:138:      const response = await fetch(
/app/frontend/src/components/fase2_operativo/SLACard.jsx:83:      const response = await fetch(`${API_BASE}/api/v2/sla/metricas`, {
/app/frontend/src/components/fase2_operativo/WorkflowList.jsx:186:      const response = await fetch(
/app/frontend/src/components/fase2_operativo/WorkflowList.jsx:199:      const contentDisposition = response.headers.get('Content-Disposition');
/app/frontend/src/components/ModalSolicitudCatalogo.jsx:115:      const response = await fetch(`${API_URL}/api/rrhh/solicitudes-catalogo`, {
/app/frontend/src/components/auditorias/useAuditoriasData.js:30:      const response = await fetch(`${API_URL}/api/v2/auditorias-programadas`, fetchOptions);
/app/frontend/src/components/auditorias/useAuditoriasData.js:42:      const response = await fetch(`${API_URL}/api/v2/auditorias-programadas/kpis`, fetchOptions);
/app/frontend/src/components/auditorias/useAuditoriasData.js:53:      const response = await fetch(
/app/frontend/src/components/auditorias/useAuditoriasData.js:68:      const response = await fetch(
/app/frontend/src/components/TabOperativasCompras.jsx:103:        fetch(`${API_URL}/api/v2/automatizaciones/operativas/compras/kpis`, { credentials: 'include' }),
/app/frontend/src/components/TabOperativasCompras.jsx:104:        fetch(`${API_URL}/api/v2/automatizaciones/operativas/compras?limite=50`, { credentials: 'include' })
/app/frontend/src/components/TabOperativasCompras.jsx:123:      const res = await fetch(
/app/frontend/src/components/TabOperativasCompras.jsx:140:        const bitRes = await fetch(
/app/frontend/src/components/TabOperativasCompras.jsx:156:      const res = await fetch(
/app/frontend/src/components/TabOperativasCompras.jsx:195:      const res = await fetch(
/app/frontend/src/components/TabOperativasCompras.jsx:224:      const res = await fetch(
/app/frontend/src/components/TabOperativasCompras.jsx:249:      const res = await fetch(
/app/frontend/src/components/GestionSolicitudesCatalogo.jsx:55:      const response = await fetch(url, {
/app/frontend/src/components/GestionSolicitudesCatalogo.jsx:79:      const response = await fetch(`${API_URL}/api/rrhh/solicitudes-catalogo/${solicitudId}`, {
/app/frontend/src/components/catalogos/ConfiguracionOperativaUnidad.jsx:54:      const response = await fetch(
/app/frontend/src/components/catalogos/ConfiguracionOperativaUnidad.jsx:83:      const response = await fetch(
/app/frontend/src/components/catalogos/ConfiguracionOperativaUnidad.jsx:118:      const response = await fetch(
/app/frontend/src/components/crm/KPIDashboardIA.jsx:10:      fetch('/api/crm/kpis?mes=5&anio=2026').then(res => res.json()),
/app/frontend/src/components/crm/KPIDashboardIA.jsx:11:      fetch('/api/crm/ia/salud-comercial?usuario_id=1&mes=5&anio=2026').then(res => res.json())
/app/frontend/src/components/crm/CuentasPanel.jsx:9:        fetch('/api/crm/cuentas')
/app/frontend/src/components/crm/PipelineKanban.jsx:10:    fetch('/api/crm/pipeline')
/app/frontend/src/components/crm/PipelineKanban.jsx:20:    fetch(`/api/crm/oportunidades/${oportunidadId}/etapa`, {
/app/frontend/src/components/crm/SolicitudesAltaPanel.jsx:9:        fetch('/api/crm/clientes/solicitudes')
/app/frontend/src/components/crm/ActividadesPanel.jsx:8:    fetch('/api/crm/actividades')
/app/frontend/src/components/crm/ActividadesPanel.jsx:18:    fetch(`/api/crm/actividades/${actividadId}/estatus`, {
/app/frontend/src/components/crm/OperacionesFlujoPanel.jsx:10:      fetch('/api/crm/cotizaciones?cuenta_id=1').then(res => res.json()),
/app/frontend/src/components/crm/OperacionesFlujoPanel.jsx:11:      fetch('/api/crm/implementaciones').then(res => res.json())
/app/frontend/src/components/crm/OperacionesFlujoPanel.jsx:22:    fetch('/api/crm/pedidos-venta/convertir', {
/app/frontend/src/components/admin/RolesList.jsx:54:      const response = await api.get('/roles');
/app/frontend/src/components/admin/ResyncPanel.jsx:107:      const response = await api.get('/admin/scheduler/resync/options');
/app/frontend/src/components/admin/ResyncPanel.jsx:120:      const response = await api.get('/admin/scheduler/resync/history?limit=20');
/app/frontend/src/components/admin/bitacora/useBitacoraRBACData.js:52:      const response = await fetch(`${API_URL}/api/admin/bitacora?${params.toString()}`, {
/app/frontend/src/components/finanzas/cuentas-bancarias/hooks/useSaldosBancarios.js:44:      const response = await api.get(url);
/app/frontend/src/components/finanzas/cuentas-bancarias/hooks/useSaldosBancarios.js:60:      const response = await api.get(`/v2/finanzas/cuentas-bancarias/${cuentaId}/saldo-actual`);
/app/frontend/src/components/finanzas/cuentas-bancarias/hooks/useSaldosBancarios.js:86:      const response = await api.get(url);
/app/frontend/src/components/finanzas/cuentas-bancarias/hooks/useSaldosBancarios.js:100:      const response = await api.get(`/v2/finanzas/saldos-bancarios/${saldoId}/historial`);
/app/frontend/src/components/finanzas/cuentas-bancarias/hooks/useCuentasBancarias.js:36:      const response = await api.get(url);
/app/frontend/src/components/finanzas/cuentas-bancarias/hooks/useCuentasBancarias.js:52:      const response = await api.get(`/v2/finanzas/cuentas-bancarias/${id}`);
/app/frontend/src/components/finanzas/cuentas-bancarias/hooks/useBancos.js:16:      const response = await api.get('/v2/finanzas/bancos');
/app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js:6: * Migrado de axios directo a cliente API centralizado para garantizar
/app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js:79:      const response = await api.get('/catalogo/consultas-rich', { params });
/app/frontend/src/components/catalogo-consultas/useCatalogoConsultasData.js:125:      const response = await api.get('/catalogos/sistemas/activos');
/app/frontend/src/components/QueryConfigWizard.js:139:      const response = await api.get(`/servers/${server.id}/queries`);
/app/frontend/src/components/centro-control/DestinatariosManager.jsx:29:      const res = await fetch(`${API_URL}/api/centro-control/destinatarios`, { headers });
/app/frontend/src/components/centro-control/DestinatariosManager.jsx:42:      const res = await fetch(`${API_URL}/api/centro-control/notificaciones/config`, { headers });
/app/frontend/src/components/centro-control/DestinatariosManager.jsx:63:      const res = await fetch(`${API_URL}/api/centro-control/destinatarios`, {
/app/frontend/src/components/centro-control/DestinatariosManager.jsx:85:      const res = await fetch(`${API_URL}/api/centro-control/destinatarios/${id}`, {
/app/frontend/src/components/centro-control/DestinatariosManager.jsx:103:      const res = await fetch(`${API_URL}/api/centro-control/test-whatsapp`, {
/app/frontend/src/components/centro-control/useCentroControlData.js:29:      const res = await api.get('/centro-control/estado');
/app/frontend/src/components/centro-control/useCentroControlData.js:38:      const res = await api.get('/centro-control/salud/resumen');
/app/frontend/src/components/centro-control/useCentroControlData.js:47:      const res = await api.get('/centro-control/alertas', { params: { solo_activas: true, limite: 50 } });
/app/frontend/src/components/centro-control/useCentroControlData.js:56:      const res = await api.get('/centro-control/fuentes');
/app/frontend/src/components/centro-control/useCentroControlData.js:65:      const res = await api.get('/centro-control/jobs');
/app/frontend/src/components/centro-control/useCentroControlData.js:74:      const res = await api.get('/centro-control/bitacora', { params: { limite: 50 } });
/app/frontend/src/components/centro-control/useCentroControlData.js:83:      const res = await api.get('/centro-control/metricas');
/app/frontend/src/components/centro-control/useCentroControlData.js:92:      const res = await api.get('/centro-control/historial', { params: { limite: 50 } });
/app/frontend/src/components/centro-control/useCentroControlData.js:101:      const res = await api.get('/centro-control/matriz-resolucion');
/app/frontend/src/components/compras/useAutorizacionComprasData.js:6:import axios from 'axios';
/app/frontend/src/components/compras/useAutorizacionComprasData.js:19:  const [almacenes, setAlmacenes] = useState([]);
/app/frontend/src/components/compras/useAutorizacionComprasData.js:77:      const response = await axios.get(`${API_URL}/api/compras/almacenes`, {
/app/frontend/src/components/compras/useAutorizacionComprasData.js:81:      setAlmacenes(response.data.almacenes || []);
/app/frontend/src/components/compras/useAutorizacionComprasData.js:86:      setAlmacenes([]);
/app/frontend/src/components/compras/useAutorizacionComprasData.js:108:      const response = await axios.get(`${API_URL}/api/compras/inventarios-fisicos`, {
/app/frontend/src/components/compras/useAutorizacionComprasData.js:129:      const response = await axios.get(`${API_URL}/api/compras/pedidos-vigentes`, {
/app/frontend/src/components/tesoreria/useTesoreriaCorteZData.js:6: * FIX BUG 2026-05-26: Usa fetchUnidadesNegocio centralizado en lugar de /api/servers
/app/frontend/src/components/tesoreria/useTesoreriaCorteZData.js:72:      const response = await api.get(`/finanzas/tesoreria/cortes-z?${params}`);
/app/frontend/src/components/tesoreria/useTesoreriaCorteZData.js:93:      const response = await api.get(`/finanzas/tesoreria/cuadres?${params}`);
/app/frontend/src/components/tesoreria/useTesoreriaCorteZData.js:109:      const response = await api.get(`/finanzas/tesoreria/cuadres/resumen?${params}`);
/app/frontend/src/lib/dashboardLoader.js:10:    { key: 'proveedores', promise: api.get('/portal/admin/all-suppliers') },
/app/frontend/src/lib/dashboardLoader.js:11:    { key: 'roles', promise: api.get('/api/roles') },
/app/frontend/src/lib/dashboardLoader.js:12:    { key: 'menus', promise: api.get('/api/sistema/menus/usuario') }
/app/frontend/src/lib/dashboardLoader.js:43:    const response = await api.get(endpoint, { signal: controller.signal });
/app/frontend/src/lib/dashboardLoader.js:61:      const response = await api.get(endpoint);
/app/frontend/src/hooks/useComercialUnitsWithFallback.js:63:      const res = await fetch("/api/comercial/units", { signal: controller.signal });
/app/frontend/src/utils/comercialStatusUtils.js:31: * @param {any} response - Respuesta del backend (axios response.data)
/app/frontend/src/utils/comercialStatusUtils.js:299: * @param {Error} error - Error de axios o fetch
/app/frontend/src/portal/pages/RegisterPage.jsx:74:      const response = await fetch(`${API_URL}/api/portal/auth/register`, {
/app/frontend/src/portal/pages/UploadInvoicePage.jsx:58:      const response = await fetch(`${API_URL}/api/portal/invoices/upload`, {
/app/frontend/src/portal/pages/DashboardPage.jsx:36:      const invoicesRes = await fetch(`${API_URL}/api/portal/invoices`, {
/app/frontend/src/portal/pages/DashboardPage.jsx:53:      const res = await fetch(`${API_URL}/api/portal/saldos`, {
/app/frontend/src/portal/pages/InvoicesPage.jsx:26:      const response = await fetch(url, {
/app/frontend/src/portal/pages/LoginPage.jsx:30:      const response = await fetch(`${API_URL}/api/portal/auth/login`, {
/app/frontend/src/portal/pages/AccountStatusPage.jsx:18:      const response = await fetch(`${API_URL}/api/portal/account-status`, {
/app/frontend/src/services/comprasUtils.js:130:  const current = requestIdMap.get(key) || 0;
/app/frontend/src/services/comprasUtils.js:146:  const current = requestIdMap.get(key) || 0;
/app/frontend/src/services/serversService.js:34: * @param {Array} servers - Array de servidores del endpoint /api/servers
/app/frontend/src/services/serversService.js:43: * Obtiene servidores operativos desde /api/servers
/app/frontend/src/services/exploradorService.js:149:    const response = await api.get(`/catalogos/sistemas-capacidades/normalizar/${encodeURIComponent(systemType)}`);
/app/frontend/src/services/exploradorService.js:172:    const response = await api.get(`/catalogos/sistemas-capacidades/diagnostico/${encodeURIComponent(systemType)}`);
```
