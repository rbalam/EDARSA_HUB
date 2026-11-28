/**
 * Adaptador temporal del Portal de Inteligencia.
 *
 * La implementación visual y de navegación vive exclusivamente en:
 * components/comercial/analytics/CanonicalTicketDrilldown
 *
 * Este archivo conserva compatibilidad con consumidores existentes.
 */
import React, { useCallback } from 'react';

import CanonicalTicketDrilldown from '../../components/comercial/analytics/CanonicalTicketDrilldown';
import { apiGet, ESTADO } from '../api/client';
import { ExportButtons } from './ExportButtons';

const DEFAULT_TICKET_COLUMNS = [
  { key: 'fecha', label: 'FECHA' },
  { key: 'hora', label: 'HORA' },
  { key: 'unidad', label: 'UNIDAD' },
  { key: 'numero_ticket', label: 'TICKET', mono: true },
  { key: 'pax', label: 'PAX', align: 'center', format: 'number' },
  { key: 'lineas', label: 'LÍNEAS', align: 'center', format: 'number' },
  { key: 'ventas', label: 'VENTAS', align: 'right', format: 'money', emphasis: true },
];

const KPI_TICKET_COLUMNS = {
  tickets: DEFAULT_TICKET_COLUMNS,
  ventas: [
    { key: 'fecha', label: 'FECHA' },
    { key: 'hora', label: 'HORA' },
    { key: 'numero_ticket', label: 'TICKET', mono: true },
    { key: 'pax', label: 'PAX', align: 'center', format: 'number' },
    { key: 'ventas', label: 'VENTAS', align: 'right', format: 'money', emphasis: true },
  ],
  pax_promedio: [
    { key: 'fecha', label: 'FECHA' },
    { key: 'hora', label: 'HORA' },
    { key: 'numero_ticket', label: 'TICKET', mono: true },
    { key: 'pax', label: 'PAX', align: 'center', format: 'number' },
    { key: 'ventas', label: 'VENTAS', align: 'right', format: 'money' },
    { key: 'venta_por_pax', label: 'VENTA / PAX', align: 'right', format: 'money', emphasis: true },
  ],
  cheque_promedio: [
    { key: 'fecha', label: 'FECHA' },
    { key: 'hora', label: 'HORA' },
    { key: 'numero_ticket', label: 'TICKET', mono: true },
    { key: 'pax', label: 'PAX', align: 'center', format: 'number' },
    { key: 'ventas', label: 'IMPORTE CHEQUE', align: 'right', format: 'money', emphasis: true },
    { key: 'vs_promedio', label: 'VS PROMEDIO', align: 'right', format: 'money' },
  ],
  pax_total: [
    { key: 'fecha', label: 'FECHA' },
    { key: 'hora', label: 'HORA' },
    { key: 'numero_ticket', label: 'TICKET', mono: true },
    { key: 'pax', label: 'PAX', align: 'center', format: 'number', emphasis: true },
    { key: 'ventas', label: 'VENTAS', align: 'right', format: 'money' },
  ],
  cheques: [
    { key: 'fecha', label: 'FECHA' },
    { key: 'hora', label: 'HORA' },
    { key: 'numero_ticket', label: 'CHEQUE / TICKET', mono: true, emphasis: true },
    { key: 'pax', label: 'PAX', align: 'center', format: 'number' },
    { key: 'ventas', label: 'IMPORTE', align: 'right', format: 'money' },
  ],
  propinas: [
    { key: 'fecha', label: 'FECHA' },
    { key: 'hora', label: 'HORA' },
    { key: 'numero_ticket', label: 'TICKET', mono: true },
    { key: 'ventas', label: 'VENTAS', align: 'right', format: 'money' },
    { key: 'propina', label: 'PROPINA', align: 'right', format: 'money', emphasis: true },
    { key: 'propina_pct', label: '% PROPINA', align: 'right', format: 'percent' },
  ],
};

const KPI_SORT_KEY = {
  ventas: 'ventas',
  pax_promedio: 'venta_por_pax',
  cheque_promedio: 'ventas',
  pax_total: 'pax',
  propinas: 'propina',
};

export function TicketDrilldownModal({
  open,
  onClose,
  unidad,
  periodo,
  fechaInicio,
  fechaFin,
  metric = 'tickets',
  kpiValor = null,
  titulo = 'Reconstrucción de Tickets',
}) {
  const scope = React.useMemo(
    () => ({
      unidad,
      businessUnitLabel:
        unidad === 'todas' || !unidad
          ? 'Consolidado'
          : unidad,
      periodo,
      fechaInicio,
      fechaFin,
      metric,
      kpiValor,
    }),
    [unidad, periodo, fechaInicio, fechaFin, metric, kpiValor]
  );

  const loadTickets = useCallback(async (
    currentScope,
    pagination = {}
  ) => {
    if (
      !currentScope?.fechaInicio
      || !currentScope?.fechaFin
    ) {
      throw new Error(
        'El contrato V2 requiere fecha inicial y fecha final'
      );
    }

    const response = await apiGet(
      '/v2/comercial/analytics/tickets',
      {
        fecha_inicio: currentScope.fechaInicio,
        fecha_fin: currentScope.fechaFin,
        unidad_negocio_id: (
          currentScope?.unidad
          && currentScope.unidad !== 'todas'
            ? currentScope.unidad
            : undefined
        ),
        page: pagination.page || 1,
      }
    );

    const payload = response.data?.data;

    if (
      response.estado !== ESTADO.OK
      || !response.data
      || response.data.success === false
      || !payload
    ) {
      throw new Error('No fue posible consultar los tickets');
    }

    const normalizedTickets = (payload.items || []).map((ticket) => {
      const ventas = Number(ticket.ventas || 0);
      const pax = Number(ticket.pax || 0);
      const propina = Number(ticket.propina || 0);
      const promedio = Number(currentScope?.kpiValor || 0);

      return {
        ...ticket,
        venta_por_pax: pax > 0 ? ventas / pax : 0,
        vs_promedio: ventas - promedio,
        propina_pct: ventas > 0 ? (propina / ventas) * 100 : 0,
      };
    });

    const sortKey = KPI_SORT_KEY[currentScope?.metric];
    const tickets = sortKey
      ? [...normalizedTickets].sort(
          (a, b) => Number(b[sortKey] || 0) - Number(a[sortKey] || 0)
        )
      : normalizedTickets;

    return {
      tickets,
      filters: {
        fecha_inicio: currentScope.fechaInicio,
        fecha_fin: currentScope.fechaFin,
        periodo_label: currentScope.periodLabel || null,
      },
      page: payload.page,
      pageSize: payload.page_size,
      total: payload.total,
      returned: payload.returned,
      hasMore: payload.has_more,
    };
  }, []);

  const loadTicketDetail = useCallback(async (ticket) => {
    if (!ticket?.ticket_pk) {
      throw new Error(
        'El backend no devolvió la identidad canónica del ticket'
      );
    }

    const response = await apiGet(
      `/v2/comercial/analytics/tickets/${
        encodeURIComponent(ticket.ticket_pk)
      }`
    );

    const payload = response.data?.data;

    if (
      response.estado !== ESTADO.OK
      || !response.data
      || response.data.success === false
      || !payload
    ) {
      throw new Error('No fue posible reconstruir el ticket');
    }

    return {
      lines: payload.lines || payload.lineas || [],
      ticket: payload.ticket || null,
    };
  }, []);

  const ticketColumns = KPI_TICKET_COLUMNS[metric] || DEFAULT_TICKET_COLUMNS;

  const renderExportActions = useCallback(({
    selectedTicket,
    tickets,
    lines,
    metadata,
  }) => {
    if (!selectedTicket && tickets.length > 0) {
      return (
        <ExportButtons
          filename="tickets"
          title="Tickets"
          columns={ticketColumns.map(({ key, label }) => ({ key, label }))}
          rows={tickets}
          meta={metadata}
          testid="drilldown-tickets-export"
        />
      );
    }

    if (selectedTicket && lines.length > 0) {
      return (
        <ExportButtons
          filename={`ticket_${selectedTicket.numero_ticket}`}
          title={`Ticket ${selectedTicket.numero_ticket}`}
          columns={[
            { key: 'codigo', label: 'Código' },
            { key: 'producto', label: 'Producto' },
            { key: 'clasificacion', label: 'Clasificación' },
            { key: 'familia', label: 'Familia' },
            { key: 'casa', label: 'Casa' },
            { key: 'grado_alcohol', label: 'Grado' },
            { key: 'cantidad', label: 'Cantidad' },
            { key: 'precio_unitario', label: 'P.Unit' },
            { key: 'importe', label: 'Importe' },
          ]}
          rows={lines}
          meta={metadata}
          testid="drilldown-lineas-export"
        />
      );
    }

    return null;
  }, [ticketColumns]);

  return (
    <CanonicalTicketDrilldown
      open={open}
      onClose={onClose}
      scope={scope}
      title={titulo}
      ticketColumns={ticketColumns}
      loadTickets={loadTickets}
      loadTicketDetail={loadTicketDetail}
      renderExportActions={renderExportActions}
    />
  );
}
