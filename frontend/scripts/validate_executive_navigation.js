const fs = require('fs');
const path = require('path');

const frontendRoot = path.resolve(__dirname, '..');
const srcRoot = path.join(frontendRoot, 'src');

const appPath = path.join(srcRoot, 'App.js');
const tableroPath = path.join(srcRoot, 'pages', 'TableroEjecutivo.js');
const adminPath = path.join(srcRoot, 'pages', 'DashboardEjecutivo.js');

const menuCandidates = [
  path.join(srcRoot, 'config', 'enterpriseMenuConfig.js'),
  path.join(srcRoot, 'config', 'enterpriseNavigationRegistry.json'),
  path.join(srcRoot, 'config', 'menuFallback.js'),
];

function readRequired(file) {
  if (!fs.existsSync(file)) {
    throw new Error(`EXECUTIVE_GUARD: falta archivo requerido: ${file}`);
  }

  return fs.readFileSync(file, 'utf8');
}

function assertCondition(condition, message) {
  if (!condition) {
    throw new Error(`EXECUTIVE_GUARD: ${message}`);
  }
}

const app = readRequired(appPath);
const tablero = readRequired(tableroPath);
readRequired(adminPath);

const compactApp = app.replace(/\s+/g, ' ');

assertCondition(
  /path=["']tablero-ejecutivo["'][^>]*element=\{<TableroEjecutivo\s*\/>\}/
    .test(compactApp),
  'la ruta /tablero-ejecutivo debe renderizar TableroEjecutivo'
);

assertCondition(
  /path=["']\/admin\/dashboard-ejecutivo["'][^>]*element=\{<DashboardEjecutivo\s*\/>\}/
    .test(compactApp),
  'la ruta administrativa debe renderizar DashboardEjecutivo'
);

assertCondition(
  !/path=["']tablero-ejecutivo["'][^>]*DashboardEjecutivo/
    .test(compactApp),
  'DashboardEjecutivo no puede ocupar la ruta principal del Menú Ejecutivo'
);

assertCondition(
  !/path=["']\/admin\/dashboard-ejecutivo["'][^>]*TableroEjecutivo/
    .test(compactApp),
  'TableroEjecutivo no puede ocupar la ruta administrativa'
);

const requiredTabs = ['comercial', 'finanzas', 'rh', 'bsc'];

for (const tab of requiredTabs) {
  const triggerPattern = new RegExp(
    `<TabsTrigger[^>]*value=["']${tab}["']`,
    'i'
  );

  const contentPattern = new RegExp(
    `<TabsContent[^>]*value=["']${tab}["']`,
    'i'
  );

  assertCondition(
    triggerPattern.test(tablero),
    `falta TabsTrigger del tab ejecutivo: ${tab}`
  );

  assertCondition(
    contentPattern.test(tablero),
    `falta TabsContent del tab ejecutivo: ${tab}`
  );
}

assertCondition(
  tablero.split('\n').length >= 1500,
  'TableroEjecutivo parece sustituido o truncado'
);

const menuText = menuCandidates
  .filter((file) => fs.existsSync(file))
  .map((file) => fs.readFileSync(file, 'utf8'))
  .join('\n');

assertCondition(
  menuText.includes('tablero-ejecutivo'),
  'el registro Enterprise debe conservar tablero-ejecutivo'
);

assertCondition(
  !menuText.includes('/admin/dashboard-ejecutivo'),
  'la ruta administrativa no puede publicarse en el menú Enterprise'
);

console.log('EXECUTIVE_NAVIGATION_GUARD=PASS');
console.log('MAIN_ROUTE=/tablero-ejecutivo');
console.log('MAIN_COMPONENT=TableroEjecutivo');
console.log('ADMIN_ROUTE=/admin/dashboard-ejecutivo');
console.log('ADMIN_COMPONENT=DashboardEjecutivo');
console.log('EXECUTIVE_TABS=comercial,finanzas,rh,bsc');
console.log('ADMIN_ROUTE_IN_ENTERPRISE_MENU=NO');
