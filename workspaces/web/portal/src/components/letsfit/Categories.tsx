import Image from "next/image";

export function Categories() {
    const categories = [
        { title: "Dia a dia", description: "O caseiro clássico e balanceado", img: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c" },
        { title: "Low Carb", description: "Refeições ricas em proteína e poucos carbos", img: "https://images.unsplash.com/photo-1603569283847-aa295f0d016a" },
        { title: "Vegetariano", description: "Vegetais frescos e proteínas alternativas", img: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd" },
        { title: "Kits Semanais", description: "Pacotes prontos com desconto para 5 ou 7 dias", img: "https://images.unsplash.com/photo-1579113800032-c38bd7635818" }
    ];

    return (
        <section className="py-12">
            <div className="text-center mb-10">
                <h2 className="text-3xl font-bold text-text">Escolha seu objetivo</h2>
                <p className="text-muted mt-2">Temos uma linha de produtos pensada para cada necessidade do seu corpo</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {categories.map((cat, i) => (
                    <div key={i} className="group relative overflow-hidden rounded-2xl bg-surface border border-border cursor-pointer transition hover:shadow-lg hover:border-primary/50">
                        <div className="h-48 w-full relative overflow-hidden">
                            <Image
                                src={cat.img}
                                alt={cat.title}
                                fill
                                className="object-cover transition duration-500 group-hover:scale-110"
                            />
                        </div>
                        <div className="p-5">
                            <h3 className="font-bold text-lg text-text mb-1">{cat.title}</h3>
                            <p className="text-sm text-muted">{cat.description}</p>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}
