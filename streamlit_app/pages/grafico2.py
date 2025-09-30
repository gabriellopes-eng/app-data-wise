import streamlit as st
import pandas as pd
import requests

# URL da API
url = "https://criancaalfabetizada.caeddigital.net/portal/functions/getDadosResultado"

# esses sao os indicadores de MATEMÁTICA do 1º ano (14) ao 5º ano (18) 
indicadores_mt = [
    "11988MT14","11988MT15","11988MT16","11988MT17","11988MT18",
    "61988MT14","61988MT15","61988MT16","61988MT17","61988MT18",
    "71988MT14","71988MT15","71988MT16","71988MT17","71988MT18",
    "12016MT14","12016MT15","12016MT16","12016MT17","12016MT18",
    "62016MT14","62016MT15","62016MT16","62016MT17","62016MT18",
    "72016MT14","72016MT15","72016MT16","72016MT17","72016MT18"
]

# minha função para buscar dados de um ciclo
def get_dados(ciclo):
    payload = {
        "CD_INDICADOR": indicadores_mt,
        "agregado": "z8yg99e75f22",  # turma
        "filtros": [
            {"operation": "equalTo","field": "DADOS.VL_FILTRO_AVALIACAO","value": ciclo}
        ],
        "filtrosAdicionais": [],
        "nivelAbaixo": "1",
        "ordenacao": [["NM_ENTIDADE","ASC"]],
        "collectionResultado": None,
        "CD_INDICADOR_LABEL": [],
        "TP_ENTIDADE_LABEL": "01",
        "_ApplicationId": "portal",
        "_ClientVersion": "js2.19.0",
        "_InstallationId": "63e7d8d8-a570-42ba-a9af-8ce8bf044cf1",
        "_SessionToken": "r:e936f6f0d778e4447c34540e4aeb61a8"
    }

    res = requests.post(url, json=payload)
    data = res.json()["result"]

    # filtrando somente Matemática
    dados_matematica = [d for d in data if d["VL_FILTRO_DISCIPLINA"] == "MATEMÁTICA"]

    df = pd.DataFrame(dados_matematica)

    # lista de colunas desejadas -> O que o professor quer
    colunas_desejadas = [
        "NM_ENTIDADE","DC_ACERTOS","DC_PONTUACAO","TX_ACERTOS",
        "NU_ACERTO_HABILIDADE_1","NU_ACERTO_HABILIDADE_2",
        "NU_ACERTO_HABILIDADE_3","NU_ACERTO_HABILIDADE_4",
        "NU_ACERTO_HABILIDADE_5","NU_ACERTO_HABILIDADE_6",
        "NU_ACERTO_HABILIDADE_7","NU_ACERTO_HABILIDADE_8",
        "NU_ACERTO_HABILIDADE_9","NU_ACERTO_HABILIDADE_10",
        "VL_FILTRO_DISCIPLINA","VL_FILTRO_AVALIACAO"
    ]

    # Seleciona apenas as colunas que existem
    df = df[[c for c in colunas_desejadas if c in df.columns]]

    return df

# busca dados dos ciclos
df_c1 = get_dados("AV12025")     
df_c2 = get_dados("AV22025")

df_c1["CICLO"] = "C1"
df_c2["CICLO"] = "C2"


# LOGICA DE ORDENAR PARA QUE CADA ALINO APAREÇA COM C1 E LOGO ABAIXO C2
df_analises = pd.concat([df_c1, df_c2], ignore_index=True) #----> concatena os dois ciclos para análises, o ignore index evita problemas de indexação
df_analises["CICLO"] = pd.Categorical(df_analises["CICLO"], categories=["C1", "C2"], ordered=True) # ----> garantir a ordem C1 antes de C2
df_analises = df_analises.sort_values(["NM_ENTIDADE", "CICLO"]).reset_index(drop=True) 


# streamlit interface
st.title("Resultados de Matemática - Encanto (2025)")

st.subheader("Tabela do Ciclo 1 (AV12025)")
st.dataframe(df_c1)

st.subheader("Tabela do Ciclo 2 (AV22025)")
st.dataframe(df_c2)

st.subheader("Tabela de Análises dos Alunos (Comparação C1 x C2)")
st.dataframe(df_analises)
