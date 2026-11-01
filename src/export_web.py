"""Gera os JSONs consumidos pelo site (web/src/data/) a partir dos Parquets de data/app/.

Não precisa do banco: os Parquets já são versionados, então o site pode ser
regenerado em qualquer máquina (e no CI) em poucos segundos. Os JSONs também
são versionados — o site é publicado como estático, sem servidor.

Uso: python src/export_web.py
"""

from __future__ import annotations

import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

import metrics
from referencias import ESTADOS

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "data" / "app"
SQL_DIR = ROOT_DIR / "sql" / "analysis"
WEB_DATA_DIR = ROOT_DIR / "web" / "src" / "data"

FUELS = ("DIESEL", "GASOLINA", "ETANOL")
REGIONS = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
BRANDS = ("BRANCA", "IPIRANGA", "VIBRA", "RAIZEN", "ALESAT", "OUTRAS")
RECENT_MONTHS = 3  # janela do "preço atual" usada no simulador e na paridade


def _clean(value):
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, 4)
    if isinstance(value, pd.Timestamp):
        return f"{value:%Y-%m}"
    return value


def _normalize(value):
    """Deixa o payload serializável: NaN -> null, floats com 4 casas, datas como 'AAAA-MM'."""
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_normalize(v) for v in value]
    return _clean(value)


def records(df: pd.DataFrame) -> list[dict]:
    return df.to_dict("records")


def write(name: str, payload) -> Path:
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = WEB_DATA_DIR / f"{name}.json"
    path.write_text(json.dumps(_normalize(payload), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def load_panels() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    def read(name: str) -> pd.DataFrame:
        df = pd.read_parquet(APP_DIR / f"precos_{name}_mensal.parquet")
        # Categorias do Parquet viram texto: evita grupos vazios nos groupby.
        for col in df.select_dtypes("category"):
            df[col] = df[col].astype(str)
        return df

    meta = json.loads((APP_DIR / "meta.json").read_text(encoding="utf-8"))
    return read("uf"), read("produto"), read("bandeira"), meta


def recent(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["data"] > df["data"].max() - pd.DateOffset(months=RECENT_MONTHS)]


def fuel(df: pd.DataFrame, f: str) -> pd.DataFrame:
    return df[df["categoria"] == f]


# ---------------------------------------------------------------- blocos do site


def build_states(uf: pd.DataFrame) -> dict:
    """Preço de cada UF no último mês vs média nacional e variação no período."""
    last, first = uf["data"].max(), uf["data"].min()
    rows, national, regions = [], {}, []
    for f in FUELS:
        d = fuel(uf, f)
        nat = metrics.serie_nacional(d)
        national[f] = {
            "first": nat["preco_medio"].iloc[0],
            "last": nat["preco_medio"].iloc[-1],
            "prev": nat["preco_medio"].iloc[-2],
            "change_pct": metrics.variacao_pct(nat["preco_medio"].iloc[-1], nat["preco_medio"].iloc[0]),
        }
        end = metrics.media_ponderada(d[d["data"] == last], ["uf"]).set_index("uf")["preco_medio"]
        start = metrics.media_ponderada(d[d["data"] == first], ["uf"]).set_index("uf")["preco_medio"]
        for code in end.index:
            rows.append(
                {
                    "fuel": f,
                    "uf": code,
                    "price": end[code],
                    "diff_pct": (end[code] / national[f]["last"] - 1) * 100,
                    "price_start": start.get(code, np.nan),
                    "change_pct": metrics.variacao_pct(end[code], start.get(code, np.nan)),
                }
            )
        reg = metrics.media_ponderada(d, ["regiao"])
        cheapest = reg["preco_medio"].min()
        for r in reg.itertuples():
            regions.append(
                {
                    "fuel": f,
                    "region": r.regiao,
                    "price": r.preco_medio,
                    "vs_cheapest_pct": (r.preco_medio / cheapest - 1) * 100,
                }
            )
    return {
        "last_month": last,
        "first_month": first,
        "national": national,
        "states": records(pd.DataFrame(rows)),
        "regions": records(pd.DataFrame(regions)),
    }


def build_evolution(uf: pd.DataFrame) -> dict:
    nat = metrics.indice_base_100(uf, por="categoria").rename(columns={"categoria": "fuel", "data": "month"})
    reg = metrics.media_ponderada(uf, ["categoria", "regiao", "data"]).rename(
        columns={"categoria": "fuel", "regiao": "region", "data": "month"}
    )
    return {
        "national": records(
            nat[["fuel", "month", "preco_medio", "indice"]].rename(columns={"preco_medio": "price", "indice": "index"})
        ),
        "regional": records(reg[["fuel", "region", "month", "preco_medio"]].rename(columns={"preco_medio": "price"})),
    }


def build_seasonality(uf: pd.DataFrame) -> dict:
    index, calendar = [], []
    for f in FUELS:
        d = fuel(uf, f)
        s = metrics.indice_sazonal(d).assign(fuel=f)
        index += records(
            s.rename(
                columns={
                    "mes": "month",
                    "indice_medio": "mean",
                    "indice_min": "min",
                    "indice_max": "max",
                    "n_anos": "years",
                }
            )
        )
        nat = metrics.serie_nacional(d)
        nat["mom_pct"] = nat["preco_medio"].pct_change() * 100
        calendar += records(
            pd.DataFrame(
                {
                    "fuel": f,
                    "year": nat["data"].dt.year,
                    "month": nat["data"].dt.month,
                    "price": nat["preco_medio"],
                    "mom_pct": nat["mom_pct"],
                }
            )
        )
    return {"index": index, "calendar": calendar}


def build_risk(uf: pd.DataFrame) -> dict:
    rows = []
    for f in FUELS:
        d = fuel(uf, f)
        vol = metrics.volatilidade_temporal(d).set_index("uf")
        disp = metrics.dispersao_postos(d).set_index("uf")["dispersao"]
        price = metrics.media_ponderada(recent(d), ["uf"]).set_index("uf")["preco_medio"]
        for code in vol.index:
            rows.append(
                {
                    "fuel": f,
                    "uf": code,
                    "price": price[code],
                    "volatility": vol.loc[code, "volatilidade"],
                    "dispersion": disp[code],
                }
            )
    return {"states": records(pd.DataFrame(rows))}


def build_gap(uf: pd.DataFrame) -> dict:
    monthly, yearly, ruler = [], [], []
    for f in FUELS:
        d = fuel(uf, f)
        g = metrics.gap_regional(d)
        monthly += records(
            g.assign(fuel=f)[["fuel", "data", "regiao_mais_cara", "regiao_mais_barata", "gap_pct"]].rename(
                columns={"data": "month", "regiao_mais_cara": "max_region", "regiao_mais_barata": "min_region"}
            )
        )
        y = g.assign(year=g["data"].dt.year).groupby("year", as_index=False)["gap_pct"].mean()
        yearly += records(y.assign(fuel=f))
        r = metrics.media_ponderada(d.assign(year=d["ano"]), ["year", "regiao"]).rename(columns={"regiao": "region"})
        ruler += records(
            r.assign(fuel=f)[["fuel", "year", "region", "preco_medio"]].rename(columns={"preco_medio": "price"})
        )
    return {"monthly": monthly, "yearly": yearly, "ruler": ruler}


def build_ethanol(uf: pd.DataFrame) -> dict:
    par = metrics.paridade_etanol_gasolina(recent(uf), por=["uf"]).sort_values("razao")
    nat = metrics.paridade_etanol_gasolina(uf, por=["data"])
    by_state = metrics.paridade_etanol_gasolina(uf, por=["data", "uf"])
    share = by_state.groupby("data", as_index=False).agg(
        share=("etanol_compensa", "mean"), states=("etanol_compensa", "sum")
    )
    return {
        "threshold": metrics.LIMIAR_PARIDADE,
        "states": records(
            par.rename(
                columns={
                    "preco_etanol": "ethanol",
                    "preco_gasolina": "gasoline",
                    "razao": "ratio",
                    "etanol_compensa": "worth",
                }
            )
        ),
        "monthly": records(
            nat[["data", "razao"]].merge(share, on="data").rename(columns={"data": "month", "razao": "ratio"})
        ),
    }


def build_brands(bandeira: pd.DataFrame, produto: pd.DataFrame) -> dict:
    ranking = []
    for f in FUELS:
        r = metrics.media_ponderada(fuel(bandeira, f), ["bandeira"])
        ref = r.loc[r["bandeira"] == "BRANCA", "preco_medio"].iloc[0]
        r["diff_pct"] = (r["preco_medio"] / ref - 1) * 100
        r["share"] = r["n_amostras"] / r["n_amostras"].sum()
        ranking += records(
            r.assign(fuel=f)[["fuel", "bandeira", "preco_medio", "diff_pct", "share"]].rename(
                columns={"bandeira": "brand", "preco_medio": "price"}
            )
        )
    products = []
    for key, premium, base in [("s10", "DIESEL S10", "DIESEL"), ("additive", "GASOLINA ADITIVADA", "GASOLINA")]:
        p = metrics.premio_produto(produto, premium=premium, base=base)
        products += records(
            p.assign(product=key)[["product", "data", "premio_rs", "premio_pct"]].rename(
                columns={"data": "month", "premio_rs": "premium_brl", "premio_pct": "premium_pct"}
            )
        )
    return {"ranking": ranking, "products": products}


def build_simulator(uf: pd.DataFrame) -> dict:
    """Preço atual (média dos últimos meses) por UF × combustível; o índice sazonal vem de seasonality.json."""
    rows = []
    for f in FUELS:
        p = metrics.media_ponderada(recent(fuel(uf, f)), ["uf"])
        rows += records(p.assign(fuel=f)[["fuel", "uf", "preco_medio"]].rename(columns={"preco_medio": "price"}))
    return {"window_months": RECENT_MONTHS, "last_month": uf["data"].max(), "prices": rows}


def build_findings(uf: pd.DataFrame, bandeira: pd.DataFrame, produto: pd.DataFrame) -> dict:
    """Os números citados nos textos do site e do README, calculados num lugar só."""
    diesel = fuel(uf, "DIESEL")
    nat = metrics.serie_nacional(diesel)
    last, first = diesel["data"].max(), diesel["data"].min()

    reg = metrics.media_ponderada(diesel, ["regiao"]).set_index("regiao")["preco_medio"].sort_values()
    others = reg.drop("Norte")

    end = metrics.media_ponderada(diesel[diesel["data"] == last], ["uf"]).set_index("uf")["preco_medio"].sort_values()
    start = metrics.media_ponderada(diesel[diesel["data"] == first], ["uf"]).set_index("uf")["preco_medio"]
    nat_last = nat["preco_medio"].iloc[-1]

    change = {f: metrics.variacao_pct(*metrics.serie_nacional(fuel(uf, f))["preco_medio"].iloc[[-1, 0]]) for f in FUELS}

    saz = metrics.indice_sazonal(diesel).set_index("mes")["indice_medio"]

    vol = metrics.volatilidade_temporal(diesel)
    disp = metrics.dispersao_postos(diesel)
    priciest = end.index[-1]

    gap = metrics.gap_regional(diesel)
    gap_year = gap.groupby(gap["data"].dt.year)["gap_pct"].mean()

    par = metrics.paridade_etanol_gasolina(recent(uf), por=["uf"])
    worth = par[par["etanol_compensa"]].sort_values("razao")["uf"].tolist()

    brands = metrics.media_ponderada(fuel(bandeira, "DIESEL"), ["bandeira"]).set_index("bandeira")["preco_medio"]
    brand_premium = (brands.drop(["BRANCA", "OUTRAS"]) / brands["BRANCA"] - 1) * 100
    s10 = metrics.premio_produto(produto, "DIESEL S10", "DIESEL")
    additive = metrics.premio_produto(produto, "GASOLINA ADITIVADA", "GASOLINA")

    return {
        "north_price": reg["Norte"],
        "others_price": others.mean(),
        "north_premium_pct": (reg["Norte"] / others.mean() - 1) * 100,
        "region_spread_others_pct": (others.max() / others.min() - 1) * 100,
        "priciest_uf": priciest,
        "priciest_price": end.iloc[-1],
        "priciest_premium_pct": (end.iloc[-1] / nat_last - 1) * 100,
        "cheapest_uf": end.index[0],
        "cheapest_price": end.iloc[0],
        "spread_brl": end.iloc[-1] - end.iloc[0],
        "diesel_now": nat_last,
        "change_pct": change,
        "states_cheaper_diesel": int((end < start.reindex(end.index)).sum()),
        "states_total": int(len(end)),
        "season_peak_month": int(saz.idxmax()),
        "season_peak_pct": saz.max() - 100,
        "season_low_month": int(saz.idxmin()),
        "season_low_pct": saz.min() - 100,
        "season_years": int(metrics.indice_sazonal(diesel)["n_anos"].max()),
        "most_volatile": vol["uf"].head(3).tolist(),
        "most_volatile_values": vol["volatilidade"].head(3).round(2).tolist(),
        "volatility_median": vol["volatilidade"].median(),
        "priciest_volatility": vol.set_index("uf").loc[priciest, "volatilidade"],
        # 1 = o estado mais estável do país.
        "priciest_stability_rank": vol.sort_values("volatilidade")["uf"].tolist().index(priciest) + 1,
        "most_dispersed": disp["uf"].head(2).tolist(),
        "most_dispersed_values": disp["dispersao"].head(2).round(2).tolist(),
        "gap_by_year": {str(k): v for k, v in gap_year.items()},
        "ethanol_worth_ufs": worth,
        "ethanol_worth_count": len(worth),
        "brand_max": brand_premium.idxmax(),
        "brand_max_pct": brand_premium.max(),
        "s10_premium_pct": s10["premio_pct"].mean(),
        "s10_premium_brl": s10["premio_rs"].mean(),
        "additive_premium_pct": additive["premio_pct"].mean(),
    }


def export() -> list[Path]:
    uf, produto, bandeira, meta = load_panels()
    findings = build_findings(uf, bandeira, produto)
    paths = [
        write(
            "meta",
            {
                **meta,
                "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "months": int(uf["data"].nunique()),
            },
        ),
        write("states", build_states(uf)),
        write("evolution", build_evolution(uf)),
        write("seasonality", build_seasonality(uf)),
        write("risk", build_risk(uf)),
        write("gap", build_gap(uf)),
        write("ethanol", build_ethanol(uf)),
        write("brands", build_brands(bandeira, produto)),
        write("simulator", build_simulator(uf)),
        write("findings", findings),
        write(
            "ufs",
            [{"uf": k, "name": nome, "region": regiao} for k, (nome, _, regiao) in sorted(ESTADOS.items())],
        ),
        write("sql", {p.stem: p.read_text(encoding="utf-8") for p in sorted(SQL_DIR.glob("*.sql"))}),
    ]
    return paths


def main() -> int:
    for path in export():
        print(f"{path.relative_to(ROOT_DIR)} ({path.stat().st_size / 1024:,.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
