#Bibliotecas Gerais
import math
import random
import time
from collections import defaultdict
from pathlib import Path

import folium
import osmnx as ox
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from folium.features import DivIcon

#Minhas implementações
from entregadores import gerar_entregadores
from geohash import buscar_proximos, geohash
from tratamento_dados import carregar_base
from trie import Trie


# Configurações gerais
st.set_page_config(
    page_title="UFood • Monitoramento de Entregadores",
    page_icon="🍴",
    layout="wide",
)

RAIZ = Path(__file__).resolve().parent.parent
BASE_RESTAURANTES = RAIZ / "data" / "base_atividade_economica_prefeitura.csv"
ARQUIVO_GRAFO = RAIZ / "data" / "bh.graphml"
LUGAR = "Belo Horizonte, Minas Gerais, Brazil"

PRECISAO_GEOHASH = 8
SIGMA_M = 700
LARANJA = "#FF6B1A"

#CSS Geral
st.markdown(
    f"""
<style>
.stApp {{ background: #0B0F14; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 1rem; }}
[data-testid="stSidebar"] {{
    background: #0F141B; border-right: 1px solid #1E2530;
    min-width: 350px; max-width: 350px;
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.4rem; }}
.logo {{ font-size: 2rem; font-weight: 800; color: #F2F4F7; line-height: 1.1; }}
.logo span {{ color: {LARANJA}; }}
.sub {{ color: #8B93A1; font-size: .85rem; margin-top: 2px; }}
.status-on {{ color: #3DDC84; font-size: .72rem; font-weight: 700; margin: 4px 0 14px 0; }}
.status-off {{ color: #8B93A1; font-size: .72rem; font-weight: 700; margin: 4px 0 14px 0; }}
.card {{
    background: #141A22; border: 1px solid #232B36; border-radius: 14px;
    padding: 14px 18px; margin-top: 10px;
}}
.card h4 {{ margin: 0 0 8px 0; color: #F2F4F7; font-size: 1.05rem; }}
.mrow {{
    display: flex; justify-content: space-between; padding: 7px 0;
    color: #AEB6C2; font-size: .9rem; border-top: 1px solid #232B36;
}}
.mrow:first-of-type {{ border-top: 1px solid #2B3340; }}
.mrow b {{ color: #F2F4F7; }}
.titulo-tabela {{ color: #F2F4F7; font-size: 1.1rem; font-weight: 700; margin: 14px 0 6px 0; }}
div.stButton > button {{
    background: {LARANJA}; color: #fff; border: 0; border-radius: 10px;
    font-weight: 700; width: 100%; height: 42px; padding: 0; transition: all .2s ease-in-out;
}}
div.stButton > button:hover {{ background: #FF8240; color: #fff; border: 0; transform: scale(1.05);}}
div.stButton > button:focus {{ box-shadow: 0 0 0 2px rgba(255,107,26,.45); color: #fff; }}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {{
    background: #141A22; border: 1px solid #232B36; border-radius: 10px;
}}
iframe {{ border-radius: 14px; border: 1px solid #232B36; }}
[data-testid="stDataFrame"] {{ border: 1px solid #232B36; border-radius: 12px; }}
</style>
""",
    unsafe_allow_html=True,
)


#Fumções de cache
@st.cache_resource(show_spinner="Carregando restaurantes...")
def carregar_restaurantes() -> pd.DataFrame:
    df = carregar_base(str(BASE_RESTAURANTES))
    df = df.drop_duplicates(subset=["NOME_FANTASIA", "latitude", "longitude"])
    df = df.sort_values(
        by=["NOME_FANTASIA"],
        key=lambda col: col.astype(str).str.lower()
    )
    return df.reset_index(drop=True)


@st.cache_resource(show_spinner="Carregando malha viária - 1ª vez demora mais ...")
def carregar_grafo():
    if ARQUIVO_GRAFO.exists():
        return ox.load_graphml(ARQUIVO_GRAFO)
    
    grafo = ox.graph_from_place(LUGAR, network_type="drive")
    ARQUIVO_GRAFO.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(grafo, ARQUIVO_GRAFO)
    return grafo


#Funções Gerais - Frota, Consulta, Visualização
def construir_indice(frota: list):
    trie = Trie()
    indice = defaultdict(list)
    for e in frota:
        if e.geohash not in indice:
            trie.inserir(e.geohash)
        indice[e.geohash].append(e)
    return trie, dict(indice)

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def escolher_precisao(raio_km: float, lat: float) -> int:
    for m in range(PRECISAO_GEOHASH, 0, -1):
        bits = 5 * m
        altura = 180 / 2 ** (bits // 2) * 111.32
        largura = 360 / 2 ** ((bits + 1) // 2) * 111.32 * math.cos(math.radians(lat))
        if min(altura, largura) >= raio_km:
            return m
    return 1

def consultar(trie, indice, lat, lon, raio_km) -> dict:
    t0 = time.perf_counter()
    m = escolher_precisao(raio_km, lat)
    chaves = buscar_proximos(trie, lat, lon, m)

    dentro, fora = [], []
    for chave in chaves:
        for e in indice.get(chave, []):
            d = haversine_km(lat, lon, e.latitude, e.longitude)
            if d <= raio_km:
                dentro.append((e, d, d / e.velocidade * 60))
            else:
                fora.append((e, d))
    dentro.sort(key=lambda x: x[1])

    return {
        "dentro": dentro,
        "fora": fora,
        "prefixo": m,
        "candidatos": len(dentro) + len(fora),
        "tempo_ms": (time.perf_counter() - t0) * 1000,
    }

def montar_mapa(lat, lon, raio_km, nome, dentro, fora) -> folium.Map:
    mapa = folium.Map(location=[lat, lon], tiles="OpenStreetMap", control_scale=True)

    dlat = raio_km / 111.32
    dlon = raio_km / (111.32 * math.cos(math.radians(lat)))
    mapa.fit_bounds([[lat - dlat, lon - dlon], [lat + dlat, lon + dlon]])

    folium.Circle(
        [lat, lon], radius=raio_km * 1000, color=LARANJA, weight=2,
        fill=True, fill_color=LARANJA, fill_opacity=0.12,
    ).add_to(mapa)

    #Entregadoresfora do raio: círculos cinza
    for e, d in fora:
        folium.CircleMarker(
            [e.latitude, e.longitude], radius=3, color="#7A8290", weight=1,
            fill=True, fill_color="#7A8290", fill_opacity=0.8,
            tooltip=f"#ENT-{e.id:04d} • fora do raio • {d:.2f} km",
        ).add_to(mapa)

    # filtrados: moto laranja até 300 pontos; acima disso, círculos vermelhos (performance)
    for e, d, eta in dentro:
        dica = f"#ENT-{e.id:04d} • {e.nome} • {d:.2f} km • {eta:.0f} min"
        if len(dentro) <= 300:
            folium.Marker(
                [e.latitude, e.longitude],
                tooltip=dica,
                icon=DivIcon(
                    html='<i class="fa fa-motorcycle" style="font-size:22px;color:#FF6B1A;'
                         'text-shadow:0 0 4px #000;"></i>',
                    icon_size=(24, 24),
                    icon_anchor=(12, 12),
                ),
            ).add_to(mapa)
        else:
            folium.CircleMarker(
                [e.latitude, e.longitude], radius=5, color=LARANJA, weight=1,
                fill=True, fill_color=LARANJA, fill_opacity=0.95, tooltip=dica,
            ).add_to(mapa)

    folium.Marker(
        [lat, lon], tooltip=nome,
        icon=folium.Icon(color="orange", icon="cutlery"),
    ).add_to(mapa)
    return mapa

def montar_tabela(dentro: list) -> pd.DataFrame:
    linhas = []
    for e, d, eta in dentro:
        disponivel = random.Random(e.id).random() < 0.7
        linhas.append({
            "ID Entregador": f"#ENT-{e.id:04d}",
            "Nome": e.nome,
            "Distância": round(d, 2),
            "ETA": round(eta, 1),
            "Status": "🟢 Disponível" if disponivel else "🟠 Em Rota",
        })
    return pd.DataFrame(linhas)

def card_metricas(res: dict | None, total_frota: int) -> str:
    if res and res["dentro"]:
        n = len(res["dentro"])
        dist = sum(d for _, d, _ in res["dentro"]) / n
        eta = sum(t for _, _, t in res["dentro"]) / n
        ativos, dist_txt, eta_txt = str(n), f"{dist:.2f} km", f"{eta:.0f} min"
    else:
        ativos, dist_txt, eta_txt = "0", "—", "—"
    cand = res["candidatos"] if res else 0
    tempo = f"{res['tempo_ms']:.2f} ms" if res else "—"
    prefixo = res["prefixo"] if res else "—"
    return f"""
<div class="card">
  <h4>Métricas Resumo</h4>
  <div class="mrow"><span>Entregadores Ativos:</span><b>{ativos}</b></div>
  <div class="mrow"><span>Distância Média:</span><b>{dist_txt}</b></div>
  <div class="mrow"><span>Tempo Médio Estimado:</span><b>{eta_txt}</b></div>
  <div class="mrow"><span>Candidatos na Trie:</span><b>{cand}</b></div>
  <div class="mrow"><span>Frota Total:</span><b>{total_frota}</b></div>
  <div class="mrow"><span>Prefixo Geohash:</span><b>{prefixo} carac.</b></div>
  <div class="mrow"><span>Tempo da Consulta:</span><b>{tempo}</b></div>
</div>
"""

#Interface da tela
st.session_state.setdefault("historico", [])
st.session_state.setdefault("geracao", 0)
em_operacao = "frota" in st.session_state

col_esq, col_dir = st.columns([1.1, 2.75], gap="large")

sb = col_esq
sm = col_dir

#Coluna esquerda
sb.markdown(
    f"""
<div class="logo" style="display: flex; align-items: center; gap: 10px;">
    <div style="background-color: #FF5722; width: 40px; height: 40px; border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                font-size: 22px; font-weight: bold; color: #0D1117;">
        🍴
    </div>
    <span style="font-size: 2.2rem; font-weight: 800; letter-spacing: -0.5px;">
        <span style="color: #FF5722;">UF</span><span style="color: #FFFFFF;">ood</span>
    </span>
</div>
<div class="sub">Trabalho de Monitoramento da Frota de Entregas • Belo Horizonte • Aluno: Joseph Patrick Alves de Moura</div>
<div class="{'status-on' if em_operacao else 'status-off'}">● {'FROTA GERADA' if em_operacao else 'NENHUMA FROTA GERADA'}</div>
""",
    unsafe_allow_html=True,
)

restaurantes = carregar_restaurantes()

busca = sb.text_input(
    "Buscar", placeholder="Digite o restaurante ou endereço...", label_visibility="collapsed"
)
termo = busca.strip()

idx = None
if termo:
    mask = restaurantes["NOME_FANTASIA"].astype(str).str.contains(
        termo, case=False, na=False, regex=False
    ) | restaurantes["endereco"].astype(str).str.contains(
        termo, case=False, na=False, regex=False
    )
    opcoes = restaurantes[mask]

    if opcoes.empty:
        sb.warning("Nenhum estabelecimento encontrado para essa busca.")
    else:
        idx = sb.selectbox(
            "Selecione qual estabelecimento deseja",
            options=list(opcoes.index),
            format_func=lambda i: f"{restaurantes.at[i, 'NOME_FANTASIA']} — {restaurantes.at[i, 'endereco']}",
        )

if "raio_m" not in st.session_state:
    st.session_state["raio_m"] = 2000

def sync_slider():
    st.session_state["raio_m"] = int(round(st.session_state["slider_km"] * 1000))

def sync_input():
    km = round(st.session_state["raio_m"] / 1000.0, 2)
    st.session_state["slider_km"] = min(max(km, 0.1), 30.0)

sb.slider(
    "Raio de busca (km)",
    min_value=0.1,
    max_value=30.0,
    value=min(max(st.session_state["raio_m"] / 1000.0, 0.1), 30.0),
    step=0.1,
    key="slider_km",
    on_change=sync_slider,
)

sb.number_input(
    "Ou digite o raio em metros (m)",
    min_value=50,
    max_value=30000,
    value=st.session_state["raio_m"],
    step=50,
    key="raio_m",
    on_change=sync_input,
)

raio_km = st.session_state["raio_m"] / 1000.0

sb.markdown("---")
n_entregadores = sb.number_input("Quantidade de entregadores (N)", 1, 50_000, 1000, step=100, width="stretch")
if sb.button("Gerar Entregadores", width="stretch"):
    with st.spinner("Gerando entregadores e ajustando para as vias..."):
        grafo = carregar_grafo()
        centros = list(zip(restaurantes["latitude"], restaurantes["longitude"]))
        t0 = time.perf_counter()
        
        frota = gerar_entregadores(int(n_entregadores), centros, grafo, SIGMA_M)
        trie, indice = construir_indice(frota)
        st.session_state.update(
            frota=frota, trie=trie, indice=indice, historico=[],
            geracao=st.session_state.geracao + 1, ultima_chave=None,
            tempo_geracao=time.perf_counter() - t0,
        )
    st.rerun()

if "frota" not in st.session_state:
    st.info("Escolha um estabelecimento, informe a quantidade de entregadores na barra lateral e clique em **Gerar Entregadores**.")
    st.stop()

if idx is None:
    st.info("Digite o nome ou o endereço de um estabelecimento para gerar o mapa.")
    st.stop()


rest = restaurantes.loc[idx]
lat_r, lon_r = float(rest["latitude"]), float(rest["longitude"])
res = consultar(st.session_state.trie, st.session_state.indice, lat_r, lon_r, raio_km)

chave = (int(idx), float(raio_km), st.session_state.geracao)
if st.session_state.get("ultima_chave") != chave:
    st.session_state.ultima_chave = chave
    st.session_state.historico.append({
        "Restaurante": rest["NOME_FANTASIA"],
        "Raio (km)": raio_km,
        "Prefixo": res["prefixo"],
        "Candidatos": res["candidatos"],
        "Dentro do raio": len(res["dentro"]),
        "Tempo (ms)": round(res["tempo_ms"], 3),
        "N frota": len(st.session_state.frota),
    })

sb.markdown(card_metricas(res, len(st.session_state.frota)), unsafe_allow_html=True)
sb.caption(f"Frota gerada em {st.session_state.tempo_geracao:.1f} s")

# Coluna direita
with sm:
    mapa = montar_mapa(lat_r, lon_r, raio_km, str(rest["NOME_FANTASIA"]), res["dentro"], res["fora"])
    st_folium(
        mapa, height=520, use_container_width=True, returned_objects=[],
        key=f"mapa_{idx}_{raio_km}_{st.session_state.geracao}",
    )

    st.markdown('<div class="titulo-tabela">Entregadores Mais Próximos (Filtrados)</div>', unsafe_allow_html=True)
    tabela = montar_tabela(res["dentro"])
    if tabela.empty:
        st.info("Nenhum entregador dentro do raio. Aumente o raio ou gere mais entregadores.")
    else:
        st.dataframe(
            tabela, hide_index=True, use_container_width=True,
            height=min(38 + 35 * len(tabela), 320),
            column_config={
                "Distância": st.column_config.NumberColumn("Distância (km)", format="%.2f km"),
                "ETA": st.column_config.NumberColumn("Tempo Estimado (ETA)", format="%.0f min"),
            },
        )

    with st.expander("Histórico de consultas (tempos para o relatório)"):
        st.dataframe(pd.DataFrame(st.session_state.historico), hide_index=True, use_container_width=True)