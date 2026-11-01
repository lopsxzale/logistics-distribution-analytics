"use client";

import { scaleBand, scaleLinear, scalePoint } from "d3-scale";
import { area, curveMonotoneX, line } from "d3-shape";
import { AnimatePresence, motion } from "motion/react";
import { useMemo, useState } from "react";
import { seasonality, simulator, ufInfo, ufs, type Fuel } from "@/lib/data";
import { fill } from "@/lib/format";
import { fuelColor } from "@/lib/labels";
import { useWidth } from "@/lib/use-size";
import { FuelToggle } from "./charts/brazil-map";
import { ChartFrame, ChartTooltip, TooltipRow } from "./chart-frame";
import { useI18n } from "./providers";

const DEFAULTS: Record<Fuel, { km: number; consumption: number }> = {
  DIESEL: { km: 10_000, consumption: 2.8 },
  GASOLINA: { km: 3_000, consumption: 11 },
  ETANOL: { km: 3_000, consumption: 7.7 },
};
// Corredor típico de distribuição (Sul–Sudeste–Centro-Oeste–Nordeste), editável.
const CORRIDOR = ["PR", "SP", "RJ", "MG", "GO", "MT", "BA", "PE"];

/** Custo mensal de combustível: litros consumidos × preço (mesma fórmula de src/metrics.py:custo_frota). */
const fleetCost = (price: number, km: number, consumption: number, vehicles: number) =>
  price * (km / consumption) * vehicles;

function Field({
  label,
  hint,
  value,
  min,
  max,
  step,
  format,
  onChange,
}: {
  label: string;
  hint?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  format: (v: number) => string;
  onChange: (v: number) => void;
}) {
  return (
    <label className="block">
      <span className="flex items-baseline justify-between gap-2 text-sm">
        <span className="text-ink-2">{label}</span>
        <span className="font-semibold tabular text-ink">{format(value)}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full accent-[var(--brand)]"
      />
      {hint && <span className="mt-1 block text-xs text-muted">{hint}</span>}
    </label>
  );
}

function CostBars({ rows, color }: { rows: { uf: string; price: number; cost: number }[]; color: string }) {
  const { t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<string | null>(null);
  const ROW = 26;
  const M = { left: 128, right: 84 };
  const height = rows.length * ROW;
  const x = scaleLinear().domain([0, Math.max(...rows.map((r) => r.cost))]).range([M.left, width - M.right]);
  const y = scaleBand<string>().domain(rows.map((r) => r.uf)).range([0, height]).padding(0.25);
  const ends = new Set([rows[0].uf, rows[rows.length - 1].uf]);
  const hovered = rows.find((r) => r.uf === hover);

  return (
    <div ref={box} className="relative">
      <svg width={width} height={height} role="img" aria-label={t.simulator.costTitle} className="block overflow-visible">
        {rows.map((r) => (
          <g
            key={r.uf}
            tabIndex={0}
            role="graphics-symbol"
            aria-label={`${ufInfo[r.uf].name}: ${f.brl0(r.cost)}`}
            className="outline-none"
            onPointerEnter={() => setHover(r.uf)}
            onPointerLeave={() => setHover(null)}
            onFocus={() => setHover(r.uf)}
            onBlur={() => setHover(null)}
          >
            <rect x={0} y={y(r.uf)} width={width} height={y.bandwidth()} fill="transparent" />
            <text x={M.left - 10} y={y(r.uf)! + y.bandwidth() / 2} dy="0.32em" textAnchor="end" className={`text-[12px] ${ends.has(r.uf) ? "fill-ink font-semibold" : "fill-ink-2"}`}>
              {width < 380 ? r.uf : ufInfo[r.uf].name}
            </text>
            <motion.rect
              x={M.left}
              y={y(r.uf)}
              height={y.bandwidth()}
              rx={3}
              fill={color}
              initial={false}
              animate={{ width: Math.max(x(r.cost) - M.left, 1), opacity: ends.has(r.uf) || hover === r.uf ? 1 : 0.5 }}
              transition={{ type: "spring", bounce: 0.15, duration: 0.6 }}
            />
            <motion.text
              y={y(r.uf)! + y.bandwidth() / 2}
              dy="0.32em"
              className="fill-ink-2 text-[11px] tabular"
              initial={false}
              animate={{ x: x(r.cost) + 6 }}
              transition={{ type: "spring", bounce: 0.15, duration: 0.6 }}
            >
              {f.brl0(r.cost)}
            </motion.text>
          </g>
        ))}
      </svg>
      {hovered && (
        <ChartTooltip x={x(hovered.cost)} y={y(hovered.uf)! + y.bandwidth() / 2} width={width}>
          <p className="mb-1 font-medium text-ink">{ufInfo[hovered.uf].name}</p>
          <TooltipRow value={f.brl0(hovered.cost)} label={t.simulator.perMonth} color={color} />
          <TooltipRow value={fill(t.simulator.perLiter, { price: f.brl3(hovered.price) })} label="" />
        </ChartTooltip>
      )}
    </div>
  );
}

function Projection({ rows, color }: { rows: { month: string; mean: number; min: number; max: number }[]; color: string }) {
  const { t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const HEIGHT = 260;
  const M = { top: 12, right: 12, bottom: 28, left: 72 };
  const x = scalePoint<string>().domain(rows.map((r) => r.month)).range([M.left, width - M.right]);
  const lo = Math.min(...rows.map((r) => r.min));
  const hi = Math.max(...rows.map((r) => r.max));
  const pad = (hi - lo) * 0.15 || hi * 0.05;
  const y = scaleLinear().domain([lo - pad, hi + pad]).nice().range([HEIGHT - M.bottom, M.top]);
  const band = area<(typeof rows)[number]>()
    .x((d) => x(d.month)!)
    .y0((d) => y(d.min))
    .y1((d) => y(d.max))
    .curve(curveMonotoneX)(rows)!;
  const path = line<(typeof rows)[number]>()
    .x((d) => x(d.month)!)
    .y((d) => y(d.mean))
    .curve(curveMonotoneX)(rows)!;
  const h = hover === null ? null : rows[hover];

  return (
    <div ref={box} className="relative">
      <svg
        width={width}
        height={HEIGHT}
        role="img"
        aria-label={t.simulator.projectionTitle}
        className="block touch-pan-y overflow-visible"
        onPointerMove={(e) => {
          const px = e.clientX - e.currentTarget.getBoundingClientRect().left;
          let best = 0;
          rows.forEach((r, i) => {
            if (Math.abs(x(r.month)! - px) < Math.abs(x(rows[best].month)! - px)) best = i;
          });
          setHover(best);
        }}
        onPointerLeave={() => setHover(null)}
      >
        {y.ticks(4).map((tick) => (
          <g key={tick}>
            <line x1={M.left} x2={width - M.right} y1={y(tick)} y2={y(tick)} stroke="var(--grid)" />
            <text x={M.left - 8} y={y(tick)} dy="0.32em" textAnchor="end" className="fill-muted text-[11px] tabular">
              {f.brlCompact(tick)}
            </text>
          </g>
        ))}
        {rows.map((r, i) =>
          i % (width < 480 ? 3 : 2) === 0 ? (
            <text key={r.month} x={x(r.month)} y={HEIGHT - 8} textAnchor="middle" className="fill-muted text-[11px]">
              {f.month(r.month)}
            </text>
          ) : null,
        )}
        <motion.path d={band} fill={color} initial={false} animate={{ d: band, opacity: 0.16 }} transition={{ duration: 0.5 }} />
        <motion.path d={path} fill="none" stroke={color} strokeWidth={2} initial={false} animate={{ d: path }} transition={{ duration: 0.5 }} />
        {rows.map((r) => (
          <motion.circle key={r.month} cx={x(r.month)} r={4} fill={color} stroke="var(--surface)" strokeWidth={2} initial={false} animate={{ cy: y(r.mean) }} transition={{ duration: 0.5 }} />
        ))}
        {h && <line x1={x(h.month)} x2={x(h.month)} y1={M.top} y2={HEIGHT - M.bottom} stroke="var(--axis)" />}
      </svg>
      {h && (
        <ChartTooltip x={x(h.month)!} y={y(h.mean)} width={width}>
          <p className="mb-1 font-medium text-ink">{f.month(h.month, "long")}</p>
          <TooltipRow value={f.brl0(h.mean)} label="" color={color} />
          <TooltipRow value={`${f.brl0(h.min)} … ${f.brl0(h.max)}`} label="" />
        </ChartTooltip>
      )}
    </div>
  );
}

export function Simulator() {
  const { t, f } = useI18n();
  const [fuel, setFuel] = useState<Fuel>("DIESEL");
  const [km, setKm] = useState(DEFAULTS.DIESEL.km);
  const [consumption, setConsumption] = useState(DEFAULTS.DIESEL.consumption);
  const [vehicles, setVehicles] = useState(10);
  const [selected, setSelected] = useState<string[]>(CORRIDOR);
  const color = fuelColor[fuel];

  const changeFuel = (next: Fuel) => {
    setFuel(next);
    setKm(DEFAULTS[next].km);
    setConsumption(DEFAULTS[next].consumption);
  };
  const toggle = (uf: string) => setSelected((s) => (s.includes(uf) ? s.filter((x) => x !== uf) : [...s, uf]));

  const result = useMemo(() => {
    const prices = simulator.prices.filter((p) => p.fuel === fuel && selected.includes(p.uf));
    if (!prices.length) return null;
    const rows = prices
      .map((p) => ({ uf: p.uf, price: p.price, cost: fleetCost(p.price, km, consumption, vehicles) }))
      .sort((a, b) => a.cost - b.cost);
    const liters = (km / consumption) * vehicles;
    const avgCost = rows.reduce((s, r) => s + r.cost, 0) / rows.length;
    const avgPrice = rows.reduce((s, r) => s + r.price, 0) / rows.length;
    // Próximos 12 meses a partir do último mês com dados, ajustados pelo índice sazonal histórico.
    const [y0, m0] = simulator.last_month.split("-").map(Number);
    const index = seasonality.index.filter((s) => s.fuel === fuel);
    const projection = Array.from({ length: 12 }, (_, i) => {
      const d = new Date(Date.UTC(y0, m0 + i, 1));
      const s = index.find((x) => x.month === d.getUTCMonth() + 1)!;
      const base = (liters * avgPrice) / 100;
      return {
        month: `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}`,
        mean: base * s.mean,
        min: base * s.min,
        max: base * s.max,
      };
    });
    const peak = projection.reduce((a, b) => (b.mean > a.mean ? b : a));
    return { rows, liters, avgCost, projection, peak, cheap: rows[0], pricey: rows[rows.length - 1] };
  }, [fuel, km, consumption, vehicles, selected]);

  return (
    <div className="grid gap-4 lg:grid-cols-[340px_minmax(0,1fr)]">
      <div className="card h-fit space-y-6 p-5 sm:p-6 lg:sticky lg:top-24">
        <FuelToggle value={fuel} onChange={changeFuel} />
        <Field label={t.simulator.inputs.km} value={km} min={500} max={30_000} step={500} format={f.int} onChange={setKm} />
        <Field
          label={t.simulator.inputs.consumption}
          hint={t.simulator.inputs.consumptionHint}
          value={consumption}
          min={1}
          max={20}
          step={0.1}
          format={(v) => f.dec(v, 1)}
          onChange={setConsumption}
        />
        <Field label={t.simulator.inputs.vehicles} value={vehicles} min={1} max={200} step={1} format={f.int} onChange={setVehicles} />
        <fieldset>
          <legend className="flex w-full items-center justify-between text-sm text-ink-2">
            {t.simulator.inputs.states}
            <span className="flex gap-1 text-xs">
              {[
                { label: t.simulator.inputs.corridor, value: CORRIDOR },
                { label: t.simulator.inputs.all, value: ufs.map((u) => u.uf) },
                { label: t.simulator.inputs.none, value: [] },
              ].map((b) => (
                <button key={b.label} type="button" onClick={() => setSelected(b.value)} className="rounded-full px-2 py-1 text-muted transition hover:bg-surface-2 hover:text-ink">
                  {b.label}
                </button>
              ))}
            </span>
          </legend>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {ufs.map((u) => {
              const on = selected.includes(u.uf);
              return (
                <button
                  key={u.uf}
                  type="button"
                  aria-pressed={on}
                  title={u.name}
                  onClick={() => toggle(u.uf)}
                  className={`w-11 rounded-lg py-1.5 font-mono text-xs font-semibold transition ${
                    on ? "bg-accent text-brand-ink" : "bg-surface-2 text-muted hover:text-ink"
                  }`}
                >
                  {u.uf}
                </button>
              );
            })}
          </div>
        </fieldset>
      </div>

      <AnimatePresence mode="wait" initial={false}>
        {result ? (
          <motion.div key="result" className="min-w-0 space-y-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-line bg-line xl:grid-cols-4">
              {[
                { label: t.simulator.kpis.liters, value: f.int(result.liters) },
                { label: t.simulator.kpis.monthly, value: f.brl0(result.avgCost) },
                { label: t.simulator.kpis.yearly, value: f.brlCompact(result.avgCost * 12) },
                {
                  label: t.simulator.kpis.savings,
                  value: f.brl0(result.pricey.cost - result.cheap.cost),
                  note: fill(t.simulator.kpis.savingsNote, { cheap: ufInfo[result.cheap.uf].name, pricey: ufInfo[result.pricey.uf].name }),
                  strong: true,
                },
              ].map((k) => (
                <div key={k.label} className={`p-4 sm:p-5 ${k.strong ? "bg-accent/10" : "bg-surface"}`}>
                  <dt className="text-xs text-muted">{k.label}</dt>
                  <dd className={`mt-1 text-xl font-semibold tracking-tight tabular sm:text-2xl ${k.strong ? "text-accent-ink" : "text-ink"}`}>{k.value}</dd>
                  {k.note && <dd className="mt-1 text-xs text-ink-2">{k.note}</dd>}
                </div>
              ))}
            </dl>
            <ChartFrame
              title={t.simulator.costTitle}
              subtitle={t.simulator.costSubtitle}
              table={{
                columns: [t.table.state, t.table.price, t.table.cost],
                rows: result.rows.map((r) => [ufInfo[r.uf].name, f.brl3(r.price), f.brl0(r.cost)]),
              }}
            >
              <CostBars rows={result.rows} color={color} />
            </ChartFrame>
            <ChartFrame
              title={t.simulator.projectionTitle}
              subtitle={t.simulator.projectionSubtitle}
              sqlId="q2_sazonalidade"
              table={{
                columns: [t.table.month, t.table.cost, "min", "max"],
                rows: result.projection.map((p) => [f.month(p.month), f.brl0(p.mean), f.brl0(p.min), f.brl0(p.max)]),
              }}
            >
              <Projection rows={result.projection} color={color} />
              <p className="mt-3 text-xs text-muted">
                <span className="font-semibold text-ink-2">{fill(t.simulator.peak, { month: f.month(result.peak.month, "long") })}.</span>{" "}
                {t.simulator.projectionNote}
              </p>
            </ChartFrame>
          </motion.div>
        ) : (
          <motion.div key="empty" className="card grid min-h-64 place-items-center p-6 text-sm text-muted" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            {t.simulator.empty}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
