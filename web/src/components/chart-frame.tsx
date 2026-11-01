"use client";

import { AnimatePresence, motion } from "motion/react";
import { useId, useState, type ReactNode } from "react";
import type { SqlId } from "@/lib/data";
import { useI18n, useSql } from "./providers";

export type LegendItem = { label: string; color: string; shape?: "square" | "dot" | "line" };

export type TableData = {
  columns: string[];
  rows: (string | number)[][];
};

export function Legend({ items }: { items: LegendItem[] }) {
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-2">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className={
              item.shape === "line"
                ? "h-0.5 w-3.5 rounded-full"
                : item.shape === "dot"
                  ? "size-2.5 rounded-full"
                  : "size-2.5 rounded-[3px]"
            }
            style={{ background: item.color }}
          />
          {item.label}
        </li>
      ))}
    </ul>
  );
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  label: string;
}) {
  const id = useId();
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-full bg-surface-2 p-1 text-xs">
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            className={`relative rounded-full px-3 py-1.5 font-medium transition-colors ${
              active ? "text-ink" : "text-muted hover:text-ink-2"
            }`}
          >
            {active && (
              <motion.span
                layoutId={`seg-${id}`}
                className="absolute inset-0 rounded-full bg-surface shadow-sm ring-1 ring-line"
                transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
              />
            )}
            <span className="relative">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}

function IconButton({
  onClick,
  children,
  pressed,
}: {
  onClick: () => void;
  children: ReactNode;
  pressed?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={pressed}
      className="inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1.5 text-xs font-medium text-ink-2 transition hover:border-transparent hover:bg-surface-2 hover:text-ink"
    >
      {children}
    </button>
  );
}

export function ChartFrame({
  title,
  subtitle,
  sqlId,
  legend,
  controls,
  table,
  children,
  className = "",
}: {
  title: string;
  subtitle?: string;
  sqlId?: SqlId;
  legend?: LegendItem[];
  controls?: ReactNode;
  table?: TableData;
  children: ReactNode;
  className?: string;
}) {
  const { t } = useI18n();
  const sql = useSql();
  const [showTable, setShowTable] = useState(false);

  return (
    <figure className={`card relative flex min-w-0 flex-col p-4 sm:p-6 ${className}`}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <figcaption className="min-w-0">
          <h3 className="text-base font-semibold tracking-tight text-ink">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
        </figcaption>
        <div className="flex flex-wrap items-center gap-2">
          {table && (
            <IconButton onClick={() => setShowTable((v) => !v)} pressed={showTable}>
              <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.5">
                {showTable ? (
                  <path d="M2 13h12M4 10V7M8 10V4M12 10V6" strokeLinecap="round" />
                ) : (
                  <path d="M2.5 3.5h11v9h-11zM2.5 6.5h11M2.5 9.5h11M6.5 3.5v9" />
                )}
              </svg>
              {showTable ? t.method.viewChart : t.method.viewTable}
            </IconButton>
          )}
          {sqlId && (
            <IconButton onClick={() => sql.open(sqlId)}>
              <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M5.5 4.5L2 8l3.5 3.5M10.5 4.5L14 8l-3.5 3.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              {t.method.viewSql}
            </IconButton>
          )}
        </div>
      </div>
      {(controls || legend) && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          {legend ? <Legend items={legend} /> : <span />}
          {controls}
        </div>
      )}
      <AnimatePresence mode="wait" initial={false}>
        {showTable && table ? (
          <motion.div
            key="table"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            data-lenis-prevent
            className="max-h-[420px] overflow-auto rounded-xl ring-1 ring-line"
          >
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-surface-2 text-xs text-muted">
                <tr>
                  {table.columns.map((c, i) => (
                    <th key={c} scope="col" className={`px-3 py-2 font-medium ${i > 0 ? "text-right" : ""}`}>
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="tabular">
                {table.rows.map((row, r) => (
                  <tr key={r} className="border-t border-line">
                    {row.map((cell, i) => (
                      <td key={i} className={`px-3 py-2 ${i > 0 ? "text-right text-ink-2" : "text-ink"}`}>
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        ) : (
          <motion.div
            key="chart"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="relative flex-1"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </figure>
  );
}

/** Tooltip posicionado dentro de um container `relative`; vira para o lado com espaço. */
export function ChartTooltip({
  x,
  y,
  width,
  children,
}: {
  x: number;
  y: number;
  width: number;
  children: ReactNode;
}) {
  const flip = x > width * 0.6;
  return (
    <motion.div
      role="status"
      className="pointer-events-none absolute z-10 min-w-36 rounded-xl border border-line bg-surface/95 px-3 py-2 text-xs shadow-xl backdrop-blur"
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1, left: x, top: y }}
      transition={{ duration: 0.18 }}
      style={{ translateX: flip ? "calc(-100% - 12px)" : "12px", translateY: "-50%" }}
    >
      {children}
    </motion.div>
  );
}

export function TooltipRow({ value, label, color }: { value: string; label: string; color?: string }) {
  return (
    <div className="flex items-center gap-2 py-0.5">
      {color && <span aria-hidden className="h-0.5 w-3 rounded-full" style={{ background: color }} />}
      <span className="font-semibold text-ink tabular">{value}</span>
      <span className="text-muted">{label}</span>
    </div>
  );
}
