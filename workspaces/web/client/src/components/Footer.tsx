"use client";

import { AppFooter, Container } from "@mrquentinha/ui";
import Image from "next/image";

import { useClientTemplate } from "@/components/ClientTemplateProvider";

export function Footer() {
  const { template } = useClientTemplate();
  const isQuentinhasTemplate = template === "client-quentinhas";

  return (
    <AppFooter className={isQuentinhasTemplate ? "border-t-2 border-primary/30 bg-surface/70" : "bg-bg/80"}>
      <Container className="flex flex-wrap items-center justify-between gap-3 py-4 text-xs text-muted">
        <div className="inline-flex items-center gap-3">
          <span className="inline-flex rounded-md bg-white/95 px-1.5 py-1 ring-1 ring-border/70 shadow-sm dark:bg-white">
            <Image
              src="/brand/original_png/icon_app_original.png"
              alt="Mr Quentinha"
              width={28}
              height={26}
            />
          </span>
          <p className="text-sm font-semibold text-text">Mr Quentinha Web Cliente</p>
        </div>
        <p>
          {isQuentinhasTemplate
            ? "Linha Quentinhas: pedido rapido, acompanhamento e confirmacao."
            : "Fluxo de checkout e pedidos em evolucao continua."}
        </p>
      </Container>
    </AppFooter>
  );
}
