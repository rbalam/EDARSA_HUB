import React, {
  useEffect,
  useMemo,
  useState
} from "react";

import {
  useLocation,
  useNavigate
} from "react-router-dom";

import {
  Activity,
  BarChart3,
  Bell,
  Boxes,
  Building2,
  Calculator,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  Contact,
  Database,
  DollarSign,
  Grid3X3,
  LayoutDashboard,
  MapPin,
  Package,
  Percent,
  PieChart,
  Plug,
  Search,
  Server,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Star,
  Store,
  UserCog,
  Users,
  Utensils,
  Wine
} from "lucide-react";

import {
  buildEnterpriseNavigation,
  flattenEnterpriseNavigation,
  isNewNavigationItem
} from "../../config/enterpriseNavigationRegistry";

import {
  fetchMenuFavoritos,
  saveMenuFavoritos
} from "../../services/menuContextService";

import EnterpriseStatusBadge from "./EnterpriseStatusBadge";

const ICONS = {
  Activity,
  BarChart3,
  Bell,
  Boxes,
  Building2,
  Calculator,
  ClipboardList,
  Contact,
  Database,
  DollarSign,
  Grid3X3,
  LayoutDashboard,
  MapPin,
  Package,
  Percent,
  PieChart,
  Plug,
  Search,
  Server,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Star,
  Store,
  UserCog,
  Users,
  Utensils,
  Wine
};

const STORAGE_KEY = "edarsahub_menu_favorites";

function iconFor(name, fallback = Grid3X3) {
  return ICONS[name] || fallback;
}

function routeMatches(currentPath, itemPath) {
  if (!currentPath || !itemPath) return false;

  return (
    currentPath === itemPath ||
    currentPath.startsWith(`${itemPath}/`)
  );
}

function cacheFavorites(routes) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(
        Array.isArray(routes) ? routes : []
      )
    );
  } catch {
    // SQL conserva la fuente canónica.
  }
}

function unitLabel(unit) {
  if (!unit) return "Sin unidad seleccionada";
  if (typeof unit === "string") return unit;

  return (
    unit.UnidadNegocioNombre ||
    unit.NombreEmpresa ||
    unit.nombre ||
    unit.Nombre ||
    unit.codigo ||
    unit.Codigo ||
    unit.unidad_negocio_nombre ||
    unit.unidad_negocio_codigo ||
    unit.UnidadNegocioID ||
    unit.id ||
    "Unidad activa"
  );
}

const stripMenuSequence = value =>
  String(value ?? "")
    .replace(/^\s*\d+\.\s*/, "")
    .trim();

const normalizeSearchText = value =>
  String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

const ENTERPRISE_GROUP_STYLE = Object.freeze([
  {
    label: "Dirección e Inteligencia",
    description: "Dirección, inteligencia comercial, BI e IA",
    color: "#3B82F6"
  },
  {
    label: "Comercial y Clientes",
    description: "Ventas, CRM y ciclo comercial",
    color: "#F59E0B"
  },
  {
    label: "Operaciones y Abasto",
    description: "Compras, inventarios, producción y mantenimiento",
    color: "#F97316"
  },
  {
    label: "Finanzas y Rentabilidad",
    description: "Finanzas, tesorería, contabilidad y costos",
    color: "#10B981"
  },
  {
    label: "Personas y Organización",
    description: "RH, directorio y gobierno corporativo",
    color: "#8B5CF6"
  },
  {
    label: "Control, Calidad y Gestión",
    description: "Control operativo, auditoría, gestión y marketing",
    color: "#EC4899"
  },
  {
    label: "Plataforma e Integraciones",
    description: "Conexiones, automatización, datos y seguridad",
    color: "#06B6D4"
  },
  {
    label: "Portales y Aplicaciones Satélite",
    description: "Portales externos y aplicaciones satélite",
    color: "#F97316"
  }
]);

const VISIBLE_ACRONYMS = new Set([
  "API",
  "BI",
  "CRM",
  "EDARSA",
  "EDARSAHUB",
  "IA",
  "NEW",
  "POS",
  "RH",
  "SQL"
]);

const VISIBLE_CONNECTORS = new Set([
  "A",
  "AL",
  "CON",
  "DE",
  "DEL",
  "E",
  "EN",
  "LA",
  "LAS",
  "LOS",
  "PARA",
  "POR",
  "Y"
]);

const stripVisibleAccents = value =>
  String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

const formatVisibleLabel = value => {
  const clean = stripVisibleAccents(
    stripMenuSequence(value)
  ).trim();

  if (!clean) return "";

  const letters = clean.replace(
    /[^A-Za-z]/g,
    ""
  );

  if (
    !letters ||
    letters !== letters.toUpperCase()
  ) {
    return clean;
  }

  return clean
    .split(/\s+/)
    .map((token, index) => {
      const match = token.match(
        /^([^A-Za-z0-9]*)([A-Za-z0-9]+)([^A-Za-z0-9]*)$/
      );

      if (!match) return token;

      const [, prefix, core, suffix] = match;
      const upper = core.toUpperCase();

      if (
        VISIBLE_ACRONYMS.has(upper) ||
        /^\d+$/.test(core)
      ) {
        return `${prefix}${upper}${suffix}`;
      }

      if (
        index > 0 &&
        VISIBLE_CONNECTORS.has(upper)
      ) {
        return (
          `${prefix}${upper.toLowerCase()}${suffix}`
        );
      }

      return (
        `${prefix}` +
        `${core.charAt(0).toUpperCase()}` +
        `${core.slice(1).toLowerCase()}` +
        `${suffix}`
      );
    })
    .join(" ");
};

const getGroupStyle = (group, index) => {
  const configured =
    ENTERPRISE_GROUP_STYLE[index];

  return {
    label:
      configured?.label ||
      formatVisibleLabel(group?.label),

    description:
      configured?.description ||
      stripVisibleAccents(
        group?.description || ""
      ),

    color:
      configured?.color ||
      "#A1A1AA"
  };
};


export default function EnterpriseNavigationMenu({
  user,
  collapsed = false,
  sqlMenus = null,
  activeBusinessUnit = null
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;

  const [query, setQuery] = useState("");
  const [expandedGroupId, setExpandedGroupId] =
    useState(null);

  const [
    expandedSectionByGroup,
    setExpandedSectionByGroup
  ] = useState({});

  const [
    favoriteRoutes,
    setFavoriteRoutes
  ] = useState(() => {
    try {
      const stored = JSON.parse(
        localStorage.getItem(STORAGE_KEY) || "[]"
      );

      return Array.isArray(stored) ? stored : [];
    } catch {
      return [];
    }
  });

  const navigation = useMemo(
    () =>
      buildEnterpriseNavigation(
        Array.isArray(sqlMenus) ? sqlMenus : []
      ),
    [sqlMenus]
  );

  const flatItems = useMemo(
    () =>
      flattenEnterpriseNavigation(
        navigation.groups
      ),
    [navigation.groups]
  );

  const allItems = useMemo(
    () => [
      ...navigation.fixedItems,
      ...flatItems
    ],
    [navigation.fixedItems, flatItems]
  );

  const activeTrail = useMemo(
    () =>
      flatItems
        .filter(
          item =>
            item.status === "active" &&
            item.path &&
            routeMatches(currentPath, item.path)
        )
        .sort(
          (left, right) =>
            String(right.path).length -
            String(left.path).length
        )[0] || null,
    [currentPath, flatItems]
  );

  useEffect(() => {
    if (activeTrail) {
      setExpandedGroupId(activeTrail.groupId);

      setExpandedSectionByGroup(previous => ({
        ...previous,
        [activeTrail.groupId]:
          activeTrail.sectionId
      }));

      return;
    }

    if (
      !expandedGroupId &&
      navigation.groups.length > 0
    ) {
      const firstGroup =
        navigation.groups.find(group =>
          (group.sections || []).some(
            section =>
              (section.items || []).length > 0
          )
        );

      const firstSection =
        firstGroup?.sections?.find(
          section =>
            (section.items || []).length > 0
        );

      if (firstGroup) {
        setExpandedGroupId(firstGroup.id);
      }

      if (firstGroup && firstSection) {
        setExpandedSectionByGroup(previous => ({
          ...previous,
          [firstGroup.id]: firstSection.id
        }));
      }
    }
  }, [
    activeTrail,
    expandedGroupId,
    navigation.groups
  ]);

  useEffect(() => {
    let cancelled = false;

    fetchMenuFavoritos()
      .then(result => {
        if (cancelled) return;

        const routes = Array.isArray(result?.rutas)
          ? result.rutas
          : [];

        if (
          result?.has_configuracion ||
          routes.length > 0
        ) {
          setFavoriteRoutes(routes);
          cacheFavorites(routes);
        }
      })
      .catch(error => {
        console.warn(
          "[ENTERPRISE_FAVORITES] Error al cargar:",
          error?.message || error
        );
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (
      process.env.NODE_ENV === "development" &&
      navigation.unclassified.length > 0
    ) {
      console.error(
        "[ENTERPRISE_GUARDIAN] Clasificación pendiente:",
        navigation.unclassified
      );
    }
  }, [navigation.unclassified]);

  const favorites = useMemo(() => {
    const result = [];

    favoriteRoutes.forEach(route => {
      const found = allItems.find(
        item =>
          item.path === route &&
          item.favoriteEligible
      );

      if (
        found &&
        !result.some(
          item => item.path === found.path
        )
      ) {
        result.push(found);
      }
    });

    return result.slice(0, 12);
  }, [allItems, favoriteRoutes]);

  const searchResults = useMemo(() => {
    const normalized = normalizeSearchText(query.trim());

    if (!normalized) return [];

    return allItems
      .filter(item => {
        const haystack = normalizeSearchText(
          [
            item.label,
            item.groupLabel,
            item.sectionLabel,
            item.cluster,
            item.path,
            ...(item.keywords || [])
          ]
            .filter(Boolean)
            .join(" ")
        );

        return haystack.includes(normalized);
      })
      .slice(0, 30);
  }, [allItems, query]);

  const navigateTo = item => {
    if (
      item?.status !== "active" ||
      !item?.path
    ) {
      return;
    }

    navigate(item.path);
  };

  const toggleFavorite = (item, event) => {
    event?.stopPropagation?.();

    if (
      !item?.favoriteEligible ||
      !item?.path
    ) {
      return;
    }

    setFavoriteRoutes(previous => {
      const current = Array.isArray(previous)
        ? previous
        : [];

      const exists = current.includes(item.path);

      const next = exists
        ? current.filter(
            route => route !== item.path
          )
        : [item.path, ...current].slice(0, 12);

      cacheFavorites(next);

      saveMenuFavoritos(next)
        .then(result => {
          const sqlRoutes = Array.isArray(
            result?.rutas
          )
            ? result.rutas
            : [];

          if (
            result?.has_configuracion ||
            sqlRoutes.length > 0 ||
            next.length === 0
          ) {
            setFavoriteRoutes(sqlRoutes);
            cacheFavorites(sqlRoutes);
          }
        })
        .catch(error => {
          console.warn(
            "[ENTERPRISE_FAVORITES] Error al guardar:",
            error?.message || error
          );
        });

      return next;
    });
  };

  const toggleGroup = groupId => {
    setExpandedGroupId(previous =>
      previous === groupId ? null : groupId
    );
  };

  const toggleSection = (groupId, sectionId) => {
    setExpandedSectionByGroup(previous => ({
      ...previous,
      [groupId]:
        previous[groupId] === sectionId
          ? null
          : sectionId
    }));
  };

  const renderItem = (
    item,
    {
      compact = false,
      showBreadcrumb = false
    } = {}
  ) => {
    const Icon = iconFor(item.icon);

    const active =
      activeTrail?.id === item.id ||
      (
        item.fixedZone &&
        item.path === currentPath
      );

    const disabled =
      item.status !== "active" ||
      !item.path;

    const favorite =
      item.favoriteEligible &&
      favoriteRoutes.includes(item.path);

    return (
      <div
        key={`${compact ? "compact" : "item"}-${item.id}`}
        className={[
          "w-full rounded-xl transition-all",
          active
            ? "bg-white/12 text-white shadow-sm"
            : disabled
              ? "text-zinc-600"
              : "text-zinc-400 hover:bg-white/8 hover:text-white"
        ].join(" ")}
        data-testid={`enterprise-item-${item.id}`}
        data-enterprise-status={item.status}
      >
        <div className="flex items-center gap-2 px-3 py-2">
          <button
            type="button"
            onClick={() => navigateTo(item)}
            disabled={disabled}
            aria-disabled={disabled}
            className={[
              "flex min-w-0 flex-1 items-start gap-3 text-left",
              disabled
                ? "cursor-not-allowed"
                : "cursor-pointer"
            ].join(" ")}
          >
            <Icon
              size={compact ? 16 : 19}
              className="mt-0.5 shrink-0"
            />

            {!collapsed && (
              <span className="min-w-0 flex-1">
                {showBreadcrumb && (
                  <span className="mb-0.5 block text-[9px] text-zinc-600">
                    {item.groupLabel}
                    {item.sectionLabel
                      ? ` · ${item.sectionLabel}`
                      : ""}
                  </span>
                )}

                <span className="flex items-start justify-between gap-2">
                  <span className="break-words text-sm font-medium leading-snug">
                    {formatVisibleLabel(item.label)}
                  </span>

                  <EnterpriseStatusBadge
                    status={item.status}
                    isNew={isNewNavigationItem(item)}
                    compact={compact}
                  />
                </span>
              </span>
            )}
          </button>

          {!collapsed &&
            item.favoriteEligible &&
            item.path && (
              <button
                type="button"
                onClick={event =>
                  toggleFavorite(item, event)
                }
                title={
                  favorite
                    ? "Quitar de favoritos"
                    : "Agregar a favoritos"
                }
                aria-label={
                  favorite
                    ? "Quitar de favoritos"
                    : "Agregar a favoritos"
                }
                data-testid={`enterprise-favorite-${item.id}`}
                className="shrink-0 rounded-lg p-1 text-zinc-600 transition-all hover:bg-white/10 hover:text-amber-400"
              >
                <Star
                  size={15}
                  className={
                    favorite
                      ? "fill-amber-400 text-amber-400"
                      : ""
                  }
                />
              </button>
            )}
        </div>
      </div>
    );
  };

  const renderSectionItems = items => {
    const renderedClusters = new Set();

    return (items || []).flatMap(item => {
      if (!item.cluster) return [renderItem(item)];
      if (renderedClusters.has(item.cluster)) return [];

      renderedClusters.add(item.cluster);
      const clusterItems = items.filter(
        candidate => candidate.cluster === item.cluster
      );

      return [
        <div
          key={"enterprise-cluster-" + item.cluster}
          className="mt-2 rounded-lg border border-white/[0.05] bg-white/[0.02] px-2 py-2"
          data-testid="enterprise-item-cluster"
        >
          <p className="px-2 pb-1 text-[10px] font-bold uppercase tracking-[0.14em] text-zinc-600">
            {formatVisibleLabel(item.cluster)}
          </p>

          <div className="space-y-1">
            {clusterItems.map(clusterItem =>
              renderItem(clusterItem)
            )}
          </div>
        </div>
      ];
    });
  };

  const visibleGroups =
    navigation.groups.filter(group =>
      (group.sections || []).some(
        section =>
          (section.items || []).length > 0
      )
    );

  if (collapsed) {
    return (
      <nav
        className="space-y-2 px-2 py-3"
        data-testid="enterprise-navigation-collapsed"
      >
        {visibleGroups.map((group, groupIndex) => {
          const Icon = iconFor(group.icon);
          const groupStyle =
            getGroupStyle(group, groupIndex);

          return (
            <button
              key={group.id}
              type="button"
              onClick={() => toggleGroup(group.id)}
              className={[
                "flex h-11 w-full items-center justify-center rounded-xl transition-all",
                expandedGroupId === group.id
                  ? "bg-white/10 text-white"
                  : "text-zinc-400 hover:bg-white/8 hover:text-white"
              ].join(" ")}
              title={groupStyle.label}
            >
              <Icon
                size={21}
                style={{ color: groupStyle.color }}
              />
            </button>
          );
        })}
      </nav>
    );
  }

  return (
    <div
      className="flex flex-col gap-4"
      data-testid="enterprise-navigation-menu"
      data-user-present={Boolean(user)}
    >
      <section
        className="space-y-2 px-3"
        data-testid="enterprise-my-space"
      >
        <p className="px-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
          Mi espacio
        </p>

        {navigation.fixedItems.map(item =>
          renderItem(item, {
            compact: true
          })
        )}

        <div className="flex items-start gap-3 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2 text-zinc-500">
          <MapPin
            size={16}
            className="mt-0.5 shrink-0"
          />

          <span className="min-w-0">
            <span className="block text-[9px] uppercase tracking-wide text-zinc-600">
              Unidad de negocio activa
            </span>

            <span className="block break-words text-xs text-zinc-400">
              {unitLabel(activeBusinessUnit)}
            </span>
          </span>
        </div>

        <div className="space-y-1">
          <p className="flex items-center gap-2 px-2 pt-1 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
            <Star size={12} />
            Favoritos
          </p>

          {favorites.length > 0 ? (
            favorites.map(item =>
              renderItem(item, {
                compact: true
              })
            )
          ) : (
            <p className="px-3 py-2 text-xs text-zinc-600">
              No hay favoritos seleccionados.
            </p>
          )}
        </div>
      </section>

      <div className="order-first relative px-3">
        <Search
          size={17}
          className="absolute left-6 top-1/2 -translate-y-1/2 text-zinc-500"
        />

        <input
          value={query}
          onChange={event =>
            setQuery(event.target.value)
          }
          placeholder="Buscar menú o tab..."
          data-testid="enterprise-navigation-search"
          className="w-full rounded-xl border border-white/10 bg-zinc-900/80 py-2.5 pl-10 pr-3 text-sm text-white outline-none transition-all placeholder:text-zinc-500 focus:border-amber-500/60"
        />
      </div>

      {query && (
        <section className="order-first space-y-1 px-3">
          <p className="px-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
            Resultados
          </p>

          {searchResults.length > 0 ? (
            searchResults.map(item =>
              renderItem(item, {
                compact: true,
                showBreadcrumb: true
              })
            )
          ) : (
            <p className="px-3 py-3 text-xs text-zinc-600">
              No se encontraron coincidencias.
            </p>
          )}
        </section>
      )}

      {!query &&
        visibleGroups.map((group, groupIndex) => {
          const GroupIcon = iconFor(group.icon);
          const groupStyle =
            getGroupStyle(group, groupIndex);

          const groupExpanded =
            expandedGroupId === group.id;

          const visibleSections =
            (group.sections || []).filter(
              section =>
                (section.items || []).length > 0
            );

          return (
            <section
              key={group.id}
              className="space-y-1 px-3"
            >
              <button
                type="button"
                onClick={() => toggleGroup(group.id)}
                className={[
                  "flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left transition-all",
                  groupExpanded
                    ? "bg-white/[0.04] text-zinc-300"
                    : "text-zinc-500 hover:bg-white/[0.03] hover:text-zinc-300"
                ].join(" ")}
                data-testid={`enterprise-group-${group.id}`}
              >
                <GroupIcon
                  size={20}
                  strokeWidth={2}
                  className="mt-0.5 shrink-0"
                  style={{
                    color: groupStyle.color
                  }}
                />

                <span className="min-w-0 flex-1">
                  <span className="block text-[15px] font-semibold normal-case leading-tight text-zinc-200">
                    {groupStyle.label}
                  </span>

                  <span className="mt-1 block text-[11px] font-normal normal-case leading-snug text-zinc-500">
                    {groupStyle.description}
                  </span>
                </span>

                {groupExpanded ? (
                  <ChevronDown size={15} />
                ) : (
                  <ChevronRight size={15} />
                )}
              </button>

              {groupExpanded &&
                visibleSections.map(section => {
                  const sectionExpanded =
                    expandedSectionByGroup[
                      group.id
                    ] === section.id;

                  return (
                    <div
                      key={`${group.id}-${section.id}`}
                      className="space-y-1 pl-2"
                    >
                      <button
                        type="button"
                        onClick={() =>
                          toggleSection(
                            group.id,
                            section.id
                          )
                        }
                        className={[
                          "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px] font-semibold leading-snug transition-all",
                          sectionExpanded
                            ? "text-zinc-300"
                            : "text-zinc-600 hover:text-zinc-400"
                        ].join(" ")}
                        data-testid={`enterprise-section-${section.id}`}
                      >
                        <span className="flex-1">
                          {formatVisibleLabel(section.label)}
                        </span>

                        {sectionExpanded ? (
                          <ChevronDown size={14} />
                        ) : (
                          <ChevronRight size={14} />
                        )}
                      </button>

                      {sectionExpanded && (
                        <div className="space-y-1 pl-1">
                          {renderSectionItems(section.items)}
                        </div>
                      )}
                    </div>
                  );
                })}
            </section>
          );
        })}

      {!query &&
        visibleGroups.length === 0 && (
          <div className="px-5 py-6 text-sm text-zinc-500">
            No hay menús autorizados para este contexto.
          </div>
        )}
    </div>
  );
}
