import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import Login from '@/pages/Login';
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
import ReportesBI from '@/pages/ReportesBI';
import MisTareas from '@/pages/MisTareas';
import { isAuthenticated } from '@/lib/auth';

// Portal de Proveedores (Subproyecto separado)
import PortalProveedoresApp from '@/portal/App';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Portal de Proveedores - Ruta separada */}
          <Route path="/portal-proveedores/*" element={<PortalProveedoresApp />} />
          
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/tablero-ejecutivo" replace />} />
            <Route path="dashboard" element={<Navigate to="/reportes" replace />} />
            <Route path="servidores" element={<Servidores />} />
            <Route path="reportes" element={<Reportes />} />
            <Route path="compras" element={<Compras />} />
            <Route path="comercial" element={<Comercial />} />
            <Route path="tablero-ejecutivo" element={<TableroEjecutivo />} />
            <Route path="catalogo-consultas" element={<CatalogoConsultas />} />
            <Route path="explorador-bd" element={<ExploradorBD />} />
            <Route path="alertas" element={<Alertas />} />
            <Route path="usuarios" element={<Usuarios />} />
            <Route path="proveedores" element={<Proveedores />} />
            {/* Nuevos módulos ERP */}
            <Route path="finanzas" element={<Finanzas />} />
            <Route path="produccion" element={<Produccion />} />
            <Route path="recursos-humanos" element={<RecursosHumanos />} />
            <Route path="reportes-bi" element={<ReportesBI />} />
            <Route path="mis-tareas" element={<MisTareas />} />
          </Route>
          
          <Route path="*" element={<Navigate to={isAuthenticated() ? "/reportes" : "/login"} replace />} />
        </Routes>
      </BrowserRouter>
      
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
