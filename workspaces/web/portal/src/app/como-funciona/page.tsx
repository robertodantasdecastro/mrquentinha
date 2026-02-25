import { HowToHeat } from "@/components/letsfit";

export const metadata = {
    title: "Como Funciona",
};

export default function ComoFuncionaPage() {
    return (
        <div className="max-w-5xl mx-auto py-12 px-4 space-y-16">
            <div className="text-center space-y-4">
                <h1 className="text-4xl md:text-5xl font-extrabold text-text">Como funciona o Mr Quentinha</h1>
                <p className="text-xl text-muted">Em poucos passos, seus almoços e jantares garantidos para a semana toda.</p>
            </div>

            <section className="grid md:grid-cols-3 gap-8">
                {[
                    { step: 1, title: "Você escolhe", desc: "Acesse nosso cardápio rotativo ou selecione um kit semanal já pensado por nossos nutricionistas." },
                    { step: 2, title: "Nós preparamos", desc: "Nossos chefs preparam tudo fresco. Se não for para consumo imediato, as marmitas são ultracongeladas." },
                    { step: 3, title: "Entregamos", desc: "Agende a entrega pro dia que for melhor. Pague na entrega com VR, VA, Cartões ou PIX antecipado." }
                ].map((item) => (
                    <div key={item.step} className="bg-surface border border-border rounded-2xl p-8 flex flex-col items-center text-center">
                        <div className="w-12 h-12 bg-primary text-white rounded-full flex items-center justify-center font-bold text-xl mb-6">
                            {item.step}
                        </div>
                        <h3 className="text-xl font-bold text-text mb-3">{item.title}</h3>
                        <p className="text-muted text-sm leading-relaxed">{item.desc}</p>
                    </div>
                ))}
            </section>

            {/* Reutilizando componente de Aquecimento do novo template */}
            <HowToHeat />
        </div>
    );
}
