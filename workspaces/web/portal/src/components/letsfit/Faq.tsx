"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

const faqs = [
    {
        q: "Como faço para agendar a entrega?",
        a: "Durante o checkout, você pode escolher a data exata da entrega. Nossa equipe garante a pontualidade no recebimento.",
    },
    {
        q: "Posso pagar com VR/VA?",
        a: "Sim! Aceitamos a maioria dos cartões de Vale Refeição e Vale Alimentação. Você escolhe a opção no carrinho e paga na máquina na hora da entrega.",
    },
    {
        q: "A comida chega congelada?",
        a: "As entregas agendadas podem ir congeladas ou prontas para consumo (frescas), você escolhe no momento da finalização do pedido no App.",
    }
];

export function Faq() {
    const [openIndex, setOpenIndex] = useState<number | null>(null);

    const toggle = (i: number) => {
        setOpenIndex(openIndex === i ? null : i);
    };

    return (
        <section className="py-16 max-w-3xl mx-auto px-4">
            <div className="text-center mb-10">
                <h2 className="text-3xl font-bold text-text">Dúvidas Frequentes</h2>
            </div>

            <div className="space-y-4">
                {faqs.map((faq, i) => {
                    const isOpen = openIndex === i;
                    return (
                        <div key={i} className="border border-border rounded-xl bg-surface overflow-hidden">
                            <button
                                onClick={() => toggle(i)}
                                className="w-full text-left px-6 py-4 font-semibold text-text flex items-center justify-between hover:bg-black/5 dark:hover:bg-white/5 transition"
                            >
                                {faq.q}
                                <ChevronDown className={`w-5 h-5 text-muted transition-transform duration-300 ${isOpen ? "rotate-180" : ""}`} />
                            </button>
                            {isOpen && (
                                <div className="px-6 pb-4 pt-0 text-muted text-sm leading-relaxed border-t border-border/50">
                                    <p className="pt-4">{faq.a}</p>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </section>
    );
}
