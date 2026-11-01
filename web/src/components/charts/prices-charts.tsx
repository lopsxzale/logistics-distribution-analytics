"use client";

import { scaleBand, scaleLinear } from "d3-scale";
import { motion } from "motion/react";
import { useState } from "react";
import { gap, REGIONS, states, ufInfo, type Fuel, type MapShapes } from "@/lib/data";
import { fill } from "@/lib/format";
import { divergingLegend, divergingStep, regionColor, regionLabel } from "@/lib/labels";
import { useWidth } from "@/lib/use-size";
import { ChartFrame, ChartTooltip, TooltipRow } from "../chart-frame";
import { useChartInView } from "../motion";
import { useI18n } from "../providers";
import { BrazilMap, DivergingLegend, FuelToggle } from "./brazil-map";

/** Satura a cor no percentil 90 para que um outlier (Acre) não deixe o resto do mapa neutro. */
function saturation(values: number[]) {
  const abs = values.map(Math.abs).sort((a, b) => a - b);
  return Math.max(abs[Math.floor(abs.length * 0.9)] ?? 1, 1);
}

function Ranking({ fuel, limit }: { fuel: Fuel; limit: number }) {
  const { t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>(420);
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<string | null>(null);
  const rows = states.states.filter((s) => s.fuel === fuel).sort((a, b) => b.diff_pct - a.diff_pct);
  const ROW = 19;
  const M = { top: 4, right: 52, bottom: 4, left: 132 };
  const height = rows.length * ROW + M.top + M.bottom;
  const lo = Math.min(0, ...rows.map((r) => r.diff_pct));
  const hi = Math.max(0, ...rows.map((r) => r.diff_pct));
  const x = scaleLinear().domain([lo, hi]).range([M.left, width - M.right]);
  const y = scaleBand<string>().domain(rows.map((r) => r.uf)).range([M.top, height - M.bottom]).padding(0.22);
  const narrow = width < 400;

  return (
    <div ref={box} className="relative">
      <svg ref={ref} width={width} height={height} role="img" aria-label={t.prices.rankTitle} className="block overflow-visible">
        <line x1={x(0)} x2={x(0)} y1={M.top} y2={height - M.bottom} stroke="var(--axis)" />
        {rows.map((r, i) => {
          const y0 = y(r.uf)!;
          const x0 = Math.min(x(0), x(r.diff_pct));
          const w = Math.max(Math.abs(x(r.diff_pct) - x(0)), 1.5);
          const dim = hover !== null && hover !== r.uf;
          return (
            <g
              key={r.uf}
              tabIndex={0}
              role="graphics-symbol"
              aria-label={`${ufInfo[r.uf].name}: ${f.spp(r.diff_pct)}`}
              className="outline-none"
              onPointerEnter={() => setHover(r.uf)}
              onPointerLeave={() => setHover(null)}
              onFocus={() => setHover(r.uf)}
              onBlur={() => setHover(null)}
            >
              <rect x={0} y={y0 - 2} width={width} height={y.bandwidth() + 4} fill="transparent" />
              <text x={M.left - 10} y={y0 + y.bandwidth() / 2} dy="0.32em" textAnchor="end" className="fill-ink-2 text-[11px]" opacity={dim ? 0.5 : 1}>
                {narrow ? r.uf : ufInfo[r.uf].name}
              </text>
              <motion.rect
                y={y0}
                height={y.bandwidth()}
                rx={3}
                fill={divergingStep(r.diff_pct, limit).fill}
                initial={{ x: x(0), width: 0 }}
                animate={{ x: inView ? x0 : x(0), width: inView ? w : 0, opacity: dim ? 0.4 : 1 }}
                transition={{ duration: 0.9, delay: inView && hover === null ? 0.1 + i * 0.02 : 0 }}
              />
              <motion.text
                x={r.diff_pct >= 0 ? x(r.diff_pct) + 6 : x(0) + 6}
                y={y0 + y.bandwidth() / 2}
                dy="0.32em"
                className="fill-ink-2 text-[11px] tabular"
                initial={{ opacity: 0 }}
                animate={{ opacity: inView ? (dim ? 0.4 : 1) : 0 }}
                transition={{ delay: hover === null ? 0.8 : 0 }}
              >
                {f.spp(r.diff_pct)}
              </motion.text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function RegionRuler({ fuel }: { fuel: Fuel }) {
  const { lang, t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<string | null>(null);
  const rows = gap.ruler.filter((r) => r.fuel === fuel);
  const years = [...new Set(rows.map((r) => r.year))];
  const gaps = Object.fromEntries(gap.yearly.filter((g) => g.fuel === fuel).map((g) => [g.year, g.gap_pct]));
  const ROW = 76;
  const M = { top: 30, right: 24, bottom: 28, left: 64 };
  const height = years.length * ROW + M.top + M.bottom - 24;
  const prices = rows.map((r) => r.price);
  const lo = Math.min(...prices);
  const hi = Math.max(...prices);
  const pad = (hi - lo) * 0.08;
  const x = scaleLinear().domain([lo - pad, hi + pad]).nice().range([M.left, width - M.right]);
  const hovered = hover ? rows.find((r) => `${r.year}-${r.region}` === hover) : undefined;

  return (
    <div ref={box} className="relative">
      <svg ref={ref} width={width} height={height} role="img" aria-label={t.prices.rulerTitle} className="block overflow-visible">
        {x.ticks(width < 520 ? 3 : 7).map((tick) => (
          <g key={tick}>
            <line x1={x(tick)} x2={x(tick)} y1={M.top - 12} y2={height - M.bottom} stroke="var(--grid)" />
            <text x={x(tick)} y={height - 8} textAnchor="middle" className="fill-muted text-[11px] tabular">
              {width < 520 ? f.dec(tick) : f.brl(tick)}
            </text>
          </g>
        ))}
        {years.map((year, yi) => {
          const cy = M.top + yi * ROW + 10;
          const yr = rows.filter((r) => r.year === year).sort((a, b) => a.price - b.price);
          const min = yr[0];
          const max = yr[yr.length - 1];
          return (
            <g key={year}>
              <text x={0} y={cy} dy="0.32em" className="fill-ink text-[13px] font-semibold tabular">
                {year}
              </text>
              <motion.line
                x1={x(min.price)}
                x2={x(max.price)}
                y1={cy}
                y2={cy}
                stroke="var(--axis)"
                strokeWidth={6}
                strokeLinecap="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: inView ? 1 : 0 }}
                transition={{ duration: 1, delay: 0.2 + yi * 0.2 }}
              />
              <motion.text
                x={(x(min.price) + x(max.price)) / 2}
                y={cy - 16}
                textAnchor="middle"
                className="fill-ink-2 text-[11px] font-medium tabular"
                initial={{ opacity: 0 }}
                animate={{ opacity: inView ? 1 : 0 }}
                transition={{ delay: 1 + yi * 0.2 }}
              >
                {t.prices.gapLabel} {f.pp(gaps[year])}
              </motion.text>
              {yr.map((r, i) => {
                const key = `${r.year}-${r.region}`;
                // Rótulos alternam acima/abaixo; o Norte (o ponto da história) fica sempre visível.
                return (
                  <g
                    key={key}
                    tabIndex={0}
                    role="graphics-symbol"
                    aria-label={`${year} · ${regionLabel(r.region, lang)}: ${f.brl3(r.price)}`}
                    className="outline-none"
                    onPointerEnter={() => setHover(key)}
                    onPointerLeave={() => setHover(null)}
                    onFocus={() => setHover(key)}
                    onBlur={() => setHover(null)}
                  >
                    <circle cx={x(r.price)} cy={cy} r={14} fill="transparent" />
                    <motion.circle
                      cx={x(r.price)}
                      cy={cy}
                      fill={regionColor[r.region]}
                      stroke="var(--surface)"
                      strokeWidth={2}
                      initial={{ r: 0 }}
                      animate={{ r: inView ? (hover === key ? 9 : 7) : 0 }}
                      transition={{ duration: 0.4, delay: hover ? 0 : 0.6 + yi * 0.2 + i * 0.05 }}
                    />
                    {(r.region === "Norte" || i === 0) && (
                      <text x={x(r.price)} y={cy + 22} textAnchor="middle" className="pointer-events-none fill-ink-2 text-[11px]">
                        {regionLabel(r.region, lang)}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      {hovered && (
        <ChartTooltip x={x(hovered.price)} y={M.top + years.indexOf(hovered.year) * ROW + 10} width={width}>
          <p className="mb-1 font-medium text-ink">
            {regionLabel(hovered.region, lang)} · {hovered.year}
          </p>
          <TooltipRow value={f.brl3(hovered.price)} label={t.prices.perLiter} color={regionColor[hovered.region]} />
        </ChartTooltip>
      )}
    </div>
  );
}

export function PricesBlock({ shapes }: { shapes: MapShapes }) {
  const { lang, t, f } = useI18n();
  const [fuel, setFuel] = useState<Fuel>("DIESEL");
  const rows = states.states.filter((s) => s.fuel === fuel);
  const byUf = Object.fromEntries(rows.map((r) => [r.uf, r]));
  const limit = saturation(rows.map((r) => r.diff_pct));
  const month = f.month(states.last_month);
  const national = f.brl(states.national[fuel].last);
  const sorted = [...rows].sort((a, b) => b.diff_pct - a.diff_pct);
  const extremes = [sorted[0].uf, sorted[sorted.length - 1].uf];
  const years = gap.yearly.filter((g) => g.fuel === fuel);

  const table = {
    columns: [t.table.state, t.table.region, t.table.price, t.table.diff],
    rows: sorted.map((r) => [
      ufInfo[r.uf].name,
      regionLabel(ufInfo[r.uf].region, lang),
      f.brl3(r.price),
      f.spp(r.diff_pct),
    ]),
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <FuelToggle value={fuel} onChange={setFuel} />
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
        <ChartFrame
          title={t.prices.mapTitle}
          subtitle={fill(t.prices.mapSubtitle, { month, national })}
          sqlId="q1_variacao_preco_tempo"
          controls={<DivergingLegend left={t.prices.below} right={t.prices.above} steps={divergingLegend} />}
          table={table}
        >
          <BrazilMap
            shapes={shapes}
            ariaLabel={t.prices.mapTitle}
            highlight={extremes}
            fillOf={(uf) => (byUf[uf] ? divergingStep(byUf[uf].diff_pct, limit).fill : undefined)}
            label={(uf) => `${ufInfo[uf].name}: ${byUf[uf] ? f.spp(byUf[uf].diff_pct) : "–"}`}
            tooltip={(uf) => (
              <>
                <p className="mb-1 font-medium text-ink">{ufInfo[uf].name}</p>
                <TooltipRow value={f.brl3(byUf[uf].price)} label={t.prices.perLiter} />
                <TooltipRow value={f.spp(byUf[uf].diff_pct)} label={t.prices.vsNational} color={divergingStep(byUf[uf].diff_pct, limit).fill} />
              </>
            )}
          />
        </ChartFrame>
        <ChartFrame title={t.prices.rankTitle} subtitle={fill(t.prices.rankSubtitle, { month })} sqlId="q1_variacao_preco_tempo" table={table}>
          <Ranking fuel={fuel} limit={limit} />
        </ChartFrame>
      </div>
      <ChartFrame
        title={t.prices.rulerTitle}
        subtitle={t.prices.rulerSubtitle}
        sqlId="q4_gap_regional"
        legend={REGIONS.map((r) => ({ label: regionLabel(r, lang), color: regionColor[r], shape: "dot" as const }))}
        table={{
          columns: [t.table.year, ...REGIONS.map((r) => regionLabel(r, lang)), t.prices.gapLabel],
          rows: years.map((y) => [
            String(y.year),
            ...REGIONS.map((r) => f.brl3(gap.ruler.find((x) => x.fuel === fuel && x.year === y.year && x.region === r)!.price)),
            f.pp(y.gap_pct),
          ]),
        }}
      >
        <RegionRuler fuel={fuel} />
        {/* A leitura "gap estável" vale para o diesel, o combustível da operação. */}
        {fuel === "DIESEL" && (
          <p className="mt-3 text-xs text-muted">
            {fill(t.prices.gapNote, {
              y0: f.pp(years[0].gap_pct),
              y1: f.pp(years[1].gap_pct),
              y2: f.pp(years[2].gap_pct),
            })}
          </p>
        )}
      </ChartFrame>
    </div>
  );
}
