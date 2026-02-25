import Link from "next/link";
import { Plus, Minus, ShoppingBag } from "lucide-react";

export function KitSimulator() {
    return (
        <section className="my-16 flex flex-col items-center justify-between rounded-3xl bg-surface border border-border p-8 md:flex-row md:p-12 gap-8">
            <div className="flex-1">
                <span className="text-primary font-bold uppercase tracking-wider text-sm mb-2 block">
                    Não sabe o que escolher?
                </span>
                <h2 className="text-3xl font-extrabold text-text mb-4">Monte seu kit para a semana!</h2>
                <p className="text-muted leading-relaxed mb-6">
                    Selecione a quantidade de dias e o tipo de dieta. Nós sugerimos as melhores opções do cardápio pra você não se preocupar mais com cozinhar no dia a dia.
                </p>
                <Link
                    href="/cardapio"
                    className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 font-semibold text-white transition hover:bg-primary-soft shadow-md shadow-primary/20"
                >
                    <ShoppingBag className="w-5 h-5" />
                    Simular kit personalizado
                </Link>
            </div>

            <div className="flex-1 w-full max-w-sm rounded-2xl bg-bg p-6 shadow-sm border border-border">
                {/* Mockup de configurador */}
                <div className="space-y-6 opacity-70 cursor-not-allowed">
                    <div className="flex items-center justify-between pointer-events-none">
                        <span className="font-semibold text-text">Quantidade de dias</span>
                        <div className="flex items-center gap-3">
                            <button className="rounded-full bg-surface p-2 text-muted border border-border"><Minus className="w-4 h-4" /></button>
                            <span className="font-bold text-lg w-4 text-center">5</span>
                            <button className="rounded-full bg-surface p-2 text-primary border border-primary/20"><Plus className="w-4 h-4" /></button>
                        </div>
                    </div>
                    <div className="space-y-2 pointer-events-none">
                        <span className="font-semibold text-text">Prefere alguma linha?</span>
                        <select className="w-full rounded-lg bg-surface border border-border px-3 py-3 text-sm text-text focus:outline-none" disabled>
                            <option>Mais pedidas da semana</option>
                        </select>
                    </div>
                </div>
            </div>
        </section>
    );
}
