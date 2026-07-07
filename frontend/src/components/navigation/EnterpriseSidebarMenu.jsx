import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Activity,
  BarChart3,
  Bell,
  Brain,
  Building,
  Building2,
  Calculator,
  CalendarCheck,
  ChevronDown,
  ChevronRight,
  ClipboardList,
  Clock,
  Contact,
  Database,
  DollarSign,
  Grid3X3,
  LayoutDashboard,
  Megaphone,
  Package,
  Percent,
  PieChart,
  Plug,
  RefreshCw,
  Search,
  Server,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Smartphone,
  Star,
  Store,
  Table,
  UserCog,
  Users,
  Utensils,
  Wine,
  Boxes
} from "lucide-react";

import {
  flattenEnterpriseMenu,
  defaultFavoriteMenuIds
} from "../../config/enterpriseMenuConfig";
import { fetchMenuFavoritos, saveMenuFavoritos } from "../../services/menuContextService";

const ICONS = {
  Activity,
  BarChart3,
  Bell,
  Brain,
  Building,
  Building2,
  Calculator,
  CalendarCheck,
  ClipboardList,
  Clock,
  Contact,
  Database,
  DollarSign,
  Grid3X3,
  LayoutDashboard,
  Megaphone,
  Package,
  Percent,
  PieChart,
  Plug,
  RefreshCw,
  Search,
  Server,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Smartphone,
  Star,
  Store,
  Table,
  UserCog,
  Users,
  Utensils,
  Wine,
  Boxes
};

function getIcon(name, fallback = Grid3X3) {
  return ICONS[name] || fallback;
}

function groupBySection(items) {
  return items.reduce((acc, item) => {
    const section = item.section || "General";
    if (!acc[section]) acc[section] = [];
    acc[section].push(item);
    return acc;
  }, {});
}

function getSqlMenuLabel(moduloCodigo, modulo, menu) {
  const menuCodigo = String(menu?.codigo || "").toLowerCase();

  if (
    moduloCodigo === "INVENTARIOS" &&
    menuCodigo === "inventarios.dashboard" &&
    menu?.ruta === "/reportes"
  ) {
    return modulo?.nombre || "Inventarios / Operaciones";
  }

  return menu?.nombre || menu?.codigo;
}

function normalizeSqlEnterpriseGroups(sqlMenus = []) {
  if (!Array.isArray(sqlMenus) || sqlMenus.length === 0) return null;

  const normalizeId = (value, fallback) => {
    const raw = String(value || fallback || "modulo").trim().toLowerCase();
    return raw
      .replace(/[^a-z0-9_.-]+/g, "-")
      .replace(/^-+|-+$/g, "") || "modulo";
  };

  return sqlMenus
    .map((modulo, index) => {
      if (!modulo || modulo.visible === false) return null;

      const codigo = String(modulo.codigo || "").trim();
      const menus = Array.isArray(modulo.menus) ? modulo.menus : [];
      const groupId = normalizeId(codigo || modulo.id, `sql-${index}`);

      const children = menus
        .filter(m => m && m.visible !== false && m.ruta)
        .map((m, menuIndex) => ({
          id: normalizeId(m.codigo || m.id, `${groupId}-${menuIndex}`),
          label: getSqlMenuLabel(codigo, modulo, m),
          path: m.ruta,
          icon: m.icono || modulo.icono || "Grid3X3",
          section: modulo.nombre || codigo || "Modulo SQL",
          source: "SQL_CANONICAL_RBAC",
          keywords: [
            m.nombre,
            m.codigo,
            m.requiere_permiso,
            modulo.nombre,
            codigo
          ].filter(Boolean)
        }));

      const fallbackPath = modulo.ruta || modulo.url_externa;
      if (children.length === 0 && fallbackPath) {
        children.push({
          id: groupId,
          label: modulo.nombre || codigo || `Modulo ${index + 1}`,
          path: fallbackPath,
          icon: modulo.icono || "Grid3X3",
          section: modulo.nombre || codigo || "Modulo SQL",
          source: "SQL_CANONICAL_RBAC",
          keywords: [modulo.nombre, codigo].filter(Boolean)
        });
      }

      if (children.length === 0) return null;

      return {
        id: groupId,
        label: modulo.nombre || codigo || `Modulo ${index + 1}`,
        icon: modulo.icono || "Grid3X3",
        color: modulo.color || "#71717A",
        description: modulo.descripcion || "",
        source: "SQL_CANONICAL_RBAC",
        children
      };
    })
    .filter(Boolean);
}

const MENU_FAVORITES_STORAGE_KEY = "edarsahub_menu_favorites";

const cacheMenuFavorites = (rutas) => {
  try {
    localStorage.setItem(
      MENU_FAVORITES_STORAGE_KEY,
      JSON.stringify(Array.isArray(rutas) ? rutas : [])
    );
  } catch {
    // cache local no disponible
  }
};

export default function EnterpriseSidebarMenu({
  user,
  collapsed = false,
  sqlMenus = null
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;
  
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState({
    inteligencia: true,
    operacion: true,
    finanzas: false,
    personas: false,
    gestion: false,
    corporativo: false,
    integraciones: false,
    administracion: true,
    satelites: true
  });

  const [favoriteIds, setFavoriteIds] = useState(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(MENU_FAVORITES_STORAGE_KEY) || "null");
      return Array.isArray(stored) && stored.length ? stored : defaultFavoriteMenuIds;
    } catch {
      return defaultFavoriteMenuIds;
    }
  });

  useEffect(() => {
    let cancelled = false;

    fetchMenuFavoritos()
      .then(result => {
        if (cancelled) return;

        const sqlFavorites = Array.isArray(result?.rutas) ? result.rutas : [];
        if (result?.has_configuracion || sqlFavorites.length > 0) {
          setFavoriteIds(sqlFavorites);
          cacheMenuFavorites(sqlFavorites);
        }
      })
      .catch(err => {
        console.warn("[MENU_FAVORITES] No se pudieron cargar favoritos SQL:", err?.message || err);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const sqlMenusForRender = Array.isArray(sqlMenus) && sqlMenus.length > 0
    ? sqlMenus
    : null;

  const groups = useMemo(() => {
    const sqlGroups = normalizeSqlEnterpriseGroups(sqlMenusForRender);

    // SQL canonico actual es la unica fuente del menu Enterprise.
    // Sin respuesta SQL autorizada, no hay fallback visual por rol ni cache.
    if (Array.isArray(sqlGroups)) {
      return sqlGroups;
    }

    return [];
  }, [sqlMenusForRender]);

  const flat = useMemo(() => flattenEnterpriseMenu(groups), [groups]);

  const getFavoriteKey = (item) => item?.path || item?.id;

  const favorites = useMemo(() => {
    const unique = [];
    favoriteIds.forEach(id => {
      const found = flat.find(x => getFavoriteKey(x) === id || x.id === id);
      if (found && !unique.some(x => x.path === found.path)) unique.push(found);
    });

    return unique.slice(0, 6);
  }, [flat, favoriteIds]);

  const searchResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];

    const results = flat.filter(item => {
      const haystack = [
        item.label,
        item.groupLabel,
        item.section,
        item.path,
        ...(item.keywords || [])
      ].join(" ").toLowerCase();

      return haystack.includes(q);
    });

    const unique = [];
    results.forEach(item => {
      if (!unique.some(x => x.path === item.path)) unique.push(item);
    });

    return unique.slice(0, 12);
  }, [query, flat]);

  const go = (item) => {
    if (!item?.path || item.comingSoon) return;
    navigate(item.path);
  };

  const toggleGroup = id => {
    setExpanded(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const toggleFavorite = (item, event) => {
    event?.stopPropagation?.();

    const favoriteKey = getFavoriteKey(item);

    if (!favoriteKey || item.comingSoon) return;

    setFavoriteIds(prev => {
      const current = Array.isArray(prev) ? prev : [];
      const exists = current.includes(favoriteKey) || current.includes(item.id);
      const next = exists
        ? current.filter(id => id !== favoriteKey && id !== item.id)
        : [favoriteKey, ...current].slice(0, 12);

      cacheMenuFavorites(next);

      saveMenuFavoritos(next)
        .then(result => {
          const sqlFavorites = Array.isArray(result?.rutas) ? result.rutas : [];
          if (result?.has_configuracion || sqlFavorites.length > 0 || next.length === 0) {
            setFavoriteIds(sqlFavorites);
            cacheMenuFavorites(sqlFavorites);
          }
        })
        .catch(err => {
          console.warn("[MENU_FAVORITES] No se pudieron guardar favoritos SQL:", err?.message || err);
        });
      return next;
    });
  };

  const renderItem = (item, compact = false) => {
    const Icon = getIcon(item.icon);
    const active = currentPath && item.path && currentPath.startsWith(item.path) && !item.comingSoon;
    const comingSoon = !!item.comingSoon;
    const favoriteKey = getFavoriteKey(item);
    const isFavorite = favoriteIds.includes(favoriteKey) || favoriteIds.includes(item.id);

    return (
      <div
        key={`${compact ? "compact" : "item"}-${item.id}`}
        data-testid={`menu-item-${item.id}`}
        className={[
          "w-full flex items-center gap-2 rounded-xl text-left transition-all group",
          compact ? "px-3 py-2 text-sm" : "px-4 py-2.5 text-[15px]",
          comingSoon
            ? "text-zinc-600 cursor-not-allowed"
            : active
              ? "bg-white/12 text-white shadow-sm"
              : "text-zinc-400 hover:bg-white/8 hover:text-white"
        ].join(" ")}
        title={comingSoon ? `${item.label} — Próximamente` : item.label}
      >
        <button
          type="button"
          onClick={() => go(item)}
          disabled={comingSoon}
          aria-disabled={comingSoon}
          className="flex items-start gap-3 flex-1 min-w-0 text-left disabled:cursor-not-allowed"
        >
          <Icon size={compact ? 17 : 20} className="shrink-0 mt-0.5" />
          {!collapsed && (
            <span className="font-medium leading-snug flex-1 flex items-start justify-between gap-2 min-w-0">
              <span className="whitespace-normal break-words">{item.label}</span>
              {comingSoon && (
                <span
                  data-testid={`menu-coming-soon-${item.id}`}
                  className="shrink-0 text-[9px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-white/5 text-zinc-500 border border-white/10"
                >
                  Pronto
                </span>
              )}
            </span>
          )}
        </button>

        {!comingSoon && !collapsed && (
          <button
            type="button"
            onClick={(event) => toggleFavorite(item, event)}
            data-testid={`menu-favorite-${item.id}`}
            title={isFavorite ? "Quitar de favoritos" : "Agregar a favoritos"}
            aria-label={isFavorite ? "Quitar de favoritos" : "Agregar a favoritos"}
            className="shrink-0 p-1 rounded-lg text-zinc-600 hover:text-amber-400 hover:bg-white/10 transition-all"
          >
            <Star
              size={compact ? 15 : 16}
              className={isFavorite ? "fill-amber-400 text-amber-400" : ""}
            />
          </button>
        )}
      </div>
    );
  };

  if (collapsed) {
    return (
      <nav className="px-2 py-3 space-y-2" data-testid="enterprise-sidebar-collapsed">
        {groups.map(group => {
          const Icon = getIcon(group.icon);
          return (
            <button
              key={group.id}
              type="button"
              onClick={() => toggleGroup(group.id)}
              className="w-full h-11 flex items-center justify-center rounded-xl text-zinc-400 hover:bg-white/8 hover:text-white"
              title={group.label}
            >
              <Icon size={22} />
            </button>
          );
        })}
      </nav>
    );
  }

  return (
    <div className="space-y-4" data-testid="enterprise-sidebar-menu">
      <div className="relative px-3">
        <Search
          size={18}
          className="absolute left-6 top-1/2 -translate-y-1/2 text-zinc-500"
        />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Buscar módulo o tablero..."
          data-testid="enterprise-menu-search"
          className="w-full bg-zinc-900/80 border border-white/10 rounded-xl py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-amber-500/60 transition-all"
        />
      </div>

      {searchResults.length > 0 && (
        <div className="px-3 space-y-1">
          <p className="px-2 text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
            Resultados
          </p>
          {searchResults.map(item => renderItem(item, true))}
        </div>
      )}

      {!query && favorites.length > 0 && (
        <div className="px-3 space-y-1">
          <p className="px-2 text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
            Favoritos
          </p>
          {favorites.map(item => renderItem(item, true))}
        </div>
      )}

      {!query && groups.map(group => {
        const Icon = getIcon(group.icon);
        const isExpanded = expanded[group.id] !== false;
        const groupedChildren = groupBySection(group.children || []);

        return (
          <div key={group.id} className="px-3 space-y-1">
            <button
              type="button"
              onClick={() => toggleGroup(group.id)}
              className="w-full flex items-center gap-2 px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500 hover:text-zinc-300 transition-all"
              data-testid={`menu-group-${group.id}`}
            >
              <Icon size={16} className="shrink-0" />
              <span className="flex-1">{group.label}</span>
              <span className="text-zinc-600">{isExpanded ? "▾" : "▸"}</span>
            </button>

            {isExpanded && Object.entries(groupedChildren).map(([section, items]) => (
              <div key={`${group.id}-${section}`} className="space-y-1">
                {section && section !== group.label && (
                  <p className="px-4 pt-1 text-[10px] font-medium text-zinc-600">
                    {section}
                  </p>
                )}
                {items.map(item => renderItem(item))}
              </div>
            ))}
          </div>
        );
      })}

      {!query && groups.length === 0 && (
        <div className="px-5 py-6 text-sm text-zinc-500">
          No hay menús disponibles para este contexto.
        </div>
      )}
    </div>
  );
}
