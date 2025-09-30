import requests
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

INSTALLATION_ID = "63e7d8d8-a570-42ba-a9af-8ce8bf044cf1"
SESSION_TOKEN   = "r:e936f6f0d778e4447c34540e4aeb61a8"

AVALIACAO_2024  = "AV22024"
AVALIACAO_2025  = "AV22025"
AGREGADO        = "4306809"   # município IBGE 

API_URL = "https://criancaalfabetizada.caeddigital.net/portal/functions/getDadosResultado"
APP_ID, CLIENT_VER = "portal", "js2.19.0"

ETAPAS = {
    "1º ANO": "ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO",
    "2º ANO": "ENSINO FUNDAMENTAL DE 9 ANOS - 2º ANO",
    "3º ANO": "ENSINO FUNDAMENTAL DE 9 ANOS - 3º ANO",
    "4º ANO": "ENSINO FUNDAMENTAL DE 9 ANOS - 4º ANO",
    "5º ANO": "ENSINO FUNDAMENTAL DE 9 ANOS - 5º ANO",
}
INDICADORES = {
    "LÍNGUA PORTUGUESA": ["12016LP14","12016LP15","12016LP16","12016LP17","12016LP18"],
    "MATEMÁTICA":        ["12016MT14","12016MT15","12016MT16","12016MT17","12016MT18"],
}

# essa eh minha api
def call_api(payload: dict) -> pd.DataFrame:
    payload.update({
        "_ApplicationId": APP_ID,
        "_ClientVersion": CLIENT_VER,
        "_InstallationId": INSTALLATION_ID,
        "_SessionToken": SESSION_TOKEN
    })
    r = requests.post(API_URL, json=payload, timeout=60)
    if r.status_code != 200:
        try:
            msg = r.json()
        except Exception:
            msg = r.text
        st.error(f"HTTP {r.status_code} — erro da API:\n{msg}")
        return pd.DataFrame()
    return pd.json_normalize(r.json().get("result", []))

def media_por_serie(disciplina: str, avaliacao: str) -> pd.DataFrame:
    linhas = []
    for serie, etapa in ETAPAS.items():
        payload = {
            "CD_INDICADOR": INDICADORES[disciplina],
            "agregado": AGREGADO,
            "filtros": [
                {"operation":"equalTo","field":"DADOS.VL_FILTRO_AVALIACAO","value":avaliacao},
                {"operation":"equalTo","field":"DADOS.VL_FILTRO_ETAPA","value":etapa},
                {"operation":"equalTo","field":"DADOS.VL_FILTRO_DISCIPLINA","value":disciplina},
            ],
            "filtrosAdicionais": [
                {"field":"DADOS.VL_FILTRO_REDE","value":"PÚBLICA","operation":"equalTo"}
            ],
            "nivelAbaixo":"1",
            "ordenacao":[["NM_ENTIDADE","ASC"]],
            "collectionResultado": None,
            "CD_INDICADOR_LABEL": [],
            "TP_ENTIDADE_LABEL": "01",
        }
        df = call_api(payload)
        media = None
        if not df.empty and "TX_ACERTOS" in df.columns:
            df["TX_ACERTOS"] = pd.to_numeric(df["TX_ACERTOS"], errors="coerce")
            media = df["TX_ACERTOS"].mean()
        linhas.append({"Série": serie, "Disciplina": disciplina, "Média": media})
    out = pd.DataFrame(linhas)
    out["Série"] = pd.Categorical(out["Série"], categories=list(ETAPAS.keys()), ordered=True)
    return out.sort_values("Série")

# meu grafico
st.set_page_config(page_title="Gráfico 2 — Δ 2025−2024 por série", layout="wide")

st.title("📊 Gráfico 2 — Evolução (Δ 2025 − 2024) por série")
sub_nivel = "Município (IBGE)" if AGREGADO.isdigit() and len(AGREGADO) == 7 else "Escola (CD_INSTITUICAO)"
st.subheader(f"LP × MT • Rede Pública • Âmbito: {sub_nivel} = {AGREGADO}")
st.markdown(
    f"**Avaliações:** 2024 = `{AVALIACAO_2024}` • 2025 = `{AVALIACAO_2025}`  \n"
    "Heatmap mostra a **variação (p.p.)** da média de **TX_ACERTOS**. "
    "**Verde** = melhorou; **vermelho** = caiu; célula vazia = faltou um dos anos."
)

# dados
df24_lp = media_por_serie("LÍNGUA PORTUGUESA", AVALIACAO_2024)
df25_lp = media_por_serie("LÍNGUA PORTUGUESA", AVALIACAO_2025)
df24_mt = media_por_serie("MATEMÁTICA",        AVALIACAO_2024)
df25_mt = media_por_serie("MATEMÁTICA",        AVALIACAO_2025)

def calc_delta(df24, df25, disciplina):
    m = pd.merge(
        df25[["Série","Média"]].rename(columns={"Média":"M25"}),
        df24[["Série","Média"]].rename(columns={"Média":"M24"}),
        on="Série", how="outer"
    )
    m["Disciplina"] = disciplina
    m["Delta"] = m["M25"] - m["M24"]
    m["Tem_2024"] = ~m["M24"].isna()
    m["Tem_2025"] = ~m["M25"].isna()
    return m

delta_full = pd.concat([
    calc_delta(df24_lp, df25_lp, "LÍNGUA PORTUGUESA"),
    calc_delta(df24_mt, df25_mt, "MATEMÁTICA"),
], ignore_index=True)

# pivot para heatmap -- mas aqui o plotly ta pegafo 
pivot = delta_full.pivot(index="Série", columns="Disciplina", values="Delta") \
                  .reindex(index=list(ETAPAS.keys()), columns=["LÍNGUA PORTUGUESA","MATEMÁTICA"])

if pivot.isna().all().all():
    st.error("Não foi possível calcular Δ porque falta 2024 e/ou 2025 em todas as séries. Verifique os rótulos das avaliações.")
else:
    max_abs = float(np.nanmax(np.abs(pivot.values))) if np.isfinite(np.nanmax(np.abs(pivot.values))) else 1.0
    fig = px.imshow(
        pivot,
        text_auto=".1f",
        color_continuous_scale="RdYlGn",
        zmin=-max_abs, zmax=max_abs, zmid=0,
        aspect="auto",
        labels=dict(color="Δ p.p.") #melhorar a barra
    )
    fig.update_layout(margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # Lista onde faltou algum ano (para a fala pública) -> rever 
    faltas = delta_full.loc[(~delta_full["Tem_2024"]) | (~delta_full["Tem_2025"]),
                            ["Série","Disciplina","Tem_2024","Tem_2025"]]
    if not faltas.empty:
        st.caption("⚠️ Séries/disciplinas sem um dos anos (células ficam vazias no heatmap):")
        faltas = faltas.replace({True:"ok", False:"faltou"})
        st.dataframe(faltas, use_container_width=True)

st.caption("Fonte: Plataforma Criança Alfabetizada (CAEd). Métrica: Δ (2025 − 2024) da média de TX_ACERTOS por série e disciplina.")
