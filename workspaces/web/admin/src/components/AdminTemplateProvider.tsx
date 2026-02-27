"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

import type { AdminTemplateType } from "@/types/template";

type AdminTemplateContextData = {
  template: AdminTemplateType;
};

const AdminTemplateContext = createContext<AdminTemplateContextData>({
  template: "admin-classic",
});

export const useAdminTemplate = () => useContext(AdminTemplateContext);

export function AdminTemplateProvider({
  children,
  initialTemplate = "admin-classic",
}: {
  children: React.ReactNode;
  initialTemplate?: AdminTemplateType;
}) {
  const [template, setTemplate] = useState<AdminTemplateType>(initialTemplate);

  useEffect(() => {
    setTemplate(initialTemplate);
  }, [initialTemplate]);

  useEffect(() => {
    document.documentElement.setAttribute("data-admin-template", template);
  }, [template]);

  return (
    <AdminTemplateContext.Provider value={{ template }}>
      {children}
    </AdminTemplateContext.Provider>
  );
}
