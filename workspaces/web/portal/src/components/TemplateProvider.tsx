"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export type TemplateType = "letsfit-clean" | "classic";

interface TemplateContextData {
  template: TemplateType;
}

const TemplateContext = createContext<TemplateContextData>({
  template: "classic",
});

export const useTemplate = () => useContext(TemplateContext);

export function PortalTemplateProvider({ children }: { children: React.ReactNode }) {
  const [template, setTemplate] = useState<TemplateType>(
    process.env.NEXT_PUBLIC_PORTAL_TEMPLATE === "letsfit-clean" ? "letsfit-clean" : "classic"
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-portal-template", template);
  }, [template]);

  return (
    <TemplateContext.Provider value={{ template }}>
      {children}
    </TemplateContext.Provider>
  );
}
