import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import WorkerConsole from '@/pages/WorkerConsole';
import Login from '@/pages/Login';
import ForgotPassword from '@/pages/ForgotPassword';
import ResetPassword from '@/pages/ResetPassword';
import Layout from '@/pages/Layout';
import Dashboard from '@/pages/Dashboard';
import Servidores from '@/pages/Servidores';
import Reportes from '@/pages/Reportes';
import Compras from '@/pages/Compras';
import Comercial from '@/pages/Comercial';
import TableroEjecutivo from '@/pages/TableroEjecutivo';
import CatalogoConsultas from '@/pages/CatalogoConsultas';
import ExploradorBD from '@/pages/ExploradorBD';
import Alertas from '@/pages/Alertas';
import Usuarios from '@/pages/Usuarios';
import Proveedores from '@/pages/Proveedores';
import Finanzas from '@/pages/Finanzas';
import Produccion from '@/pages/Produccion';
import RecursosHumanos from '@/pages/RecursosHumanos';
import ImportadorRH from '@/pages/ImportadorRH';
import ReportesBI from '@/pages/ReportesBI';
import MisTareas from '@/pages/MisTareas';
import Catalogos from '@/pages/Catalogos';
import Scheduler from '@/pages/Scheduler';
import AuditoriasProgramadas from '@/pages/AuditoriasProgramadas';
import CentroControl from '@/pages/CentroControl';
import ConfigAsignaciones from '@/pages/ConfigAsignaciones';
import DBACredentialManager from '@/pages/DBACredentialManager';
import ConfiguracionOperativaUnidades from '@/pages/ConfiguracionOperativaUnidades';
import CalendarioCorporativo from '@/pages/CalendarioCorporativo';

// CRM Enterprise
import CRMDashboard from '@/pages/crm/CRMDashboard';

// Módulos Satélites
import SuperCajaPage from '@/pages/satelites/SuperCajaPage';
import ComanderoPage from '@/pages/satelites/ComanderoPage';
import COAHome from '@/pages/satelites/COAHome';
import LeadsPage from '@/pages/crm/LeadsPage';
import OportunidadesPage from '@/pages/crm/OportunidadesPage';
import PipelinePage from '@/pages/crm/PipelinePage';
// CRM Comercial (Enterprise-Grade)
import CuentasPage from '@/pages/crm/CuentasPage';
import SolicitudesAltaPage from '@/pages/crm/SolicitudesAltaPage';
import CotizacionesPage from '@/pages/crm/CotizacionesPage';
import PedidosPage from '@/pages/crm/PedidosPage';
import RemisionesPage from '@/pages/crm/RemisionesPage';
// CRM Fases 6-15
import ActividadesPage from '@/pages/crm/ActividadesPage';
import OperacionesPage from '@/pages/crm/OperacionesPage';
import ImplementacionesPage from '@/pages/crm/ImplementacionesPage';
import PostventaPage from '@/pages/crm/PostventaPage';
import KPIsPage from '@/pages/crm/KPIsPage';

// Tablajería
import TablajeriaDashboard from '@/pages/tablajeria/TablajeriaDashboard';
import PlantillasPage from '@/pages/tablajeria/PlantillasPage';
import OrdenesPage from '@/pages/tablajeria/OrdenesPage';
import CapturaDirectaPage from '@/pages/tablajeria/CapturaDirectaPage';
import LotesProveedorPage from '@/pages/tablajeria/LotesProveedorPage';

// Cava de Socios
import { CavaSociosDashboard, SociosList, SocioDetail, SocioForm, InventarioCava, ConsumosCava, BlindAuditCava } from '@/pages/cava-socios';

// Cavas Corporativas B2B
import CavasCorporativasDashboard from '@/pages/cavas-corporativas/CavasCorporativasDashboard';

// Catalogo Ampliado / Gobierno Corporativo
import CatalogoAmpliadoDashboard from '@/pages/catalogo-ampliado/CatalogoAmpliadoDashboard';

// Costos y Márgenes (FASE 1C-3D)
import CostosMargenes from '@/pages/comercial/CostosMargenes';
import CatalogoEnriquecido from '@/pages/comercial/CatalogoEnriquecido';

// Motor de Precios IA y Benchmark (FASE 1C-3I-D)
import PricingIA from '@/pages/comercial/PricingIA';

// P3-02: Sync Monitor SQL-First
import SyncMonitor from '@/pages/SyncMonitor';

import { isAuthenticated } from '@/lib/auth';

/**
 * Redirección del catch-all: evita el logout espurio al navegar a rutas
 * desconocidas. Si hay sesión activa → tablero; si no → login.
 */
function CatchAllRedirect() {
  return isAuthenticated()
    ? <Navigate to="/tablero-ejecutivo" replace />
    : <Navigate to="/login" replace />;
}

// Portal de Proveedores (Subproyecto separado)
import PortalProveedoresApp from '@/portal/App';

// Portal de Inteligencia Comercial IA (Subproyecto separado)
import PortalInteligenciaApp from '@/portal-inteligencia/App';
import ComingSoonPage from '@/pages/ComingSoonPage';
import DashboardEjecutivo from './pages/DashboardEjecutivo';
import CentroExcepciones from './pages/CentroExcepciones';
import AdminHub from './pages/AdminHub';
import IAAsistente from './pages/IAAsistente';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
          <Route path="/worker-console" element={<ProtectedRoute><WorkerConsole /></ProtectedRoute>} />
          <Route path="/admin" element={<AdminHub />} />
          <Route path="/admin/centro-excepciones" element={<CentroExcepciones />} />
          <Route path="/admin/dashboard-ejecutivo" element={<DashboardEjecutivo />} />
            {/* Portales Externos (sin auth del CRM) - DEBEN IR PRIMERO */}
            <Route path="/portal-proveedores/*" element={<PortalProveedoresApp />} />
            <Route path="/inteligencia-comercial/*" element={<PortalInteligenciaApp />} />
            
            {/* Auth Pages */}
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            
            {/* CRM Principal (requiere auth) */}
            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route index element={<Navigate to="/tablero-ejecutivo" replace />} />
              <Route path="dashboard" element={<Navigate to="/reportes" replace />} />
              <Route path="servidores" element={<Servidores />} />
              <Route path="reportes" element={<Reportes />} />
              <Route path="ia" element={<IAAsistente />} />
              <Route path="compras" element={<Compras />} />
              <Route path="comercial" element={<Comercial />} />
              {/* Rutas Comercial/Ventas - Integración Menú SQL (FASE 1A) */}
              <Route path="comercial/clientes" element={<Navigate to="/crm/cuentas" replace />} />
              {/* FASE 1C-3D: Costos y Márgenes */}
              <Route path="comercial/costos-margenes" element={<CostosMargenes />} />
              <Route path="comercial/catalogo-enriquecido" element={<CatalogoEnriquecido />} />
              {/* FASE 1C-3I-D: Motor de Precios IA y Benchmark */}
              <Route path="comercial/pricing-ia" element={<PricingIA />} />
              {/* Rutas alternativas comercial/crm → crm principal */}
              <Route path="comercial/crm/cuentas" element={<Navigate to="/crm/cuentas" replace />} />
              <Route path="comercial/crm/solicitudes" element={<Navigate to="/crm/solicitudes-alta" replace />} />
              {/* CRM Enterprise */}
              <Route path="crm" element={<Navigate to="/crm/dashboard" replace />} />
              <Route path="crm/dashboard" element={<CRMDashboard />} />
              <Route path="crm/leads" element={<LeadsPage />} />
              <Route path="crm/oportunidades" element={<OportunidadesPage />} />
              <Route path="crm/pipeline" element={<PipelinePage />} />
              {/* CRM Comercial (Enterprise-Grade) */}
              <Route path="crm/cuentas" element={<CuentasPage />} />
              <Route path="crm/solicitudes-alta" element={<SolicitudesAltaPage />} />
              <Route path="crm/cotizaciones" element={<CotizacionesPage />} />
              <Route path="crm/pedidos" element={<PedidosPage />} />
              <Route path="crm/remisiones" element={<RemisionesPage />} />
              {/* CRM Fases 6-15 */}
              <Route path="crm/actividades" element={<ActividadesPage />} />
              <Route path="crm/operaciones" element={<OperacionesPage />} />
              <Route path="crm/implementaciones" element={<ImplementacionesPage />} />
              <Route path="crm/postventa" element={<PostventaPage />} />
              <Route path="crm/kpis" element={<KPIsPage />} />
              <Route path="tablero-ejecutivo" element={<TableroEjecutivo />} />
              <Route path="catalogo-consultas" element={<CatalogoConsultas />} />
              <Route path="explorador-bd" element={<ExploradorBD />} />
              <Route path="alertas" element={<Alertas />} />
              <Route path="usuarios" element={<Usuarios />} />
              <Route path="proveedores" element={<Proveedores />} />
              {/* Nuevos módulos ERP */}
              <Route path="finanzas" element={<Finanzas />} />
              <Route path="produccion" element={<Produccion />} />
              <Route path="produccion/tablajeria" element={<TablajeriaDashboard />} />
              <Route path="produccion/tablajeria/plantillas" element={<PlantillasPage />} />
              <Route path="produccion/tablajeria/ordenes" element={<OrdenesPage />} />
              <Route path="produccion/tablajeria/captura-directa" element={<CapturaDirectaPage />} />
              {/* Rutas alternativas para tablajería */}
              <Route path="tablajeria" element={<TablajeriaDashboard />} />
              <Route path="tablajeria/dashboard" element={<TablajeriaDashboard />} />
              <Route path="tablajeria/ordenes" element={<OrdenesPage />} />
              <Route path="tablajeria/captura-directa" element={<CapturaDirectaPage />} />
              <Route path="tablajeria/plantillas" element={<PlantillasPage />} />
              <Route path="tablajeria/lotes-proveedor" element={<LotesProveedorPage />} />
              {/* Cava de Socios */}
              <Route path="cava-socios" element={<CavaSociosDashboard />} />
              <Route path="cava-socios/socios" element={<SociosList />} />
              <Route path="cava-socios/socios/nuevo" element={<SocioForm />} />
              <Route path="cava-socios/socios/:id" element={<SocioDetail />} />
              <Route path="cava-socios/socios/:id/editar" element={<SocioForm />} />
              <Route path="cava-socios/inventario" element={<InventarioCava />} />
              <Route path="cava-socios/consumos" element={<ConsumosCava />} />
              <Route path="cava-socios/auditoria-ciega" element={<BlindAuditCava />} />
              {/* Cavas Corporativas B2B - reglas y RBAC permanecen en backend */}
              <Route path="cavas-corporativas" element={<CavasCorporativasDashboard />} />
              {/* Catalogo Ampliado - frontend consume exclusivamente /api/catalogo-ampliado */}
              <Route path="catalogo-ampliado" element={<CatalogoAmpliadoDashboard />} />
              <Route path="recursos-humanos" element={<RecursosHumanos />} />
              <Route path="importador-rh" element={<ImportadorRH />} />
              <Route path="reportes-bi" element={<ReportesBI />} />
              <Route path="mis-tareas" element={<MisTareas />} />
              <Route path="catalogos" element={<Catalogos />} />
              <Route path="scheduler" element={<Scheduler />} />
              <Route path="automatizaciones" element={<AuditoriasProgramadas />} />
              <Route path="auditorias-programadas" element={<Navigate to="/automatizaciones" replace />} />
              <Route path="centro-control" element={<CentroControl />} />
              <Route path="configuracion/asignaciones" element={<ConfigAsignaciones />} />
              <Route path="admin/dba-credential" element={<DBACredentialManager />} />
              <Route path="admin/configuracion-operativa" element={<ConfiguracionOperativaUnidades />} />
              <Route path="admin/calendario-corporativo" element={<CalendarioCorporativo />} />
              <Route path="admin/sync-monitor" element={<SyncMonitor />} />
              {/* Módulos Satélites */}
              <Route path="super-caja" element={<SuperCajaPage />} />
              <Route path="comandero" element={<ComanderoPage />} />
              <Route path="coa" element={<COAHome />} />

              {/* Módulos registrados pendientes de implementación */}
              <Route path="pos/generico" element={<ComingSoonPage title="Punto de Venta" />} />
              <Route path="pos/caja" element={<ComingSoonPage title="Caja POS" />} />
              <Route path="compras/proveedores" element={<ComingSoonPage title="Proveedores de Compras" />} />
              <Route path="compras/ordenes" element={<ComingSoonPage title="Órdenes de Compra" />} />
              <Route path="inventarios/existencias" element={<ComingSoonPage title="Existencias de Inventario" />} />
              <Route path="edarsa-go" element={<ComingSoonPage title="EDARSA GO" />} />
              <Route path="edarsa-go/links" element={<ComingSoonPage title="Links de Pago" />} />
              <Route path="portal/proveedores" element={<Navigate to="/portal-proveedores" replace />} />
              <Route path="portal/comisionistas" element={<ComingSoonPage title="Portal Comisionistas" />} />
              <Route path="portal/clientes" element={<ComingSoonPage title="Portal Clientes" />} />
              <Route path="chef-ia" element={<ComingSoonPage title="Chef IA" />} />
              {/* Redirect /operativo → /reportes (Dashboard Operativo ahora es tab dentro de Operaciones) */}
              <Route path="operativo" element={<Navigate to="/reportes?tab=operativo" replace />} />
            </Route>
            
            {/* Catch-all global - DEBE IR AL FINAL y FUERA del Layout.
                IMPORTANTE: si el usuario está autenticado, una ruta desconocida
                (ej. ítem de menú aún sin pantalla) NO debe expulsarlo al login;
                se le envía al tablero. Solo si NO hay sesión va a /login. */}
            <Route path="*" element={<CatchAllRedirect />} />
          </Routes>
          
          <Toaster position="top-right" richColors />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
