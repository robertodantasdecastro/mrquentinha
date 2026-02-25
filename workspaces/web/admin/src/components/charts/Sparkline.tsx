import type { HTMLAttributes } from "react";

type SparklineProps = HTMLAttributes<SVGSVGElement> & {
  values: number[];
};

function buildPath(values: number[], width: number, height: number): string {
  if (values.length === 0) {
    return "";
  }

  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;

  const step = width / (values.length - 1 || 1);
  return values
    .map((value, index) => {
      const x = index * step;
      const y = height - ((value - min) / range) * height;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

export function Sparkline({ values, className, ...props }: SparklineProps) {
  const width = 220;
  const height = 60;
  const path = buildPath(values, width, height);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Grafico de tendencia"
      className={["h-12 w-full", className].filter(Boolean).join(" ")}
      {...props}
    >
      <path
        d={path}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        className="text-primary"
      />
      <path
        d={`${path} L ${width} ${height} L 0 ${height} Z`}
        className="fill-primary/10"
      />
    </svg>
  );
}
