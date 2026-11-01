"use client";

import { motion, useMotionTemplate, useMotionValue, useSpring } from "motion/react";
import { useRef, type ReactNode } from "react";
import { findings, meta } from "@/lib/data";
import { fill } from "@/lib/format";
import { scrollToId } from "@/lib/lenis";
import { site } from "@/site.config";
import { CountUp } from "./motion";
import { useI18n } from "./providers";

/** Botão que é levemente atraído pelo cursor. */
function Magnetic({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useSpring(0, { stiffness: 220, damping: 18 });
  const y = useSpring(0, { stiffness: 220, damping: 18 });
  return (
    <motion.div
      ref={ref}
      style={{ x, y }}
      onPointerMove={(e) => {
        if (e.pointerType !== "mouse" || !ref.current) return;
        const r = ref.current.getBoundingClientRect();
        x.set((e.clientX - r.left - r.width / 2) * 0.25);
        y.set((e.clientY - r.top - r.height / 2) * 0.35);
      }}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
      }}
    >
      {children}
    </motion.div>
  );
}

export function Hero() {
  const { t, f } = useI18n();
  const mx = useMotionValue(50);
  const my = useMotionValue(30);
  const spotlight = useMotionTemplate`radial-gradient(600px circle at ${mx}% ${my}%, var(--glow-a), transparent 60%)`;

  const stats = [
    { label: t.hero.kpis.records, value: meta.registros, format: f.compact },
    { label: t.hero.kpis.cities, value: meta.municipios, format: f.int },
    { label: t.hero.kpis.diesel, value: findings.diesel_now, format: (v: number) => f.brl(v) },
    { label: t.hero.kpis.change, value: findings.change_pct.DIESEL, format: (v: number) => f.spp(v) },
  ];

  return (
    <section
      id="top"
      className="relative isolate flex min-h-[100svh] flex-col justify-center overflow-hidden px-4 pb-16 pt-28 sm:px-6"
      onPointerMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        mx.set(((e.clientX - r.left) / r.width) * 100);
        my.set(((e.clientY - r.top) / r.height) * 100);
      }}
    >
      {/* Fundo: grade, orbes animados e spotlight do cursor */}
      <div aria-hidden className="bg-grid absolute inset-0 -z-10 opacity-70" />
      <motion.div
        aria-hidden
        className="absolute -left-40 top-10 -z-10 size-[520px] rounded-full blur-3xl"
        style={{ background: "var(--glow-a)" }}
        animate={{ x: [0, 80, -20, 0], y: [0, 40, 90, 0], scale: [1, 1.1, 0.95, 1] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden
        className="absolute -right-32 bottom-0 -z-10 size-[460px] rounded-full blur-3xl"
        style={{ background: "var(--glow-b)" }}
        animate={{ x: [0, -70, 10, 0], y: [0, -50, -10, 0], scale: [1, 0.92, 1.08, 1] }}
        transition={{ duration: 26, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div aria-hidden className="absolute inset-0 -z-10 hidden md:block" style={{ background: spotlight }} />

      <div className="mx-auto w-full max-w-6xl">
        {/* Entrada do hero em CSS: anima já na primeira pintura, sem esperar a hidratação (LCP). */}
        <p
          style={{ animationDelay: "0.05s" }}
          className="rise mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-surface/60 px-3 py-1.5 text-xs font-medium text-ink-2 backdrop-blur"
        >
          <span className="relative flex size-2">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-accent opacity-60" />
            <span className="relative inline-flex size-2 rounded-full bg-accent" />
          </span>
          {t.hero.eyebrow}
        </p>

        <h1
          aria-label={t.hero.title}
          className="max-w-4xl text-balance text-4xl font-semibold leading-[1.02] tracking-tight text-ink sm:text-6xl lg:text-7xl"
        >
          {t.hero.title.split(" ").map((word, i, words) => (
            <span key={i} aria-hidden className="inline-block overflow-hidden pb-[0.12em] align-top">
              <span className="word-rise inline-block" style={{ animationDelay: `${0.12 + i * 0.045}s` }}>
                {word}
                {i < words.length - 1 ? " " : ""}
              </span>
            </span>
          ))}
        </h1>

        <p className="slide-up mt-6 max-w-2xl text-base leading-relaxed text-ink-2 sm:text-lg">
          {fill(t.hero.lede, {
            records: f.int(meta.registros),
            cities: f.int(meta.municipios),
            start: f.date(meta.periodo_inicio),
            end: f.date(meta.periodo_fim),
          })}
        </p>

        <div style={{ animationDelay: "0.5s" }} className="rise mt-9 flex flex-wrap items-center gap-3">
          <Magnetic>
            <button
              onClick={() => scrollToId("summary")}
              className="group inline-flex h-12 items-center gap-2 rounded-full bg-ink px-6 text-sm font-semibold text-page shadow-lg transition hover:shadow-xl"
            >
              {t.hero.ctaPrimary}
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden className="transition-transform group-hover:translate-y-0.5">
                <path d="M8 3v10M3.5 8.5L8 13l4.5-4.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </Magnetic>
          <Magnetic>
            <button
              onClick={() => scrollToId("simulator")}
              className="inline-flex h-12 items-center gap-2 rounded-full bg-accent px-6 text-sm font-semibold text-brand-ink shadow-lg transition hover:shadow-xl"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                <path d="M3 7h11v9H3zM14 10h4l3 3v3h-7M7.5 19.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM17.5 19.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z" strokeLinejoin="round" />
              </svg>
              {t.hero.ctaSimulator}
            </button>
          </Magnetic>
          {site.repo && (
            <Magnetic>
              <a
                href={site.repo}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-12 items-center gap-2 rounded-full border border-line bg-surface/60 px-6 text-sm font-semibold text-ink backdrop-blur transition hover:bg-surface"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden>
                  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38v-1.33c-2.23.48-2.7-1.07-2.7-1.07-.36-.92-.89-1.17-.89-1.17-.73-.5.06-.49.06-.49.8.06 1.23.83 1.23.83.72 1.22 1.88.87 2.34.66.07-.52.28-.87.51-1.07-1.78-.2-3.65-.89-3.65-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48v2.2c0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
                </svg>
                {t.hero.ctaSecondary}
              </a>
            </Magnetic>
          )}
        </div>

        <motion.dl
          initial="hidden"
          animate="show"
          variants={{ show: { transition: { staggerChildren: 0.08, delayChildren: 0.6 } } }}
          className="mt-14 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-line bg-line sm:mt-20 lg:grid-cols-4"
        >
          {stats.map((s) => (
            <motion.div
              key={s.label}
              variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.7 } } }}
              className="bg-surface/80 p-4 backdrop-blur sm:p-6"
            >
              <dt className="text-xs text-muted sm:text-sm">{s.label}</dt>
              <dd className="mt-1 text-2xl font-semibold tracking-tight text-ink sm:text-4xl">
                <CountUp value={s.value} format={s.format} />
              </dd>
            </motion.div>
          ))}
        </motion.dl>
      </div>

      <motion.div
        aria-hidden
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.8 }}
        className="absolute bottom-6 left-1/2 hidden -translate-x-1/2 flex-col items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-muted [@media(min-height:960px)]:sm:flex"
      >
        {t.hero.scroll}
        <span className="relative h-10 w-px overflow-hidden bg-line">
          <motion.span
            className="absolute inset-x-0 top-0 h-4 bg-ink-2"
            animate={{ y: [-16, 40] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          />
        </span>
      </motion.div>
    </section>
  );
}
