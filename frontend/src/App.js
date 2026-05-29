import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/contexts/AuthContext';
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

// CRM Enterprise
import CRMDashboard from '@/pages/crm/CRMDashboard';
import LeadsPage from '@/pages/crm/LeadsPage';
import OportunidadesPage from '@/pages/crm/OportunidadesPage';
import PipelinePage from '@/pages/crm/PipelinePage';
// CRM Comercial (Enterprise-Grade)
import CuentasPage from '@/pages/crm/CuentasPage';
import SolicitudesAltaPage from '@/pages/crm/SolicitudesAltaPage';
import CotizacionesPage from '@/pages/crm/CotizacionesPage';
import PedidosPage from '@/pages/crm/PedidosPage';
import RemisionesPage from '@/pages/crm/RemisionesPage';

// Tablajería
import TablajeriaDashboard from '@/pages/tablajeria/TablajeriaDashboard';
import PlantillasPage from '@/pages/tablajeria/PlantillasPage';
import OrdenesPage from '@/pages/tablajeria/OrdenesPage';
import CapturaDirectaPage from '@/pages/tablajeria/CapturaDirectaPage';

// Cava de Socios
import { CavaSociosDashboard, SociosList, SocioDetail, SocioForm } from '@/pages/cava-socios';

// Costos y Márgenes (FASE 1C-3D)
import CostosMargenes from '@/pages/comercial/CostosMargenes';

// Motor de Precios IA y Benchmark (FASE 1C-3I-D)
import PricingIA from '@/pages/comercial/PricingIA';

import { isAuthenticated } from '@/lib/auth';

// Portal de Proveedores (Subproyecto separado)
import PortalProveedoresApp from '@/portal/App';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
            {/* Portal de Proveedores - Ruta separada */}
            <Route path="/portal-proveedores/*" element={<PortalProveedoresApp />} />
          
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/tablero-ejecutivo" replace />} />
            <Route path="dashboard" element={<Navigate to="/reportes" replace />} />
            <Route path="servidores" element={<Servidores />} />
            <Route path="reportes" element={<Reportes />} />
            <Route path="compras" element={<Compras />} />
            <Route path="comercial" element={<Comercial />} />
            {/* Rutas Comercial/Ventas - Integración Menú SQL (FASE 1A) */}
            <Route path="comercial/clientes" element={<Navigate to="/crm/cuentas" replace />} />
            {/* FASE 1C-3D: Costos y Márgenes */}
            <Route path="comercial/costos-margenes" element={<CostosMargenes />} />
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
            {/* Cava de Socios */}
            <Route path="cava-socios" element={<CavaSociosDashboard />} />
            <Route path="cava-socios/socios" element={<SociosList />} />
            <Route path="cava-socios/socios/nuevo" element={<SocioForm />} />
            <Route path="cava-socios/socios/:id" element={<SocioDetail />} />
            <Route path="cava-socios/socios/:id/editar" element={<SocioForm />} />
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
            {/* Redirect /operativo → /reportes (Dashboard Operativo ahora es tab dentro de Operaciones) */}
            <Route path="operativo" element={<Navigate to="/reportes?tab=operativo" replace />} />
          </Route>
          
          <Route path="*" element={<Navigate to={isAuthenticated() ? "/reportes" : "/login"} replace />} />
          </Routes>
          
          <Toaster position="top-right" richColors />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
