import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { DollarSign, BookOpen, CreditCard, Building2, FileSpreadsheet, Construction } from 'lucide-react';

export default function Finanzas() {
  const modulos = [
    { nombre: 'Libro Mayor', descripcion: 'Registro contable general', icon: BookOpen },
    { nombre: 'Cuentas por Cobrar', descripcion: 'Seguimiento de cobranza a clientes', icon: DollarSign },
    { nombre: 'Cuentas por Pagar', descripcion: 'Control de pagos a proveedores', icon: CreditCard },
    { nombre: 'Activos Fijos', descripcion: 'Inventario y depreciación de activos', icon: Building2 },
    { nombre: 'Conciliación Bancaria', descripcion: 'Verificación de movimientos bancarios', icon: FileSpreadsheet },
  ];

  return (
    <div className="p-6" data-testid="finanzas-page">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-800">Finanzas y Contabilidad</h1>
        <p className="text-zinc-500">Gestión financiera y contable de la empresa</p>
      </div>

      {/* Banner de próximamente */}
      <Card className="mb-6 border-2 border-dashed border-amber-300 bg-amber-50">
        <CardContent className="py-8 text-center">
          <Construction className="h-16 w-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-amber-700 mb-2">Módulo en Desarrollo</h2>
          <p className="text-amber-600">
            Este módulo estará disponible próximamente. Incluirá todas las funcionalidades 
            de gestión financiera y contable.
          </p>
        </CardContent>
      </Card>

      {/* Preview de funcionalidades */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
