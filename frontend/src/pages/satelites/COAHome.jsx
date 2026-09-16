const modules = [
  { title: 'Expedientes', description: 'Seguimiento central de operaciones administrativas y su trazabilidad.' },
  { title: 'Facturacion', description: 'Recepcion, validacion, timbrado, distribucion y seguimiento documental.' },
  { title: 'Nominas', description: 'Control de relaciones de pago, fondeo, dispersion y comprobantes.' },
  { title: 'Comisiones', description: 'Validacion de reglas administrativas configurables por empresa y operacion.' },
  { title: 'Incidencias', description: 'Excepciones, diferencias, documentos faltantes y autorizaciones pendientes.' }
];

export default function COAHome() {
  return (
    <div className="space-y-6 p-6" data-testid="coa-home">
      <div>
        <p className="text-sm font-medium text-muted-foreground">Satelites / COA</p>
        <h1 className="text-2xl font-semibold tracking-tight">Centro de Operaciones Administrativas</h1>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
          Satelite operativo para concentrar expedientes, documentos, validaciones y flujos administrativos.
          Esta pantalla inicial no presenta datos simulados ni ejecuta movimientos financieros.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {modules.map((module) => (
          <section key={module.title} className="rounded-lg border bg-card p-5 shadow-sm">
            <h2 className="font-semibold">{module.title}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{module.description}</p>
          </section>
        ))}
      </div>
      <section className="rounded-lg border border-dashed p-5">
        <h2 className="font-semibold">Estado de implementacion</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Bootstrap de navegacion. Las fuentes canonicas, RBAC, expedientes, reglas de comision, Gmail y WhatsApp se habilitaran en fases posteriores con validacion independiente.
        </p>
      </section>
    </div>
  );
}
