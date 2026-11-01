"use client";

import { scaleBand, scaleLinear } from "d3-scale";
import { motion } from "motion/react";
import { useState } from "react";
import { seasonality, type Fuel } from "@/lib/data";
import { divergingLegend, divergingStep, fuelColor, fuelLabel } from "@/lib/labels";
import { useWidth } from "@/lib/use-size";
import { ChartFrame, ChartTooltip, TooltipRow } from "../chart-frame";
import { useChartInView } from "../motion";
import { useI18n } from "../providers";
import { DivergingLegend, FuelToggle } from "./brazil-map";

const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1);

function SeasonalIndex({ fuel }: { fuel: Fuel }) {
  const { lang, t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<number | null>(null);
  const HEIGHT = 300;
  const M = { top: 20, right: 8, bottom: 30, left: 36 };
  const rows = seasonality.index.filter((d) => d.fuel === fuel);
  const lo = Math.min(...rows.map((r) => r.min));
  const hi = Math.max(...rows.map((r) => r.max));
  const x = scaleBand<number>().domain(MONTHS).range([M.left, width - M.right]).padding(0.35);
  const y = scaleLinear().domain([Math.min(lo, 99) - 0.5, Math.max(hi, 101) + 0.5]).nice().range([HEIGHT - M.bottom, M.top]);
  const color = fuelColor[fuel];
  const h = hover === null ? null : rows[hover];

  return (
    <ChartFrame
      title={t.seasonality.indexTitle}
      subtitle={t.seasonality.indexSubtitle}
      sqlId="q2_sazonalidade"
      legend={[
        { label: fuelLabel(fuel, lang), color },
        { label: t.seasonality.range, color: "var(--ink-2)", shape: "line" },
      ]}
      table={{
        columns: [t.table.month, t.seasonality.indexCol, "min", "max"],
        rows: rows.map((r) => [f.monthName(r.month, "long"), f.dec(r.mean, 1), f.dec(r.min, 1), f.dec(r.max, 1)]),
      }}
    >
      <div ref={box} className="relative">
        <svg ref={ref} width={width} height={HEIGHT} role="img" aria-label={t.seasonality.indexTitle} className="block overflow-visible">
          {y.ticks(5).map((tick) => (
            <g key={tick}>
              <line x1={M.left} x2={width - M.right} y1={y(tick)} y2={y(tick)} stroke={tick === 100 ? "var(--axis)" : "var(--grid)"} />
              <text x={M.left - 8} y={y(tick)} dy="0.32em" textAnchor="end" className="fill-muted text-[11px] tabular">
                {tick}
              </text>
            </g>
          ))}
          {rows.map((r, i) => {
            const cx = x(r.month)! + x.bandwidth() / 2;
            const top = Math.min(y(r.mean), y(100));
            const bar = Math.max(Math.abs(y(r.mean) - y(100)), 1.5);
            const dim = hover !== null && hover !== i;
            return (
              <g
                key={r.month}
                tabIndex={0}
                role="graphics-symbol"
                aria-label={`${f.monthName(r.month, "long")}: ${f.dec(r.mean, 1)}`}
                className="outline-none"
                onPointerEnter={() => setHover(i)}
                onPointerLeave={() => setHover(null)}
                onFocus={() => setHover(i)}
                onBlur={() => setHover(null)}
              >
                <rect x={x(r.month)! - 4} y={M.top} width={x.bandwidth() + 8} height={HEIGHT - M.top - M.bottom} fill={hover === i ? "var(--surface-2)" : "transparent"} rx={6} />
                <motion.rect
                  x={x(r.month)}
                  width={x.bandwidth()}
                  rx={3}
                  fill={color}
                  initial={{ y: y(100), height: 0 }}
                  animate={{ y: inView ? top : y(100), height: inView ? bar : 0, opacity: dim ? 0.4 : 1 }}
                  transition={{ duration: 0.8, delay: hover === null ? 0.1 + i * 0.05 : 0 }}
                />
                <motion.line
                  x1={cx}
                  x2={cx}
                  y1={y(r.min)}
                  y2={y(r.max)}
                  stroke="var(--ink-2)"
                  strokeWidth={1.5}
                  strokeLinecap="round"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: inView ? (dim ? 0.3 : 0.9) : 0 }}
                  transition={{ delay: 0.9 }}
                />
                <text x={cx} y={HEIGHT - 10} textAnchor="middle" className="fill-muted text-[11px]">
                  {width < 480 ? f.monthName(r.month).charAt(0).toUpperCase() : f.monthName(r.month)}
                </text>
              </g>
            );
          })}
        </svg>
        {h && hover !== null && (
          <ChartTooltip x={x(h.month)! + x.bandwidth() / 2} y={y(h.mean)} width={width}>
            <p className="mb-1 font-medium text-ink">{f.monthName(h.month, "long")}</p>
            <TooltipRow value={f.spp(h.mean - 100)} label={t.seasonality.vsYear} color={color} />
            <TooltipRow value={`${f.spp(h.min - 100)} … ${f.spp(h.max - 100)}`} label={t.seasonality.range} />
          </ChartTooltip>
        )}
      </div>
    </ChartFrame>
  );
}

function Calendar({ fuel }: { fuel: Fuel }) {
  const { t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<string | null>(null);
  const rows = seasonality.calendar.filter((d) => d.fuel === fuel);
  const years = [...new Set(rows.map((r) => r.year))];
  const M = { top: 22, right: 0, bottom: 0, left: 40 };
  const CELL_H = 88;
  const height = years.length * CELL_H + M.top;
  const x = scaleBand<number>().domain(MONTHS).range([M.left, width - M.right]).padding(0.06);
  const y = scaleBand<number>().domain(years).range([M.top, height]).padding(0.08);
  const showText = x.bandwidth() > 30;
  const hovered = rows.find((r) => `${r.year}-${r.month}` === hover);

  return (
    <ChartFrame
      title={t.seasonality.calendarTitle}
      subtitle={t.seasonality.calendarSubtitle}
      sqlId="q2_sazonalidade"
      controls={<DivergingLegend left={t.seasonality.down} right={t.seasonality.up} steps={divergingLegend} />}
      table={{
        columns: [t.table.month, t.table.price, t.table.change],
        rows: rows.map((r) => [`${f.monthName(r.month)}/${r.year}`, f.brl3(r.price), r.mom_pct === null ? "–" : f.spp(r.mom_pct)]),
      }}
    >
      <div ref={box} className="relative">
        <svg ref={ref} width={width} height={height} role="img" aria-label={t.seasonality.calendarTitle} className="block overflow-visible">
          {MONTHS.map((m) => (
            <text key={m} x={x(m)! + x.bandwidth() / 2} y={12} textAnchor="middle" className="fill-muted text-[11px]">
              {width < 480 ? f.monthName(m).charAt(0).toUpperCase() : f.monthName(m)}
            </text>
          ))}
          {years.map((yr) => (
            <text key={yr} x={0} y={y(yr)! + y.bandwidth() / 2} dy="0.32em" className="fill-ink-2 text-[12px] font-semibold tabular">
              {yr}
            </text>
          ))}
          {rows.map((r, i) => {
            const key = `${r.year}-${r.month}`;
            const step = r.mom_pct === null ? { fill: "var(--surface-2)", ink: "var(--ink)" } : divergingStep(r.mom_pct, 3);
            return (
              <g
                key={key}
                tabIndex={0}
                role="graphics-symbol"
                aria-label={`${f.monthName(r.month)}/${r.year}: ${f.brl3(r.price)}`}
                className="outline-none"
                onPointerEnter={() => setHover(key)}
                onPointerLeave={() => setHover(null)}
                onFocus={() => setHover(key)}
                onBlur={() => setHover(null)}
              >
                <motion.rect
                  x={x(r.month)}
                  y={y(r.year)}
                  width={x.bandwidth()}
                  height={y.bandwidth()}
                  rx={6}
                  fill={step.fill}
                  stroke={hover === key ? "var(--ink)" : "none"}
                  strokeWidth={1.5}
                  initial={{ opacity: 0, scale: 0.6 }}
                  animate={{ opacity: inView ? 1 : 0, scale: inView ? 1 : 0.6 }}
                  style={{ transformBox: "fill-box", transformOrigin: "center" }}
                  transition={{ duration: 0.4, delay: 0.1 + i * 0.012 }}
                />
                {showText && (
                  <text
                    x={x(r.month)! + x.bandwidth() / 2}
                    y={y(r.year)! + y.bandwidth() / 2}
                    dy="0.32em"
                    textAnchor="middle"
                    className="pointer-events-none text-[10px] font-medium tabular sm:text-[11px]"
                    style={{ fill: step.ink }}
                  >
                    {f.dec(r.price)}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
        {hovered && (
          <ChartTooltip x={x(hovered.month)! + x.bandwidth() / 2} y={y(hovered.year)! + y.bandwidth() / 2} width={width}>
            <p className="mb-1 font-medium text-ink">
              {f.monthName(hovered.month, "long")} {hovered.year}
            </p>
            <TooltipRow value={f.brl3(hovered.price)} label="/L" />
            {hovered.mom_pct !== null && <TooltipRow value={f.spp(hovered.mom_pct)} label={hovered.mom_pct < 0 ? t.seasonality.down : t.seasonality.up} />}
          </ChartTooltip>
        )}
      </div>
    </ChartFrame>
  );
}

export function SeasonalityCharts() {
  const [fuel, setFuel] = useState<Fuel>("DIESEL");
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <FuelToggle value={fuel} onChange={setFuel} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2 [&>*]:min-w-0">
        <SeasonalIndex fuel={fuel} />
        <Calendar fuel={fuel} />
      </div>
    </div>
  );
}
