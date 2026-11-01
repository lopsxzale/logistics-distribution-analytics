"use client";

import { median } from "d3-array";
import { scaleBand, scaleLinear } from "d3-scale";
import { motion } from "motion/react";
import { useState } from "react";
import { risk, ufInfo, type Fuel } from "@/lib/data";
import { fuelColor } from "@/lib/labels";
import { useWidth } from "@/lib/use-size";
import { ChartFrame, ChartTooltip, TooltipRow } from "../chart-frame";
import { useChartInView } from "../motion";
import { useI18n } from "../providers";
import { FuelToggle } from "./brazil-map";

type Row = (typeof risk.states)[number];

function Scatter({ rows, fuel }: { rows: Row[]; fuel: Fuel }) {
  const { t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<string | null>(null);
  const HEIGHT = 380;
  const M = { top: 32, right: 20, bottom: 44, left: 48 };
  const px = rows.map((r) => r.price);
  const vy = rows.map((r) => r.volatility);
  const padX = (Math.max(...px) - Math.min(...px)) * 0.06;
  const x = scaleLinear().domain([Math.min(...px) - padX, Math.max(...px) + padX]).nice().range([M.left, width - M.right]);
  const y = scaleLinear().domain([0, Math.max(...vy) * 1.1]).nice().range([HEIGHT - M.bottom, M.top]);
  const mx = median(px)!;
  const my = median(vy)!;
  const color = fuelColor[fuel];
  // Rótulos fixos só nos estados que contam a história: os 3 mais voláteis, o mais caro e o mais barato.
  const byVol = [...rows].sort((a, b) => b.volatility - a.volatility);
  const byPrice = [...rows].sort((a, b) => b.price - a.price);
  const labeled = new Set([...byVol.slice(0, 3), byPrice[0], byPrice[byPrice.length - 1]].map((r) => r.uf));
  const hovered = rows.find((r) => r.uf === hover);
  const q = t.risk.quadrants;

  return (
    <div ref={box} className="relative">
      <svg ref={ref} width={width} height={HEIGHT} role="img" aria-label={t.risk.scatterTitle} className="block overflow-visible">
        {y.ticks(5).map((tick) => (
          <g key={tick}>
            <line x1={M.left} x2={width - M.right} y1={y(tick)} y2={y(tick)} stroke="var(--grid)" />
            <text x={M.left - 8} y={y(tick)} dy="0.32em" textAnchor="end" className="fill-muted text-[11px] tabular">
              {f.pp(tick, 0)}
            </text>
          </g>
        ))}
        {x.ticks(width < 520 ? 4 : 7).map((tick) => (
          <text key={tick} x={x(tick)} y={HEIGHT - M.bottom + 18} textAnchor="middle" className="fill-muted text-[11px] tabular">
            {f.dec(tick)}
          </text>
        ))}
        <text x={width - M.right} y={HEIGHT - 4} textAnchor="end" className="fill-muted text-[11px]">
          {t.risk.xLabel} →
        </text>
        <text x={M.left - 40} y={10} className="fill-muted text-[11px]">
          ↑ {t.risk.yLabel}
        </text>
        <line x1={M.left} x2={width - M.right} y1={HEIGHT - M.bottom} y2={HEIGHT - M.bottom} stroke="var(--axis)" />
        <line x1={x(mx)} x2={x(mx)} y1={M.top} y2={HEIGHT - M.bottom} stroke="var(--axis)" strokeDasharray="4 4" />
        <line x1={M.left} x2={width - M.right} y1={y(my)} y2={y(my)} stroke="var(--axis)" strokeDasharray="4 4" />
        {width > 520 &&
          [
            { label: q.cheapVolatile, x: M.left + 8, y: M.top + 14, anchor: "start" },
            { label: q.priceyVolatile, x: width - M.right - 8, y: M.top + 14, anchor: "end" },
            { label: q.cheapStable, x: M.left + 8, y: HEIGHT - M.bottom - 10, anchor: "start" },
            { label: q.priceyStable, x: width - M.right - 8, y: HEIGHT - M.bottom - 10, anchor: "end" },
          ].map((l) => (
            <text key={l.label} x={l.x} y={l.y} textAnchor={l.anchor as "start" | "end"} className="fill-muted text-[11px] uppercase tracking-wider">
              {l.label}
            </text>
          ))}
        {rows.map((r, i) => {
          const dim = hover !== null && hover !== r.uf;
          return (
            <g
              key={r.uf}
              tabIndex={0}
              role="graphics-symbol"
              aria-label={`${ufInfo[r.uf].name}: ${f.brl3(r.price)}, ±${f.pp(r.volatility)}`}
              className="outline-none"
              onPointerEnter={() => setHover(r.uf)}
              onPointerLeave={() => setHover(null)}
              onFocus={() => setHover(r.uf)}
              onBlur={() => setHover(null)}
            >
              <circle cx={x(r.price)} cy={y(r.volatility)} r={13} fill="transparent" />
              <motion.circle
                cx={x(r.price)}
                cy={y(r.volatility)}
                fill={color}
                stroke="var(--surface)"
                strokeWidth={2}
                initial={{ r: 0 }}
                animate={{ r: inView ? (hover === r.uf ? 8 : 6) : 0, opacity: dim ? 0.3 : 1 }}
                transition={{ r: { duration: 0.5, delay: hover ? 0 : 0.2 + i * 0.03 }, opacity: { duration: 0.2 } }}
              />
              {(labeled.has(r.uf) || hover === r.uf) && (
                <motion.text
                  x={x(r.price) + 10}
                  y={y(r.volatility)}
                  dy="0.32em"
                  className="pointer-events-none fill-ink-2 text-[11px] font-semibold"
                  style={{ paintOrder: "stroke", stroke: "var(--surface)", strokeWidth: 3 }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: inView ? (dim ? 0.3 : 1) : 0 }}
                  transition={{ delay: hover ? 0 : 1.2 }}
                >
                  {r.uf}
                </motion.text>
              )}
            </g>
          );
        })}
      </svg>
      {hovered && (
        <ChartTooltip x={x(hovered.price)} y={y(hovered.volatility)} width={width}>
          <p className="mb-1 font-medium text-ink">{ufInfo[hovered.uf].name}</p>
          <TooltipRow value={f.brl3(hovered.price)} label={t.risk.price} color={color} />
          <TooltipRow value={`±${f.pp(hovered.volatility)}`} label={t.risk.volatility} />
          <TooltipRow value={f.pp(hovered.dispersion)} label={t.risk.dispersion} />
        </ChartTooltip>
      )}
    </div>
  );
}

function Dispersion({ rows, fuel }: { rows: Row[]; fuel: Fuel }) {
  const { t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>(320);
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const top = [...rows].sort((a, b) => b.dispersion - a.dispersion).slice(0, 12);
  const ROW = 26;
  const M = { left: 128, right: 48 };
  const height = top.length * ROW;
  const x = scaleLinear().domain([0, top[0].dispersion]).range([M.left, width - M.right]);
  const y = scaleBand<string>().domain(top.map((r) => r.uf)).range([0, height]).padding(0.28);

  return (
    <div ref={box}>
      <svg ref={ref} width={width} height={height} role="img" aria-label={t.risk.dispersionTitle} className="block overflow-visible">
        {top.map((r, i) => (
          <g key={r.uf}>
            <text x={M.left - 10} y={y(r.uf)! + y.bandwidth() / 2} dy="0.32em" textAnchor="end" className="fill-ink-2 text-[12px]">
              {width < 360 ? r.uf : ufInfo[r.uf].name}
            </text>
            <motion.rect
              x={M.left}
              y={y(r.uf)}
              height={y.bandwidth()}
              rx={3}
              fill={fuelColor[fuel]}
              initial={{ width: 0 }}
              animate={{ width: inView ? x(r.dispersion) - M.left : 0 }}
              transition={{ duration: 0.9, delay: 0.1 + i * 0.05 }}
            />
            <motion.text
              x={x(r.dispersion) + 6}
              y={y(r.uf)! + y.bandwidth() / 2}
              dy="0.32em"
              className="fill-ink-2 text-[11px] tabular"
              initial={{ opacity: 0 }}
              animate={{ opacity: inView ? 1 : 0 }}
              transition={{ delay: 0.9 }}
            >
              {f.pp(r.dispersion)}
            </motion.text>
          </g>
        ))}
      </svg>
    </div>
  );
}

export function RiskCharts() {
  const { t, f } = useI18n();
  const [fuel, setFuel] = useState<Fuel>("DIESEL");
  const rows = risk.states.filter((r) => r.fuel === fuel);
  const table = {
    columns: [t.table.state, t.table.price, t.risk.volatility, t.risk.dispersion],
    rows: [...rows]
      .sort((a, b) => b.volatility - a.volatility)
      .map((r) => [ufInfo[r.uf].name, f.brl3(r.price), `±${f.pp(r.volatility)}`, f.pp(r.dispersion)]),
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <FuelToggle value={fuel} onChange={setFuel} />
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,7fr)_minmax(0,4fr)] [&>*]:min-w-0">
        <ChartFrame title={t.risk.scatterTitle} subtitle={t.risk.scatterSubtitle} sqlId="q3_volatilidade_estado" table={table}>
          <Scatter rows={rows} fuel={fuel} />
        </ChartFrame>
        <ChartFrame title={t.risk.dispersionTitle} subtitle={t.risk.dispersionSubtitle} sqlId="q3_volatilidade_estado" table={table}>
          <Dispersion rows={rows} fuel={fuel} />
        </ChartFrame>
      </div>
    </div>
  );
}
