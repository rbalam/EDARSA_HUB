import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, LogIn, Mail, Lock, Building2 } from 'lucide-react';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post('/auth/login', { email, password });
      // login() del AuthContext ya mapea a loginWithData (setea token en memoria)
      login(response.data.token, response.data.user);
      toast.success('Inicio de sesión exitoso');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Columna izquierda - Visual corporativa */}
      <div 
        className="hidden lg:flex lg:w-1/2 xl:w-[55%] relative bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1766642672890-0ae5a0439d92?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjh8MHwxfHNlYXJjaHwzfHxjb3Jwb3JhdGUlMjBvZmZpY2UlMjBidWlsZGluZyUyMG1vZGVybiUyMGdsYXNzJTIwYXJjaGl0ZWN0dXJlJTIwYnVzaW5lc3N8ZW58MHx8fHwxNzc3NDc5NzQzfDA&ixlib=rb-4.1.0&q=85')`
        }}
      >
        {/* Overlay oscuro azulado */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/90 via-slate-800/85 to-emerald-900/80" />
        
        {/* Contenido de la columna izquierda */}
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          {/* Logo superior */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center border border-emerald-500/30">
              <Building2 className="h-5 w-5 text-emerald-400" />
            </div>
            <span className="text-white/90 font-medium text-lg">EDARSA</span>
          </div>
          
          {/* Contenido principal */}
          <div className="space-y-6">
            <h1 className="text-4xl xl:text-5xl font-bold text-white leading-tight">
              EDARSA HUB
            </h1>
            <p className="text-xl text-emerald-300/90 font-medium">
              Sistema Integral de Gestión Operativa
            </p>
            <p className="text-slate-300/80 text-lg max-w-md leading-relaxed">
              Centraliza tus operaciones, indicadores, procesos y decisiones en una sola plataforma.
            </p>
            
            {/* Indicadores */}
            <div className="flex gap-8 pt-4">
              <div className="space-y-1">
                <p className="text-3xl font-bold text-white">5+</p>
                <p className="text-sm text-slate-400">Módulos integrados</p>
              </div>
              <div className="space-y-1">
                <p className="text-3xl font-bold text-white">100%</p>
                <p className="text-sm text-slate-400">Datos en tiempo real</p>
              </div>
              <div className="space-y-1">
                <p className="text-3xl font-bold text-white">24/7</p>
                <p className="text-sm text-slate-400">Disponibilidad</p>
              </div>
            </div>
          </div>
          
          {/* Footer izquierdo */}
          <div className="text-slate-500 text-sm">
            © 2026 EDARSA HUB. Todos los derechos reservados.
          </div>
        </div>
      </div>

      {/* Columna derecha - Formulario de login */}
      <div className="w-full lg:w-1/2 xl:w-[45%] flex items-center justify-center bg-slate-50 p-6 sm:p-8 lg:p-12" data-testid="login-card">
        {/* Header móvil - solo visible en pantallas pequeñas */}
        <div className="lg:hidden absolute top-0 left-0 right-0 bg-slate-900 p-4 flex items-center justify-center gap-2">
          <Building2 className="h-5 w-5 text-emerald-400" />
          <span className="text-white font-medium">EDARSA HUB</span>
        </div>

        <div className="w-full max-w-md lg:mt-0 mt-16">
          {/* Título del formulario */}
          <div className="mb-8">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-800 mb-2">
              Iniciar Sesión
            </h2>
            <p className="text-slate-500">
              Ingresa tus credenciales para acceder al sistema
            </p>
          </div>

          {/* Card de login */}
          <Card className="bg-white border-slate-200 shadow-lg shadow-slate-200/50">
            <CardContent className="p-6 sm:p-8">
              <form onSubmit={handleLogin} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-slate-700 font-medium">
                    Correo Electrónico
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="usuario@empresa.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      disabled={loading}
                      className="pl-10 bg-slate-50 border-slate-200 text-slate-800 placeholder:text-slate-400 focus:border-emerald-500 focus:ring-emerald-500"
                      data-testid="login-email-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-slate-700 font-medium">
                    Contraseña
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      disabled={loading}
                      className="pl-10 bg-slate-50 border-slate-200 text-slate-800 placeholder:text-slate-400 focus:border-emerald-500 focus:ring-emerald-500"
                      data-testid="login-password-input"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-slate-800 hover:bg-slate-900 text-white h-11 text-base font-medium transition-all duration-200"
                  disabled={loading}
                  data-testid="login-submit-button"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Iniciando sesión...
                    </>
                  ) : (
                    <>
                      Ingresar
                      <LogIn className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              </form>

              {/* Enlace de recuperación de contraseña */}
              <div className="mt-4 text-center">
                <Link 
                  to="/forgot-password" 
                  className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
                  data-testid="forgot-password-link"
                >
                  ¿Olvidaste tu contraseña?
                </Link>
              </div>

              {/* Credenciales de prueba */}
              <div className="mt-6 pt-5 border-t border-slate-100">
                <p className="text-xs text-slate-400 text-center mb-2">Credenciales de prueba</p>
                <div className="bg-slate-50 rounded-lg p-3 text-center">
                  <p className="text-sm text-slate-600">
                    <span className="text-slate-400">Usuario:</span>{' '}
                    <span className="font-mono text-slate-700">admin@inventario.com</span>
                  </p>
                  <p className="text-sm text-slate-600">
                    <span className="text-slate-400">Contraseña:</span>{' '}
                    <span className="font-mono text-slate-700">admin123</span>
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Footer móvil */}
          <p className="lg:hidden mt-6 text-center text-xs text-slate-400">
            © 2026 EDARSA HUB. Todos los derechos reservados.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
