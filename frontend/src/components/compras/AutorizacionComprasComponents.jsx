/**
 * Componentes para Autorización de Compras
 */
import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import {
  ShoppingCart, Package, TrendingUp, AlertTriangle, 
  Loader2, CheckCircle2, XCircle
} from 'lucide-react';

// ============================================================================
// Selector de Almacenes
// ============================================================================

export function AlmacenesSelector({ 
  almacenes, 
  selectedAlmacenes, 
  todosAlmacenes, 
  onToggle, 
  onToggleTodos,
  disabled 
}) {
  if (almacenes.length === 0) {
    return (
      <div className="text-center py-4 text-zinc-500 text-sm">
        No hay almacenes disponibles
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 pb-2 border-b">
        <Checkbox
          id="todos-almacenes"
          checked={todosAlmacenes}
          onCheckedChange={onToggleTodos}
          disabled={disabled}
        />
        <Label htmlFor="todos-almacenes" className="font-medium cursor-pointer">
          Todos los almacenes ({almacenes.length})
        </Label>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-48 overflow-y-auto">
        {almacenes.map(almacen => (
          <div key={almacen.id} className="flex items-center gap-2">
            <Checkbox
              id={`almacen-${almacen.id}`}
              checked={selectedAlmacenes.includes(almacen.id)}
              onCheckedChange={() => onToggle(almacen.id)}
              disabled={disabled || todosAlmacenes}
            />
            <Label 
              htmlFor={`almacen-${almacen.id}`} 
              className="text-sm cursor-pointer truncate"
              title={almacen.nombre}
            >
              {almacen.nombre}
            </Label>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Resumen de Pedido
// ============================================================================

export function ResumenPedido({ resumen, formatCurrency }) {
  if (!resumen) return null;

  const items = [
    { label: 'Total Artículos', value: resumen.total_articulos, icon: Package },
    { label: 'Artículos con Pedido', value: resumen.articulos_con_pedido, icon: ShoppingCart, color: 'text-blue-600' },
    { label: 'Valor Estimado', value: formatCurrency(resumen.valor_estimado), icon: TrendingUp, color: 'text-green-600' },
    { label: 'Alertas', value: resumen.alertas || 0, icon: AlertTriangle, color: 'text-amber-600' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {items.map(item => (
        <Card key={item.label}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-zinc-500">{item.label}</span>
              <item.icon className={`w-4 h-4 ${item.color || 'text-zinc-400'}`} />
            </div>
            <p className="text-xl font-bold">{item.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ============================================================================
// Info Inventario
// ============================================================================

export function InfoInventario({ info }) {
  if (!info) return null;

  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Package className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-medium text-blue-900">Inventario Físico Base</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2 text-sm">
              <div>
                <span className="text-blue-600">Folio:</span>
                <span className="ml-2 font-medium">{info.folio}</span>
              </div>
              <div>
                <span className="text-blue-600">Fecha:</span>
                <span className="ml-2">{info.fecha}</span>
              </div>
              <div>
                <span className="text-blue-600">Almacén:</span>
                <span className="ml-2">{info.almacen}</span>
              </div>
              <div>
                <span className="text-blue-600">Artículos:</span>
                <span className="ml-2">{info.total_articulos}</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Estado Badge para Pedidos
// ============================================================================

export function EstadoPedidoBadge({ estado }) {
  const config = {
    pendiente: { class: 'bg-amber-100 text-amber-800', text: 'Pendiente' },
    aprobado: { class: 'bg-green-100 text-green-800', text: 'Aprobado' },
    rechazado: { class: 'bg-red-100 text-red-800', text: 'Rechazado' },
    parcial: { class: 'bg-blue-100 text-blue-800', text: 'Parcial' },
  };

  const cfg = config[estado?.toLowerCase()] || config.pendiente;

  return (
    <Badge className={`${cfg.class} hover:${cfg.class}`}>
      {cfg.text}
    </Badge>
  );
}

// ============================================================================
// Loading Skeleton
// ============================================================================

export function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-8 bg-zinc-200 rounded w-1/3"></div>
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={`skeleton-${i}`} className="h-24 bg-zinc-100 rounded"></div>
        ))}
      </div>
      <div className="h-64 bg-zinc-100 rounded"></div>
    </div>
  );
}

// ============================================================================
// Empty State
// ============================================================================

export function EmptyState({ message, icon: Icon = Package }) {
  return (
    <div className="text-center py-12">
      <Icon className="w-12 h-12 mx-auto text-zinc-300 mb-4" />
      <p className="text-zinc-500">{message}</p>
    </div>
  );
}
