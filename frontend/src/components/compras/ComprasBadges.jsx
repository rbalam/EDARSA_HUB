/**
 * EDARSA HUB - Badges de Compras
 * ==============================
 * Componentes de badges reutilizables para el módulo de compras.
 * 
 * FASE 4E: Extraído de TabOperativasCompras.jsx
 * 
 * Componentes:
 * - EstadoBadge: Badge de estado de pedido (PEDIDO_DETECTADO, EN_REVISION_GERENCIA, etc.)
 * - RecomendacionBadge: Badge de recomendación (URGENTE, COMPRAR, NO_COMPRAR, REVISAR)
 * - EstadoProductoBadge: Badge de estado de producto (CRITICO, FALTANTE, OPTIMO, SOBRANTE)
 */

import React from 'react';
import { Badge } from '@/components/ui/badge';
import {
  Clock,
  AlertTriangle,
  Eye,
  Send,
  CheckCircle2,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';

/**
 * Badge de estado de pedido de compra
 * Estados: PEDIDO_DETECTADO, PENDIENTE_INVENTARIO_FISICO, AUDITORIA_EN_PROCESO,
 *          EN_REVISION_GERENCIA, PENDIENTE_TESORERIA, APROBADO, RECHAZADO
 */
export const EstadoBadge = ({ estado }) => {
  const config = {
    PEDIDO_DETECTADO: { color: 'bg-zinc-100 text-zinc-800', icon: Clock, label: 'Detectado' },
    PENDIENTE_INVENTARIO_FISICO: { color: 'bg-amber-100 text-amber-800', icon: AlertTriangle, label: 'Pend. Inventario' },
    AUDITORIA_EN_PROCESO: { color: 'bg-blue-100 text-blue-800', icon: Clock, label: 'En Proceso' },
    EN_REVISION_GERENCIA: { color: 'bg-purple-100 text-purple-800', icon: Eye, label: 'Revisión Gerencia' },
    PENDIENTE_TESORERIA: { color: 'bg-cyan-100 text-cyan-800', icon: Send, label: 'Pend. Tesorería' },
    APROBADO: { color: 'bg-green-100 text-green-800', icon: CheckCircle2, label: 'Aprobado' },
    RECHAZADO: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Rechazado' },
  };
  
  const { color, icon: Icon, label } = config[estado] || { color: 'bg-zinc-100 text-zinc-800', icon: Clock, label: estado };
  
  return (
    <Badge className={`${color} text-xs flex items-center gap-1`} data-testid={`badge-estado-${estado}`}>
      <Icon className="w-3 h-3" />
      {label}
    </Badge>
  );
};

/**
 * Badge de recomendación de compra
 * Estados: URGENTE, COMPRAR, NO_COMPRAR, REVISAR
 */
export const RecomendacionBadge = ({ recomendacion }) => {
  const config = {
    URGENTE: { color: 'bg-red-500 text-white', label: 'URGENTE' },
    COMPRAR: { color: 'bg-amber-500 text-white', label: 'Comprar' },
    NO_COMPRAR: { color: 'bg-green-500 text-white', label: 'No Comprar' },
    REVISAR: { color: 'bg-blue-500 text-white', label: 'Revisar' },
  };
  
  const { color, label } = config[recomendacion] || { color: 'bg-zinc-500 text-white', label: recomendacion };
  
  return <Badge className={`${color} text-xs`}>{label}</Badge>;
};

/**
 * Badge de estado de producto en inventario
 * Estados: CRITICO, FALTANTE, OPTIMO, SOBRANTE
 */
export const EstadoProductoBadge = ({ estado }) => {
  const config = {
    CRITICO: { color: 'text-red-600', icon: TrendingDown, bg: 'bg-red-50' },
    FALTANTE: { color: 'text-amber-600', icon: TrendingDown, bg: 'bg-amber-50' },
    OPTIMO: { color: 'text-green-600', icon: Minus, bg: 'bg-green-50' },
    SOBRANTE: { color: 'text-blue-600', icon: TrendingUp, bg: 'bg-blue-50' },
  };
  
  const { color, icon: Icon, bg } = config[estado] || { color: 'text-zinc-600', icon: Minus, bg: 'bg-zinc-50' };
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${color} ${bg}`}>
      <Icon className="w-3 h-3" />
      {estado}
    </span>
  );
};

// Export por defecto del objeto con todos los badges
export default {
  EstadoBadge,
  RecomendacionBadge,
  EstadoProductoBadge,
};
