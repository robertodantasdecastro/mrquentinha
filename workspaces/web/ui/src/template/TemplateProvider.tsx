"use client";

import { useEffect } from "react";
import type { PropsWithChildren } from "react";

type TemplateProviderProps = PropsWithChildren<{
  template?: "clean";
}>;

export function TemplateProvider({
  children,
  template = "clean",
}: TemplateProviderProps) {
  useEffect(() => {
    document.documentElement.setAttribute("data-template", template);
  }, [template]);

  return <>{children}</>;
}
