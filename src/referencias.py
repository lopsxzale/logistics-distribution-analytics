"""Tabelas de referência estáticas: UFs, normalização de produtos e de bandeiras."""

# uf -> (nome_estado, regiao_sigla, regiao_nome)
ESTADOS: dict[str, tuple[str, str, str]] = {
    "AC": ("Acre", "N", "Norte"),
    "AL": ("Alagoas", "NE", "Nordeste"),
    "AP": ("Amapá", "N", "Norte"),
    "AM": ("Amazonas", "N", "Norte"),
    "BA": ("Bahia", "NE", "Nordeste"),
    "CE": ("Ceará", "NE", "Nordeste"),
    "DF": ("Distrito Federal", "CO", "Centro-Oeste"),
    "ES": ("Espírito Santo", "SE", "Sudeste"),
    "GO": ("Goiás", "CO", "Centro-Oeste"),
    "MA": ("Maranhão", "NE", "Nordeste"),
    "MT": ("Mato Grosso", "CO", "Centro-Oeste"),
    "MS": ("Mato Grosso do Sul", "CO", "Centro-Oeste"),
    "MG": ("Minas Gerais", "SE", "Sudeste"),
    "PA": ("Pará", "N", "Norte"),
    "PB": ("Paraíba", "NE", "Nordeste"),
    "PR": ("Paraná", "S", "Sul"),
    "PE": ("Pernambuco", "NE", "Nordeste"),
    "PI": ("Piauí", "NE", "Nordeste"),
    "RJ": ("Rio de Janeiro", "SE", "Sudeste"),
    "RN": ("Rio Grande do Norte", "NE", "Nordeste"),
    "RS": ("Rio Grande do Sul", "S", "Sul"),
    "RO": ("Rondônia", "N", "Norte"),
    "RR": ("Roraima", "N", "Norte"),
    "SC": ("Santa Catarina", "S", "Sul"),
    "SP": ("São Paulo", "SE", "Sudeste"),
    "SE": ("Sergipe", "NE", "Nordeste"),
    "TO": ("Tocantins", "N", "Norte"),
}

# Valores reais da coluna "Produto" dos CSVs da ANP -> categoria analítica.
MAPA_PRODUTO: dict[str, str] = {
    "GASOLINA": "GASOLINA",
    "GASOLINA ADITIVADA": "GASOLINA",
    "ETANOL": "ETANOL",
    "ETANOL HIDRATADO": "ETANOL",
    "DIESEL": "DIESEL",
    "DIESEL S10": "DIESEL",
    "OLEO DIESEL": "DIESEL",
    "OLEO DIESEL S10": "DIESEL",
    "GNV": "GNV",
}

# GNV é cotado em R$/m³; os demais em R$/litro. Por isso fica fora das comparações.
CATEGORIAS_ANALISE: tuple[str, ...] = ("GASOLINA", "ETANOL", "DIESEL")

# Rebrandings ao longo da série (BR Distribuidora -> Vibra, ALE -> Alesat).
SINONIMOS_BANDEIRA: dict[str, str] = {
    "VIBRA ENERGIA": "VIBRA",
    "PETROBRAS DISTRIBUIDORA S.A.": "VIBRA",
    "ALE": "ALESAT",
}
BANDEIRAS_PRINCIPAIS: tuple[str, ...] = ("BRANCA", "IPIRANGA", "VIBRA", "RAIZEN", "ALESAT")


def categoria_de(produto_raw: str) -> str:
    chave = produto_raw.strip().upper()
    return MAPA_PRODUTO.get(chave, chave)


def normalizar_bandeira(bandeira: str | None) -> str:
    """Unifica sinônimos e agrupa a cauda longa em 'OUTRAS'."""
    if not bandeira or not str(bandeira).strip():
        return "OUTRAS"
    chave = str(bandeira).strip().upper()
    chave = SINONIMOS_BANDEIRA.get(chave, chave)
    return chave if chave in BANDEIRAS_PRINCIPAIS else "OUTRAS"
