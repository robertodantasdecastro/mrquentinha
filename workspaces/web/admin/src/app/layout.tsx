import { TemplateProvider } from "@mrquentinha/ui";
import type { Metadata } from "next";

import { AdminShell } from "@/components/AdminShell";

import "./globals.css";

const initThemeScript = `
(function () {
  try {
    var key = "mrq-admin-theme";
    var storedTheme = localStorage.getItem(key);
    var hasStoredTheme = storedTheme === "light" || storedTheme === "dark";
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var resolvedTheme = hasStoredTheme ? storedTheme : (prefersDark ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", resolvedTheme);
  } catch (error) {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();
`;

export const metadata: Metadata = {
  title: {
    default: "Mr Quentinha | Admin Web",
    template: "%s | Mr Quentinha",
  },
  description: "Aplicacao web de gestao do ecossistema Mr Quentinha.",
  icons: {
    icon: "/brand/png/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: initThemeScript }} />
      </head>
      <body className="bg-bg text-text antialiased">
        <TemplateProvider template="clean">
          <div className="flex min-h-screen flex-col">
            <AdminShell />
            <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-5 md:px-6 md:py-8">
              {children}
            </main>
          </div>
        </TemplateProvider>
      </body>
    </html>
  );
}
