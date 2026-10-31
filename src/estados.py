"""Seed estático das 27 UFs brasileiras com nome completo e região."""

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

# produto_raw (valores reais confirmados na coluna "Produto" dos CSVs da ANP) -> categoria normalizada
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


def categoria_de(produto_raw: str) -> str:
    chave = produto_raw.strip().upper()
    return MAPA_PRODUTO.get(chave, chave)
