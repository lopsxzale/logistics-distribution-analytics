import type { Locale } from "@/i18n/config";

const intlLocale: Record<Locale, string> = { pt: "pt-BR", en: "en-US" };

export function formatters(locale: Locale) {
  const loc = intlLocale[locale];
  const cache = new Map<string, Intl.NumberFormat>();
  const nf = (key: string, opts: Intl.NumberFormatOptions) => {
    if (!cache.has(key)) cache.set(key, new Intl.NumberFormat(loc, opts));
    return cache.get(key)!;
  };

  return {
    /** 98.199 */
    int: (v: number) => nf("int", { maximumFractionDigits: 0 }).format(v),
    /** 4,29 */
    dec: (v: number, digits = 2) =>
      nf(`dec${digits}`, { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v),
    /** 12,1% */
    pct: (v: number, digits = 1) =>
      nf(`pct${digits}`, {
        style: "percent",
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }).format(v),
    /** R$ 160,24 */
    brl: (v: number) =>
      nf("brl", { style: "currency", currency: "BRL", maximumFractionDigits: 2 }).format(v),
    /** R$ 6,094 (preço por litro com 3 casas) */
    brl3: (v: number) =>
      nf("brl3", { style: "currency", currency: "BRL", minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(v),
    /** R$ 12.480 (custos de frota, sem centavos) */
    brl0: (v: number) =>
      nf("brl0", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(v),
    /** 24,3% a partir de pontos percentuais (24.25) */
    pp: (v: number, digits = 1) =>
      nf(`pp${digits}`, { style: "percent", minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v / 100),
    /** +24,3% / −4,9% a partir de pontos percentuais (sinal de menos tipográfico) */
    spp: (v: number, digits = 1) =>
      nf(`spp${digits}`, {
        style: "percent",
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
        signDisplay: "exceptZero",
      })
        .format(v / 100)
        .replace("-", "−"),
    /** fev / Feb */
    monthName: (m: number, style: "short" | "long" = "short") =>
      new Intl.DateTimeFormat(loc, { month: style, timeZone: "UTC" })
        .format(new Date(Date.UTC(2024, m - 1, 1)))
        .replace(".", ""),
    /** R$ 15,7 mi */
    brlCompact: (v: number) =>
      nf("brlc", {
        style: "currency",
        currency: "BRL",
        notation: "compact",
        // Mínimo explícito: sem ele, versões de ICU diferentes (Node no build x navegador)
        // geram "R$ 772,0 mil" x "R$ 772 mil" e quebram a hidratação.
        minimumFractionDigits: 0,
        maximumFractionDigits: 1,
      }).format(v),
    /** 12,9 mil */
    compact: (v: number) =>
      nf("compact", { notation: "compact", minimumFractionDigits: 0, maximumFractionDigits: 1 }).format(
        v,
      ),
    /** −0,88 (sinal de menos tipográfico) */
    signed: (v: number, digits = 2) =>
      nf(`signed${digits}`, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
        signDisplay: "exceptZero",
      })
        .format(v)
        .replace("-", "−"),
    /** dez/25 (curto) ou dezembro de 2025 (longo) */
    month: (ym: string, style: "short" | "long" = "short") => {
      const [y, m] = ym.split("-").map(Number);
      const date = new Date(Date.UTC(y, m - 1, 1));
      if (style === "long") {
        return new Intl.DateTimeFormat(loc, { month: "long", year: "numeric", timeZone: "UTC" }).format(date);
      }
      const name = new Intl.DateTimeFormat(loc, { month: "short", timeZone: "UTC" }).format(date).replace(".", "");
      return `${name}/${String(y).slice(2)}`;
    },
    date: (iso: string) =>
      new Intl.DateTimeFormat(loc, { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(
        new Date(`${iso}T00:00:00Z`),
      ),
  };
}

export type Formatters = ReturnType<typeof formatters>;

/** Substitui {chave} no texto. */
export function fill(template: string, vars: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? `{${k}}`));
}

export const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
