import re
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# ===================== CONFIG / TOKENS =====================
API_URL = "https://criancaalfabetizada.caeddigital.net/portal/functions/getDadosResultado"
APP_ID = "portal"
CLIENT_VER = "js2.19.0"

# >>> PREENCHA COM SEUS TOKENS <<<
INSTALLATION_ID = "63e7d8d8-a570-42ba-a9af-8ce8bf044cf1"
SESSION_TOKEN   = "r:e936f6f0d778e4447c34540e4aeb61a8"

AVALIACAO_2025 = "AV22025"

IND_TURMA = {
    "LÍNGUA PORTUGUESA": ["72016LP14","72016LP15","72016LP16","72016LP17","72016LP18"],
    "MATEMÁTICA":        ["72016MT14","72016MT15","72016MT16","72016MT17","72016MT18"],
}

# ===================== FUNÇÕES =====================
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

def fetch_turmas_da_escola_2025(cd_escola: str, disciplina: str) -> pd.DataFrame:
    payload = {
        "CD_INDICADOR": IND_TURMA[disciplina],
        "agregado": cd_escola,  # escola
        "filtros": [
            {"operation":"equalTo","field":"DADOS.VL_FILTRO_AVALIACAO","value":AVALIACAO_2025},
            {"operation":"equalTo","field":"DADOS.VL_FILTRO_DISCIPLINA","value":disciplina},
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
    return call_api(payload)

def extrair_habilidades(row: pd.Series) -> pd.DataFrame:
    habs = []
    for col in row.index:
        if col.startswith("TX_ACERTO_HABILIDADE_"):
            val = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(val):
                num = col.split("_")[-1]
                habs.append({"Habilidade": f"H{num}", "Valor": float(val)})
    df = pd.DataFrame(habs)
    if not df.empty:
        # ordena por número da habilidade
        df["__ord"] = df["Habilidade"].str.replace("H","",regex=False).astype(int)
        df = df.sort_values("__ord").drop(columns="__ord")
    return df

# ===================== UI =====================
st.set_page_config(page_title="Gráfico 4 — Habilidades por turma (2025)", layout="wide")
st.title("Gráfico 4 — Habilidades por Turma (apenas 2025)")
st.caption("Selecione uma escola e depois uma turma. Os gráficos mostram percentual de acertos por habilidade em Língua Portuguesa e Matemática.")
st.markdown("---")

# Estado da página
if "g4" not in st.session_state:
    st.session_state["g4"] = {
        "cd_escola": None,
        "turmas": pd.DataFrame(),
        "df_lp": pd.DataFrame(),
        "df_mt": pd.DataFrame(),
        "cd_turma": None,
    }

# Entrada de escola
cd_escola_input = st.text_input("Código da escola (CD_INSTITUICAO)", value=st.session_state["g4"]["cd_escola"] or "43188265")

# Se o usuário trocou o código, limpa dados carregados
if st.session_state["g4"]["cd_escola"] and cd_escola_input.strip() != st.session_state["g4"]["cd_escola"]:
    st.session_state["g4"].update({"turmas": pd.DataFrame(), "df_lp": pd.DataFrame(), "df_mt": pd.DataFrame(), "cd_turma": None})

# Botão: carrega e salva em sessão
if st.button("Carregar turmas", type="primary"):
    cd_escola = cd_escola_input.strip()
    df_lp = fetch_turmas_da_escola_2025(cd_escola, "LÍNGUA PORTUGUESA")
    df_mt = fetch_turmas_da_escola_2025(cd_escola, "MATEMÁTICA")

    # normaliza nomes/ids
    for df in (df_lp, df_mt):
        if not df.empty:
            if "NM_TURMA" not in df.columns:
                df["NM_TURMA"] = df.get("NM_ENTIDADE", "")
            if "CD_TURMA" not in df.columns:
                df["CD_TURMA"] = df.get("CD_ENTIDADE", "")

    turmas = pd.concat(
        [
            df_lp[["CD_TURMA","NM_TURMA"]] if not df_lp.empty else pd.DataFrame(columns=["CD_TURMA","NM_TURMA"]),
            df_mt[["CD_TURMA","NM_TURMA"]] if not df_mt.empty else pd.DataFrame(columns=["CD_TURMA","NM_TURMA"]),
        ],
        ignore_index=True
    ).drop_duplicates().sort_values("NM_TURMA")

    if turmas.empty:
        st.warning("Não encontrei turmas para 2025 nesta escola.")
    else:
        # salva tudo na sessão
        st.session_state["g4"].update({
            "cd_escola": cd_escola,
            "turmas": turmas,
            "df_lp": df_lp,
            "df_mt": df_mt,
            # define turma padrão
            "cd_turma": turmas.iloc[0]["CD_TURMA"]
        })

# Se temos turmas na sessão, mostra o selectbox e SEMPRE plota
g4 = st.session_state["g4"]
if not g4["turmas"].empty:

    # selectbox que atualiza o state
    label_opts = [f'{r.NM_TURMA} — ({r.CD_TURMA})' for _, r in g4["turmas"].iterrows()]
    # calcula índice atual
    try:
        idx_atual = list(g4["turmas"]["CD_TURMA"]).index(g4["cd_turma"])
    except Exception:
        idx_atual = 0
    escolha = st.selectbox("Escolha a turma", options=label_opts, index=idx_atual)
    st.session_state["g4"]["cd_turma"] = escolha.split("(")[-1].rstrip(")")

    # pega linhas LP/MT dessa turma
    row_lp = pd.Series(dtype="object")
    row_mt = pd.Series(dtype="object")
    if not g4["df_lp"].empty:
        m = g4["df_lp"]["CD_TURMA"] == g4["cd_turma"]
        if m.any(): row_lp = g4["df_lp"][m].iloc[0]
    if not g4["df_mt"].empty:
        m = g4["df_mt"]["CD_TURMA"] == g4["cd_turma"]
        if m.any(): row_mt = g4["df_mt"][m].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Língua Portuguesa — habilidades (%)")
        if row_lp.empty:
            st.info("Sem registro de LP para esta turma em 2025.")
        else:
            hab_lp = extrair_habilidades(row_lp)
            if hab_lp.empty:
                st.info("Sem campos de habilidades para LP nesta turma.")
            else:
                fig_lp = px.bar(hab_lp, x="Habilidade", y="Valor", text="Valor", labels={"Valor":"% de acerto"})
                fig_lp.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                fig_lp.update_layout(yaxis=dict(range=[0,100]), margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig_lp, use_container_width=True)
            tx_lp = pd.to_numeric(row_lp.get("TX_ACERTOS"), errors="coerce")
            if pd.notna(tx_lp):
                st.caption(f"**TX_ACERTOS (LP): {tx_lp:.0f}%**")

    with col2:
        st.subheader("Matemática — habilidades (%)")
        if row_mt.empty:
            st.info("Sem registro de MT para esta turma em 2025.")
        else:
            hab_mt = extrair_habilidades(row_mt)
            if hab_mt.empty:
                st.info("Sem campos de habilidades para MT nesta turma.")
            else:
                fig_mt = px.bar(hab_mt, x="Habilidade", y="Valor", text="Valor", labels={"Valor":"% de acerto"})
                fig_mt.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                fig_mt.update_layout(yaxis=dict(range=[0,100]), margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig_mt, use_container_width=True)
            tx_mt = pd.to_numeric(row_mt.get("TX_ACERTOS"), errors="coerce")
            if pd.notna(tx_mt):
                st.caption(f"**TX_ACERTOS (MT): {tx_mt:.0f}%**")

    st.markdown("---")
    st.caption("Fonte: CAEd — **TX_ACERTOS (%)** por habilidade (LP/MT), 2025. Os campos `TX_ACERTO_HABILIDADE_*` variam conforme a série/modelo.")
else:
    st.info("Informe o código da escola e clique em **Carregar turmas**.")
