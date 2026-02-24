"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

type ThemeToggleProps = {
  storageKey?: string;
  className?: string;
};

function resolveTheme(storageKey: string): Theme {
  if (typeof window === "undefined") {
    return "light";
  }

  const fromAttr = document.documentElement.getAttribute("data-theme");
  if (fromAttr === "light" || fromAttr === "dark") {
    return fromAttr;
  }

  const fromStorage = window.localStorage.getItem(storageKey);
  if (fromStorage === "light" || fromStorage === "dark") {
    return fromStorage;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function applyTheme(theme: Theme, storageKey: string): void {
  document.documentElement.setAttribute("data-theme", theme);
  window.localStorage.setItem(storageKey, theme);
}

export function ThemeToggle({
  storageKey = "mrq-theme",
  className,
}: ThemeToggleProps) {
  const [theme, setTheme] = useState<Theme>(() => resolveTheme(storageKey));

  useEffect(() => {
    applyTheme(theme, storageKey);
  }, [storageKey, theme]);

  return (
    <button
      type="button"
      onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
      className={[
        "rounded-md border border-border bg-surface px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-muted transition hover:border-primary hover:text-primary",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Alternar tema"
      title="Alternar tema"
    >
      Tema
    </button>
  );
}
