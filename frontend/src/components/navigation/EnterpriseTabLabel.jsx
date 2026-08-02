import React from "react";

import tabRegistry from "../../config/enterpriseTabRegistry.json";
import {
  isNewNavigationItem
} from "../../config/enterpriseNavigationRegistry";
import EnterpriseStatusBadge from "./EnterpriseStatusBadge";

export default function EnterpriseTabLabel({
  tabId,
  children
}) {
  const tab = (tabRegistry.tabs || []).find(
    item => item.id === tabId
  );

  if (!tab) {
    return <span>{children}</span>;
  }

  const status = tab.status || "comingSoon";

  return (
    <span className="inline-flex items-center gap-2">
      <span>{children}</span>

      <EnterpriseStatusBadge
        status={status}
        isNew={isNewNavigationItem({
          ...tab,
          status
        })}
        compact
      />
    </span>
  );
}
