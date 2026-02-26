import type { Metadata } from "next";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { PortalTemplateProvider } from "@/components/TemplateProvider";
import { fetchPortalActiveTemplate } from "@/lib/portalTemplate";

import "./globals.css";

const initThemeScript = `
(function () {
  try {
    var stored = localStorage.getItem("mrq-theme");
    var hasStored = stored === "light" || stored === "dark";
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    var resolved = hasStored ? stored : (prefersDark ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", resolved);
  } catch (error) {
    document.documentElement.setAttribute("data-theme", "light");
  }
})();
`;

export const metadata: Metadata = {
  title: {
    default: "Mr Quentinha | Marmitas e Gestao Inteligente",
    template: "%s | Mr Quentinha",
  },
  description:
    "Portal institucional do Mr Quentinha com cardapio em tempo real, app e contato.",
  metadataBase: new URL("https://www.mrquentinha.com.br"),
  icons: {
    icon: "/brand/png/favicon.ico",
  },
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const template = await fetchPortalActiveTemplate("home");

  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: initThemeScript }} />
      </head>
      <body className="bg-bg text-text antialiased">
        <PortalTemplateProvider initialTemplate={template}>
          <div className="flex min-h-screen flex-col">
            <Header />
            <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 md:px-6 md:py-10">
              {children}
            </main>
            <Footer />
          </div>
        </PortalTemplateProvider>
      </body>
    </html>
  );
}
