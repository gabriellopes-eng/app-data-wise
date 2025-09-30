import requests
import pandas as pd
import plotly.express as px
import streamlit as st

INSTALLATION_ID = "63e7d8d8-a570-42ba-a9af-8ce8bf044cf1"
SESSION_TOKEN   = "r:e936f6f0d778e4447c34540e4aeb61a8"

AVALIACAO_2024  = "AV22024"
AVALIACAO_2025  = "AV22025"

# Escolha do agregado (município ou escola)
AGREGADO = "4306809"  # Município de Encantado/RS <- Parece que eu tenho que por 

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

#  FUNÇÕES AUXILIARES 
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

def media_por_serie(disciplina: str,  avaliacao: str) -> pd.DataFrame:
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
        linhas.append({
            "Série": serie,
            "Disciplina": disciplina,
            "Ano": "2024" if avaliacao==AVALIACAO_2024 else "2025",
            "TX_ACERTOS_MEDIA": media
        })
    out = pd.DataFrame(linhas)
    out["Série"] = pd.Categorical(out["Série"], categories=list(ETAPAS.keys()), ordered=True)
    return out.sort_values("Série")

#LAYOUT STREAMLIT
st.set_page_config(page_title="Análise 1 - Evolução 2024×2025", layout="wide")

st.title("❖ Análise 1 - Evolução dos Resultados (1º ao 5º ano)")
st.markdown(f"""
**Comparativo por disciplina** — Rede Pública  
**Âmbito:** Município (IBGE) = `{AGREGADO}`  

Avaliações consideradas:  
- **2024** = `{AVALIACAO_2024}`  
- **2025** = `{AVALIACAO_2025}`  

Cada barra representa a **média de TX_ACERTOS (%)** do 1º ao 5º ano em cada disciplina.
""")

# Coleta dados
df_24_lp = media_por_serie("LÍNGUA PORTUGUESA", AVALIACAO_2024)
df_25_lp = media_por_serie("LÍNGUA PORTUGUESA", AVALIACAO_2025)
df_24_mt = media_por_serie("MATEMÁTICA",        AVALIACAO_2024)
df_25_mt = media_por_serie("MATEMÁTICA",        AVALIACAO_2025)

plot_df = pd.concat([df_24_lp, df_25_lp, df_24_mt, df_25_mt], ignore_index=True)

if plot_df.empty or plot_df["TX_ACERTOS_MEDIA"].isna().all():
    st.error("⚠️ Sem dados retornados pela API. Verifique tokens ou rótulos das avaliações.")
else:
    fig = px.bar(
        plot_df,
        x="Série", y="TX_ACERTOS_MEDIA",
        color="Ano", barmode="group",
        facet_col="Disciplina", facet_col_spacing=0.10,
        text="TX_ACERTOS_MEDIA",
        labels={"TX_ACERTOS_MEDIA":"TX_ACERTOS (média %)"},
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(
        yaxis=dict(range=[0,100]),
        showlegend=True,
        margin=dict(l=20,r=20,t=40,b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
