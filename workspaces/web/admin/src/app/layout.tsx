import { FormFieldGuard, TemplateProvider } from "@mrquentinha/ui";
import type { Metadata } from "next";

import { AdminTemplateProvider } from "@/components/AdminTemplateProvider";
import { AdminShell } from "@/components/AdminShell";
import { GlobalNetworkPreloader } from "@/components/GlobalNetworkPreloader";
import { fetchAdminActiveTemplate } from "@/lib/adminTemplate";

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

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const template = await fetchAdminActiveTemplate();

  return (
    <html lang="pt-BR" suppressHydrationWarning data-admin-template={template}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: initThemeScript }} />
      </head>
      <body className="bg-bg text-text antialiased">
        <AdminTemplateProvider initialTemplate={template}>
          <TemplateProvider template="clean">
            <GlobalNetworkPreloader />
            <FormFieldGuard />
            <AdminShell>{children}</AdminShell>
          </TemplateProvider>
        </AdminTemplateProvider>
      </body>
    </html>
  );
}
