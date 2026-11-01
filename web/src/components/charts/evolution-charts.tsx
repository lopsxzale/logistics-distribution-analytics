"use client";

import { scaleBand, scaleLinear, scalePoint } from "d3-scale";
import { curveMonotoneX, line } from "d3-shape";
import { motion } from "motion/react";
import { useState } from "react";
import { evolution, FUELS, states, ufInfo, type Fuel } from "@/lib/data";
import { fill } from "@/lib/format";
import { fuelColor, fuelLabel } from "@/lib/labels";
import { useWidth } from "@/lib/use-size";
import { ChartFrame, ChartTooltip, TooltipRow } from "../chart-frame";
import { useChartInView } from "../motion";
import { useI18n } from "../providers";
import { FuelToggle } from "./brazil-map";

const HEIGHT = 440;

function IndexChart() {
  const { lang, t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<number | null>(null);
  const M = { top: 16, right: 92, bottom: 30, left: 40 };
  const months = [...new Set(evolution.national.map((d) => d.month))];
  const series = FUELS.map((fuel) => ({ fuel, rows: evolution.national.filter((d) => d.fuel === fuel) }));
  const values = evolution.national.map((d) => d.index);

  const x = scalePoint<string>().domain(months).range([M.left, width - M.right]);
  const y = scaleLinear()
    .domain([Math.min(...values) - 2, Math.max(...values) + 2])
    .nice()
    .range([HEIGHT - M.bottom, M.top]);
  const path = line<{ month: string; index: number }>()
    .x((d) => x(d.month)!)
    .y((d) => y(d.index))
    .curve(curveMonotoneX);
  const step = width < 560 ? 12 : 6;

  const onMove = (clientX: number, rect: DOMRect) => {
    const px = clientX - rect.left;
    let best = 0;
    months.forEach((m, i) => {
      if (Math.abs(x(m)! - px) < Math.abs(x(months[best])! - px)) best = i;
    });
    setHover(best);
  };

  return (
    <ChartFrame
      title={t.evolution.indexTitle}
      subtitle={t.evolution.indexSubtitle}
      sqlId="q1_variacao_preco_tempo"
      legend={FUELS.map((fu) => ({ label: fuelLabel(fu, lang), color: fuelColor[fu], shape: "line" as const }))}
      table={{
        columns: [t.table.month, ...FUELS.map((fu) => fuelLabel(fu, lang))],
        rows: months.map((m, i) => [f.month(m), ...series.map((s) => `${f.brl3(s.rows[i].price)} · ${f.dec(s.rows[i].index, 1)}`)]),
      }}
    >
      <div ref={box} className="relative">
        <svg
          ref={ref}
          width={width}
          height={HEIGHT}
          role="img"
          aria-label={t.evolution.indexTitle}
          className="block touch-pan-y overflow-visible"
          onPointerMove={(e) => onMove(e.clientX, e.currentTarget.getBoundingClientRect())}
          onPointerLeave={() => setHover(null)}
        >
          {y.ticks(5).map((tick) => (
            <g key={tick}>
              <line x1={M.left} x2={width - M.right} y1={y(tick)} y2={y(tick)} stroke={tick === 100 ? "var(--axis)" : "var(--grid)"} />
              <text x={M.left - 8} y={y(tick)} dy="0.32em" textAnchor="end" className="fill-muted text-[11px] tabular">
                {tick}
              </text>
            </g>
          ))}
          {months.map((m, i) =>
            i % step === 0 ? (
              <text key={m} x={x(m)} y={HEIGHT - 8} textAnchor="middle" className="fill-muted text-[11px]">
                {f.month(m)}
              </text>
            ) : null,
          )}
          {hover !== null && <line x1={x(months[hover])} x2={x(months[hover])} y1={M.top} y2={HEIGHT - M.bottom} stroke="var(--axis)" />}
          {series.map((s, i) => {
            const last = s.rows[s.rows.length - 1];
            return (
              <g key={s.fuel}>
                <motion.path
                  d={path(s.rows)!}
                  fill="none"
                  stroke={fuelColor[s.fuel]}
                  strokeWidth={2}
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: inView ? 1 : 0 }}
                  transition={{ duration: 1.6, delay: i * 0.2, ease: [0.65, 0, 0.35, 1] }}
                />
                <motion.text
                  x={x(last.month)! + 8}
                  y={y(last.index)}
                  dy="0.32em"
                  className="fill-ink text-[12px] font-semibold tabular"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: inView ? 1 : 0 }}
                  transition={{ delay: 1.6 + i * 0.2 }}
                >
                  {fuelLabel(s.fuel, lang)} {f.spp(last.index - 100)}
                </motion.text>
                {hover !== null && (
                  <circle cx={x(months[hover])} cy={y(s.rows[hover].index)} r={4.5} fill={fuelColor[s.fuel]} stroke="var(--surface)" strokeWidth={2} />
                )}
              </g>
            );
          })}
        </svg>
        {hover !== null && (
          <ChartTooltip x={x(months[hover])!} y={HEIGHT / 2} width={width}>
            <p className="mb-1 font-medium text-ink">{f.month(months[hover], "long")}</p>
            {series.map((s) => (
              <TooltipRow key={s.fuel} value={f.brl3(s.rows[hover].price)} label={fuelLabel(s.fuel, lang)} color={fuelColor[s.fuel]} />
            ))}
          </ChartTooltip>
        )}
      </div>
    </ChartFrame>
  );
}

function Dumbbell() {
  const { lang, t, f } = useI18n();
  const [fuel, setFuel] = useState<Fuel>("DIESEL");
  const [box, width] = useWidth<HTMLDivElement>(420);
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<string | null>(null);
  const rows = states.states.filter((s) => s.fuel === fuel).sort((a, b) => a.change_pct - b.change_pct);
  const ROW = 17;
  const M = { top: 4, right: 56, bottom: 26, left: 34 };
  const height = rows.length * ROW + M.top + M.bottom;
  const all = rows.flatMap((r) => [r.price, r.price_start]);
  const x = scaleLinear()
    .domain([Math.min(...all), Math.max(...all)])
    .nice()
    .range([M.left, width - M.right]);
  const y = scaleBand<string>().domain(rows.map((r) => r.uf)).range([M.top, height - M.bottom]);
  const color = fuelColor[fuel];
  const hovered = rows.find((r) => r.uf === hover);

  return (
    <ChartFrame
      title={t.evolution.dumbbellTitle}
      subtitle={fill(t.evolution.dumbbellSubtitle, { start: f.month(states.first_month), end: f.month(states.last_month) })}
      sqlId="q1_variacao_preco_tempo"
      controls={<FuelToggle value={fuel} onChange={setFuel} />}
      table={{
        columns: [t.table.state, f.month(states.first_month), f.month(states.last_month), t.table.change],
        rows: rows.map((r) => [ufInfo[r.uf].name, f.brl3(r.price_start), f.brl3(r.price), f.spp(r.change_pct)]),
      }}
    >
      <div ref={box} className="relative">
        <svg ref={ref} width={width} height={height} role="img" aria-label={`${t.evolution.dumbbellTitle} · ${fuelLabel(fuel, lang)}`} className="block overflow-visible">
          {x.ticks(width < 420 ? 3 : 5).map((tick) => (
            <g key={tick}>
              <line x1={x(tick)} x2={x(tick)} y1={M.top} y2={height - M.bottom} stroke="var(--grid)" />
              <text x={x(tick)} y={height - 8} textAnchor="middle" className="fill-muted text-[11px] tabular">
                {f.brl(tick)}
              </text>
            </g>
          ))}
          {rows.map((r, i) => {
            const cy = y(r.uf)! + y.bandwidth() / 2;
            const dim = hover !== null && hover !== r.uf;
            return (
              <g
                key={r.uf}
                tabIndex={0}
                role="graphics-symbol"
                aria-label={`${ufInfo[r.uf].name}: ${f.brl3(r.price_start)} → ${f.brl3(r.price)} (${f.spp(r.change_pct)})`}
                className="outline-none"
                opacity={dim ? 0.35 : 1}
                onPointerEnter={() => setHover(r.uf)}
                onPointerLeave={() => setHover(null)}
                onFocus={() => setHover(r.uf)}
                onBlur={() => setHover(null)}
              >
                <rect x={0} y={y(r.uf)} width={width} height={y.bandwidth()} fill="transparent" />
                <text x={M.left - 8} y={cy} dy="0.32em" textAnchor="end" className="fill-ink-2 font-mono text-[10px]">
                  {r.uf}
                </text>
                <motion.line
                  y1={cy}
                  y2={cy}
                  stroke={color}
                  strokeOpacity={0.45}
                  strokeWidth={2}
                  initial={{ x1: x(r.price_start), x2: x(r.price_start) }}
                  animate={{ x1: x(r.price_start), x2: inView ? x(r.price) : x(r.price_start) }}
                  transition={{ duration: 0.8, delay: 0.2 + i * 0.02 }}
                />
                <circle cx={x(r.price_start)} cy={cy} r={3.5} fill="var(--surface)" stroke={color} strokeWidth={1.5} />
                <motion.circle
                  cy={cy}
                  r={4}
                  fill={color}
                  initial={{ cx: x(r.price_start) }}
                  animate={{ cx: inView ? x(r.price) : x(r.price_start) }}
                  transition={{ duration: 0.8, delay: 0.2 + i * 0.02 }}
                />
                <text x={width - M.right + 8} y={cy} dy="0.32em" className="fill-ink-2 text-[10px] tabular">
                  {f.spp(r.change_pct)}
                </text>
              </g>
            );
          })}
        </svg>
        {hovered && (
          <ChartTooltip x={x(hovered.price)} y={y(hovered.uf)! + y.bandwidth() / 2} width={width}>
            <p className="mb-1 font-medium text-ink">{ufInfo[hovered.uf].name}</p>
            <TooltipRow value={f.brl3(hovered.price_start)} label={t.evolution.start} />
            <TooltipRow value={f.brl3(hovered.price)} label={t.evolution.end} color={color} />
            <TooltipRow value={f.spp(hovered.change_pct)} label="" />
          </ChartTooltip>
        )}
      </div>
    </ChartFrame>
  );
}

export function EvolutionCharts() {
  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] [&>*]:min-w-0">
      <IndexChart />
      <Dumbbell />
    </div>
  );
}
