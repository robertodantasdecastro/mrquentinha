"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

import type { ClientTemplateType } from "@/types/template";

type ClientTemplateContextData = {
  template: ClientTemplateType;
};

const ClientTemplateContext = createContext<ClientTemplateContextData>({
  template: "client-classic",
});

export const useClientTemplate = () => useContext(ClientTemplateContext);

export function ClientTemplateProvider({
  children,
  initialTemplate = "client-classic",
}: {
  children: React.ReactNode;
  initialTemplate?: ClientTemplateType;
}) {
  const [template, setTemplate] = useState<ClientTemplateType>(initialTemplate);

  useEffect(() => {
    setTemplate(initialTemplate);
  }, [initialTemplate]);

  useEffect(() => {
    document.documentElement.setAttribute("data-client-template", template);
  }, [template]);

  return (
    <ClientTemplateContext.Provider value={{ template }}>
      {children}
    </ClientTemplateContext.Provider>
  );
}
