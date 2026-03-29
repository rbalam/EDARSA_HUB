import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Users, Wallet, Calendar, UserCheck, FileText, Construction } from 'lucide-react';

export default function RecursosHumanos() {
  const modulos = [
    { nombre: 'Gestión de Nómina', descripcion: 'Cálculo y dispersión de sueldos', icon: Wallet },
    { nombre: 'Expedientes de Empleados', descripcion: 'Documentación y datos del personal', icon: FileText },
    { nombre: 'Control de Asistencias', descripcion: 'Registro de entradas y salidas', icon: UserCheck },
    { nombre: 'Vacaciones y Permisos', descripcion: 'Solicitudes y autorizaciones', icon: Calendar },
  ];

  return (
    <div className="p-6" data-testid="rrhh-page">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-800">Recursos Humanos</h1>
        <p className="text-zinc-500">Gestión del capital humano de la organización</p>
      </div>

      {/* Banner de próximamente */}
      <Card className="mb-6 border-2 border-dashed border-green-300 bg-green-50">
        <CardContent className="py-8 text-center">
          <Construction className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-green-700 mb-2">Módulo en Desarrollo</h2>
          <p className="text-green-600">
            Este módulo estará disponible próximamente. Incluirá gestión completa 
            de nómina, asistencias y expedientes.
          </p>
        </CardContent>
      </Card>

      {/* Preview de funcionalidades */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {modulos.map((modulo, index) => {
          const Icon = modulo.icon;
          return (
            <Card key={index} className="border opacity-60 hover:opacity-80 transition-opacity">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-zinc-100">
                    <Icon className="h-5 w-5 text-zinc-500" />
                  </div>
                  <CardTitle className="text-sm font-medium">{modulo.nombre}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-zinc-400">{modulo.descripcion}</p>
                <span className="inline-block mt-2 text-xs px-2 py-1 bg-zinc-100 text-zinc-500 rounded">
                  Próximamente
                </span>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
