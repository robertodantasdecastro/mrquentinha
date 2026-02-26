import Image from "next/image";

export type CategoryItem = {
  title: string;
  description: string;
  image_url?: string;
};

type CategoriesProps = {
  title?: string;
  subtitle?: string;
  items?: CategoryItem[];
};

const CATEGORY_DEFAULTS: CategoryItem[] = [
  {
    title: "Dia a dia",
    description: "O caseiro classico e balanceado",
    image_url: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
  },
  {
    title: "Low Carb",
    description: "Refeicoes ricas em proteina e poucos carboidratos",
    image_url: "https://images.unsplash.com/photo-1603569283847-aa295f0d016a",
  },
  {
    title: "Vegetariano",
    description: "Vegetais frescos e proteinas alternativas",
    image_url: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd",
  },
  {
    title: "Kits Semanais",
    description: "Pacotes prontos para 5 ou 7 dias",
    image_url: "https://images.unsplash.com/photo-1579113800032-c38bd7635818",
  },
];

const FALLBACK_IMAGE_URL =
  "https://images.unsplash.com/photo-1546069901-ba9599a7e63c";

export function Categories({
  title = "Escolha seu objetivo",
  subtitle = "Temos uma linha de produtos pensada para cada necessidade do seu corpo",
  items = CATEGORY_DEFAULTS,
}: CategoriesProps) {
  return (
    <section className="py-12">
      <div className="mb-10 text-center">
        <h2 className="text-3xl font-bold text-text">{title}</h2>
        <p className="mt-2 text-muted">{subtitle}</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((category, index) => (
          <article
            key={`${category.title}-${index}`}
            className="group relative cursor-pointer overflow-hidden rounded-2xl border border-border bg-surface transition hover:border-primary/50 hover:shadow-lg"
          >
            <div className="relative h-48 w-full overflow-hidden">
              <Image
                src={category.image_url || FALLBACK_IMAGE_URL}
                alt={category.title}
                fill
                className="object-cover transition duration-500 group-hover:scale-110"
              />
            </div>
            <div className="p-5">
              <h3 className="mb-1 text-lg font-bold text-text">{category.title}</h3>
              <p className="text-sm text-muted">{category.description}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
