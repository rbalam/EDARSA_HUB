import React, { useMemo, useState } from "react";
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
  enterpriseMenuGroups,
  flattenEnterpriseMenu,
  filterEnterpriseMenuByRole,
  defaultFavoriteMenuIds
} from "../../config/enterpriseMenuConfig";

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

export default function EnterpriseSidebarMenu({
  user,
  collapsed = false
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
      const stored = JSON.parse(localStorage.getItem("edarsahub_menu_favorites") || "null");
      return Array.isArray(stored) && stored.length ? stored : defaultFavoriteMenuIds;
    } catch {
      return defaultFavoriteMenuIds;
    }
  });

  const groups = useMemo(
    () => filterEnterpriseMenuByRole(enterpriseMenuGroups, user),
    [user]
  );

  const flat = useMemo(() => flattenEnterpriseMenu(groups), [groups]);

  const favorites = useMemo(() => {
    const unique = [];
    favoriteIds.forEach(id => {
      const found = flat.find(x => x.id === id);
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

    if (!item?.id || item.comingSoon) return;

    setFavoriteIds(prev => {
      const current = Array.isArray(prev) ? prev : [];
      const exists = current.includes(item.id);
      const next = exists
        ? current.filter(id => id !== item.id)
        : [item.id, ...current].slice(0, 12);

      localStorage.setItem("edarsahub_menu_favorites", JSON.stringify(next));
      return next;
    });
  };

  const renderItem = (item, compact = false) => {
    const Icon = getIcon(item.icon);
    const active = currentPath && item.path && currentPath.startsWith(item.path) && !item.comingSoon;
    const comingSoon = !!item.comingSoon;
    const isFavorite = favoriteIds.includes(item.id);

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
          className="flex items-center gap-3 flex-1 min-w-0 text-left disabled:cursor-not-allowed"
        >
          <Icon size={compact ? 17 : 20} className="shrink-0" />
          {!collapsed && (
            <span className="font-medium leading-tight flex-1 flex items-center justify-between gap-2 min-w-0">
              <span className="truncate">{item.label}</span>
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
    <nav className="px-4 py-4 space-y-5" data-testid="enterprise-sidebar-menu">
      {/* Buscador */}
      <div className="relative">
        <Search
          size={18}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"
        />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Buscar módulo o tablero..."
          data-testid="enterprise-menu-search"
          className="w-full bg-zinc-900/80 border border-white/10 rounded-xl py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-amber-500/60"
        />
      </div>

      {query.trim() ? (
        /* Resultados de búsqueda */
        <section className="space-y-2">
          <div className="text-xs font-bold tracking-widest text-amber-500 uppercase">
            Resultados
          </div>

          <div className="space-y-1">
            {searchResults.length ? (
              searchResults.map(item => renderItem(item, true))
            ) : (
              <div className="text-sm text-zinc-500 px-2 py-3">
                Sin resultados.
              </div>
            )}
          </div>
        </section>
      ) : (
        <>
          {/* Favoritos */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold tracking-widest text-amber-500 uppercase">
              <Star size={14} />
              Mis Favoritos
            </div>

            <div className="grid grid-cols-1 gap-1">
              {favorites.map(item => renderItem(item, true))}
            </div>
          </section>

          {/* Menú Enterprise */}
          <section className="space-y-2">
            <div className="text-xs font-bold tracking-widest text-zinc-500 uppercase">
              Menú Enterprise
            </div>

            {groups.map(group => {
              const Icon = getIcon(group.icon);
              const open = expanded[group.id];
              const sections = groupBySection(group.children);

              return (
                <div key={group.id} className="rounded-2xl overflow-hidden" data-testid={`menu-group-${group.id}`}>
                  <button
                    onClick={() => toggleGroup(group.id)}
                    className="w-full flex items-center justify-between gap-3 px-4 py-3 rounded-2xl text-zinc-300 hover:bg-white/8 hover:text-white transition-all"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Icon
                        size={22}
                        className="shrink-0"
                        style={{ color: group.color }}
                      />

                      <div className="min-w-0 text-left">
                        <div className="font-bold leading-tight">
                          {group.label}
                        </div>
                        <div className="text-xs text-zinc-500 truncate">
                          {group.description}
                        </div>
                      </div>
                    </div>

                    {open ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                  </button>

                  {open && (
                    <div className="mt-1 ml-4 pl-3 border-l border-white/10 space-y-3">
                      {Object.entries(sections).map(([section, items]) => (
                        <div key={`${group.id}-${section}`} className="space-y-1">
                          {Object.keys(sections).length > 1 && (
                            <div className="px-4 pt-2 text-[11px] font-bold uppercase tracking-widest text-zinc-600">
                              {section}
                            </div>
                          )}

                          {items.map(item => renderItem(item))}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </section>
        </>
      )}
    </nav>
  );
}
