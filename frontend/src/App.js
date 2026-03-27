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
import Alertas from '@/pages/Alertas';
import Usuarios from '@/pages/Usuarios';
import { isAuthenticated } from '@/lib/auth';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="servidores" element={<Servidores />} />
            <Route path="reportes" element={<Reportes />} />
            <Route path="compras" element={<Compras />} />
            <Route path="comercial" element={<Comercial />} />
            <Route path="tablero-ejecutivo" element={<TableroEjecutivo />} />
            <Route path="catalogo-consultas" element={<CatalogoConsultas />} />
            <Route path="alertas" element={<Alertas />} />
            <Route path="usuarios" element={<Usuarios />} />
          </Route>
          
          <Route path="*" element={<Navigate to={isAuthenticated() ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </BrowserRouter>
      
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
