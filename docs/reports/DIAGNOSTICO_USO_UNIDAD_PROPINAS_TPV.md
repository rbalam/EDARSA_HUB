# Diagnóstico uso real de Unidad de Negocio en PropinasTPV

## Objetivo

Validar si PropinasTPV ya usa `corporateSelected.unidades_negocio` para consultar KPIs y tabla.

## Problema observado

La barra de Corporate Filters existe, pero los KPI pueden quedar en $0.00 / ERROR si la búsqueda sigue usando estado local antiguo o parámetros no alineados.

## Variables de unidad
```text
41:  const { filters: corporateFilters, status: corporateStatus } = useCorporateFilters();
62:    unidad_negocio_id: '' // SUBFASE 3.5: Cambiado de server_id a unidad_negocio_id
66:  const sucursales = corporateFilters?.sucursales || [];
67:  const empresas = corporateFilters?.empresas || [];
68:  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
69:  const [loadingUnidades, setLoadingUnidades] = useState(false);
76:    cargarUnidadesNegocio();
85:  // SUBFASE 3.5: Cargar unidades desde endpoint EDARSAHUB v2
86:  const cargarUnidadesNegocio = async () => {
87:    setLoadingUnidades(true);
90:      const resV2 = await fetch(`${API_URL}/api/finanzas/propinas/v2/unidades`, {
96:        // Formatear unidades desde EDARSAHUB
97:        const unidades = (dataV2.unidades || []).map(u => ({
98:          id: u.unidad_negocio_id,
99:          nombre: u.unidad_negocio_nombre,
104:        setUnidadesNegocio(unidades);
106:        // Si solo hay 1 unidad, seleccionarla automáticamente
107:        if (unidades.length === 1) {
108:          setFiltros(prev => ({ ...prev, unidad_negocio_id: unidades[0].id }));
113:      // Fallback: usar unidades de Corporate Filters
114:      const unidadesCF = corporateFilters?.unidades_negocio || [];
115:      if (unidadesCF.length > 0) {
116:        const unidades = unidadesCF.map(u => ({
123:        setUnidadesNegocio(unidades);
124:        if (unidades.length === 1) {
125:          setFiltros(prev => ({ ...prev, unidad_negocio_id: unidades[0].id }));
129:      logger.error('Error cargando unidades:', error);
131:      setLoadingUnidades(false);
162:      // Usar unidad_negocio_id para filtro (o TODAS si vacío)
163:      if (filtros.unidad_negocio_id) {
164:        params.append('unidad_negocio_id', filtros.unidad_negocio_id);
166:        params.append('unidad_negocio_id', 'TODAS');
180:          server_name: p.unidad_negocio_nombre,
181:          sucursal_nombre: p.sucursal_nombre || p.unidad_negocio_nombre,
202:          unidad_negocio_id: p.unidad_negocio_id,
342:                {/* Selector de Unidad de Negocio - SUBFASE 3.5: Usa unidad_negocio_id */}
344:                  <Label className="text-xs text-zinc-500">Unidad de Negocio</Label>
347:                    {unidadesNegocio.length === 1 ? (
349:                        {unidadesNegocio[0].nombre}
353:                        value={filtros.unidad_negocio_id}
354:                        onChange={(e) => setFiltros({...filtros, unidad_negocio_id: e.target.value})}
356:                        disabled={loadingUnidades}
357:                        data-testid="filtro-unidad"
359:                        <option value="">{loadingUnidades ? "Cargando..." : "Todas las unidades"}</option>
360:                        {unidadesNegocio.map(u => (
483:            key: "unidades_negocio",
484:            label: "Unidad de Negocio",
485:            placeholder: "Seleccione unidad",
```
## Funciones de carga/búsqueda
```text
75:    // cargarDatosAuxiliares eliminado - ahora usa Corporate Filters
76:    cargarUnidadesNegocio();
80:    if (activeTab === 'configuracion') cargarConfigs();
81:    else if (activeTab === 'cuadre') cargarPropinas();
86:  const cargarUnidadesNegocio = async () => {
90:      const resV2 = await fetch(`${API_URL}/api/finanzas/propinas/v2/unidades`, {
135:  const cargarConfigs = useCallback(async () => {
138:      const res = await fetch(`${API_URL}/api/finanzas/propinas/config/all`, {
153:  const cargarPropinas = useCallback(async () => {
158:      const params = new URLSearchParams();
159:      params.append('fecha_inicio', filtros.fecha_inicio);
160:      params.append('fecha_fin', filtros.fecha_fin);
164:        params.append('unidad_negocio_id', filtros.unidad_negocio_id);
166:        params.append('unidad_negocio_id', 'TODAS');
170:      const res = await fetch(`${API_URL}/api/finanzas/propinas/v2/detalle?${params.toString()}`, {
178:        const propinasTransformadas = (data.detalle || []).map(p => ({
236:        ? `${API_URL}/api/finanzas/propinas/config`
237:        : `${API_URL}/api/finanzas/propinas/config/${configData.id}`;
239:      const res = await fetch(url, {
247:        await cargarConfigs();
406:                <Button onClick={cargarPropinas} variant="outline" data-testid="btn-buscar-propinas">
408:                  Buscar
447:            onRefresh={cargarConfigs}
```
## Endpoints y parámetros
```text
56:  const [totalesServer, setTotalesServer] = useState(null); // Totales del servidor
59:    fecha_inicio: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
60:    fecha_fin: new Date().toISOString().split('T')[0],
61:    estado: '',
62:    unidad_negocio_id: '' // SUBFASE 3.5: Cambiado de server_id a unidad_negocio_id
66:  const sucursales = corporateFilters?.sucursales || [];
67:  const empresas = corporateFilters?.empresas || [];
68:  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
85:  // SUBFASE 3.5: Cargar unidades desde endpoint EDARSAHUB v2
90:      const resV2 = await fetch(`${API_URL}/api/finanzas/propinas/v2/unidades`, {
96:        // Formatear unidades desde EDARSAHUB
97:        const unidades = (dataV2.unidades || []).map(u => ({
98:          id: u.unidad_negocio_id,
99:          nombre: u.unidad_negocio_nombre,
104:        setUnidadesNegocio(unidades);
106:        // Si solo hay 1 unidad, seleccionarla automáticamente
107:        if (unidades.length === 1) {
108:          setFiltros(prev => ({ ...prev, unidad_negocio_id: unidades[0].id }));
113:      // Fallback: usar unidades de Corporate Filters
114:      const unidadesCF = corporateFilters?.unidades_negocio || [];
115:      if (unidadesCF.length > 0) {
116:        const unidades = unidadesCF.map(u => ({
123:        setUnidadesNegocio(unidades);
124:        if (unidades.length === 1) {
125:          setFiltros(prev => ({ ...prev, unidad_negocio_id: unidades[0].id }));
129:      logger.error('Error cargando unidades:', error);
138:      const res = await fetch(`${API_URL}/api/finanzas/propinas/config/all`, {
159:      params.append('fecha_inicio', filtros.fecha_inicio);
160:      params.append('fecha_fin', filtros.fecha_fin);
162:      // Usar unidad_negocio_id para filtro (o TODAS si vacío)
163:      if (filtros.unidad_negocio_id) {
164:        params.append('unidad_negocio_id', filtros.unidad_negocio_id);
166:        params.append('unidad_negocio_id', 'TODAS');
170:      const res = await fetch(`${API_URL}/api/finanzas/propinas/v2/detalle?${params.toString()}`, {
180:          server_name: p.unidad_negocio_nombre,
181:          sucursal_nombre: p.sucursal_nombre || p.unidad_negocio_nombre,
195:            estado: 'PENDIENTE' // Estado por defecto
202:          unidad_negocio_id: p.unidad_negocio_id,
236:        ? `${API_URL}/api/finanzas/propinas/config`
237:        : `${API_URL}/api/finanzas/propinas/config/${configData.id}`;
272:  // SUBFASE 3.5: Usar totales del servidor si están disponibles
274:    // Si tenemos totales del servidor EDARSAHUB, usarlos
342:                {/* Selector de Unidad de Negocio - SUBFASE 3.5: Usa unidad_negocio_id */}
347:                    {unidadesNegocio.length === 1 ? (
349:                        {unidadesNegocio[0].nombre}
353:                        value={filtros.unidad_negocio_id}
354:                        onChange={(e) => setFiltros({...filtros, unidad_negocio_id: e.target.value})}
357:                        data-testid="filtro-unidad"
359:                        <option value="">{loadingUnidades ? "Cargando..." : "Todas las unidades"}</option>
360:                        {unidadesNegocio.map(u => (
373:                    value={filtros.fecha_inicio}
374:                    onChange={(e) => setFiltros({...filtros, fecha_inicio: e.target.value})}
383:                    value={filtros.fecha_fin}
384:                    onChange={(e) => setFiltros({...filtros, fecha_fin: e.target.value})}
392:                    value={filtros.estado}
393:                    onChange={(e) => setFiltros({...filtros, estado: e.target.value})}
395:                    data-testid="filtro-estado"
397:                    title="Filtro de estado pendiente de implementar"
435:              empresas={empresas}
436:              sucursales={sucursales}
463:                <li><strong>Sucursal</strong>: Si existe config para la sucursal específica, se usa.</li>
464:                <li><strong>Empresa</strong>: Si no hay config de sucursal, se busca por empresa.</li>
483:            key: "unidades_negocio",
485:            placeholder: "Seleccione unidad",
```
## Fetch prohibidos
```text
```
## Build
```text
  Line 44:6:  React Hook useEffect has a missing dependency: 'verifySession'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

Search for the keywords to learn more about each warning.
To ignore, add // eslint-disable-next-line to the line before.

File sizes after gzip:

  883.28 kB (-4 B)  build/static/js/main.06e46126.js
  46.35 kB          build/static/js/239.e39fb35b.chunk.js
  43.29 kB          build/static/js/455.ba0306d1.chunk.js
  20.67 kB          build/static/css/main.2773ac81.css
  8.73 kB           build/static/js/977.8591a78c.chunk.js

The bundle size is significantly larger than recommended.
Consider reducing it with code splitting: https://goo.gl/9VhYWB
You can also analyze the project dependencies: https://goo.gl/LeUzfb

The project was built assuming it is hosted at /.
You can control this with the homepage field in your package.json.

The build folder is ready to be deployed.
You may serve it with a static server:

  yarn global add serve
  serve -s build

Find out more about deployment here:

  https://cra.link/deployment

```
