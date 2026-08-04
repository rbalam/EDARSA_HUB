import React from 'react';

/**
 * Contenedor canónico para módulos preparados para tabs.
 *
 * Reglas:
 * - La navegación de tabs es responsabilidad de este componente.
 * - La lógica de negocio permanece dentro del contenido de cada tab.
 * - Los tabs deshabilitados no montan contenido ni ejecutan consultas.
 * - Agregar un nuevo tab no requiere reescribir la página anfitriona.
 */
export default function TabbedModuleShell({
  title,
  description,
  icon: Icon,
  tabs,
  activeTab,
  onTabChange,
  children
}) {
  const safeTabs = Array.isArray(tabs) ? tabs : [];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-6">
        <div className="flex items-start gap-3">
          {Icon && (
            <div className="p-2 rounded-lg bg-blue-50 text-blue-700">
              <Icon className="w-7 h-7" />
            </div>
          )}

          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {title}
            </h1>

            {description && (
              <p className="mt-1 text-gray-500">
                {description}
              </p>
            )}
          </div>
        </div>
      </header>

      <nav
        className="mb-6 border-b border-gray-200"
        aria-label={`Secciones de ${title}`}
      >
        <div className="flex flex-wrap gap-1">
          {safeTabs.map((tab) => {
            const isActive = tab.id === activeTab;
            const isDisabled = Boolean(tab.disabled);

            return (
              <button
                key={tab.id}
                type="button"
                disabled={isDisabled}
                onClick={() => {
                  if (!isDisabled) {
                    onTabChange(tab.id);
                  }
                }}
                className={[
                  'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                  isActive
                    ? 'border-blue-600 text-blue-700'
                    : 'border-transparent text-gray-500 hover:text-gray-800',
                  isDisabled
                    ? 'cursor-not-allowed opacity-50'
                    : 'cursor-pointer'
                ].join(' ')}
                aria-current={isActive ? 'page' : undefined}
              >
                {tab.label}

                {tab.badge && (
                  <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs">
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      <section>
        {children}
      </section>
    </div>
  );
}
