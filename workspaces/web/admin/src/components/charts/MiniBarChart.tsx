import type { HTMLAttributes } from "react";

type MiniBarChartProps = HTMLAttributes<HTMLDivElement> & {
  values: number[];
};

export function MiniBarChart({ values, className, ...props }: MiniBarChartProps) {
  const max = Math.max(...values, 1);

  return (
    <div
      className={["flex items-end gap-2", className].filter(Boolean).join(" ")}
      aria-label="Grafico de barras"
      {...props}
    >
      {values.map((value, index) => (
        <div
          key={`${value}-${index}`}
          className="flex-1 rounded-md bg-primary/20"
          style={{ height: `${Math.round((value / max) * 72) + 12}px` }}
        >
          <div className="h-full rounded-md bg-primary/70" />
        </div>
      ))}
    </div>
  );
}
