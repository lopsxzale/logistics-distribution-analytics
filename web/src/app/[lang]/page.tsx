import { geoIdentity, geoPath } from "d3-geo";
import type { FeatureCollection, Geometry } from "geojson";
import { notFound } from "next/navigation";
import { codeToHtml } from "shiki";
import { BrandsCharts } from "@/components/charts/brands-chart";
import { EthanolCharts } from "@/components/charts/ethanol-charts";
import { EvolutionCharts } from "@/components/charts/evolution-charts";
import { PricesBlock } from "@/components/charts/prices-charts";
import { RiskCharts } from "@/components/charts/risk-charts";
import { SeasonalityCharts } from "@/components/charts/seasonality-charts";
import { About, Actions, Footer, Method } from "@/components/closing";
import { Header } from "@/components/header";
import { Hero } from "@/components/hero";
import { Providers, type HighlightedSql } from "@/components/providers";
import { Section } from "@/components/section";
import { Simulator } from "@/components/simulator";
import { Summary } from "@/components/summary";
import geo from "@/data/br_estados.geo.json";
import { hasLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n";
import { ethanol, findings as fd, meta, simulator, sqlFiles, states, ufInfo, type MapShapes } from "@/lib/data";
import { fill, formatters } from "@/lib/format";
import { brandLabel } from "@/lib/labels";

// Destaque de sintaxe roda no build; o cliente recebe só o HTML pronto.
async function highlightSql(): Promise<HighlightedSql> {
  const entries = await Promise.all(
    Object.entries(sqlFiles).map(async ([id, raw]) => {
      const html = await codeToHtml(raw, {
        lang: "sql",
        themes: { light: "github-light", dark: "github-dark" },
        defaultColor: "light",
      });
      return [id, { html, raw }] as const;
    }),
  );
  return Object.fromEntries(entries);
}

// Paths do mapa calculados no build: o GeoJSON (~270 KB) nunca vai para o navegador.
// Projeção plana (lon/lat) com eixo y invertido: suficiente para o Brasil e imune à ordem dos anéis.
function mapShapes(): MapShapes {
  const width = 600;
  const height = 580;
  const fc = geo as unknown as FeatureCollection<Geometry, { sigla: string }>;
  const projection = geoIdentity().reflectY(true).fitSize([width, height], fc);
  const path = geoPath(projection).digits(1);
  const paths: Record<string, string> = {};
  const centroids: Record<string, [number, number]> = {};
  for (const feature of fc.features) {
    paths[feature.properties.sigla] = path(feature) ?? "";
    centroids[feature.properties.sigla] = path.centroid(feature).map((v) => Math.round(v)) as [number, number];
  }
  return { width, height, paths, centroids };
}

export default async function Page({ params }: PageProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();
  const t = getDictionary(lang);
  const f = formatters(lang);
  const sql = await highlightSql();
  const shapes = mapShapes();

  const ufName = (uf: string) => ufInfo[uf].name;
  const list = (items: string[]) =>
    items.length > 1 ? `${items.slice(0, -1).join(", ")} ${lang === "pt" ? "e" : "and"} ${items[items.length - 1]}` : items[0];
  const bestEthanol = [...ethanol.states].sort((a, b) => a.ratio - b.ratio)[0];
  const month = f.month(states.last_month);

  return (
    <Providers lang={lang} sql={sql}>
      <Header />
      <main>
        <Hero />
        <Summary />

        <Section
          id="prices"
          index="01"
          eyebrow={t.prices.eyebrow}
          title={t.prices.title}
          lede={fill(t.prices.lede, {
            others: f.brl(fd.others_price),
            north: f.brl(fd.north_price),
            premium: f.spp(fd.north_premium_pct),
            month,
            priciest: ufName(fd.priciest_uf),
            priciestPct: f.spp(fd.priciest_premium_pct),
          })}
          takeaway={t.prices.takeaway}
        >
          <PricesBlock shapes={shapes} />
        </Section>

        <Section
          id="evolution"
          index="02"
          eyebrow={t.evolution.eyebrow}
          title={fill(t.evolution.title, { diesel: f.spp(fd.change_pct.DIESEL), gasoline: f.spp(fd.change_pct.GASOLINA) })}
          lede={fill(t.evolution.lede, {
            diesel: f.spp(fd.change_pct.DIESEL),
            cheaper: fd.states_cheaper_diesel,
            total: fd.states_total,
            gasoline: f.spp(fd.change_pct.GASOLINA),
            ethanol: f.spp(fd.change_pct.ETANOL),
          })}
          takeaway={t.evolution.takeaway}
        >
          <EvolutionCharts />
        </Section>

        <Section
          id="seasonality"
          index="03"
          eyebrow={t.seasonality.eyebrow}
          title={t.seasonality.title}
          lede={fill(t.seasonality.lede, {
            peak: f.monthName(fd.season_peak_month, "long"),
            peakPct: f.pp(fd.season_peak_pct),
            low: f.monthName(fd.season_low_month, "long"),
            lowPct: f.pp(-fd.season_low_pct),
            years: fd.season_years,
          })}
          takeaway={t.seasonality.takeaway}
        >
          <SeasonalityCharts />
        </Section>

        <Section
          id="risk"
          index="04"
          eyebrow={t.risk.eyebrow}
          title={t.risk.title}
          lede={fill(t.risk.lede, {
            priciest: ufName(fd.priciest_uf),
            priciestVol: f.pp(fd.priciest_volatility),
            volatile: list(fd.most_volatile.map(ufName)),
            dispersed: list(fd.most_dispersed.map((uf, i) => `${ufName(uf)} (${f.pp(fd.most_dispersed_values[i])})`)),
          })}
          takeaway={t.risk.takeaway}
        >
          <RiskCharts />
        </Section>

        <Section
          id="ethanol"
          index="05"
          eyebrow={t.ethanol.eyebrow}
          title={fill(t.ethanol.title, { count: fd.ethanol_worth_count })}
          lede={fill(t.ethanol.lede, {
            ufs: list(fd.ethanol_worth_ufs.map(ufName)),
            best: ufName(bestEthanol.uf),
            bestPct: f.pct(bestEthanol.ratio),
          })}
          takeaway={t.ethanol.takeaway}
        >
          <EthanolCharts shapes={shapes} />
        </Section>

        <Section
          id="brands"
          index="06"
          eyebrow={t.brands.eyebrow}
          title={t.brands.title}
          lede={fill(t.brands.lede, {
            brand: brandLabel(fd.brand_max, lang),
            brandPct: f.spp(fd.brand_max_pct),
            s10: f.spp(fd.s10_premium_pct),
            s10brl: f.brl3(fd.s10_premium_brl),
            additive: f.spp(fd.additive_premium_pct),
          })}
          takeaway={t.brands.takeaway}
        >
          <BrandsCharts />
        </Section>

        <Section
          id="simulator"
          index="07"
          eyebrow={t.simulator.eyebrow}
          title={t.simulator.title}
          lede={fill(t.simulator.lede, { months: simulator.window_months, last: f.month(simulator.last_month) })}
          takeaway={t.simulator.takeaway}
        >
          <Simulator />
        </Section>

        <Section id="actions" index="08" eyebrow={t.actions.eyebrow} title={t.actions.title} lede={t.actions.lede}>
          <Actions />
        </Section>

        <Section id="method" index="09" eyebrow={t.method.eyebrow} title={t.method.title} lede={t.method.lede}>
          <Method />
        </Section>

        <About />
      </main>
      <Footer generatedAt={meta.generated_at} />
    </Providers>
  );
}
