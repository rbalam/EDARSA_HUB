/**
 * EDARSA HUB - RH Reclutamiento
 * =============================
 * Gestión de vacantes y candidatos para reclutamiento.
 * 
 * FASE 4E: Extraído de RecursosHumanos.js
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Briefcase,
  Users,
  UserPlus,
  Plus,
  Building2,
  Star,
  Mail,
  Phone,
  ExternalLink,
  FileText,
  Inbox,
} from 'lucide-react';

/**
 * Configuración de estatus de candidatos
 */
const ESTATUS_CANDIDATO = [
  { value: 'Recibido', color: 'bg-zinc-100 text-zinc-700' },
  { value: 'En Revision', color: 'bg-blue-100 text-blue-700' },
  { value: 'Entrevista', color: 'bg-purple-100 text-purple-700' },
  { value: 'Finalista', color: 'bg-amber-100 text-amber-700' },
  { value: 'Contratado', color: 'bg-green-100 text-green-700' },
  { value: 'Rechazado', color: 'bg-red-100 text-red-700' },
];

/**
 * KPI Card simple
 */
const KpiCard = ({ title, value, borderColor, textColor }) => (
  <Card className={`border-l-4 ${borderColor}`}>
    <CardContent className="pt-4">
      <p className="text-xs text-zinc-500 uppercase">{title}</p>
      <p className={`text-2xl font-bold ${textColor}`}>{value}</p>
    </CardContent>
  </Card>
);

/**
 * Componente de Reclutamiento
 */
export default function RhReclutamiento({
  // Data
  vacantes = [],
  candidatos = [],
  // Handlers
  handleVerScriptRecl,
  handleNuevoCandidato,
  handleNuevaVacante,
  handleCambiarEstatusCandidato,
  // Helpers
  setSelectedVacante,
}) {
  // Cálculos
  const vacAbiertas = vacantes.filter(v => v.Estatus === 'Abierta').length;
  const candPendientes = candidatos.filter(c => c.Estatus === 'Recibido' || c.Estatus === 'En Revision').length;
  const contratados = candidatos.filter(c => c.Estatus === 'Contratado').length;

  return (
    <div className="space-y-6" data-testid="rh-reclutamiento">
      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          title="Vacantes Abiertas"
          value={vacAbiertas}
          borderColor="border-l-blue-500"
          textColor="text-blue-600"
        />
        <KpiCard
          title="Total Candidatos"
          value={candidatos.length}
          borderColor="border-l-purple-500"
          textColor="text-purple-600"
        />
        <KpiCard
          title="Pendientes Revisión"
          value={candPendientes}
          borderColor="border-l-amber-500"
          textColor="text-amber-600"
        />
        <KpiCard
          title="Contratados"
          value={contratados}
          borderColor="border-l-green-500"
          textColor="text-green-600"
        />
      </div>

      {/* Acciones */}
      <div className="flex flex-wrap gap-3 justify-between">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleVerScriptRecl} data-testid="btn-script-recl">
            <FileText className="h-4 w-4 mr-1" />
            Ver Script SQL
          </Button>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => handleNuevoCandidato()} data-testid="btn-nuevo-candidato">
            <UserPlus className="h-4 w-4 mr-1" />
            Nuevo Candidato
          </Button>
          <Button size="sm" className="bg-zinc-900 text-white" onClick={handleNuevaVacante} data-testid="btn-nueva-vacante">
            <Plus className="h-4 w-4 mr-1" />
            Nueva Vacante
          </Button>
        </div>
      </div>

      {/* Vacantes */}
      <VacantesCard
        vacantes={vacantes}
        setSelectedVacante={setSelectedVacante}
        handleNuevoCandidato={handleNuevoCandidato}
      />

      {/* Candidatos */}
      <CandidatosTable
        candidatos={candidatos}
        handleCambiarEstatusCandidato={handleCambiarEstatusCandidato}
      />
    </div>
  );
}

/**
 * Card de Vacantes
 */
function VacantesCard({ vacantes, setSelectedVacante, handleNuevoCandidato }) {
  return (
    <Card data-testid="vacantes-card">
      <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
        <CardTitle className="text-base flex items-center gap-2">
          <Briefcase className="h-5 w-5" />
          Vacantes ({vacantes.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {vacantes.length === 0 ? (
          <div className="text-center py-8 text-zinc-400">
            <Inbox className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No hay vacantes registradas</p>
            <p className="text-xs">Ejecuta el script SQL para crear las tablas</p>
          </div>
        ) : (
          <div className="divide-y">
            {vacantes.map((vac) => (
              <div key={vac.VacanteID} className="p-4 hover:bg-zinc-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">{vac.Titulo}</h4>
                      <EstatusBadge estatus={vac.Estatus} />
                    </div>
                    <div className="text-sm text-zinc-500 flex flex-wrap gap-3">
                      <span className="flex items-center gap-1">
                        <Building2 className="h-3 w-3" />
                        {vac.Nombre_Sucursal}
                      </span>
                      <span className="flex items-center gap-1">
                        <Briefcase className="h-3 w-3" />
                        {vac.Nombre_Puesto}
                      </span>
                      {vac.Salario_Max > 0 && (
                        <span className="text-green-600">
                          ${vac.Salario_Min?.toLocaleString()} - ${vac.Salario_Max?.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                      {vac.Total_Candidatos || 0} candidatos
                    </span>
                    <Button variant="ghost" size="sm" onClick={() => {
                      setSelectedVacante(vac);
                      handleNuevoCandidato(vac.VacanteID);
                    }} data-testid={`btn-add-candidato-${vac.VacanteID}`}>
                      <UserPlus className="h-4 w-4 text-blue-600" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Badge de Estatus de Vacante
 */
function EstatusBadge({ estatus }) {
  const colorClass = 
    estatus === 'Abierta' ? 'bg-green-100 text-green-700' :
    estatus === 'En Proceso' ? 'bg-blue-100 text-blue-700' :
    'bg-zinc-100 text-zinc-700';

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {estatus}
    </span>
  );
}

/**
 * Tabla de Candidatos
 */
function CandidatosTable({ candidatos, handleCambiarEstatusCandidato }) {
  return (
    <Card data-testid="candidatos-table">
      <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
        <CardTitle className="text-base flex items-center gap-2">
          <Users className="h-5 w-5" />
          Candidatos ({candidatos.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-zinc-100">
              <tr>
                <th className="text-left p-3 font-medium">Candidato</th>
                <th className="text-left p-3 font-medium">Vacante</th>
                <th className="text-left p-3 font-medium">Contacto</th>
                <th className="text-left p-3 font-medium">Fecha</th>
                <th className="text-left p-3 font-medium">Estatus</th>
                <th className="text-center p-3 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {candidatos.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-zinc-400">
                    No hay candidatos registrados
                  </td>
                </tr>
              ) : (
                candidatos.map((cand) => {
                  const estatusInfo = ESTATUS_CANDIDATO.find(e => e.value === cand.Estatus) || ESTATUS_CANDIDATO[0];
                  return (
                    <tr key={cand.CandidatoID} className="border-b hover:bg-zinc-50">
                      <td className="p-3">
                        <div className="font-medium">{cand.Nombre_Completo}</div>
                        {cand.Puntuacion && (
                          <div className="flex items-center gap-1 text-xs text-amber-600">
                            <Star className="h-3 w-3 fill-amber-400" />
                            {cand.Puntuacion}/100
                          </div>
                        )}
                      </td>
                      <td className="p-3 text-zinc-600">{cand.Vacante_Titulo}</td>
                      <td className="p-3">
                        <div className="flex flex-col gap-1 text-xs">
                          <span className="flex items-center gap-1">
                            <Mail className="h-3 w-3 text-zinc-400" />
                            {cand.Email}
                          </span>
                          {cand.Telefono && (
                            <span className="flex items-center gap-1">
                              <Phone className="h-3 w-3 text-zinc-400" />
                              {cand.Telefono}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-3 text-xs text-zinc-500">
                        {cand.Fecha_Aplicacion ? new Date(cand.Fecha_Aplicacion).toLocaleDateString('es-MX') : '-'}
                      </td>
                      <td className="p-3">
                        <select
                          value={cand.Estatus}
                          onChange={(e) => handleCambiarEstatusCandidato(cand.CandidatoID, e.target.value)}
                          className={`px-2 py-1 rounded text-xs font-medium border-0 cursor-pointer ${estatusInfo.color}`}
                          data-testid={`select-estatus-${cand.CandidatoID}`}
                        >
                          {ESTATUS_CANDIDATO.map(e => (
                            <option key={e.value} value={e.value}>{e.value}</option>
                          ))}
                        </select>
                      </td>
                      <td className="p-3 text-center">
                        {cand.CV_URL && (
                          <Button variant="ghost" size="sm" onClick={() => window.open(cand.CV_URL, '_blank')} data-testid={`btn-cv-${cand.CandidatoID}`}>
                            <ExternalLink className="h-4 w-4 text-blue-600" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
