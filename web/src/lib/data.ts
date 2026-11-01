// Dados gerados por `python src/export_web.py` (a partir de data/app/*.parquet). Não editar à mão.
// Convenção: campos *_pct já estão em pontos percentuais (24.25 = +24,25%).
import metaJson from "@/data/meta.json";
import statesJson from "@/data/states.json";
import evolutionJson from "@/data/evolution.json";
import seasonalityJson from "@/data/seasonality.json";
import riskJson from "@/data/risk.json";
import gapJson from "@/data/gap.json";
import ethanolJson from "@/data/ethanol.json";
import brandsJson from "@/data/brands.json";
import simulatorJson from "@/data/simulator.json";
import findingsJson from "@/data/findings.json";
import ufsJson from "@/data/ufs.json";
import sqlJson from "@/data/sql.json";

export const FUELS = ["DIESEL", "GASOLINA", "ETANOL"] as const;
export type Fuel = (typeof FUELS)[number];

export const REGIONS = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"] as const;
export type Region = (typeof REGIONS)[number];

export type Brand = "BRANCA" | "IPIRANGA" | "VIBRA" | "RAIZEN" | "ALESAT" | "OUTRAS";

export type Meta = {
  ultima_carga: string;
  periodo_inicio: string;
  periodo_fim: string;
  registros: number;
  ufs: number;
  municipios: number;
  generated_at: string;
  months: number;
};

export type StatePrice = {
  fuel: Fuel;
  uf: string;
  price: number;
  diff_pct: number;
  price_start: number;
  change_pct: number;
};

export type RegionPrice = { fuel: Fuel; region: Region; price: number; vs_cheapest_pct: number };

export type Findings = {
  north_price: number;
  others_price: number;
  north_premium_pct: number;
  region_spread_others_pct: number;
  priciest_uf: string;
  priciest_price: number;
  priciest_premium_pct: number;
  cheapest_uf: string;
  cheapest_price: number;
  spread_brl: number;
  diesel_now: number;
  change_pct: Record<Fuel, number>;
  states_cheaper_diesel: number;
  states_total: number;
  season_peak_month: number;
  season_peak_pct: number;
  season_low_month: number;
  season_low_pct: number;
  season_years: number;
  most_volatile: string[];
  most_volatile_values: number[];
  volatility_median: number;
  priciest_volatility: number;
  priciest_stability_rank: number;
  most_dispersed: string[];
  most_dispersed_values: number[];
  gap_by_year: Record<string, number>;
  ethanol_worth_ufs: string[];
  ethanol_worth_count: number;
  brand_max: Brand;
  brand_max_pct: number;
  s10_premium_pct: number;
  s10_premium_brl: number;
  additive_premium_pct: number;
};

export const meta = metaJson as Meta;

export const states = statesJson as {
  last_month: string;
  first_month: string;
  national: Record<Fuel, { first: number; last: number; prev: number; change_pct: number }>;
  states: StatePrice[];
  regions: RegionPrice[];
};

export const evolution = evolutionJson as {
  national: { fuel: Fuel; month: string; price: number; index: number }[];
  regional: { fuel: Fuel; region: Region; month: string; price: number }[];
};

export const seasonality = seasonalityJson as {
  index: { fuel: Fuel; month: number; mean: number; min: number; max: number; years: number }[];
  calendar: { fuel: Fuel; year: number; month: number; price: number; mom_pct: number | null }[];
};

export const risk = riskJson as {
  states: { fuel: Fuel; uf: string; price: number; volatility: number; dispersion: number }[];
};

export const gap = gapJson as {
  monthly: { fuel: Fuel; month: string; max_region: Region; min_region: Region; gap_pct: number }[];
  yearly: { fuel: Fuel; year: number; gap_pct: number }[];
  ruler: { fuel: Fuel; year: number; region: Region; price: number }[];
};

export const ethanol = ethanolJson as {
  threshold: number;
  states: { uf: string; ethanol: number; gasoline: number; ratio: number; worth: boolean }[];
  monthly: { month: string; ratio: number; share: number; states: number }[];
};

export const brands = brandsJson as {
  ranking: { fuel: Fuel; brand: Brand; price: number; diff_pct: number; share: number }[];
  products: { product: "s10" | "additive"; month: string; premium_brl: number; premium_pct: number }[];
};

export const simulator = simulatorJson as {
  window_months: number;
  last_month: string;
  prices: { fuel: Fuel; uf: string; price: number }[];
};

export const findings = findingsJson as Findings;

export const ufs = ufsJson as { uf: string; name: string; region: Region }[];
export const ufInfo = Object.fromEntries(ufs.map((u) => [u.uf, u])) as Record<string, (typeof ufs)[number]>;

export const sqlFiles = sqlJson as Record<string, string>;
export type SqlId = keyof typeof sqlJson;

/** Paths SVG dos estados, calculados no build (page.tsx) e passados aos mapas. */
export type MapShapes = { width: number; height: number; paths: Record<string, string>; centroids: Record<string, [number, number]> };
