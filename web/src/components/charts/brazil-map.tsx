"use client";

import { motion } from "motion/react";
import { useState, type ReactNode } from "react";
import { FUELS, type Fuel, type MapShapes } from "@/lib/data";
import { fuelLabel } from "@/lib/labels";
import { useWidth } from "@/lib/use-size";
import { ChartTooltip, Segmented } from "../chart-frame";
import { useChartInView } from "../motion";
import { useI18n } from "../providers";

export function FuelToggle({ value, onChange }: { value: Fuel; onChange: (f: Fuel) => void }) {
  const { lang, t } = useI18n();
  return (
    <Segmented
      label={t.fuel}
      value={value}
      onChange={onChange}
      options={FUELS.map((f) => ({ value: f, label: fuelLabel(f, lang) }))}
    />
  );
}

/** Legenda da escala divergente em degraus, com rótulos nas pontas. */
export function DivergingLegend({ left, right, steps }: { left: string; right: string; steps: string[] }) {
  return (
    <div className="flex items-center gap-2 text-xs text-ink-2">
      <span>{left}</span>
      <span className="flex overflow-hidden rounded-full" aria-hidden>
        {steps.map((c) => (
          <span key={c} className="h-2.5 w-5" style={{ background: c }} />
        ))}
      </span>
      <span>{right}</span>
    </div>
  );
}

/** Coroplético do Brasil: paths pré-calculados no build, cores por estado vindas do chamador. */
export function BrazilMap({
  shapes,
  fillOf,
  label,
  tooltip,
  ariaLabel,
  highlight = [],
}: {
  shapes: MapShapes;
  fillOf: (uf: string) => string | undefined;
  label: (uf: string) => string;
  tooltip: (uf: string) => ReactNode;
  ariaLabel: string;
  highlight?: string[];
}) {
  const [box, width] = useWidth<HTMLDivElement>(480);
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<string | null>(null);
  const scale = width / shapes.width;
  const ufs = Object.keys(shapes.paths);

  return (
    <div ref={box} className="relative mx-auto w-full max-w-[560px]">
      <svg
        ref={ref}
        viewBox={`0 0 ${shapes.width} ${shapes.height}`}
        width="100%"
        role="img"
        aria-label={ariaLabel}
        className="block overflow-visible"
      >
        {/* DF fica dentro de GO: desenhado por último para receber o hover. */}
        {[...ufs.filter((u) => u !== "DF"), "DF"].map((uf, i) => {
          const fill = fillOf(uf);
          return (
            <motion.path
              key={uf}
              d={shapes.paths[uf]}
              fill={fill ?? "var(--surface-2)"}
              stroke={hover === uf ? "var(--ink)" : "var(--surface)"}
              strokeWidth={hover === uf ? 2 : 1}
              strokeLinejoin="round"
              tabIndex={0}
              role="graphics-symbol"
              aria-label={label(uf)}
              className="cursor-pointer outline-none transition-[fill] duration-500"
              initial={{ opacity: 0 }}
              animate={{ opacity: inView ? (hover && hover !== uf ? 0.55 : 1) : 0 }}
              transition={{ opacity: { duration: hover ? 0.2 : 0.6, delay: hover ? 0 : 0.1 + i * 0.025 } }}
              onPointerEnter={() => setHover(uf)}
              onPointerLeave={() => setHover(null)}
              onFocus={() => setHover(uf)}
              onBlur={() => setHover(null)}
            />
          );
        })}
        {highlight.map((uf) => {
          const [cx, cy] = shapes.centroids[uf];
          return (
            <text
              key={uf}
              x={cx}
              y={cy}
              textAnchor="middle"
              dy="0.35em"
              className="pointer-events-none fill-ink text-[15px] font-semibold"
              style={{ paintOrder: "stroke", stroke: "var(--surface)", strokeWidth: 3 }}
            >
              {uf}
            </text>
          );
        })}
      </svg>
      {hover && (
        <ChartTooltip x={shapes.centroids[hover][0] * scale} y={shapes.centroids[hover][1] * scale} width={width}>
          {tooltip(hover)}
        </ChartTooltip>
      )}
    </div>
  );
}
