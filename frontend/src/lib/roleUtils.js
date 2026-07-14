/**
 * Normalización canónica de roles para controles visuales.
 *
 * La autorización real siempre debe validarse también en backend.
 */

const ROLE_ALIASES = Object.freeze({
  USUARIO: 'USUARIO',
  USER: 'USUARIO',

  VISOR: 'VISOR',
  OPERADOR: 'OPERADOR',
  AUDITOR: 'AUDITOR',
  MAQUILADOR: 'MAQUILADOR',
  SUPERVISOR: 'SUPERVISOR',

  GERENTE: 'GERENTE',
  GERENTEOPS: 'GERENTE',

  TESORERIA: 'TESORERIA',

  DIRECTOR: 'DIRECCION',
  DIRECCION: 'DIRECCION',

  ADMIN: 'ADMIN',
  ADMINISTRADOR: 'ADMIN',

  SUPERADMIN: 'SUPERADMIN',
  SUPERADMINISTRADOR: 'SUPERADMIN',
});


export const ROLE_LEVELS = Object.freeze({
  USUARIO: 10,
  VISOR: 10,
  OPERADOR: 20,
  AUDITOR: 30,
  MAQUILADOR: 40,
  SUPERVISOR: 50,
  GERENTE: 60,
  TESORERIA: 60,
  DIRECCION: 80,
  ADMIN: 90,
  SUPERADMIN: 100,
});


const extractRoleValue = (userOrRole) => {
  if (typeof userOrRole === 'string') {
    return userOrRole;
  }

  if (!userOrRole || typeof userOrRole !== 'object') {
    return '';
  }

  return (
    userOrRole.role_code
    || userOrRole.CodigoRol
    || userOrRole.codigo_rol
    || userOrRole.role
    || userOrRole.rol
    || userOrRole.NombreRol
    || userOrRole.nombre_rol
    || userOrRole.sec_rol
    || ''
  );
};


export const normalizeRole = (userOrRole) => {
  const rawRole = extractRoleValue(userOrRole);

  const compactRole = String(rawRole)
    .trim()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/[\s_-]+/g, '');

  return ROLE_ALIASES[compactRole] || '';
};


export const isSuperAdmin = (userOrRole) => {
  return normalizeRole(userOrRole) === 'SUPERADMIN';
};


export const isAdminRole = (userOrRole) => {
  const role = normalizeRole(userOrRole);
  return role === 'ADMIN' || role === 'SUPERADMIN';
};


export const hasMinimumRole = (userOrRole, requiredRole) => {
  const current = normalizeRole(userOrRole);
  const required = normalizeRole(requiredRole);

  if (!current || !required) {
    return false;
  }

  const currentLevel = ROLE_LEVELS[current];
  const requiredLevel = ROLE_LEVELS[required];

  if (
    typeof currentLevel !== 'number'
    || typeof requiredLevel !== 'number'
  ) {
    return false;
  }

  return currentLevel >= requiredLevel;
};
