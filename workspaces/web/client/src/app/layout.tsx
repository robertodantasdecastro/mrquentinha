import { FormFieldGuard, TemplateProvider } from "@mrquentinha/ui";
import type { Metadata } from "next";

import { ClientTemplateProvider } from "@/components/ClientTemplateProvider";
import { Footer } from "@/components/Footer";
import { GlobalNetworkPreloader } from "@/components/GlobalNetworkPreloader";
import { Header } from "@/components/Header";
import { fetchClientActiveTemplate } from "@/lib/clientTemplate";

import "./globals.css";

const initThemeScript = `
(function () {
  try {
    var key = "mrq-client-theme";
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
    default: "Mr Quentinha | Web Cliente",
    template: "%s | Mr Quentinha",
  },
  description:
    "Aplicacao web cliente do Mr Quentinha para consultar cardapio e criar pedidos.",
  icons: {
    icon: "/brand/png/favicon.ico",
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const template = await fetchClientActiveTemplate();

  return (
    <html
      lang="pt-BR"
      suppressHydrationWarning
      data-client-template={template}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: initThemeScript }} />
      </head>
      <body className="bg-bg text-text antialiased">
        <ClientTemplateProvider initialTemplate={template}>
          <TemplateProvider template="clean">
            <GlobalNetworkPreloader />
            <FormFieldGuard />
            <div className="flex min-h-screen flex-col">
              <Header />
              <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-5 md:px-6 md:py-8">
                {children}
              </main>
              <Footer />
            </div>
          </TemplateProvider>
        </ClientTemplateProvider>
      </body>
    </html>
  );
}
