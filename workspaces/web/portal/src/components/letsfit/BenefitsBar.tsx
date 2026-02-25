import { CheckCircle2, Clock, Truck, CreditCard } from "lucide-react";

export function BenefitsBar() {
    const benefits = [
        { icon: <Clock className="h-6 w-6 text-primary" />, text: "Pronto em 5 min" },
        { icon: <Truck className="h-6 w-6 text-primary" />, text: "Entrega agendada" },
        { icon: <CheckCircle2 className="h-6 w-6 text-primary" />, text: "Ingredientes selecionados" },
        { icon: <CreditCard className="h-6 w-6 text-primary" />, text: "Aceitamos VR e VA" },
    ];

    return (
        <section className="bg-surface py-6 px-4 md:px-8 border-y border-border flex flex-wrap justify-center gap-6 md:gap-12">
            {benefits.map((benefit, i) => (
                <div key={i} className="flex items-center gap-3">
                    {benefit.icon}
                    <span className="font-medium text-sm text-text">{benefit.text}</span>
                </div>
            ))}
        </section>
    );
}
