/**
 * Hook CANÓNICO para el detalle de movimientos / consumos de un producto.
 * =======================================================================
 * Regla de centralización: usado en Análisis (Reportes.js) y Auditoría
 * (Compras.js) al hacer doble clic sobre una celda de Movimientos / Ventas.
 *
 * Fuente única: SIEMPRE consulta los endpoints canónicos del backend, que ya
 * aceptan la `unidad` canónica (codigo/pk) o el server_id legacy y funcionan
 * para MPRO y SoftRestaurant:
 *   - POST /compras/detalle-movimientos
 *   - POST /compras/detalle-consumos   (delegado a la misma lógica de ventas)
 *
 * Normaliza la respuesta a una forma única: { movimientos, totales }.
 */
import { useState, useCallback } from 'react';
import api from '@/lib/api';
import logger from '@/services/logger';

const ESTADO_INICIAL = {
  open: false,
  loading: false,
  tipo: 'movimientos', // 'movimientos' | 'consumos'
  codigo: '',
  producto: '',
  movimientos: [],
  totales: {},
  error: null,
};

function _mensajeError(error, tipo) {
  if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
    return 'Tiempo de espera agotado. El servidor externo no responde.';
  }
  if (error?.response?.data?.detail) {
    return String(error.response.data.detail).substring(0, 150);
  }
  return `Error al obtener detalle de ${tipo === 'consumos' ? 'consumos' : 'movimientos'}`;
}

export function useDetalleProducto() {
  const [detalle, setDetalle] = useState(ESTADO_INICIAL);

  const _cargar = useCallback(async (endpoint, tipo, params) => {
    const {
      serverId,
      sucursal,
      codigo,
      producto,
      fechaInicio,
      fechaFin,
      almacenes,
    } = params || {};

    setDetalle({
      ...ESTADO_INICIAL,
      open: true,
      loading: true,
      tipo,
      codigo: codigo || '',
      producto: producto || '',
    });

    try {
      const response = await api.post(
        endpoint,
        {
          server_id: serverId,
          sucursal: sucursal,
          codigo: codigo,
          fecha_inicio: fechaInicio,
          fecha_fin: fechaFin,
          almacenes: Array.isArray(almacenes)
            ? almacenes
            : almacenes
            ? [almacenes]
            : [],
        },
        { timeout: 30000 }
      );

      const d = response.data || {};
      if (d.error) {
        setDetalle((prev) => ({
          ...prev,
          loading: false,
          movimientos: [],
          totales: {},
          error: d.error,
        }));
      } else {
        setDetalle((prev) => ({
          ...prev,
          loading: false,
          movimientos: d.movimientos || d.consumos || [],
          totales: d.totales || {},
          error: null,
        }));
      }
    } catch (error) {
      logger.error(`[useDetalleProducto] Error (${tipo}):`, error);
      setDetalle((prev) => ({
        ...prev,
        loading: false,
        movimientos: [],
        totales: {},
        error: _mensajeError(error, tipo),
      }));
    }
  }, []);

  const abrirMovimientos = useCallback(
    (params) => _cargar('/compras/detalle-movimientos', 'movimientos', params),
    [_cargar]
  );

  const abrirConsumos = useCallback(
    (params) => _cargar('/compras/detalle-consumos', 'consumos', params),
    [_cargar]
  );

  const cerrar = useCallback(() => setDetalle(ESTADO_INICIAL), []);

  return { detalle, abrirMovimientos, abrirConsumos, cerrar };
}

export default useDetalleProducto;
