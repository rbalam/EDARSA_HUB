import React from "react";

export default function HospitalityDashboard() {
  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-2xl font-bold">EDARSAHUB Hospitality</h1>
        <p className="text-gray-500">
          Módulo satélite en preparación. SQL-first, sin MongoDB, sin LIVE operativo.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-2xl border p-4 shadow-sm">
          <h2 className="font-semibold">Multiconectividad</h2>
          <p className="text-sm text-gray-500">PMS, OTAs, channel managers y conectores globales.</p>
        </div>

        <div className="rounded-2xl border p-4 shadow-sm">
          <h2 className="font-semibold">Automatización</h2>
          <p className="text-sm text-gray-500">Check-in, room service, tickets, SLA y Guest Success.</p>
        </div>

        <div className="rounded-2xl border p-4 shadow-sm">
          <h2 className="font-semibold">ERP Integrado</h2>
          <p className="text-sm text-gray-500">RBAC, finanzas, nómina, comandero, inventarios y BI.</p>
        </div>
      </div>
    </div>
  );
}
