import React from 'react';
import { Link } from 'react-router-dom';

export default function AdminHub() {
  const cards = [
    {
      title: 'Dashboard Ejecutivo',
      desc: 'KPIs corporativos: ventas, tickets, PAX, compras, precios y rentabilidad base.',
      path: '/admin/dashboard-ejecutivo',
      status: 'SQL-First',
    },
    {
      title: 'Centro de Excepciones',
      desc: 'Alertas estratégicas BSC: margen negativo, precio cero, pedidos sin detalle e inventarios a revisar.',
      path: '/admin/centro-excepciones',
      status: 'BSC',
    },
    {
      title: 'Monitor de Sincronización',
      desc: 'Estado de servidores, procesos, errores, registros sincronizados y procesos stale.',
      path: '/admin/sync-monitor',
      status: 'Operación',
    },
  ];

  return (
    <div className="p-6 bg-gray-50 min-h-screen space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Administración Corporativa</h1>
        <p className="text-sm text-gray-600">
          Centro directivo EDARSAHUB · SQL-First · Balanced Scorecard · Gestión por excepciones
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cards.map((c) => (
          <Link
            key={c.path}
            to={c.path}
            className="bg-white rounded-lg shadow p-5 hover:shadow-md transition border border-gray-100"
          >
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-lg font-semibold text-gray-900">{c.title}</h2>
              <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                {c.status}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-3">{c.desc}</p>
            <div className="text-sm text-blue-700 font-medium mt-4">
              Abrir →
            </div>
          </Link>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow p-5">
        <h2 className="font-semibold text-gray-900 mb-3">Modelo de Gestión</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
          <Box title="Financiera" text="Ventas, margen, rentabilidad, costos y EBITDA." />
          <Box title="Cliente" text="PAX, ticket promedio, recurrencia, quejas y servicio." />
          <Box title="Procesos Internos" text="Compras, inventarios, sync, producción y operación." />
          <Box title="Aprendizaje" text="RH, capacitación, productividad y desempeño." />
        </div>
      </div>
    </div>
  );
}

function Box({ title, text }) {
  return (
    <div className="border rounded p-3 bg-gray-50">
      <p className="font-semibold text-gray-900">{title}</p>
      <p className="text-gray-600 mt-1">{text}</p>
    </div>
  );
}
