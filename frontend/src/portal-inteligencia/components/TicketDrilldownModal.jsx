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

export function TicketDrilldownModal({
  open,
  onClose,
  unidad,
  periodo,
  fechaInicio,
  fechaFin,
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
    }),
    [unidad, periodo, fechaInicio, fechaFin]
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

    return {
      tickets: payload.items || [],
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
          columns={[
            { key: 'fecha', label: 'Fecha' },
            { key: 'hora', label: 'Hora' },
            { key: 'unidad', label: 'Unidad' },
            { key: 'numero_ticket', label: 'Ticket' },
            { key: 'pax', label: 'PAX' },
            { key: 'lineas', label: 'Líneas' },
            { key: 'ventas', label: 'Ventas' },
            { key: 'propina', label: 'Propina' },
          ]}
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
  }, []);

  return (
    <CanonicalTicketDrilldown
      open={open}
      onClose={onClose}
      scope={scope}
      title={titulo}
      loadTickets={loadTickets}
      loadTicketDetail={loadTicketDetail}
      renderExportActions={renderExportActions}
    />
  );
}
