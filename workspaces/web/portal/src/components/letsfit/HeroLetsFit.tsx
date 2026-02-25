import Link from "next/link";
import { ArrowRight, Info } from "lucide-react";

export function HeroLetsFit() {
    return (
        <section className="relative overflow-hidden rounded-2xl bg-surface p-8 md:p-16 flex flex-col items-center text-center gap-6">
            <div
                className="absolute inset-0 z-0 opacity-10 bg-[url('https://images.unsplash.com/photo-1546069901-ba9599a7e63c')] bg-cover bg-center"
            />
            <div className="z-10 max-w-2xl">
                <span className="inline-block rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary mb-4">
                    Comida de verdade, pronta em minutos
                </span>
                <h1 className="text-4xl md:text-6xl font-extrabold text-text tracking-tight mb-6">
                    Sua rotina mais leve e <span className="text-primary">saborosa</span>
                </h1>
                <p className="text-lg text-muted mb-8 leading-relaxed">
                    Marmitas saudáveis, balanceadas e feitas com ingredientes selecionados. Agende sua entrega e aproveite o melhor da alimentação prática.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <Link
                        href="/cardapio"
                        className="flex items-center gap-2 rounded-full bg-primary px-8 py-4 text-base font-bold text-white transition hover:bg-primary-soft w-full sm:w-auto justify-center"
                    >
                        Ver cardápio de hoje
                        <ArrowRight className="h-5 w-5" />
                    </Link>
                    <Link
                        href="/como-funciona"
                        className="flex items-center gap-2 rounded-full border-2 border-primary/20 bg-transparent px-8 py-4 text-base font-bold text-text transition hover:border-primary hover:text-primary w-full sm:w-auto justify-center"
                    >
                        Como funciona
                        <Info className="h-5 w-5" />
                    </Link>
                </div>
            </div>
        </section>
    );
}
