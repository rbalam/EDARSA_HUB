import {
  hasMinimumRole,
  isAdminRole,
  isSuperAdmin,
  normalizeRole,
} from './roleUtils';


describe('roleUtils', () => {
  test.each([
    ['SuperAdministrador', 'SUPERADMIN'],
    ['SUPERADMIN', 'SUPERADMIN'],
    ['SUPER_ADMIN', 'SUPERADMIN'],
    ['SUPERADMINISTRADOR', 'SUPERADMIN'],
    ['Administrador', 'ADMIN'],
    ['ADMINISTRADOR', 'ADMIN'],
    ['admin', 'ADMIN'],
    ['Dirección', 'DIRECCION'],
    ['GERENTE_OPS', 'GERENTE'],
  ])('normaliza %s como %s', (input, expected) => {
    expect(normalizeRole(input)).toBe(expected);
  });

  test('resuelve el rol desde estructuras de usuario', () => {
    expect(normalizeRole({ CodigoRol: 'SUPERADMIN' }))
      .toBe('SUPERADMIN');

    expect(normalizeRole({ role: 'Administrador' }))
      .toBe('ADMIN');
  });

  test('SUPERADMIN hereda capacidades de ADMIN', () => {
    expect(isAdminRole('SUPERADMIN')).toBe(true);
    expect(isAdminRole('SuperAdministrador')).toBe(true);
    expect(hasMinimumRole('SUPERADMIN', 'Administrador'))
      .toBe(true);
  });

  test('ADMIN no hereda capacidades exclusivas de SUPERADMIN', () => {
    expect(isSuperAdmin('Administrador')).toBe(false);
    expect(hasMinimumRole('Administrador', 'SuperAdministrador'))
      .toBe(false);
  });

  test('no concede acceso por coincidencias parciales', () => {
    expect(isAdminRole('ADMIN_AUXILIAR')).toBe(false);
    expect(isAdminRole('NO_ADMIN')).toBe(false);
    expect(isSuperAdmin('SUPER_VISOR')).toBe(false);
  });

  test('rechaza roles desconocidos o vacíos', () => {
    expect(hasMinimumRole('ROL_DESCONOCIDO', 'Administrador'))
      .toBe(false);

    expect(hasMinimumRole(null, 'Administrador'))
      .toBe(false);
  });
});
