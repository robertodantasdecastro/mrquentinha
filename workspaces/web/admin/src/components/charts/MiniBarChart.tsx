import type { HTMLAttributes } from "react";

type MiniBarChartProps = HTMLAttributes<HTMLDivElement> & {
  values: number[];
};

export function MiniBarChart({ values, className, ...props }: MiniBarChartProps) {
  const max = Math.max(...values, 1);
  const palette = [
    "var(--mrq-chart-1)",
    "var(--mrq-chart-2)",
    "var(--mrq-chart-3)",
    "var(--mrq-chart-4)",
  ];

  return (
    <div
      className={[
        "rounded-lg border border-border bg-bg p-3",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Grafico de barras"
      {...props}
    >
      <div className="flex h-[98px] items-end gap-2">
        {values.map((value, index) => (
          <div
            key={`${value}-${index}`}
            className="flex-1 rounded-md"
            style={{
              height: `${Math.round((value / max) * 72) + 16}px`,
              backgroundColor: palette[index % palette.length],
              opacity: 0.85,
            }}
          />
        ))}
      </div>
    </div>
  );
}
