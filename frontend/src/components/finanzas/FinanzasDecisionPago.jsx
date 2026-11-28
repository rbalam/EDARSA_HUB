import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  CreditCard,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import api from '../../lib/api';

export default function FinanzasDecisionPago({
  unidadesNegocio,
  selectedUnidad,
  loadingUnidades,
  onUnidadChange,
  onAbrirCxp,
  canApplyPeriodOverride = false,
  formatCurrency
}) {
  const [decisionDashboard, setDecisionDashboard] = useState(null);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [decisionError, setDecisionError] = useState('');
  const [drilldown, setDrilldown] = useState(null);
  const [drilldownLoading, setDrilldownLoading] = useState(false);
  const [selectedProveedor, setSelectedProveedor] = useState(null);
  const [analysisPeriod, setAnalysisPeriod] = useState('previous_month');
  const [effectivePeriodOverride, setEffectivePeriodOverride] = useState(false);
  const [refreshNonce, setRefreshNonce] = useState(0);

  useEffect(() => {
    let mounted = true;

    const loadDecisionDashboard = async () => {
      setDecisionLoading(true);
      setDecisionError('');

      try {
        const params = new URLSearchParams();

        if (selectedUnidad) {
          params.append(
            'unidad_negocio_pk',
            selectedUnidad
          );
        }

        if (
          effectivePeriodOverride &&
          analysisPeriod !== 'previous_month'
        ) {
          const range = resolveAnalysisPeriod();

          if (range?.inicio && range?.fin) {
            params.append(
              'fecha_referencia_inicio',
              range.inicio
            );
            params.append(
              'fecha_referencia_fin',
              range.fin
            );
            params.append(
              'aplicar_periodo_como_limite',
              'true'
            );
          }
        }

        const response = await api.get(
          `/finanzas/cuentas-por-pagar/decision-dashboard?${params.toString()}`
        );

        if (mounted) {
          setDecisionDashboard(
            response.data || null
          );
        }
      } catch (error) {
        if (mounted) {
          setDecisionDashboard(null);
          setDecisionError(
            error?.response?.data?.detail ||
            error?.message ||
            'No se pudo cargar el límite de pago.'
          );
        }
      } finally {
        if (mounted) {
          setDecisionLoading(false);
        }
      }
    };

    loadDecisionDashboard();

    return () => {
      mounted = false;
    };
  }, [
    selectedUnidad,
    effectivePeriodOverride,
    analysisPeriod,
    refreshNonce
  ]);

  const resolveAnalysisPeriod = () => {
    if (!periodoReferencia?.fecha_fin) {
      return null;
    }

    const effectiveEnd = new Date(
      `${periodoReferencia.fecha_fin}T00:00:00`
    );

    if (analysisPeriod === 'previous_month') {
      return {
        inicio: periodoReferencia.fecha_inicio,
        fin: periodoReferencia.fecha_fin
      };
    }

    const monthsMap = {
      last_3_months: 3,
      last_6_months: 6,
      last_12_months: 12
    };

    const months = monthsMap[analysisPeriod];

    if (!months) {
      return {
        inicio: periodoReferencia.fecha_inicio,
        fin: periodoReferencia.fecha_fin
      };
    }

    const start = new Date(
      effectiveEnd.getFullYear(),
      effectiveEnd.getMonth() - months + 1,
      1
    );

    const yyyy = start.getFullYear();
    const mm = String(
      start.getMonth() + 1
    ).padStart(2, '0');

    return {
      inicio: `${yyyy}-${mm}-01`,
      fin: periodoReferencia.fecha_fin
    };
  };

  const loadDrilldown = async (proveedorId = null) => {
    setDrilldownLoading(true);

    try {
      const params = new URLSearchParams();

      if (selectedUnidad) {
        params.append(
          'unidad_negocio_pk',
          selectedUnidad
        );
      }

      if (proveedorId) {
        params.append(
          'proveedor_id',
          proveedorId
        );
      }

      const analysisRange =
        resolveAnalysisPeriod();

      if (analysisRange?.inicio) {
        params.append(
          'fecha_referencia_inicio',
          analysisRange.inicio
        );
      }

      if (analysisRange?.fin) {
        params.append(
          'fecha_referencia_fin',
          analysisRange.fin
        );
      }

      const response = await api.get(
        `/finanzas/cuentas-por-pagar/decision-dashboard/drilldown?${params.toString()}`
      );

      setDrilldown(response.data || null);
      setSelectedProveedor(
        proveedorId || null
      );
    } catch (error) {
      setDecisionError(
        error?.response?.data?.detail ||
        error?.message ||
        'No se pudo cargar el drilldown.'
      );
    } finally {
      setDrilldownLoading(false);
    }
  };

  const periodoReferencia =
    decisionDashboard?.periodo_referencia || null;

  const decisionResumen =
    decisionDashboard?.resumen || {};

  const renderDashboardAmount = (field) => {
    if (decisionLoading) return 'Cargando...';
    if (!decisionDashboard) return 'No disponible';
    const value = decisionResumen?.[field];
    return value == null ? 'No disponible' : formatCurrency(value);
  };

  return (
    <div
      className="space-y-6"
      data-testid="finanzas-decision-pago"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-zinc-900">
            Tablero de Decisión de Pago
          </h2>
          <p className="mt-1 text-sm text-zinc-500">
            Capacidad de pago y obligaciones seleccionadas.
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label
              htmlFor="decision-pago-unidad"
              className="mb-1 block text-xs font-medium text-zinc-600"
            >
              Unidad de negocio
            </label>

            <select
              id="decision-pago-unidad"
              value={selectedUnidad || ''}
              onChange={(event) => onUnidadChange(event.target.value)}
              disabled={loadingUnidades}
              className="h-10 min-w-56 rounded-md border border-zinc-300 bg-white px-3 text-sm"
            >
              <option value="">
                Todas las unidades permitidas
              </option>

              {(unidadesNegocio || []).map((unidad) => (
                <option
                  key={unidad.id}
                  value={unidad.id}
                >
                  {unidad.nombre || unidad.codigo || unidad.id}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="decision-pago-analysis-period"
              className="mb-1 block text-xs font-medium text-zinc-600"
            >
              Período de análisis
            </label>

            <select
              id="decision-pago-analysis-period"
              value={analysisPeriod}
              onChange={(event) => {
                setAnalysisPeriod(
                  event.target.value
                );
                setEffectivePeriodOverride(false);
                setDrilldown(null);
                setSelectedProveedor(null);
              }}
              className="h-10 min-w-48 rounded-md border border-zinc-300 bg-white px-3 text-sm"
            >
              <option value="previous_month">
                Mes anterior
              </option>
              <option value="last_3_months">
                Últimos 3 meses
              </option>
              <option value="last_6_months">
                Últimos 6 meses
              </option>
              <option value="last_12_months">
                Últimos 12 meses
              </option>
            </select>

            <div className="mt-1 max-w-52 text-[11px] text-zinc-400">
              {effectivePeriodOverride
                ? 'Este período está aplicado como límite efectivo.'
                : 'Solo análisis. El límite efectivo sigue usando mes anterior.'}
            </div>

            {analysisPeriod !== 'previous_month' && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="mt-2"
                disabled={!canApplyPeriodOverride}
                onClick={() =>
                  setEffectivePeriodOverride(
                    (current) => !current
                  )
                }
              >
                {effectivePeriodOverride
                  ? 'Volver al límite por defecto'
                  : canApplyPeriodOverride
                    ? 'Aplicar como límite efectivo'
                    : 'Requiere autorización'}
              </Button>
            )}
          </div>

          <Button
            variant="outline"
            onClick={() => setRefreshNonce((value) => value + 1)}
            disabled={decisionLoading}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${
                decisionLoading ? 'animate-spin' : ''
              }`}
            />
            Actualizar
          </Button>

          <Button onClick={onAbrirCxp}>
            <CreditCard className="mr-2 h-4 w-4" />
            Ver Cuentas por Pagar
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardContent className="p-5">
            <div className="text-sm text-zinc-500">
              Saldo pendiente
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {renderDashboardAmount('saldo_cxp')}
            </div>
            <div className="mt-1 text-xs text-zinc-500">
              Saldo canónico de CxP
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="text-sm text-zinc-500">
              Seleccionado para pago
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {renderDashboardAmount('comprometido')}
            </div>
            <div className="mt-1 text-xs text-zinc-500">
              Comprometido canónico
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="text-sm text-zinc-500">
              Autorizado
            </div>
            <div className="mt-2 text-2xl font-semibold">
              {renderDashboardAmount('autorizado')}
            </div>
            <div className="mt-1 text-xs text-zinc-500">
              Autorizado canónico
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <BarChart3 className="h-4 w-4" />
              Límite de pago
            </div>

            <div className="mt-2 text-2xl font-semibold">
              {decisionLoading
                ? 'Cargando...'
                : decisionDashboard
                  ? formatCurrency(
                      decisionResumen.limite_pago
                    )
                  : 'No disponible'}
            </div>

            <div className="mt-1 text-xs text-zinc-500">
              {periodoReferencia
                ? `Referencia ${periodoReferencia.fecha_inicio} a ${periodoReferencia.fecha_fin}`
                : 'Promedio histórico canónico'}
            </div>

            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              disabled={
                !decisionDashboard ||
                drilldownLoading
              }
              onClick={() => loadDrilldown()}
            >
              {drilldownLoading
                ? 'Cargando...'
                : 'Ver cómo se construye'}
            </Button>
          </CardContent>
        </Card>
      </div>

      {decisionError && (
        <Card>
          <CardContent className="p-4">
            <div className="flex gap-2 text-sm text-amber-700">
              <AlertCircle className="h-4 w-4 mt-0.5" />
              <span>{decisionError}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {decisionDashboard && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="p-5">
              <div className="text-sm text-zinc-500">
                Comprometido contra límite
              </div>
              <div className="mt-2 text-xl font-semibold">
                {formatCurrency(
                  decisionResumen.comprometido
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="text-sm text-zinc-500">
                Disponible
              </div>
              <div className="mt-2 text-xl font-semibold">
                {formatCurrency(
                  decisionResumen.disponible
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="text-sm text-zinc-500">
                Utilización del límite
              </div>
              <div className="mt-2 text-xl font-semibold">
                {decisionResumen.porcentaje_utilizado == null
                  ? 'N/D'
                  : `${decisionResumen.porcentaje_utilizado}%`}
              </div>

              {decisionResumen.excede_limite && (
                <div className="mt-2 text-xs font-medium text-amber-700">
                  El monto comprometido supera el límite calculado.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {drilldown && (
        <div className="space-y-4">
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-zinc-900">
                    Construcción del promedio de compras
                  </h3>
                  <p className="mt-1 text-xs text-zinc-500">
                    Drilldown hasta recepción individual.
                  </p>
                </div>

                {selectedProveedor && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadDrilldown()}
                  >
                    Todos los proveedores
                  </Button>
                )}
              </div>

              {!selectedProveedor &&
                (drilldown.proveedores || []).length > 0 && (
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="py-2 pr-4">
                          Proveedor
                        </th>
                        <th className="py-2 pr-4 text-right">
                          Entradas
                        </th>
                        <th className="py-2 pr-4 text-right">
                          Compras
                        </th>
                        <th className="py-2 text-right">
                          Promedio entrada
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {drilldown.proveedores.map((row) => (
                        <tr
                          key={`${row.unidad_negocio_pk}-${row.proveedor_id}`}
                          className="border-b"
                        >
                          <td className="py-2 pr-4">
                            <button
                              type="button"
                              className="font-medium underline underline-offset-2"
                              onDoubleClick={() =>
                                loadDrilldown(
                                  row.proveedor_id
                                )
                              }
                              onClick={() =>
                                loadDrilldown(
                                  row.proveedor_id
                                )
                              }
                            >
                              {row.proveedor_nombre ||
                                `Proveedor ${row.proveedor_id}`}
                            </button>
                          </td>
                          <td className="py-2 pr-4 text-right">
                            {row.recepciones}
                          </td>
                          <td className="py-2 pr-4 text-right">
                            {formatCurrency(
                              row.total_compras
                            )}
                          </td>
                          <td className="py-2 text-right">
                            {formatCurrency(
                              row.ticket_promedio
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {(drilldown.recepciones || []).length > 0 && (
                <div className="mt-5 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="py-2 pr-4">
                          Fecha
                        </th>
                        <th className="py-2 pr-4">
                          Entrada
                        </th>
                        <th className="py-2 pr-4">
                          Proveedor
                        </th>
                        <th className="py-2 pr-4 text-right">
                          Subtotal
                        </th>
                        <th className="py-2 pr-4 text-right">
                          Impuesto
                        </th>
                        <th className="py-2 text-right">
                          Total
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {drilldown.recepciones.map(
                        (row, index) => (
                          <tr
                            key={`${row.folio_recepcion}-${row.fecha_recepcion}-${index}`}
                            className="border-b"
                          >
                            <td className="py-2 pr-4">
                              {row.fecha_recepcion}
                            </td>
                            <td className="py-2 pr-4 font-medium">
                              {row.folio_recepcion}
                            </td>
                            <td className="py-2 pr-4">
                              {row.proveedor_nombre ||
                                row.proveedor_id}
                            </td>
                            <td className="py-2 pr-4 text-right">
                              {formatCurrency(
                                row.subtotal
                              )}
                            </td>
                            <td className="py-2 pr-4 text-right">
                              {formatCurrency(
                                row.impuesto_total
                              )}
                            </td>
                            <td className="py-2 text-right font-medium">
                              {formatCurrency(
                                row.total
                              )}
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {facturas.length === 0 && (
        <Card>
          <CardContent className="p-8">
            <div className="flex gap-3">
              <AlertCircle className="mt-0.5 h-5 w-5 text-zinc-400" />
              <div>
                <div className="font-medium text-zinc-800">
                  Sin CxP disponible
                </div>
                <div className="mt-1 text-sm text-zinc-500">
                  No existen obligaciones para el alcance actual.
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {metrics.autorizadas > 0 && (
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <CheckCircle2 className="h-4 w-4" />
          Las autorizaciones mostradas proceden del contrato CxP actual.
        </div>
      )}
    </div>
  );
}
