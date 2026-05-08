/**
 * Utilidades compartidas para el módulo de Propinas TPV
 */

export const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2
  }).format(value);
};

export const formatPercent = (value) => {
  if (value === null || value === undefined) return '-';
  return `${(value * 100).toFixed(2)}%`;
};

export const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('es-MX', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};

export const getDefaultConfig = () => ({
  alcance: { tipo: 'GLOBAL', server_id: null, empresa_id: null, sucursal_id: null },
  vigencia: { fecha_inicio: new Date().toISOString().split('T')[0], fecha_fin: null, activa: true },
  parametros: { porcentaje_comision: 0.02, tolerancia_descuadre: 5.0, dias_para_cuadrar: 1 },
  motivo_cambio: ''
});
