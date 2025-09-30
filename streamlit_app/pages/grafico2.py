import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ================== CONFIG ==================
st.set_page_config(page_title="Gráfico 2 - Tabela e Comparativo (C1 x C2)", layout="wide")

URL = "https://criancaalfabetizada.caeddigital.net/portal/functions/getDadosResultado"

# Indicadores de MATEMÁTICA do 1º ano (14) ao 5º ano (18)
INDICADORES_MT = [
    "11988MT14","11988MT15","11988MT16","11988MT17","11988MT18",
    "61988MT14","61988MT15","61988MT16","61988MT17","61988MT18",
    "71988MT14","71988MT15","71988MT16","71988MT17","71988MT18",
    "12016MT14","12016MT15","12016MT16","12016MT17","12016MT18",
    "62016MT14","62016MT15","62016MT16","62016MT17","62016MT18",
    "72016MT14","72016MT15","72016MT16","72016MT17","72016MT18"
]

# Turma alvo (ajuste se necessário)
TURMA_ID = "z8yg99e75f22"

# Tokens (já funcionando no teu ambiente)
APP_ID = "portal"
CLIENT_VER = "js2.19.0"
INSTALLATION_ID = "63e7d8d8-a570-42ba-a9af-8ce8bf044cf1"
SESSION_TOKEN   = "r:e936f6f0d778e4447c34540e4aeb61a8"

# ================== FUNÇÃO DE BUSCA ==================
def get_dados(ciclo: str) -> pd.DataFrame:
    payload = {
        "CD_INDICADOR": INDICADORES_MT,
        "agregado": TURMA_ID,                # TURMA
        "filtros": [
            {"operation": "equalTo", "field": "DADOS.VL_FILTRO_AVALIACAO", "value": ciclo}
        ],
        "filtrosAdicionais": [],
        "nivelAbaixo": "1",
        "ordenacao": [["NM_ENTIDADE", "ASC"]],
        "collectionResultado": None,
        "CD_INDICADOR_LABEL": [],
        "TP_ENTIDADE_LABEL": "01",
        "_ApplicationId": APP_ID,
        "_ClientVersion": CLIENT_VER,
        "_InstallationId": INSTALLATION_ID,
        "_SessionToken": SESSION_TOKEN
    }

    res = requests.post(URL, json=payload)
    res.raise_for_status()
    data = res.json().get("result", [])

    # Filtra apenas Matemática (por via das dúvidas)
    dados_matematica = [d for d in data if d.get("VL_FILTRO_DISCIPLINA") == "MATEMÁTICA"]
    if not dados_matematica:
        return pd.DataFrame()

    df = pd.DataFrame(dados_matematica)

    colunas_desejadas = [
        "NM_ENTIDADE","DC_ACERTOS","DC_PONTUACAO","TX_ACERTOS",
        "NU_ACERTO_HABILIDADE_1","NU_ACERTO_HABILIDADE_2",
        "NU_ACERTO_HABILIDADE_3","NU_ACERTO_HABILIDADE_4",
        "NU_ACERTO_HABILIDADE_5","NU_ACERTO_HABILIDADE_6",
        "NU_ACERTO_HABILIDADE_7","NU_ACERTO_HABILIDADE_8",
        "NU_ACERTO_HABILIDADE_9","NU_ACERTO_HABILIDADE_10",
        "VL_FILTRO_DISCIPLINA","VL_FILTRO_AVALIACAO",

         "NM_INSTITUICAO",       # nome da escola/turma
    "CD_INSTITUICAO",       # código da escola (útil também)
    "NM_MUNICIPIO",         # município
    "CD_MUNICIPIO",
    "VL_FILTRO_ETAPA"

    ]



    df = df[[c for c in colunas_desejadas if c in df.columns]].copy()

    # Garante TX_ACERTOS numérico e ordenação por nome
    if "TX_ACERTOS" in df.columns:
        df["TX_ACERTOS"] = pd.to_numeric(df["TX_ACERTOS"], errors="coerce")
    if "NM_ENTIDADE" in df.columns:
        df = df.sort_values("NM_ENTIDADE", kind="stable")

    return df.reset_index(drop=True)

# ================== TÍTULO ==================
st.title("📘 Gráfico 2 — Comparativo por Aluno (Ciclo 1 × Ciclo 2) — Matemática")

st.caption("""
**O que você verá abaixo:**
- **Ciclo 1 (AV12025)** → Tabela por aluno (TX_ACERTOS, pontuação, habilidades).
- **Ciclo 2 (AV22025)** → Tabela por aluno (mesmas colunas).
- **Tabela de análises (C1 seguido de C2 para cada aluno)**.
- **Gráfico comparativo** com barras agrupadas (TX_ACERTOS C1 × C2 por aluno).
""")

# ================== BUSCA E TABELAS ==================
df_c1 = get_dados("AV12025")
df_c2 = get_dados("AV22025")

df_c1["CICLO"] = "C1"
df_c2["CICLO"] = "C2"



st.subheader("Tabela do Ciclo 1 (AV12025)")
st.dataframe(df_c1, use_container_width=True)

st.subheader("Tabela do Ciclo 2 (AV22025)")
st.dataframe(df_c2, use_container_width=True)

# Junta C1 e C2 e ordena para que cada aluno tenha C1 e logo abaixo C2
df_analises = pd.concat([df_c1, df_c2], ignore_index=True)
df_analises["CICLO"] = pd.Categorical(df_analises["CICLO"], categories=["C1", "C2"], ordered=True)
df_analises = df_analises.sort_values(["NM_ENTIDADE", "CICLO"], kind="stable").reset_index(drop=True)

st.subheader("Tabela de Análises dos Alunos (Comparação C1 × C2)")
st.dataframe(df_analises[["NM_ENTIDADE","CICLO","TX_ACERTOS","DC_PONTUACAO"]], use_container_width=True)


st.subheader("Comparativo Visual — Taxa de Acertos por Aluno (Ciclo 1 × Ciclo 2)")

# dados para o gráfico que eu queria
df_plot = df_analises[["NM_ENTIDADE", "CICLO", "TX_ACERTOS"]].dropna().copy()

# ordena alunos pela nota do C2 como base (C1 pode ser menor ou maior)
ordem = (
    df_plot[df_plot["CICLO"] == "C2"]
    .sort_values("TX_ACERTOS", ascending=True)["NM_ENTIDADE"]
    .tolist()
)
# fallback: se não tiver C2 pra todos
if not ordem:
    ordem = df_plot.sort_values("TX_ACERTOS", ascending=True)["NM_ENTIDADE"].tolist()


fig = px.bar(
    df_plot,
    y="NM_ENTIDADE", x="TX_ACERTOS",
    color="CICLO", barmode="group",
    orientation="h",
    category_orders={"NM_ENTIDADE": ordem},
    color_discrete_map={"C1": "#1f77b4", "C2": "#ff7f0e"}, # azul e laranja (Plotly)
    title="Taxa de Acertos por Aluno — Ciclo 1 vs Ciclo 2 (Matemática)",
)

# rótulos visíveis e legíveis
fig.update_traces(
    texttemplate="%{x:.0f}%",
    textposition="outside",            # fora da barra para não colidir
    cliponaxis=False,                  # permite o texto “sair” do eixo
)

# layout mais limpo e alto o bastante para todos os alunos
fig.update_layout(
    height= max(400, 22 * len(ordem) + 140),  # altura dinâmica
    xaxis=dict(
        title="Taxa de Acertos (%)",
        range=[0, 100],
        tickmode="linear",
        tick0=0,
        dtick=10,
        showgrid=True,
        gridcolor="rgba(255,255,255,.15)",
    ),
    yaxis=dict(title="Aluno"),
    bargap=0.25,
    bargroupgap=0.08,
    margin=dict(l=180, r=40, t=60, b=40),
    legend_title_text="Ciclo",
)

st.plotly_chart(fig, use_container_width=True)


# Ranking de variação (C2 - C1) por aluno
pivot = df_analises.pivot(index="NM_ENTIDADE", columns="CICLO", values="TX_ACERTOS")
pivot["Δ (C2 - C1)"] = pivot["C2"] - pivot["C1"]
st.subheader("Variação por aluno (Δ C2 − C1)")
st.dataframe(
    pivot.sort_values("Δ (C2 - C1)", ascending=False).round(1).reset_index(),
    use_container_width=True
)




