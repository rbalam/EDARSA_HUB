import React from "react";

export default function EnterpriseStatusBadge({
  status = "active",
  isNew = false,
  compact = false
}) {
  const base = [
    "inline-flex shrink-0 items-center rounded-full border font-bold uppercase",
    compact
      ? "px-1.5 py-0.5 text-[8px]"
      : "px-2 py-0.5 text-[9px]"
  ].join(" ");

  if (status === "planned") {
    return (
      <span
        className={`${base} border-sky-500/25 bg-sky-500/10 text-sky-300`}
        data-enterprise-status="planned"
      >
        Planeado
      </span>
    );
  }

  if (status === "comingSoon") {
    return (
      <span
        className={`${base} border-white/10 bg-white/5 text-zinc-500`}
        data-enterprise-status="coming-soon"
      >
        Próximamente
      </span>
    );
  }

  if (isNew) {
    return (
      <span
        className={`${base} border-emerald-400/30 bg-emerald-400/15 text-emerald-300`}
        data-enterprise-status="new"
      >
        NEW
      </span>
    );
  }

  return null;
}
