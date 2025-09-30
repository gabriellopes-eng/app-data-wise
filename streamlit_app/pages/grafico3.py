import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# meus tokens e config
API_URL = "https://criancaalfabetizada.caeddigital.net/portal/functions/getDadosResultado"
APP_ID = "portal"
CLIENT_VER = "js2.19.0"

# meus tokens
INSTALLATION_ID = "63e7d8d8-a570-42ba-a9af-8ce8bf044cf1"
SESSION_TOKEN   = "r:e936f6f0d778e4447c34540e4aeb61a8"

# Rótulo  da avaliação 2025 
AVALIACAO_2025 = "AV22025"

# para o modo "todas as turmas da escola"
IND_TURMA = {
    "LÍNGUA PORTUGUESA": ["72016LP14","72016LP15","72016LP16","72016LP17","72016LP18"],
    "MATEMÁTICA":        ["72016MT14","72016MT15","72016MT16","72016MT17","72016MT18"],
}
#  para o modo "uma turma"
IND_ALUNO = {
    "LÍNGUA PORTUGUESA": ["12016LP14","12016LP15","12016LP16","12016LP17","12016LP18"],
    "MATEMÁTICA":        ["12016MT14","12016MT15","12016MT16","12016MT17","12016MT18"],
}

# minhas funcoes auxiliares
def call_api(payload: dict) -> pd.DataFrame:
    payload.update({
        "_ApplicationId": APP_ID,
        "_ClientVersion": CLIENT_VER,
        "_InstallationId": INSTALLATION_ID,
        "_SessionToken": SESSION_TOKEN,
    })
    try:
        r = requests.post(API_URL, json=payload, timeout=60)
        if r.status_code != 200:
            try:
                msg = r.json()
            except Exception:
                msg = r.text
            st.error(f"HTTP {r.status_code} — erro da API: {msg}")
            return pd.DataFrame()
        return pd.json_normalize(r.json().get("result", []))
    except Exception as e:
        st.error(f"Falha de requisição: {e}")
        return pd.DataFrame()

def df_turma_2025_por_escola(cd_escola: str) -> pd.DataFrame:
    """Todas as turmas da escola (LP × MT por turma) em 2025 — usa indicadores 72016…"""
    linhas = []
    for disc, indicadores in IND_TURMA.items():
        payload = {
            "CD_INDICADOR": indicadores,
            "agregado": cd_escola,  # escola
            "filtros": [
                {"operation":"equalTo","field":"DADOS.VL_FILTRO_AVALIACAO","value":AVALIACAO_2025},
                {"operation":"equalTo","field":"DADOS.VL_FILTRO_DISCIPLINA","value":disc},
            ],
            "filtrosAdicionais": [
                {"field":"DADOS.VL_FILTRO_REDE","value":"MUNICIPAL","operation":"equalTo"}
            ],
            "nivelAbaixo":"1",
            "ordenacao":[["NM_ENTIDADE","ASC"]],
            "collectionResultado": None,
            "CD_INDICADOR_LABEL": [],
            "TP_ENTIDADE_LABEL": "01",
        }
        df = call_api(payload)
        if df.empty:
            continue
        df["TX_ACERTOS"] = pd.to_numeric(df["TX_ACERTOS"], errors="coerce")
        nome = df["NM_TURMA"].fillna(df["NM_ENTIDADE"])
        for i in range(len(df)):
            linhas.append({
                "Turma": str(nome.iloc[i]),
                "Disciplina": disc,
                "TX_ACERTOS": float(df["TX_ACERTOS"].iloc[i]) if pd.notna(df["TX_ACERTOS"].iloc[i]) else None
            })
    out = pd.DataFrame(linhas)
    if not out.empty:
        out = out.sort_values(["Turma","Disciplina"])
    return out

def df_lp_mt_de_uma_turma(cd_turma: str) -> pd.DataFrame:
    """
    Uma turma (LP × MT) em 2025 — consulta ALUNOS (12016…) da turma e tira a média da TX_ACERTOS.
    Isso funciona mesmo quando a consulta direta 72016… por turma não retorna linhas.
    """
    linhas = []
    for disc, indicadores in IND_ALUNO.items():
        payload = {
            "CD_INDICADOR": indicadores,
            "agregado": cd_turma,  # turma
            "filtros": [
                {"operation":"equalTo","field":"DADOS.VL_FILTRO_AVALIACAO","value":AVALIACAO_2025},
                {"operation":"equalTo","field":"DADOS.VL_FILTRO_DISCIPLINA","value":disc},
            ],
            "filtrosAdicionais": [
                {"field":"DADOS.VL_FILTRO_REDE","value":"MUNICIPAL","operation":"equalTo"}
            ],
            "nivelAbaixo":"1",   # desce para ALUNO
            "ordenacao":[["NM_ENTIDADE","ASC"]],
            "collectionResultado": None,
            "CD_INDICADOR_LABEL": [],
            "TP_ENTIDADE_LABEL": "01",
        }
        df = call_api(payload)
        if df.empty or "TX_ACERTOS" not in df.columns:
            continue
        df["TX_ACERTOS"] = pd.to_numeric(df["TX_ACERTOS"], errors="coerce")
        tx = df["TX_ACERTOS"].mean()
        if pd.notna(tx):
            linhas.append({"Disciplina": disc, "TX_ACERTOS": float(tx)})
    return pd.DataFrame(linhas)

# streamlit
st.set_page_config(page_title="Gráfico 3 — Destaque (apenas 2025)", layout="wide")

st.title("Gráfico 3 — Destaque por escola/turma (apenas 2025)")
st.caption("Cada barra representa a **média de TX_ACERTOS (%)** em **Língua Portuguesa** e **Matemática** no recorte escolhido.")
st.markdown("---")

colA, colB = st.columns([1,1], gap="large")
with colA:
    modo = st.radio(
        "Escolha o recorte",
        ["Uma turma (LP × MT)", "Todas as turmas da escola (LP × MT por turma)"],
        index=0
    )

# Exemplos padrão (você pode trocar)
cd_escola_default = "43188265"     # EMEF MUNDO ENCANTADO
cd_turma_default  = "z8yg99e75f22" # 1º ANO A

if modo.startswith("Uma turma"):
    cd_turma = st.text_input("Código da turma (CD_TURMA)", value=cd_turma_default)
    if st.button("Gerar gráfico", type="primary"):
        dados = df_lp_mt_de_uma_turma(cd_turma.strip())
        if dados.empty:
            st.warning("Sem dados 2025 para a turma selecionada. Verifique o ID e o rótulo da avaliação.")
        else:
            fig = px.bar(
                dados, x="Disciplina", y="TX_ACERTOS",
                text="TX_ACERTOS", range_y=[0,100],
                labels={"TX_ACERTOS":"TX_ACERTOS (%)"},
                title=None
            )
            fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            fig.update_layout(margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
else:
    cd_escola = st.text_input("Código da escola (CD_INSTITUICAO)", value=cd_escola_default)
    if st.button("Gerar gráfico", type="primary"):
        df_escola = df_turma_2025_por_escola(cd_escola.strip())
        if df_escola.empty:
            st.warning("Sem dados 2025 para as turmas da escola selecionada. Verifique o código e o rótulo da avaliação.")
        else:
            fig = px.bar(
                df_escola, x="Turma", y="TX_ACERTOS",
                color="Disciplina", barmode="group",
                text="TX_ACERTOS", range_y=[0,100],
                labels={"TX_ACERTOS":"TX_ACERTOS (%)", "Turma":"Turma"},
                title=None
            )
            fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
            fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), legend_title_text="Disciplina")
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Fonte: Plataforma Criança Alfabetizada (CAEd). Métrica: **TX_ACERTOS (%)** em 2025.")
