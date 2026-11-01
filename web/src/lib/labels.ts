import type { Locale } from "@/i18n/config";
import type { Brand, Fuel, Region } from "./data";

const FUEL: Record<Locale, Record<Fuel, string>> = {
  pt: { DIESEL: "Diesel", GASOLINA: "Gasolina", ETANOL: "Etanol" },
  en: { DIESEL: "Diesel", GASOLINA: "Gasoline", ETANOL: "Ethanol" },
};

const REGION: Record<Locale, Record<Region, string>> = {
  pt: { Norte: "Norte", Nordeste: "Nordeste", "Centro-Oeste": "Centro-Oeste", Sudeste: "Sudeste", Sul: "Sul" },
  en: { Norte: "North", Nordeste: "Northeast", "Centro-Oeste": "Center-West", Sudeste: "Southeast", Sul: "South" },
};

const BRAND: Record<Locale, Record<Brand, string>> = {
  pt: { BRANCA: "Bandeira branca", IPIRANGA: "Ipiranga", VIBRA: "Vibra (BR)", RAIZEN: "Raízen (Shell)", ALESAT: "Alesat", OUTRAS: "Outras" },
  en: { BRANCA: "Unbranded", IPIRANGA: "Ipiranga", VIBRA: "Vibra (BR)", RAIZEN: "Raízen (Shell)", ALESAT: "Alesat", OUTRAS: "Others" },
};

export const fuelLabel = (fuel: Fuel, lang: Locale) => FUEL[lang][fuel];
export const regionLabel = (region: Region, lang: Locale) => REGION[lang][region];
export const brandLabel = (brand: Brand, lang: Locale) => BRAND[lang][brand];

/** Cor fixa por entidade (nunca pela posição). */
export const fuelColor: Record<Fuel, string> = {
  DIESEL: "var(--fuel-diesel)",
  GASOLINA: "var(--fuel-gasolina)",
  ETANOL: "var(--fuel-etanol)",
};

export const regionColor: Record<Region, string> = {
  Norte: "var(--region-1)",
  Nordeste: "var(--region-2)",
  "Centro-Oeste": "var(--region-4)",
  Sudeste: "var(--region-3)",
  Sul: "var(--region-5)",
};

const DIV_STEPS = ["n3", "n2", "n1", "0", "p1", "p2", "p3"] as const;

/** Escala divergente em 7 degraus: valor negativo = azul (abaixo da referência), positivo = vermelho. */
export function divergingStep(value: number, limit: number) {
  const t = Math.max(-1, Math.min(1, value / limit));
  const i = Math.round((t + 1) * 3);
  const step = DIV_STEPS[i];
  return { fill: `var(--div-${step})`, ink: `var(--div-ink-${step})` };
}

export const divergingLegend = DIV_STEPS.map((s) => `var(--div-${s})`);
