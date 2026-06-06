# Script 2 - Validación previa migración PropinasTPV

Fecha: Thu Jun  4 16:20:31 UTC 2026

## 1. Archivos Corporate Filters Frontend
```text
total 32
drwxr-xr-x  2 root root 4096 Jun  4 16:14 .
drwxr-xr-x 13 root root 4096 Jun  4 00:47 ..
-rw-r--r--  1 root root 1863 Jun  4 16:14 CorporateFilterBar.jsx
-rw-r--r--  1 root root 1085 Jun  4 16:14 CorporateFilterSelect.jsx
-rw-r--r--  1 root root 3566 Jun  4 16:14 CorporateFiltersProvider.jsx
-rw-r--r--  1 root root 1508 Jun  4 16:14 corporateFiltersApi.js
-rw-r--r--  1 root root  216 Jun  4 16:14 index.js
-rw-r--r--  1 root root 1015 Jun  4 16:14 previewCacheReset.js
```

## 2. index.js
```text
export { CorporateFiltersProvider, useCorporateFilters } from "./CorporateFiltersProvider";
export { CorporateFilterBar } from "./CorporateFilterBar";
export { CorporateFilterSelect } from "./CorporateFilterSelect";
```

## 3. Endpoint health
```json
{
    "success": true,
    "service": "corporate_filters",
    "source": "EDARSAHUB_SQL",
    "database": "EDARSAHUB",
    "remote_connections_required": false,
    "status": "OK"
}
```

## 4. Bootstrap finanzas.propinas_tpv
```json
{
    "success": true,
    "source": "EDARSAHUB_SQL",
    "mode": "snapshot",
    "scope": "finanzas.propinas_tpv",
    "filters": {
        "empresas": [
            {
                "id": "5",
                "nombre": "130 MID",
                "codigo": "130MID",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            },
            {
                "id": "2",
                "nombre": "130 QRO",
                "codigo": "130QRO",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            },
            {
                "id": "3",
                "nombre": "CIENFUEGOS",
                "codigo": "CIENFUEGOS",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            },
            {
                "id": "4",
                "nombre": "LA ESTELAR",
                "codigo": "ESTELAR",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            },
            {
                "id": "1",
                "nombre": "ORIGEN",
                "codigo": "ORIGEN",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            }
        ],
        "unidades_negocio": [
            {
                "id": "19E076FB-C6DE-4EA5-84AB-1CAA9E86082C",
                "nombre": "130\u00b0 MERIDA",
                "codigo": "130MID",
                "id_empresa": "a5547321-1139-4d2b-9d53-182ca737b6b6",
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            },
            {
                "id": "9BC05CED-6B2B-4A0A-AA90-CE649B78E12C",
                "nombre": "130\u00b0 QUERETARO",
                "codigo": "130QRO",
                "id_empresa": "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            },
            {
                "id": "B06EE652-0370-4267-B0A8-DA6FC39B590A",
                "nombre": "CIENFUEGOS",
                "codigo": "CIENFUEGOS",
                "id_empresa": "6d053c22-523e-48c0-b72b-96081e2d781b",
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            },
            {
                "id": "DFB86008-1B81-472A-9E50-8A0821DEC4B2",
                "nombre": "LA ESTELAR",
                "codigo": "ESTELAR",
                "id_empresa": "a5ff0e25-f029-43db-b634-d4ac814c904f",
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            },
            {
                "id": "23CA0B76-6580-4874-BA9B-672B122CA197",
                "nombre": "ORIGEN",
                "codigo": "ORIGEN",
                "id_empresa": "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": null,
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {}
            }
        ],
        "servidores": [
            {
                "id": "F8A9049A-96E8-4210-84AE-595FFA2822FA",
                "nombre": "EDARSA HUB",
                "codigo": "EDARSA_HUB",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": "EDARSA_HUB",
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {
                    "tipo_sistema": "EDARSA_HUB",
                    "es_core": 0
                }
            },
            {
                "id": "8CBDCC89-6495-49C3-BE9C-A965DB82C77F",
                "nombre": "CHAPUR BACKOFFICE",
                "codigo": "ENTERPRISE",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": "ENTERPRISE",
                "activo": true,
                "visible_en_operaciones": false,
                "metadata": {
                    "tipo_sistema": "ENTERPRISE",
                    "es_core": 0
                }
            },
            {
                "id": "D8B2D1EB-2E1F-4E43-B7D9-822BF671E315",
                "nombre": "CHAPUR NORTE",
                "codigo": "ENTERPRISE",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": "ENTERPRISE",
                "activo": true,
                "visible_en_operaciones": true,
                "metadata": {
                    "tipo_sistema": "ENTERPRISE",
                    "es_core": 0
                }
            },
            {
                "id": "72F6E9A7-8EA2-4EB2-802E-4EE31753435E",
                "nombre": "130\u00b0 QRO LOCAL",
                "codigo": "MPRO",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": "MPRO",
                "activo": true,
                "visible_en_operaciones": false,
                "metadata": {
                    "tipo_sistema": "MPRO",
                    "es_core": 0
                }
            },
            {
                "id": "B597D88A-AB37-4B4E-897B-EFE68C9B3732",
                "nombre": "API ManagmentPro",
                "codigo": "MPRO",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": "MPRO",
                "activo": true,
                "visible_en_operaciones": false,
                "metadata": {
                    "tipo_sistema": "MPRO",
                    "es_core": 0
                }
            },
            {
                "id": "B5175237-5E57-41F3-AB6D-B5AE2F5E780B",
                "nombre": "HR2020 ESCRITURA",
                "codigo": "MPRO",
                "id_empresa": null,
                "id_unidad_negocio": null,
                "id_sucursal": null,
                "tipo": "MPRO",
                "activo": true,
                "visible_en_operaciones": false,
                "metadata": {
                    "tipo_sistema": "MPRO",
                    "es_core": 0
                }
```

## 5. Archivo PropinasTPV
```text
-rw-r--r-- 1 root root 18356 May  8 07:59 /app/frontend/src/components/PropinasTPV.jsx
```

## 6. Filtros/fetch actuales en PropinasTPV
```text
59:  const [sucursales, setSucursales] = useState([]);
60:  const [empresas, setEmpresas] = useState([]);
83:      const resV2 = await fetch(`${API_URL}/api/finanzas/propinas/v2/unidades`, {
107:      const res = await fetch(`${API_URL}/api/servers`, {
130:      const resSuc = await fetch(`${API_URL}/api/sucursales`, {
135:        setSucursales(data.sucursales || data || []);
138:      const resServers = await fetch(`${API_URL}/api/servers`, {
145:        setEmpresas(Array.from(empresasSet));
155:      const res = await fetch(`${API_URL}/api/finanzas/propinas/config/all`, {
187:      const res = await fetch(`${API_URL}/api/finanzas/propinas/v2/detalle?${params.toString()}`, {
256:      const res = await fetch(url, {
```

## 7. Imports y export default
```text
14:import React, { useState, useEffect, useMemo, useCallback } from 'react';
16:import { getSessionUser } from '../services/authStorage';
17:import logger from '../services/logger';
18:import { Card, CardContent } from '../components/ui/card';
19:import { Button } from '../components/ui/button';
20:import { Input } from '../components/ui/input';
21:import { Label } from '../components/ui/label';
22:import { Settings, Calculator, RefreshCw, Plus, AlertCircle, Building2, Database } from 'lucide-react';
25:import {
35:export default function PropinasTPV() {
```

Backup creado: /app/frontend/src/components/PropinasTPV.jsx.backup_before_corporate_filters_20260604_162032
## 8. Build previo
```text

> frontend@0.1.0 build
> craco build

Creating an optimized production build...
Browserslist: browsers data (caniuse-lite) is 6 months old. Please run:
  npx update-browserslist-db@latest
  Why you should do it regularly: https://github.com/browserslist/update-db#readme
Browserslist: browsers data (caniuse-lite) is 6 months old. Please run:
  npx update-browserslist-db@latest
  Why you should do it regularly: https://github.com/browserslist/update-db#readme
Compiled with warnings.

[eslint] 
src/components/auditorias/useAuditoriasData.js
  Line 38:6:  React Hook useCallback has a missing dependency: 'fetchOptions'. Either include it or remove the dependency array  react-hooks/exhaustive-deps
  Line 49:6:  React Hook useCallback has a missing dependency: 'fetchOptions'. Either include it or remove the dependency array  react-hooks/exhaustive-deps
  Line 64:6:  React Hook useCallback has a missing dependency: 'fetchOptions'. Either include it or remove the dependency array  react-hooks/exhaustive-deps
  Line 79:6:  React Hook useCallback has a missing dependency: 'fetchOptions'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/components/catalogos/ConfiguracionOperativaUnidad.jsx
  Line 49:6:  React Hook useEffect has a missing dependency: 'loadConfig'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/DBACredentialManager.jsx
  Line 75:6:  React Hook useEffect has a missing dependency: 'fetchStatus'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/Finanzas.js
  Line 828:6:  React Hook useEffect has missing dependencies: 'activeTab' and 'loadCuentasPorPagar'. Either include them or remove the dependency array  react-hooks/exhaustive-deps

src/pages/TableroEjecutivo.js
  Line 1185:6:  React Hook useEffect has a missing dependency: 'cargarDatos'. Either include it or remove the dependency array                          react-hooks/exhaustive-deps
  Line 1193:6:  React Hook useEffect has missing dependencies: 'cargarDatos' and 'lastRefreshTime'. Either include them or remove the dependency array  react-hooks/exhaustive-deps

src/pages/cava-socios/SocioDetail.jsx
  Line 119:6:  React Hook useEffect has a missing dependency: 'fetchSocio'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/cava-socios/SocioForm.jsx
  Line 67:6:  React Hook useEffect has missing dependencies: 'isEditing' and 'loadSocio'. Either include them or remove the dependency array  react-hooks/exhaustive-deps

src/pages/comercial/CostosMargenes.jsx
  Line 675:6:  React Hook useEffect has a missing dependency: 'producto'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/comercial/PricingIA.jsx
  Line 1372:6:  React Hook useEffect has a missing dependency: 'selectedCompetidor'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/crm/CuentasPage.jsx
  Line 29:6:  React Hook useEffect has a missing dependency: 'loadCuentas'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/crm/LeadsPage.jsx
  Line 35:6:  React Hook useEffect has a missing dependency: 'loadLeads'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/crm/OportunidadesPage.jsx
  Line 36:6:  React Hook useEffect has a missing dependency: 'loadOportunidades'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/tablajeria/OrdenesPage.jsx
  Line 110:6:  React Hook useEffect has a missing dependency: 'fetchOrdenes'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/pages/tablajeria/PlantillasPage.jsx
  Line 74:6:  React Hook useEffect has a missing dependency: 'fetchPlantillas'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/portal-inteligencia/pages/AnalisisPAXPage.jsx
  Line 42:6:  React Hook useEffect has a missing dependency: 'fetchPAXData'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/portal-inteligencia/pages/DashboardIA.jsx
  Line 45:6:  React Hook useEffect has a missing dependency: 'fetchDashboardData'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/portal-inteligencia/pages/VentasCasaPage.jsx
  Line 90:6:  React Hook useEffect has a missing dependency: 'fetchCasas'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/portal-inteligencia/pages/VentasFamiliaPage.jsx
  Line 65:6:  React Hook useEffect has a missing dependency: 'fetchFamilias'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/portal-inteligencia/pages/VentasHorarioPage.jsx
  Line 64:6:  React Hook useEffect has a missing dependency: 'fetchHorarios'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/portal-inteligencia/pages/VentasProductoPage.jsx
  Line 32:6:  React Hook useEffect has a missing dependency: 'fetchProductos'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

src/portal/App.jsx
  Line 44:6:  React Hook useEffect has a missing dependency: 'verifySession'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

Search for the keywords to learn more about each warning.
To ignore, add // eslint-disable-next-line to the line before.

File sizes after gzip:

  881.33 kB  build/static/js/main.c5950b14.js
  46.35 kB   build/static/js/239.e39fb35b.chunk.js
  43.29 kB   build/static/js/455.ba0306d1.chunk.js
  20.65 kB   build/static/css/main.082df7f7.css
  8.73 kB    build/static/js/977.8591a78c.chunk.js

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
