import { Zap, Snowflake } from "lucide-react";

export function HowToHeat() {
    return (
        <section className="py-16 bg-surface/50 border-y border-border">
            <div className="text-center mb-12">
                <h2 className="text-3xl font-bold text-text">Fácil de preparar e armazenar</h2>
                <p className="text-muted mt-3 max-w-2xl mx-auto">Embalagens livres de bisfenol que vão direto do freezer para o micro-ondas. Qualidade e sabor mantidos pela tecnologia de ultracongelamento.</p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto px-4">
                {/* Freeze */}
                <div className="rounded-2xl bg-bg border border-border p-8 flex flex-col items-center text-center">
                    <div className="h-16 w-16 bg-blue-500/10 text-blue-500 rounded-full flex items-center justify-center mb-6">
                        <Snowflake className="w-8 h-8" />
                    </div>
                    <h3 className="text-xl font-bold text-text mb-3">Conservação</h3>
                    <p className="text-muted leading-relaxed text-sm">
                        Nossas marmitas são entregues frescas ou ultracongeladas. Você pode mantê-las na geladeira por até 3 dias, ou armazenar no freezer por 30 dias sem perder o sabor e as propriedades nutricionais.
                    </p>
                </div>

                {/* Heat */}
                <div className="rounded-2xl bg-bg border border-border p-8 flex flex-col items-center text-center">
                    <div className="h-16 w-16 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-6">
                        <Zap className="w-8 h-8" />
                    </div>
                    <h3 className="text-xl font-bold text-text mb-3">Aquecimento</h3>
                    <p className="text-muted leading-relaxed text-sm">
                        Tire do freezer, faça um pequeno furo na película plástica e aqueça no micro-ondas de <strong>5 a 7 minutos</strong>, ou direto no banho-maria.
                    </p>
                </div>
            </div>
        </section>
    );
}
