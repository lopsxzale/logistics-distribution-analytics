"use client";

import { scaleBand, scaleLinear } from "d3-scale";
import { motion } from "motion/react";
import { useState } from "react";
import { brands, findings, type Fuel } from "@/lib/data";
import { brandLabel, fuelColor } from "@/lib/labels";
import { useWidth } from "@/lib/use-size";
import { ChartFrame, ChartTooltip, TooltipRow } from "../chart-frame";
import { CountUp, Reveal, useChartInView } from "../motion";
import { useI18n } from "../providers";
import { FuelToggle } from "./brazil-map";

function BrandBars({ fuel }: { fuel: Fuel }) {
  const { lang, t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<string | null>(null);
  const rows = brands.ranking.filter((r) => r.fuel === fuel).sort((a, b) => b.diff_pct - a.diff_pct);
  const ROW = 44;
  const M = { left: 128, right: 150 };
  const height = rows.length * ROW;
  const lo = Math.min(0, ...rows.map((r) => r.diff_pct));
  const hi = Math.max(...rows.map((r) => r.diff_pct));
  const x = scaleLinear().domain([lo, hi]).range([M.left, width - M.right]);
  const y = scaleBand<string>().domain(rows.map((r) => r.brand)).range([0, height]).padding(0.32);
  const hovered = rows.find((r) => r.brand === hover);

  return (
    <div ref={box} className="relative">
      <svg ref={ref} width={width} height={height} role="img" aria-label={t.brands.chartTitle} className="block overflow-visible">
        <line x1={x(0)} x2={x(0)} y1={0} y2={height} stroke="var(--axis)" />
        {rows.map((r, i) => {
          const isBase = r.brand === "BRANCA";
          const x0 = Math.min(x(0), x(r.diff_pct));
          const w = Math.max(Math.abs(x(r.diff_pct) - x(0)), 2);
          return (
            <g
              key={r.brand}
              tabIndex={0}
              role="graphics-symbol"
              aria-label={`${brandLabel(r.brand, lang)}: ${f.spp(r.diff_pct)}, ${f.brl3(r.price)}`}
              className="outline-none"
              onPointerEnter={() => setHover(r.brand)}
              onPointerLeave={() => setHover(null)}
              onFocus={() => setHover(r.brand)}
              onBlur={() => setHover(null)}
            >
              <rect x={0} y={y(r.brand)! - 6} width={width} height={y.bandwidth() + 12} rx={8} fill={hover === r.brand ? "var(--surface-2)" : "transparent"} />
              <text x={M.left - 12} y={y(r.brand)! + y.bandwidth() / 2} dy="0.32em" textAnchor="end" className={`text-[13px] ${isBase ? "fill-ink font-semibold" : "fill-ink-2"}`}>
                {brandLabel(r.brand, lang)}
              </text>
              <motion.rect
                y={y(r.brand)}
                height={y.bandwidth()}
                rx={4}
                fill={isBase ? "var(--axis)" : fuelColor[fuel]}
                initial={{ x: x(0), width: 0 }}
                animate={{ x: inView ? x0 : x(0), width: inView ? w : 0 }}
                transition={{ duration: 0.9, delay: 0.1 + i * 0.08 }}
              />
              <motion.text
                x={Math.max(x(r.diff_pct), x(0)) + 10}
                y={y(r.brand)! + y.bandwidth() / 2}
                dy="0.32em"
                className="text-[12px] tabular"
                initial={{ opacity: 0 }}
                animate={{ opacity: inView ? 1 : 0 }}
                transition={{ delay: 0.9 + i * 0.05 }}
              >
                <tspan className="fill-ink font-semibold">{isBase ? "0%" : f.spp(r.diff_pct)}</tspan>
                <tspan className="fill-muted"> · {f.brl3(r.price)}</tspan>
              </motion.text>
            </g>
          );
        })}
      </svg>
      {hovered && (
        <ChartTooltip x={Math.max(x(hovered.diff_pct), x(0))} y={y(hovered.brand)! + y.bandwidth() / 2} width={width}>
          <p className="mb-1 font-medium text-ink">{brandLabel(hovered.brand, lang)}</p>
          <TooltipRow value={f.brl3(hovered.price)} label="/L" color={fuelColor[fuel]} />
          <TooltipRow value={f.pct(hovered.share)} label={t.brands.share} />
        </ChartTooltip>
      )}
    </div>
  );
}

export function BrandsCharts() {
  const { lang, t, f } = useI18n();
  const [fuel, setFuel] = useState<Fuel>("DIESEL");
  const rows = brands.ranking.filter((r) => r.fuel === fuel).sort((a, b) => b.diff_pct - a.diff_pct);
  const stats = [
    { label: t.brands.s10, value: findings.s10_premium_pct, note: `${f.brl3(findings.s10_premium_brl)}/L · ${t.brands.s10Note}` },
    { label: t.brands.additive, value: findings.additive_premium_pct, note: t.brands.additiveNote },
  ];

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
      <ChartFrame
        title={t.brands.chartTitle}
        subtitle={t.brands.chartSubtitle}
        sqlId="q6_bandeiras"
        controls={<FuelToggle value={fuel} onChange={setFuel} />}
        table={{
          columns: [t.table.brand, t.table.price, t.table.diff, t.brands.share],
          rows: rows.map((r) => [brandLabel(r.brand, lang), f.brl3(r.price), f.spp(r.diff_pct), f.pct(r.share)]),
        }}
      >
        <BrandBars fuel={fuel} />
      </ChartFrame>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
        {stats.map((s, i) => (
          <Reveal key={s.label} delay={0.1 * i}>
            <div className="card h-full p-5">
              <p className="text-xs font-medium uppercase tracking-wider text-muted">{s.label}</p>
              <p className="mt-2 text-3xl font-semibold tracking-tight text-ink">
                <CountUp value={s.value} format={(v) => f.spp(v, 1)} />
              </p>
              <p className="mt-1 text-xs text-ink-2">{s.note}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </div>
  );
}
