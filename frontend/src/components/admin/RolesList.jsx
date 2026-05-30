// /app/frontend/src/components/admin/RolesList.jsx
// Componente de listado de roles con fallback robusto

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Shield, Users, RefreshCw, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';

// ROLES POR DEFECTO: Se usan si la API falla (500, 403, timeout)
const ROLES_DEFAULT = [
  { id: 1, nombre_rol: 'Administrador', activo: true, permisos: ['all'] },
  { id: 2, nombre_rol: 'Usuario', activo: true, permisos: ['read'] },
  { id: 3, nombre_rol: 'Supervisor', activo: true, permisos: ['read', 'write'] }
];

const LOCALSTORAGE_KEY = 'edarsa_roles_cache';

const RolesList = () => {
  const [roles, setRoles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [usandoFallback, setUsandoFallback] = useState(false);

  // Guardar roles en localStorage para caché
  const guardarEnCache = (rolesData) => {
    try {
      localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(rolesData));
    } catch (e) {
      console.warn('[RolesList] No se pudo guardar en localStorage:', e);
    }
  };

  // Recuperar roles desde localStorage
  const recuperarDeCache = () => {
    try {
      const cached = localStorage.getItem(LOCALSTORAGE_KEY);
      if (cached) {
        return JSON.parse(cached);
      }
    } catch (e) {
      console.warn('[RolesList] Error leyendo caché:', e);
    }
    return null;
  };

  // Cargar roles con fallback robusto
  const cargarRoles = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get('/roles');
      const rolesData = response.data?.roles || response.data || [];
      
      if (rolesData.length > 0) {
        setRoles(rolesData);
        setUsandoFallback(false);
        guardarEnCache(rolesData); // Actualizar caché
      } else {
        // API respondió pero sin datos - usar fallback
        throw new Error('API retornó lista vacía');
      }
    } catch (err) {
      const statusCode = err.response?.status;
      console.warn(`[RolesList] Error ${statusCode || 'RED'} cargando roles:`, err.message);
      
      // FALLBACK ESCALONADO:
      // 1. Primero intentar localStorage
      const cachedRoles = recuperarDeCache();
      if (cachedRoles && cachedRoles.length > 0) {
        console.log('[RolesList] Usando roles desde caché local');
        setRoles(cachedRoles);
        setError(`Usando datos en caché (Error ${statusCode || 'de red'})`);
      } else {
        // 2. Si no hay caché, usar roles estáticos por defecto
        console.log('[RolesList] Usando roles por defecto estáticos');
        setRoles(ROLES_DEFAULT);
        setError(`Usando roles por defecto (Error ${statusCode || 'de red'})`);
      }
      setUsandoFallback(true);
    } finally {
      // CRÍTICO: SIEMPRE detener loading para evitar UI congelada
      setIsLoading(false);
    }
  };

  useEffect(() => {
    cargarRoles();
  }, []);

  // Renderizado de loading
  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="flex items-center justify-center gap-3">
            <RefreshCw className="h-6 w-6 animate-spin text-zinc-400" />
            <span className="text-zinc-500">Cargando roles...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Roles del Sistema
          </CardTitle>
          <p className="text-sm text-zinc-500 mt-1">
            {roles.length} rol(es) configurado(s)
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={cargarRoles}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </CardHeader>
      
      <CardContent>
        {/* Alerta de fallback */}
        {usandoFallback && (
          <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <span className="text-sm text-amber-600">
              {error || 'Mostrando datos de respaldo'}
            </span>
          </div>
        )}

        {/* Lista de roles */}
        <div className="space-y-3">
          {roles.length === 0 ? (
            <div className="text-center py-8 text-zinc-500">
              <Users className="h-12 w-12 mx-auto mb-3 text-zinc-300" />
              <p>No hay roles configurados</p>
            </div>
          ) : (
            roles.map((rol) => (
              <div 
                key={rol.id} 
                className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg border"
              >
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-zinc-400" />
                  <div>
                    <p className="font-medium">{rol.nombre_rol || rol.name}</p>
                    <p className="text-xs text-zinc-500">ID: {rol.id}</p>
                  </div>
                </div>
                <Badge 
                  variant={rol.activo !== false ? 'default' : 'secondary'}
                  className={rol.activo !== false ? 'bg-green-500/20 text-green-700' : ''}
                >
                  {rol.activo !== false ? 'Activo' : 'Inactivo'}
                </Badge>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default RolesList;
