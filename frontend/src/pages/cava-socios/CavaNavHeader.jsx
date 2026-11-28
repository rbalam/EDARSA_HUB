import React from 'react';
import { Wine, Users, Package, TrendingDown, Layers, Plus, RefreshCw, ClipboardCheck, ArrowRightLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate, useLocation } from 'react-router-dom';
import { CorporateFilterSelect } from '../../filters';

export default function CavaNavHeader({ title, subtitle, onRefresh, loading }) {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;
  const searchParams = new URLSearchParams(location.search);
  const currentTab = searchParams.get('tab') || 'custodia';

  const navItems = [
    { label: 'Dashboard', path: '/cava-socios', icon: Layers, active: currentPath === '/cava-socios' },
    { label: 'Socios', path: '/cava-socios/socios', icon: Users, active: currentPath.startsWith('/cava-socios/socios') },
    { label: 'Botellas en Custodia', path: '/cava-socios/inventario?tab=custodia', icon: Wine, active: currentPath === '/cava-socios/inventario' && currentTab === 'custodia' },
    { label: 'Carga Inv. Inicial', path: '/cava-socios/inventario?tab=inicial', icon: Plus, active: currentPath === '/cava-socios/inventario' && currentTab === 'inicial' },
    { label: 'Kardex Canónico (PZ)', path: '/cava-socios/inventario?tab=kardex', icon: ArrowRightLeft, active: currentPath === '/cava-socios/inventario' && currentTab === 'kardex' },
    { label: 'Auditoría Física', path: '/cava-socios/inventario?tab=fisico', icon: ClipboardCheck, active: currentPath === '/cava-socios/inventario' && currentTab === 'fisico' },
    { label: 'Auditoría Ciega', path: '/cava-socios/auditoria-ciega', icon: ClipboardCheck, active: currentPath === '/cava-socios/auditoria-ciega' },
    { label: 'Bitácora Consumos', path: '/cava-socios/consumos', icon: TrendingDown, active: currentPath === '/cava-socios/consumos' },
  ];

  return (
    <div className="space-y-4 mb-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-zinc-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-100 rounded-xl text-purple-700 shadow-inner">
            <Wine className="h-7 w-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-zinc-900 flex items-center gap-2">
              {title || 'Portal de Cava de Socios'}
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 uppercase tracking-wide">
                Canónico PZ
              </span>
            </h1>
            <p className="text-sm text-muted-foreground">
              {subtitle || 'Gestión integral de membresías, custodia de botellas, balance Kardex y auditorías'}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-end gap-2">
          <div className="min-w-[260px]">
            <CorporateFilterSelect
              filterKey="unidades_negocio"
              label="Unidad de negocio"
              placeholder="Selecciona una unidad"
            />
          </div>

          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={loading} className="gap-1.5">
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </Button>
          )}

          <Button size="sm" onClick={() => navigate('/cava-socios/socios/nuevo')} className="gap-1.5 bg-purple-700 hover:bg-purple-800 text-white">
            <Plus className="h-4 w-4" />
            Nuevo Socio
          </Button>
        </div>
      </div>

      {/* Operative Navigation Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b border-zinc-200">
        {navItems.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              type="button"
              onClick={() => navigate(item.path)}
              className={`flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${
                item.active
                  ? 'bg-purple-700 text-white shadow-sm'
                  : 'text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100'
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
