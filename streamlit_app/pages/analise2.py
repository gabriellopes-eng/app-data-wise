import streamlit as st
import pandas as pd
import requests
import plotly.express as px

#  CONFIG BÁSICA 
st.set_page_config(page_title="Análise 2 — Comparativo C1×C2 por aluno", layout="wide")

URL = "https://criancaalfabetizada.caeddigital.net/portal/functions/getDadosResultado"

# Turma alvo (eu (Gabriel) precisa ajustar isso se necessário)
TURMA_ID = "z8yg99e75f22"

# Tokens (os meus TOKENS já funcionam aí)
APP_ID = "portal"
CLIENT_VER = "js2.19.0"
INSTALLATION_ID = "63e7d8d8-a570-42ba-a9af-8ce8bf044cf1"
SESSION_TOKEN   = "r:e936f6f0d778e4447c34540e4aeb61a8"

# Ciclos alvo - Preciso ajustar se o rotulo mudar
CICLO_1 = "AV12025"
CICLO_2 = "AV22025"

# ================== INDICADORES ==================
def make_indicadores(disciplina: str) -> list[str]:
    """Monta a lista de indicadores (1º ao 5º ano, todos os ‘prefixos’) para a disciplina escolhida."""
    sufixo = "MT" if disciplina == "MATEMÁTICA" else "LP"
    bases  = ["11988", "61988", "71988", "12016", "62016", "72016"]
    anos   = ["14", "15", "16", "17", "18"]  # 1º→5º
    return [f"{b}{sufixo}{a}" for b in bases for a in anos]

# ================== BUSCA ==================
def get_dados(ciclo: str, disciplina: str) -> pd.DataFrame:
    indicadores = make_indicadores(disciplina)
    payload = {
        "CD_INDICADOR": indicadores,
        "agregado": TURMA_ID,                 # turmas → retorna linhas por ALUNO
        "filtros": [
            {"operation": "equalTo", "field": "DADOS.VL_FILTRO_AVALIACAO", "value": ciclo},
            {"operation": "equalTo", "field": "DADOS.VL_FILTRO_DISCIPLINA", "value": disciplina},
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

    res = requests.post(URL, json=payload, timeout=60)
    res.raise_for_status()
    data = res.json().get("result", [])
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Seleciona colunas principais +
    # todas as colunas de NU_ACERTO_HABILIDADE_* que existirem
    base_cols = [
        "NM_ENTIDADE", "DC_ACERTOS", "DC_PONTUACAO", "TX_ACERTOS",
        "VL_FILTRO_DISCIPLINA", "VL_FILTRO_AVALIACAO",
        "NM_MUNICIPIO", "NM_INSTITUICAO", "VL_FILTRO_ETAPA"
    ]
    hab_cols = [c for c in df.columns if c.startswith("NU_ACERTO_HABILIDADE_")]
    keep = [c for c in base_cols if c in df.columns] + hab_cols

    df = df[keep].copy()
    if "TX_ACERTOS" in df.columns:
        df["TX_ACERTOS"] = pd.to_numeric(df["TX_ACERTOS"], errors="coerce")

    # Ordena por nome para consistência
    if "NM_ENTIDADE" in df.columns:
        df = df.sort_values("NM_ENTIDADE", kind="stable")

    return df.reset_index(drop=True)

# SELETOR + CABEÇALHO) 
st.title(f"❖ Análise 2 - Comparativo por Aluno (Ciclo 1 × Ciclo 2)")

disciplina = st.selectbox("Escolha a disciplina:", ["MATEMÁTICA", "LÍNGUA PORTUGUESA"], index=0)

st.caption("""
O painel mostra:
- **Ciclo 1** (C1) e **Ciclo 2** (C2) por aluno, incluindo TX_ACERTOS e pontuação.
- Tabela comparativa com C1 seguido de C2 para cada aluno.
- Gráfico de barras **horizontais** (cores **azul** = C1, **laranja** = C2).
- Ranking de variação **Δ (C2 − C1)**.
""")

# CONSULTA 
df_c1 = get_dados(CICLO_1, disciplina)
df_c2 = get_dados(CICLO_2, disciplina)

# Contexto (se disponível)
if not df_c1.empty:
    municipio  = df_c1["NM_MUNICIPIO"].iloc[0]    if "NM_MUNICIPIO"   in df_c1.columns else "—"
    instituicao= df_c1["NM_INSTITUICAO"].iloc[0]  if "NM_INSTITUICAO" in df_c1.columns else "—"
    etapa      = df_c1["VL_FILTRO_ETAPA"].iloc[0] if "VL_FILTRO_ETAPA" in df_c1.columns else "—"
    st.markdown(f"""
**Contexto da análise**  
- Município: **{municipio}**  
- Escola/Turma: **{instituicao}**  
- Etapa: **{etapa}**  
""")

# TABELAS 
df_c1["CICLO"] = "C1"
df_c2["CICLO"] = "C2"


st.subheader(f"◇ Tabela do Ciclo 1 ({CICLO_1} - {disciplina})")
st.dataframe(df_c1, use_container_width=True)
st.subheader(f"◇ Tabela do Ciclo 2 ({CICLO_2} - {disciplina})")
st.dataframe(df_c2, use_container_width=True)

# Junta e ordena para C1 seguido de C2 por aluno
df_analises = pd.concat([df_c1, df_c2], ignore_index=True)
df_analises["CICLO"] = pd.Categorical(df_analises["CICLO"], categories=["C1", "C2"], ordered=True)
df_analises = df_analises.sort_values(["NM_ENTIDADE", "CICLO"], kind="stable").reset_index(drop=True)

st.subheader("◇ Tabela de Análises (C1 seguido de C2 para cada aluno) - {disciplina}")
st.dataframe(df_analises[["NM_ENTIDADE","CICLO","TX_ACERTOS","DC_PONTUACAO"]], use_container_width=True)

# ================== GRÁFICO (barras horizontais) ==================
st.subheader("◈ Comparativo Visual - Taxa de Acertos por Aluno (C1 × C2) - {disciplina}")

df_plot = df_analises[["NM_ENTIDADE", "CICLO", "TX_ACERTOS"]].dropna().copy()

# ordena pelo valor de C2 (ou pelos valores existentes, se faltar C2)
ordem = (
    df_plot[df_plot["CICLO"] == "C2"]
    .sort_values("TX_ACERTOS", ascending=True)["NM_ENTIDADE"]
    .tolist()
)
if not ordem:
    ordem = df_plot.sort_values("TX_ACERTOS", ascending=True)["NM_ENTIDADE"].tolist()

fig = px.bar(
    df_plot,
    y="NM_ENTIDADE", x="TX_ACERTOS",
    color="CICLO", barmode="group",
    orientation="h",
    category_orders={"NM_ENTIDADE": ordem},
    color_discrete_map={"C1": "#1f77b4", "C2": "#ff7f0e"},  # azul / laranja
    title=f"Taxa de Acertos por Aluno — {disciplina} — C1 ({CICLO_1}) vs C2 ({CICLO_2})",
)
fig.update_traces(texttemplate="%{x:.0f}%", textposition="outside", cliponaxis=False)
fig.update_layout(
    height=max(420, 22 * len(ordem) + 140),
    xaxis=dict(title="Taxa de Acertos (%)", range=[0, 100], tickmode="linear", tick0=0, dtick=10),
    yaxis=dict(title="Aluno"),
    bargap=0.25, bargroupgap=0.08,
    margin=dict(l=180, r=40, t=60, b=40),
    legend_title_text="Ciclo",
)
st.plotly_chart(fig, use_container_width=True)

#  Δ MEU RANKING 
if not df_plot.empty:
    pivot = df_analises.pivot(index="NM_ENTIDADE", columns="CICLO", values="TX_ACERTOS")
    if {"C1","C2"}.issubset(pivot.columns):
        pivot["Δ (C2 - C1)"] = pivot["C2"] - pivot["C1"]
        st.subheader("◈ Variação por aluno (Δ C2 − C1) - {disciplina}")
        st.dataframe(
            pivot.sort_values("Δ (C2 - C1)", ascending=False).round(1).reset_index(),
            use_container_width=True
        )