"use client";

import Lenis from "lenis";
import { MotionConfig } from "motion/react";
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Locale } from "@/i18n/config";
import { getDictionary } from "@/i18n";
import { formatters } from "@/lib/format";
import { setLenis } from "@/lib/lenis";
import type { SqlId } from "@/lib/data";
import { SqlModal } from "./sql-modal";

const I18nContext = createContext<Locale>("pt");

export function useI18n() {
  const lang = useContext(I18nContext);
  return useMemo(() => ({ lang, t: getDictionary(lang), f: formatters(lang) }), [lang]);
}

type SqlContextValue = { open: (id: SqlId) => void };
const SqlContext = createContext<SqlContextValue>({ open: () => {} });
export const useSql = () => useContext(SqlContext);

export type HighlightedSql = Record<string, { html: string; raw: string }>;

function useSmoothScroll() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const lenis = new Lenis({ lerp: 0.09, anchors: { offset: -72 }, autoRaf: true });
    setLenis(lenis);
    return () => {
      setLenis(null);
      lenis.destroy();
    };
  }, []);
}

export function Providers({
  lang,
  sql,
  children,
}: {
  lang: Locale;
  sql: HighlightedSql;
  children: ReactNode;
}) {
  const [openSql, setOpenSql] = useState<SqlId | null>(null);
  const sqlValue = useMemo(() => ({ open: setOpenSql }), []);
  useSmoothScroll();

  return (
    <I18nContext.Provider value={lang}>
      <MotionConfig reducedMotion="user" transition={{ ease: [0.22, 1, 0.36, 1] }}>
        <SqlContext.Provider value={sqlValue}>
          {children}
          <SqlModal id={openSql} sql={sql} onClose={() => setOpenSql(null)} />
        </SqlContext.Provider>
      </MotionConfig>
    </I18nContext.Provider>
  );
}
