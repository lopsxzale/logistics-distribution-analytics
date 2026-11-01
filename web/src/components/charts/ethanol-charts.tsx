"use client";

import { scaleBand, scaleLinear } from "d3-scale";
import { motion } from "motion/react";
import { useState } from "react";
import { ethanol, ufInfo, type MapShapes } from "@/lib/data";
import { divergingLegend, divergingStep, fuelColor, fuelLabel } from "@/lib/labels";
import { useWidth } from "@/lib/use-size";
import { ChartFrame, ChartTooltip, TooltipRow } from "../chart-frame";
import { useChartInView } from "../motion";
import { useI18n } from "../providers";
import { BrazilMap, DivergingLegend } from "./brazil-map";

const LIMIT_PP = 8; // a cor satura 8 p.p. acima ou abaixo da linha de 70%

function ShareChart() {
  const { t, f } = useI18n();
  const [box, width] = useWidth<HTMLDivElement>();
  const [ref, inView] = useChartInView<SVGSVGElement>();
  const [hover, setHover] = useState<number | null>(null);
  const HEIGHT = 400;
  const M = { top: 12, right: 8, bottom: 28, left: 40 };
  const rows = ethanol.monthly;
  const x = scaleBand<string>().domain(rows.map((r) => r.month)).range([M.left, width - M.right]).padding(0.2);
  const y = scaleLinear().domain([0, 1]).range([HEIGHT - M.bottom, M.top]);
  const step = width < 560 ? 12 : 6;
  const h = hover === null ? null : rows[hover];

  return (
    <div ref={box} className="relative">
      <svg ref={ref} width={width} height={HEIGHT} role="img" aria-label={t.ethanol.shareTitle} className="block overflow-visible">
        {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
          <g key={tick}>
            <line x1={M.left} x2={width - M.right} y1={y(tick)} y2={y(tick)} stroke="var(--grid)" />
            <text x={M.left - 8} y={y(tick)} dy="0.32em" textAnchor="end" className="fill-muted text-[11px] tabular">
              {f.pct(tick, 0)}
            </text>
          </g>
        ))}
        {rows.map((r, i) => (
          <g
            key={r.month}
            tabIndex={0}
            role="graphics-symbol"
            aria-label={`${f.month(r.month)}: ${r.states}`}
            className="outline-none"
            onPointerEnter={() => setHover(i)}
            onPointerLeave={() => setHover(null)}
            onFocus={() => setHover(i)}
            onBlur={() => setHover(null)}
          >
            <rect x={x(r.month)} y={M.top} width={x.bandwidth()} height={HEIGHT - M.top - M.bottom} fill="transparent" />
            <motion.rect
              x={x(r.month)}
              width={x.bandwidth()}
              rx={Math.min(3, x.bandwidth() / 3)}
              fill={fuelColor.ETANOL}
              initial={{ y: y(0), height: 0 }}
              animate={{
                y: inView ? y(r.share) : y(0),
                height: inView ? Math.max(y(0) - y(r.share), r.share > 0 ? 2 : 0) : 0,
                opacity: hover === null || hover === i ? 1 : 0.4,
              }}
              transition={{ duration: 0.7, delay: hover === null ? 0.1 + i * 0.015 : 0 }}
            />
            {i % step === 0 && (
              <text x={x(r.month)! + x.bandwidth() / 2} y={HEIGHT - 8} textAnchor="middle" className="fill-muted text-[11px]">
                {f.month(r.month)}
              </text>
            )}
          </g>
        ))}
        <line x1={M.left} x2={width - M.right} y1={y(0)} y2={y(0)} stroke="var(--axis)" />
      </svg>
      {h && hover !== null && (
        <ChartTooltip x={x(h.month)! + x.bandwidth() / 2} y={y(h.share) - 10} width={width}>
          <p className="mb-1 font-medium text-ink">{f.month(h.month, "long")}</p>
          <TooltipRow value={`${h.states}`} label={t.ethanol.statesLabel} color={fuelColor.ETANOL} />
          <TooltipRow value={f.pct(h.ratio)} label={t.ethanol.ratio} />
        </ChartTooltip>
      )}
    </div>
  );
}

export function EthanolCharts({ shapes }: { shapes: MapShapes }) {
  const { lang, t, f } = useI18n();
  const byUf = Object.fromEntries(ethanol.states.map((s) => [s.uf, s]));
  // Quem fica abaixo de 70% sempre ganha a cor de 'compensa', mesmo colado na linha de corte.
  const pts = (ratio: number) => {
    const v = (ratio - ethanol.threshold) * 100;
    return v <= 0 ? Math.min(v, -1.4) : v;
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,6fr)_minmax(0,6fr)] [&>*]:min-w-0">
      <ChartFrame
        title={t.ethanol.mapTitle}
        subtitle={t.ethanol.mapSubtitle}
        sqlId="q5_paridade_etanol_gasolina"
        controls={<DivergingLegend left={t.ethanol.worth} right={t.ethanol.notWorth} steps={divergingLegend} />}
        table={{
          columns: [t.table.state, fuelLabel("ETANOL", lang), fuelLabel("GASOLINA", lang), t.ethanol.ratio],
          rows: ethanol.states.map((s) => [ufInfo[s.uf].name, f.brl3(s.ethanol), f.brl3(s.gasoline), f.pct(s.ratio)]),
        }}
      >
        <BrazilMap
          shapes={shapes}
          ariaLabel={t.ethanol.mapTitle}
          highlight={ethanol.states.filter((s) => s.worth).map((s) => s.uf)}
          fillOf={(uf) => (byUf[uf] ? divergingStep(pts(byUf[uf].ratio), LIMIT_PP).fill : undefined)}
          label={(uf) => `${ufInfo[uf].name}: ${byUf[uf] ? f.pct(byUf[uf].ratio) : "–"}`}
          tooltip={(uf) => (
            <>
              <p className="mb-1 font-medium text-ink">{ufInfo[uf].name}</p>
              <TooltipRow
                value={f.pct(byUf[uf].ratio)}
                label={byUf[uf].worth ? t.ethanol.worth : t.ethanol.notWorth}
                color={divergingStep(pts(byUf[uf].ratio), LIMIT_PP).fill}
              />
              <TooltipRow value={f.brl3(byUf[uf].ethanol)} label={fuelLabel("ETANOL", lang)} />
              <TooltipRow value={f.brl3(byUf[uf].gasoline)} label={fuelLabel("GASOLINA", lang)} />
            </>
          )}
        />
      </ChartFrame>
      <ChartFrame
        title={t.ethanol.shareTitle}
        subtitle={t.ethanol.shareSubtitle}
        sqlId="q5_paridade_etanol_gasolina"
        table={{
          columns: [t.table.month, t.ethanol.statesLabel, t.ethanol.ratio],
          rows: ethanol.monthly.map((m) => [f.month(m.month), String(m.states), f.pct(m.ratio)]),
        }}
      >
        <ShareChart />
      </ChartFrame>
    </div>
  );
}
