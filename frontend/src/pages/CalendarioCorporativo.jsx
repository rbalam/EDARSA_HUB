import React, { useMemo, useState } from 'react';
import {
  CalendarDays,
  Building2,
  UserRound,
  Filter,
  ShieldCheck
} from 'lucide-react';

import TabbedModuleShell from '../components/navigation/TabbedModuleShell';

const TABS = [
  {
    id: 'dias-especiales',
    label: 'Días especiales'
  },
  {
    id: 'comparativos',
    label: 'Comparativos',
    badge: 'Próximamente',
    disabled: true
  },
  {
    id: 'mis-selecciones',
    label: 'Mis selecciones',
    badge: 'Próximamente',
    disabled: true
  },
  {
    id: 'administracion',
    label: 'Administración',
    badge: 'V1.2',
    disabled: true
  }
];

function CalendarOverview() {
  const capabilities = [
    {
      icon: Building2,
      title: 'Fechas comerciales corporativas',
      description:
        'Fechas comerciales con alcance de empresa y visibilidad controlada.'
    },
    {
      icon: CalendarDays,
      title: 'Fechas comerciales por unidad',
      description:
        'Fechas comerciales aplicables a una o varias unidades de negocio.'
    },
    {
      icon: UserRound,
      title: 'Comparativos comerciales',
      description:
        'Selección de la misma fecha comercial entre distintos años y periodos.'
    },
    {
      icon: Filter,
      title: 'Selecciones guardadas',
      description:
        'Última selección y filtros comerciales favoritos por usuario.'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-0.5 h-5 w-5 text-blue-700" />

          <div>
            <h2 className="font-semibold text-blue-900">
              Estructura segura preparada
            </h2>

            <p className="mt-1 text-sm text-blue-700">
              Este módulo canónico está aislado de Horarios Operativos.
              En esta fase no ejecuta consultas, no guarda datos y no
              modifica la configuración del día operativo.
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {capabilities.map(({ icon: Icon, title, description }) => (
          <article
            key={title}
            className="rounded-xl border bg-white p-5 shadow-sm"
          >
            <Icon className="h-6 w-6 text-blue-600" />

            <h3 className="mt-3 font-semibold text-gray-900">
              {title}
            </h3>

            <p className="mt-1 text-sm text-gray-500">
              {description}
            </p>
          </article>
        ))}
      </div>

      <div className="rounded-xl border border-dashed bg-gray-50 p-6">
        <h2 className="font-semibold text-gray-900">
          Próxima fase
        </h2>

        <p className="mt-2 text-sm text-gray-600">
          Implementar en V1.0 únicamente días especiales comerciales con contrato canónico, RBAC y fuente SQL única. El calendario corporativo transversal completo queda preparado para V1.2.
        </p>
      </div>
    </div>
  );
}

export default function CalendarioCorporativo() {
  const [activeTab, setActiveTab] = useState('dias-especiales');

  const content = useMemo(() => {
    switch (activeTab) {
      case 'dias-especiales':
      default:
        return <CalendarOverview />;
    }
  }, [activeTab]);

  return (
    <TabbedModuleShell
      title="Días Especiales Comerciales"
      description="Fechas comerciales canónicas para análisis Ejecutivo, Comercial e Inteligencia Comercial."
      icon={CalendarDays}
      tabs={TABS}
      activeTab={activeTab}
      onTabChange={setActiveTab}
    >
      {content}
    </TabbedModuleShell>
  );
}
