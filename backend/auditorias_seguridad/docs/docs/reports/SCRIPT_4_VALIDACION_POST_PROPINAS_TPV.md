# Script 4 - Validación post migración PropinasTPV

Fecha: Thu Jun  4 16:31:19 UTC 2026

## 1. Uso de Corporate Filters
```text
25:import { CorporateFiltersProvider, useCorporateFilters } from '../filters';
39:function PropinasTPVContent() {
41:  const { filters: corporateFilters, status: corporateStatus } = useCorporateFilters();
478:    <CorporateFiltersProvider scope="finanzas.propinas_tpv">
479:      <PropinasTPVContent />
480:    </CorporateFiltersProvider>
```

## 2. Fetch directos prohibidos
```text
```

## 3. Endpoints propios de propinas conservados
```text
90:      const resV2 = await fetch(`${API_URL}/api/finanzas/propinas/v2/unidades`, {
138:      const res = await fetch(`${API_URL}/api/finanzas/propinas/config/all`, {
170:      const res = await fetch(`${API_URL}/api/finanzas/propinas/v2/detalle?${params.toString()}`, {
236:        ? `${API_URL}/api/finanzas/propinas/config`
237:        : `${API_URL}/api/finanzas/propinas/config/${configData.id}`;
```

## 4. Bootstrap Corporate Filters
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
```

## 5. Build frontend
```text
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

## Checklist visual en navegador

Validar manualmente:

1. Abrir módulo Finanzas / Propinas TPV.
2. Confirmar que el tablero carga sin errores.
3. Confirmar que selector de Unidad de Negocio funciona.
4. Confirmar que no aparece error en consola.
5. Confirmar que no se hacen requests a:
    - /api/servers
    - /api/sucursales

## Resultado técnico

PropinasTPV migrado a Corporate Filters.
