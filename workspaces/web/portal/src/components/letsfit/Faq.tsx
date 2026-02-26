"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

export type FaqItem = {
  question: string;
  answer: string;
};

type FaqProps = {
  title?: string;
  items?: FaqItem[];
};

const FAQ_DEFAULTS: FaqItem[] = [
  {
    question: "Como faco para agendar a entrega?",
    answer:
      "Durante o checkout, voce escolhe a data de entrega disponivel para sua regiao.",
  },
  {
    question: "Posso pagar com VR/VA?",
    answer:
      "Sim. Aceitamos as principais redes de vale refeicao e vale alimentacao.",
  },
  {
    question: "A comida chega congelada?",
    answer:
      "Voce pode escolher entrega fresca para o dia ou ultracongelada para estocar.",
  },
];

export function Faq({ title = "Duvidas frequentes", items = FAQ_DEFAULTS }: FaqProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="mx-auto max-w-3xl px-4 py-16">
      <div className="mb-10 text-center">
        <h2 className="text-3xl font-bold text-text">{title}</h2>
      </div>

      <div className="space-y-4">
        {items.map((faq, index) => {
          const isOpen = openIndex === index;
          return (
            <article
              key={`${faq.question}-${index}`}
              className="overflow-hidden rounded-xl border border-border bg-surface"
            >
              <button
                type="button"
                onClick={() => setOpenIndex(isOpen ? null : index)}
                className="flex w-full items-center justify-between px-6 py-4 text-left font-semibold text-text transition hover:bg-black/5 dark:hover:bg-white/5"
              >
                {faq.question}
                <ChevronDown
                  className={`h-5 w-5 text-muted transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`}
                />
              </button>
              {isOpen && (
                <div className="border-t border-border/50 px-6 pb-4 pt-0 text-sm leading-relaxed text-muted">
                  <p className="pt-4">{faq.answer}</p>
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
