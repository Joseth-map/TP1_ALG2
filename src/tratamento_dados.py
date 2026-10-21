import pandas as pd
from pyproj import Transformer

transformer = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True)

TIPOS = {
    "RUA": "Rua",
    "AVE": "Avenida",
    "BEC": "Beco",
    "PCA": "Praça",
    "ROD": "Rodovia",
    "ALA": "Alameda",
    "EST": "Estrada",
    "TRV": "Travessa",
    "VIA": "Via",
    "VDP": "Viaduto",
    "LRG": "Largo",
    "TRE": "Trevo",
}

def consertar_tipo(tipo) -> str:
    original = str(tipo).strip()
    return TIPOS.get(original.upper(), original)

def carregar_base(url: str):
    base = pd.read_csv(url)
    base.columns = base.columns.str.strip()

    cnaes = "5611203|5611202|5611205|5620104"
    nomes = "BAR |LANCHONETE|RESTAURANTE"

    filtro_cnae = base["CNAE"].astype(str).str.contains(cnaes, na=False)
    filtro_nome = base["NOME_FANTASIA"].astype(str).str.contains(nomes, case=False, na=False)

    base_filtrada = base[filtro_cnae | filtro_nome].copy()

    base_filtrada["DESC_LOGRADOURO"] = base_filtrada["DESC_LOGRADOURO"].map(consertar_tipo)

    coordenadas = base_filtrada["GEOMETRIA"].dropna().str.replace("POINT (", "", regex=False).str.replace(")", "", regex=False).str.split(expand=True).astype(float)

    long, lat = transformer.transform(coordenadas[0].values, coordenadas[1].values)

    base_filtrada.loc[coordenadas.index, "longitude"] = long
    base_filtrada.loc[coordenadas.index, "latitude"] = lat

    base_filtrada["endereco"] = (
        base_filtrada["DESC_LOGRADOURO"].astype(str)
        + " "
        + base_filtrada["NOME_LOGRADOURO"].astype(str)
        + ", "
        + base_filtrada["NUMERO_IMOVEL"].astype(str)
        + " - "
        + base_filtrada["NOME_BAIRRO"].astype(str)
    )

    base_filtrada = base_filtrada.dropna(subset=["latitude", "longitude", "NOME_FANTASIA"])

    return base_filtrada[["NOME_FANTASIA", "endereco", "GEOMETRIA", "latitude", "longitude"]]