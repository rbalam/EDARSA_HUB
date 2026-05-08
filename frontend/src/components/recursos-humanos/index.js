/**
 * EDARSA HUB - Recursos Humanos Components Index
 * ==============================================
 * Índice de componentes extraídos del módulo RH.
 * 
 * FASE 4E: Desacoplamiento de RecursosHumanos.js
 */

// Dashboard
export { default as RhDashboard } from './RhDashboard';

// Colaboradores
export { default as RhColaboradores } from './RhColaboradores';

// Incidencias
export { default as RhIncidencias } from './RhIncidencias';

// Nóminas (Kanban)
export { default as RhNominas } from './RhNominas';

// Catálogos
export { default as RhCatalogos } from './RhCatalogos';

// Reclutamiento
export { default as RhReclutamiento } from './RhReclutamiento';

// Asistencia
export { default as RhAsistencia } from './RhAsistencia';

// Shared Components
export {
  RhLoadingState,
  RhEmptyState,
  EstatusLaboralBadge,
  EtapaNominaBadge,
  RhFilters,
  RhPagination,
} from './shared/RhSharedComponents';
