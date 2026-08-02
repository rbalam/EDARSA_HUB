import registry from "./enterpriseNavigationRegistry.json";

const VALID_STATUSES = new Set([
  "active",
  "comingSoon",
  "planned"
]);

const clean = value => String(value || "").trim();

const sorter = (left, right) => {
  const leftOrder = Number(left?.order ?? 999999);
  const rightOrder = Number(right?.order ?? 999999);

  if (leftOrder !== rightOrder) {
    return leftOrder - rightOrder;
  }

  return String(left?.label || "").localeCompare(
    String(right?.label || ""),
    "es",
    { sensitivity: "base" }
  );
};

function createGroups() {
  return registry.groups
    .slice()
    .sort(sorter)
    .map(group => ({
      ...group,
      sections: (group.sections || [])
        .slice()
        .sort(sorter)
        .map(section => ({
          ...section,
          items: []
        }))
    }));
}

function locate(groups, groupId, sectionId) {
  const group = groups.find(item => item.id === groupId);

  if (!group) return null;

  const section = (group.sections || []).find(
    item => item.id === sectionId
  );

  return section ? { group, section } : null;
}

function heuristic(modulo, menu = null) {
  const value = [
    menu?.codigo,
    menu?.nombre,
    menu?.descripcion,
    menu?.ruta
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  const result = (groupId, sectionId) => ({
    groupId,
    sectionId,
    status: "comingSoon",
    needsClassification: true
  });

  if (/(portal|comandero|punto de venta|\bpos\b|cava|super caja|edarsa go)/.test(value)) {
    return result("portales-satelites", "aplicaciones-satelite");
  }

  if (/(finanz|contab|banco|tesorer|comision|costo|margen|rentab|chef)/.test(value)) {
    return result("finanzas-rentabilidad", "costos-rentabilidad");
  }

  if (/(compra|inventar|almacen|tablaj|produccion)/.test(value)) {
    return result("operaciones-abasto", "inventarios-almacenes");
  }

  if (/(crm|cliente|lead|oportunidad|cotiza|pedido|remision|postventa)/.test(value)) {
    return result("comercial-clientes", "crm");
  }

  if (/(recurso humano|empleado|colaborador|persona|organizacion|socio)/.test(value)) {
    return result("personas-organizacion", "recursos-humanos");
  }

  if (/(calidad|auditor|control|proyecto|workflow|marketing|incidencia)/.test(value)) {
    return result("control-calidad-gestion", "control-operativo");
  }

  if (/(direccion|ejecutivo|inteligencia|analit|reporte|pronostico|\bia\b)/.test(value)) {
    return result("direccion-inteligencia", "analitica-bi");
  }

  return result("plataforma-integraciones", "administracion-seguridad");
}

function sourceIsActive(value) {
  return (
    value !== false &&
    value !== 0 &&
    value !== "0"
  );
}

function createItem({
  id,
  metadata,
  modulo,
  menu,
  source
}) {
  const path = clean(
    menu?.ruta ||
    metadata?.expectedPath ||
    modulo?.ruta ||
    modulo?.url_externa
  ) || null;

  const activeInSql = sourceIsActive(
    menu ? menu.activo : modulo?.activo
  );

  let status = metadata?.status || "active";

  if (!VALID_STATUSES.has(status)) {
    status = "comingSoon";
  }

  if (!activeInSql || !path) {
    status = "comingSoon";
  }

  return {
    id,
    label:
      metadata?.label ||
      menu?.nombre ||
      modulo?.nombre ||
      id,
    path,
    icon:
      menu?.icono ||
      modulo?.icono ||
      "Grid3X3",
    order:
      metadata?.order ??
      menu?.orden ??
      modulo?.orden ??
      999999,
    status,
    activeInSql,
    favoriteEligible:
      status === "active" &&
      activeInSql &&
      Boolean(path),
    releasedAt: metadata?.releasedAt || null,
    fixedZone: metadata?.fixedZone || null,
    cluster: metadata?.cluster || null,
    needsClassification:
      metadata?.needsClassification === true,
    source,
    moduloCodigo: clean(modulo?.codigo),
    menuCodigo: clean(menu?.codigo),
    keywords: [
      metadata?.label,
      menu?.codigo,
      menu?.nombre,
      menu?.descripcion,
      menu?.ruta,
      metadata?.cluster,
      status === "active" ? "activo" : null,
      status === "comingSoon" ? "proximamente pronto" : null,
      status === "planned" ? "planeado futuro" : null,
      metadata?.releasedAt ? "new nuevo" : null
    ].filter(Boolean)
  };
}

export function buildEnterpriseNavigation(sqlModules = []) {
  const groups = createGroups();
  const fixedItems = [];
  const unclassified = [];
  const seenIds = new Set();
  const seenPaths = new Set();

  const add = (metadata, item) => {
    if (!metadata || !item || seenIds.has(item.id)) {
      return;
    }

    if (item.path && seenPaths.has(item.path)) {
      unclassified.push({
        ...item,
        reason: "DUPLICATE_PATH"
      });
      return;
    }

    if (item.fixedZone === "my-space") {
      fixedItems.push(item);
      seenIds.add(item.id);

      if (item.path) {
        seenPaths.add(item.path);
      }

      return;
    }

    const location = locate(
      groups,
      metadata.groupId,
      metadata.sectionId
    );

    if (!location) {
      unclassified.push({
        ...item,
        reason: "INVALID_GROUP_OR_SECTION"
      });
      return;
    }

    location.section.items.push(item);
    seenIds.add(item.id);

    if (item.path) {
      seenPaths.add(item.path);
    }

    if (item.needsClassification) {
      unclassified.push({
        ...item,
        reason: "HEURISTIC_CLASSIFICATION"
      });
    }
  };

  (Array.isArray(sqlModules) ? sqlModules : []).forEach(
    (modulo, moduleIndex) => {
      if (!modulo || modulo.visible === false) {
        return;
      }

      const moduleCode = clean(modulo.codigo);
      const moduleMetadata =
        registry.moduleMappings[moduleCode] ||
        heuristic(modulo);

      const menus = Array.isArray(modulo.menus)
        ? modulo.menus
        : [];

      if (menus.length === 0) {
        const item = createItem({
          id: `module:${moduleCode || modulo.id || moduleIndex}`,
          metadata: {
            ...moduleMetadata,
            status: "comingSoon"
          },
          modulo,
          menu: null,
          source: "SQL_CANONICAL_RBAC"
        });

        add(moduleMetadata, item);
        return;
      }

      menus.forEach((menuItem, menuIndex) => {
        if (!menuItem || menuItem.visible === false) {
          return;
        }

        const menuCode = clean(menuItem.codigo);

        const metadata =
          registry.menuMappings[menuCode] ||
          heuristic(modulo, menuItem);

        const item = createItem({
          id: `menu:${menuCode || menuItem.id || `${moduleIndex}-${menuIndex}`}`,
          metadata,
          modulo,
          menu: menuItem,
          source: "SQL_CANONICAL_RBAC"
        });

        add(metadata, item);
      });
    }
  );

  const authorizedGroupIds = new Set(
    groups
      .filter(group =>
        (group.sections || []).some(
          section => (section.items || []).length > 0
        )
      )
      .map(group => group.id)
  );

  (registry.plannedItems || [])
    .filter(item => authorizedGroupIds.has(item.groupId))
    .forEach(metadata => {
      const location = locate(
        groups,
        metadata.groupId,
        metadata.sectionId
      );

      if (!location) return;

      location.section.items.push({
        id: metadata.id,
        label: metadata.label,
        path: null,
        icon: "Sparkles",
        order: metadata.order,
        status: "planned",
        activeInSql: false,
        favoriteEligible: false,
        releasedAt: null,
        fixedZone: null,
        cluster: null,
        source: "ENTERPRISE_ARCHITECTURE",
        keywords: [
          metadata.label,
          "planeado",
          "futuro"
        ]
      });
    });

  groups.forEach(group => {
    (group.sections || []).forEach(section => {
      section.items.sort(sorter);
    });
  });

  fixedItems.sort(sorter);

  return {
    groups,
    fixedItems,
    unclassified
  };
}

export function flattenEnterpriseNavigation(groups = []) {
  return groups.flatMap(group =>
    (group.sections || []).flatMap(section =>
      (section.items || []).map(item => ({
        ...item,
        groupId: group.id,
        groupLabel: group.label,
        groupIcon: group.icon,
        sectionId: section.id,
        sectionLabel: section.label
      }))
    )
  );
}

export function isNewNavigationItem(item, now = new Date()) {
  if (
    !item ||
    item.status !== "active" ||
    !item.releasedAt
  ) {
    return false;
  }

  const releasedAt = new Date(item.releasedAt);

  if (Number.isNaN(releasedAt.getTime())) {
    return false;
  }

  const age = now.getTime() - releasedAt.getTime();

  const maximum =
    Number(registry.newBadgeDays || 30) *
    24 *
    60 *
    60 *
    1000;

  return age >= 0 && age <= maximum;
}

export function getEnterpriseRegistry() {
  return registry;
}

export default registry;
