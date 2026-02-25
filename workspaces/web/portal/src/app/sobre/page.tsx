export const metadata = {
    title: "Sobre o Mr Quentinha",
};

export default function SobrePage() {
    return (
        <div className="max-w-4xl mx-auto py-12 px-4 space-y-12">
            <div className="text-center space-y-4">
                <h1 className="text-4xl md:text-5xl font-extrabold text-text">Muito prazer, somos o Mr Quentinha</h1>
                <p className="text-xl text-muted">Acreditamos que a alimentação saudável não precisa dar trabalho.</p>
            </div>

            <section className="bg-surface border border-border rounded-2xl p-8 md:p-12 space-y-6">
                <h2 className="text-2xl font-bold text-text">Nossa História</h2>
                <div className="text-muted leading-relaxed space-y-4">
                    <p>
                        Tudo começou com uma dor simples: como manter uma dieta nutritiva em meio a uma rotina agitada de reuniões e entregas profissionais? Muitas vezes, a conveniência do delivery tradicional significa sacrificar a nutrição em nome da rapidez.
                    </p>
                    <p>
                        O <strong>Mr Quentinha</strong> nasceu para preencher essa lacuna. Nós conectamos a paixão pela culinária de verdade (feita por chefs, com ingredientes que você conhece) com a conveniência da entrega agendada e ultracongelada.
                    </p>
                </div>
            </section>

            <section className="grid md:grid-cols-2 gap-8">
                <div className="bg-bg border border-border rounded-2xl p-8">
                    <h3 className="text-xl font-bold text-primary mb-3">Qualidade</h3>
                    <p className="text-muted text-sm leading-relaxed">
                        Nada de conservantes estranhos. Nossas marmitas são feitas com foco na densidade nutricional, com muito sabor e temperos naturais.
                    </p>
                </div>
                <div className="bg-bg border border-border rounded-2xl p-8">
                    <h3 className="text-xl font-bold text-primary mb-3">Tecnologia</h3>
                    <p className="text-muted text-sm leading-relaxed">
                        Utilizamos o ultracongelamento, o que significa temperatura caindo bruscamente num curto espaço de tempo. Resultado? Cor, sabor e nutrientes preservados.
                    </p>
                </div>
            </section>
        </div>
    );
}
