"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import type { TemplateType } from "@/lib/portalTemplate";

interface TemplateContextData {
  template: TemplateType;
}

const TemplateContext = createContext<TemplateContextData>({
  template: "classic",
});

export const useTemplate = () => useContext(TemplateContext);

export function PortalTemplateProvider({
  children,
  initialTemplate = "classic",
}: {
  children: React.ReactNode;
  initialTemplate?: TemplateType;
}) {
  const [template, setTemplate] = useState<TemplateType>(initialTemplate);

  useEffect(() => {
    setTemplate(initialTemplate);
  }, [initialTemplate]);

  useEffect(() => {
    document.documentElement.setAttribute("data-portal-template", template);
  }, [template]);

  return (
    <TemplateContext.Provider value={{ template }}>
      {children}
    </TemplateContext.Provider>
  );
}
