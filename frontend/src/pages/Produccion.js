import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Factory, ClipboardList, Layers, Clock, Wrench, Construction } from 'lucide-react';

export default function Produccion() {
  const modulos = [
    { nombre: 'Órdenes de Fabricación', descripcion: 'Gestión de órdenes de producción', icon: ClipboardList },
    { nombre: 'Lista de Materiales (BOM)', descripcion: 'Estructura de productos y recetas', icon: Layers },
    { nombre: 'Control de Tiempos', descripcion: 'Seguimiento de tiempos de planta', icon: Clock },
    { nombre: 'Mantenimiento', descripcion: 'Programación de mantenimiento preventivo', icon: Wrench },
  ];

  return (
    <div className="p-6" data-testid="produccion-page">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-800">Producción (MRP)</h1>
        <p className="text-zinc-500">Planificación de recursos de manufactura</p>
      </div>

      {/* Banner de próximamente */}
      <Card className="mb-6 border-2 border-dashed border-blue-300 bg-blue-50">
        <CardContent className="py-8 text-center">
          <Construction className="h-16 w-16 text-blue-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-blue-700 mb-2">Módulo en Desarrollo</h2>
          <p className="text-blue-600">
            Este módulo estará disponible próximamente. Permitirá gestionar la producción,
            recetas y control de planta.
          </p>
        </CardContent>
      </Card>

      {/* Preview de funcionalidades */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {modulos.map((modulo) => {
          const Icon = modulo.icon;
          return (
            <Card key={modulo.nombre} className="border opacity-60 hover:opacity-80 transition-opacity">
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
