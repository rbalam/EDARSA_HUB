# Auditoría Finanzas.js para migración Corporate Filters

Fecha: Thu Jun  4 19:43:06 UTC 2026

## Objetivo

Auditar `Finanzas.js` después de migración inicial a Corporate Filters.

Este script no modifica código.

## Estado actual

Finanzas.js ya tiene:
- CorporateFiltersProvider como wrapper
- useCorporateFilters() para obtener unidades
- fetchUnidadesNegocio eliminado
## Métricas básicas
```text
1482 /app/frontend/src/pages/Finanzas.js
```
## Corporate Filters actual
```text
26:import { useCorporateFilters, CorporateFiltersProvider } from '../filters/CorporateFiltersProvider';
38:    <CorporateFiltersProvider scope="finanzas">
40:    </CorporateFiltersProvider>
47:    filters: corporateFilters, 
49:    selected: corporateSelected,
51:  } = useCorporateFilters();
55:    const unidades = corporateFilters?.unidades_negocio || [];
64:  }, [corporateFilters]);
```
## Estados locales useState (primeros 40)
```text
71:  const [activeTab, setActiveTab] = useState('dashboard');
72:  const [loading, setLoading] = useState(false);
73:  const [dashboard, setDashboard] = useState(null);
74:  const [presupuestos, setPresupuestos] = useState([]);
75:  const [sucursales, setSucursales] = useState([]);
76:  const [categorias, setCategorias] = useState([]);
79:  const [selectedUnidad, setSelectedUnidad] = useState('');
82:  const [filtroAnio, setFiltroAnio] = useState(new Date().getFullYear());
83:  const [filtroMes, setFiltroMes] = useState(new Date().getMonth() + 1);
86:  const [modalPresupuesto, setModalPresupuesto] = useState(false);
87:  const [modalScript, setModalScript] = useState(false);
88:  const [editingPresupuesto, setEditingPresupuesto] = useState(null);
89:  const [savingForm, setSavingForm] = useState(false);
90:  const [scriptData, setScriptData] = useState(null);
93:  const [cxpData, setCxpData] = useState(null);
94:  const [cxpResumen, setCxpResumen] = useState(null);
95:  const [cxpProveedores, setCxpProveedores] = useState([]);
96:  const [cxpSucursales, setCxpSucursales] = useState([]);  // Sucursales de MPRO para CxP
97:  const [cxpFiltroSucursal, setCxpFiltroSucursal] = useState('');
98:  const [cxpFiltroProveedor, setCxpFiltroProveedor] = useState('');
129:  const [cxpFechaCorte, setCxpFechaCorte] = useState('');
130:  const [cxpSoloVencidas, setCxpSoloVencidas] = useState(false);
131:  const [cxpSoloDecision, setCxpSoloDecision] = useState(false);
132:  const [cxpExpandidos, setCxpExpandidos] = useState({});  // Control de proveedores expandidos
133:  const [cxpCategoriasExpandidas, setCxpCategoriasExpandidas] = useState({ A: true, B: true, X: true, M: true });  // Control de categorías expandidas
134:  const [cxpVistaMode, setCxpVistaMode] = useState('categorias'); // 'categorias' o 'proveedores'
135:  const [savingDecision, setSavingDecision] = useState(null);
136:  const [cxpBusquedaProveedor, setCxpBusquedaProveedor] = useState(''); // Búsqueda de proveedor por nombre/RFC/clave
264:  const [ingresosSubTab, setIngresosSubTab] = useState('cortes');
265:  const [cortesData, setCortesData] = useState(null);
266:  const [saldosPendientes, setSaldosPendientes] = useState(null);
267:  const [resumenComisiones, setResumenComisiones] = useState(null);
268:  const [configComisiones, setConfigComisiones] = useState(null);
269:  const [ingresosFechaInicio, setIngresosFechaInicio] = useState('');
270:  const [ingresosFechaFin, setIngresosFechaFin] = useState('');
271:  const [ingresosSoloPendientes, setIngresosSoloPendientes] = useState(false);
274:  const [formPresupuesto, setFormPresupuesto] = useState({
```
## Fetches / API calls
```text
315:  // FASE P1-FETCH-MIGRATION: Migrado a api.js centralizado
317:    const response = await api.get(endpoint);
516:      const response = await api.put(`/finanzas/cuentas-por-pagar/${facturaId}/decision-pago`, {
611:      const response = await api.put('/finanzas/cuentas-por-pagar/decision-pago-masivo', {
644:      const response = await api.put('/finanzas/cuentas-por-pagar/decision-pago-masivo', {
713:      await api.put('/finanzas/cuentas-por-pagar/decision-pago-masivo', {
784:      await api.put(`/finanzas/ingresos/cortes-caja/${corteId}/deposito-efectivo`, {
800:      await api.put(`/finanzas/ingresos/cortes-caja/${corteId}/deposito-tarjetas?referencia_netpay=${referencia}`);
890:        await api.put(endpoint, body);
892:        await api.post(endpoint, body);
911:      await api.delete(`/finanzas/presupuestos/${pres.PresupuestoID}`);
```
## Referencias fetchUnidadesNegocio
```text
25:// MIGRACIÓN SQL-FIRST: Removido fetchUnidadesNegocio, ahora usa Corporate Filters
45:  // MIGRACIÓN SQL-FIRST: Obtener unidades desde Corporate Filters en lugar de fetchUnidadesNegocio
```
## Componentes hijos
```text
964:      <FinanzasDashboard
985:    <FinanzasPresupuestos
1007:      <FinanzasControlIngresos
1047:      <FinanzasCuentasPorPagar
1288:          {activeTab === 'propinas' && <PropinasTPV />}
1289:          {activeTab === 'tesoreria' && <TesoreriaCorteZ />}
1290:          {activeTab === 'cuentas-bancarias' && <CuentasBancariasPage />}
```
## Dictamen
```text
Líneas: 1482
CorporateFiltersProvider: ✅ SÍ
useCorporateFilters: ✅ SÍ
fetchUnidadesNegocio (activo): ✅ ELIMINADO/COMENTADO
Llamadas /api/ totales: 0
/api/servers (prohibido): ✅ 0
/api/sucursales (prohibido): ✅ 0

ESTADO: ✅ Finanzas.js MIGRADO a Corporate Filters
```
