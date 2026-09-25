const fs = require("fs");
const path = require("path");

const FRONTEND = path.resolve(__dirname, "..");
const SRC = path.join(FRONTEND, "src");

const readJson = relative =>
  JSON.parse(
    fs.readFileSync(
      path.join(FRONTEND, relative),
      "utf8"
    )
  );

const registry = readJson(
  "src/config/enterpriseNavigationRegistry.json"
);

const tabRegistry = readJson(
  "src/config/enterpriseTabRegistry.json"
);

const routeBaseline = readJson(
  "src/config/enterpriseRouteBaseline.json"
);

const tabBaseline = readJson(
  "src/config/enterpriseTabBaseline.json"
);

const errors = [];
const fail = message => errors.push(message);

const validStatuses = new Set([
  "active",
  "comingSoon",
  "planned"
]);

const groupIds = new Set();
const sectionIds = new Set();

(registry.groups || []).forEach(group => {
  if (!group.id) {
    fail("GROUP_WITHOUT_ID");
    return;
  }

  if (groupIds.has(group.id)) {
    fail(`DUPLICATE_GROUP_ID:${group.id}`);
  }

  groupIds.add(group.id);

  (group.sections || []).forEach(section => {
    if (!section.id) {
      fail(`SECTION_WITHOUT_ID:${group.id}`);
      return;
    }

    if (sectionIds.has(section.id)) {
      fail(`DUPLICATE_SECTION_ID:${section.id}`);
    }

    sectionIds.add(section.id);
  });
});

if (groupIds.size !== 8) {
  fail(
    `ENTERPRISE_GROUP_COUNT:${groupIds.size}:EXPECTED_8`
  );
}

function validateLocation(identifier, metadata) {
  if (!groupIds.has(metadata.groupId)) {
    fail(
      `INVALID_GROUP:${identifier}:${metadata.groupId}`
    );
  }

  if (!sectionIds.has(metadata.sectionId)) {
    fail(
      `INVALID_SECTION:${identifier}:${metadata.sectionId}`
    );
  }

  if (!validStatuses.has(metadata.status)) {
    fail(
      `INVALID_STATUS:${identifier}:${metadata.status}`
    );
  }
}

const legacyIds = new Set(
  registry.legacyActiveIds || []
);

const expectedPaths = new Map();

Object.entries(
  registry.moduleMappings || {}
).forEach(([code, metadata]) => {
  validateLocation(`module:${code}`, metadata);
});

Object.entries(
  registry.menuMappings || {}
).forEach(([code, metadata]) => {
  validateLocation(`menu:${code}`, metadata);

  if (metadata.status === "active") {
    const hasReleaseDate =
      metadata.releasedAt &&
      !Number.isNaN(
        new Date(metadata.releasedAt).getTime()
      );

    if (!metadata.legacy && !hasReleaseDate) {
      fail(
        `ACTIVE_MENU_WITHOUT_RELEASE_DATE:${code}`
      );
    }

    if (
      metadata.legacy &&
      !legacyIds.has(code)
    ) {
      fail(
        `UNAUTHORIZED_LEGACY_FLAG:${code}`
      );
    }
  }

  if (
    metadata.status !== "active" &&
    metadata.releasedAt
  ) {
    fail(
      `NON_ACTIVE_WITH_RELEASE_DATE:${code}`
    );
  }

  if (metadata.expectedPath) {
    if (
      expectedPaths.has(metadata.expectedPath)
    ) {
      fail(
        `DUPLICATE_EXPECTED_PATH:${metadata.expectedPath}:` +
        `${expectedPaths.get(metadata.expectedPath)}:${code}`
      );
    }

    expectedPaths.set(
      metadata.expectedPath,
      code
    );
  }
});

const plannedIds = new Set();

(registry.plannedItems || []).forEach(item => {
  validateLocation(item.id, item);

  if (plannedIds.has(item.id)) {
    fail(`DUPLICATE_PLANNED_ID:${item.id}`);
  }

  plannedIds.add(item.id);

  if (item.status !== "planned") {
    fail(
      `PLANNED_ITEM_INVALID_STATUS:${item.id}`
    );
  }

  if (
    item.path ||
    item.expectedPath
  ) {
    fail(
      `PLANNED_ITEM_WITH_ROUTE:${item.id}`
    );
  }
});

function sourceFiles(root) {
  const output = [];

  function walk(directory) {
    fs.readdirSync(
      directory,
      { withFileTypes: true }
    ).forEach(entry => {
      if (
        [
          "node_modules",
          "build",
          "dist",
          "graphify-out"
        ].includes(entry.name)
      ) {
        return;
      }

      const full = path.join(
        directory,
        entry.name
      );

      if (entry.isDirectory()) {
        walk(full);
        return;
      }

      if (
        !/\.(js|jsx|ts|tsx)$/.test(entry.name) ||
        entry.name.includes(".bak")
      ) {
        return;
      }

      output.push(full);
    });
  }

  walk(root);
  return output;
}

const routePattern =
  /<Route\b[^>]*?\bpath\s*=\s*["']([^"']+)["']/gis;

const tabPattern =
  /<TabsTrigger\b[^>]*>|<[A-Za-z][A-Za-z0-9_.-]*\b(?=[^>]*\brole\s*=\s*["']tab["'])[^>]*>/gis;

const valuePattern =
  /\bvalue\s*=\s*["']([^"']+)["']/i;

const testIdPattern =
  /\bdata-testid\s*=\s*["']([^"']+)["']/i;

const enterpriseTabPattern =
  /\bdata-enterprise-tab-id\s*=\s*["']([^"']+)["']/i;

const normalizeRoute = route => {
  const clean = String(route || "").trim();

  if (clean === "*") return clean;

  return clean.startsWith("/")
    ? clean
    : `/${clean}`;
};

const currentRoutes = new Set();
const currentTabs = [];

sourceFiles(SRC).forEach(file => {
  const relative =
    "frontend/" +
    path
      .relative(FRONTEND, file)
      .split(path.sep)
      .join("/");

  const content = fs.readFileSync(file, "utf8");

  let match;

  while (
    (match = routePattern.exec(content)) !== null
  ) {
    currentRoutes.add(
      normalizeRoute(match[1])
    );
  }

  const tabCounters = {};

  while (
    (match = tabPattern.exec(content)) !== null
  ) {
    const tag = match[0];

    const valueMatch =
      valuePattern.exec(tag);

    const testIdMatch =
      testIdPattern.exec(tag);

    const identity = valueMatch
      ? valueMatch[1]
      : (
          testIdMatch
            ? testIdMatch[1]
            : "tab"
        );

    const baseSignature =
      `${relative}|${identity}`;

    tabCounters[baseSignature] =
      (tabCounters[baseSignature] || 0) + 1;

    currentTabs.push({
      signature:
        `${baseSignature}|${tabCounters[baseSignature]}`,
      file: relative,
      enterpriseTabId:
        enterpriseTabPattern.exec(tag)?.[1] ||
        null
    });
  }
});

const baselineRoutes = new Set(
  routeBaseline.routes || []
);

const exemptions = new Set(
  (registry.routeExemptions || []).map(
    item =>
      typeof item === "string"
        ? item
        : item.path
  )
);

currentRoutes.forEach(route => {
  if (baselineRoutes.has(route)) return;
  if (expectedPaths.has(route)) return;
  if (exemptions.has(route)) return;

  fail(
    `NEW_ROUTE_WITHOUT_ENTERPRISE_CLASSIFICATION:${route}`
  );
});

const baselineTabs = new Set(
  tabBaseline.signatures || []
);

const registeredTabs = new Map(
  (tabRegistry.tabs || []).map(tab => [
    tab.id,
    tab
  ])
);

currentTabs.forEach(tab => {
  if (baselineTabs.has(tab.signature)) {
    return;
  }

  if (!tab.enterpriseTabId) {
    fail(
      `NEW_TAB_WITHOUT_ENTERPRISE_ID:${tab.signature}`
    );
    return;
  }

  const metadata =
    registeredTabs.get(tab.enterpriseTabId);

  if (!metadata) {
    fail(
      `NEW_TAB_NOT_REGISTERED:${tab.enterpriseTabId}`
    );
    return;
  }

  validateLocation(
    `tab:${tab.enterpriseTabId}`,
    metadata
  );
});

registeredTabs.forEach((tab, tabId) => {
  validateLocation(`tab:${tabId}`, tab);

  if (!tab.parentScreen && !tab.parentRoute) {
    fail(`TAB_WITHOUT_PARENT:${tabId}`);
  }

  if (tab.status === "active") {
    const validRelease =
      tab.releasedAt &&
      !Number.isNaN(
        new Date(tab.releasedAt).getTime()
      );

    if (!validRelease) {
      fail(
        `ACTIVE_TAB_WITHOUT_RELEASE_DATE:${tabId}`
      );
    }
  }
});

const layout = fs.readFileSync(
  path.join(SRC, "pages", "Layout.js"),
  "utf8"
);

if (
  !layout.includes(
    "const USE_ENTERPRISE_MENU = true"
  )
) {
  fail("ENTERPRISE_MENU_NOT_ENABLED");
}

if (
  !layout.includes(
    "EnterpriseNavigationMenu"
  )
) {
  fail(
    "CANONICAL_ENTERPRISE_COMPONENT_NOT_USED"
  );
}

if (errors.length > 0) {
  console.error(
    "ENTERPRISE_NAVIGATION_GUARDIAN=FAIL"
  );

  errors.forEach(error =>
    console.error(`ERROR=${error}`)
  );

  process.exit(1);
}

console.log(
  "ENTERPRISE_NAVIGATION_GUARDIAN=PASS"
);
console.log(`GROUPS=${groupIds.size}`);
console.log(
  `MODULE_MAPPINGS=${
    Object.keys(
      registry.moduleMappings || {}
    ).length
  }`
);
console.log(
  `MENU_MAPPINGS=${
    Object.keys(
      registry.menuMappings || {}
    ).length
  }`
);
console.log(
  `PLANNED_ITEMS=${
    (registry.plannedItems || []).length
  }`
);
console.log(
  `REGISTERED_FUTURE_TABS=${
    registeredTabs.size
  }`
);
console.log(
  `NEW_BADGE_DAYS=${
    registry.newBadgeDays
  }`
);
