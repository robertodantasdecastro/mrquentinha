import { InlinePreloader } from "@/components/InlinePreloader";

export default function Loading() {
  return (
    <div className="px-1 py-2">
      <InlinePreloader message="Carregando pagina do portal..." />
    </div>
  );
}
