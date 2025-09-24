import requests
import pandas as pd
import json

URL = "https://criancaalfabetizada.caeddigital.net/portal/functions/getDadosResultado"
HEADERS = {"content-type": "application/json"}

CD_INDICADOR = [
    "11988LP14","11988LP15","11988LP16","11988LP17","11988LP18",
    "11988MT14","11988MT15","11988MT16","11988MT17","11988MT18",
    "61988LP14","61988LP15","61988LP16","61988LP17","61988LP18",
    "61988MT14","61988MT15","61988MT16","61988MT17","61988MT18",
    "71988LP14","71988LP15","71988LP16","71988LP17","71988LP18",
    "71988MT14","71988MT15","71988MT16","71988MT17","71988MT18",
    "12016LP14","12016LP15","12016LP16","12016LP17","12016LP18",
    "12016MT14","12016MT15","12016MT16","12016MT17","12016MT18",
    "62016LP14","62016LP15","62016LP16","62016LP17","62016LP18",
    "62016MT14","62016MT15","62016MT16","62016MT17","62016MT18",
    "72016LP14","72016LP15","72016LP16","72016LP17","72016LP18",
    "72016MT14","72016MT15","72016MT16","72016MT17","72016MT18"
]

# A) TURMAS por ESCOLA (fetch-classes-by-school
payload = {
    "CD_INDICADOR": CD_INDICADOR,
    "agregado": "43188265",  # Pelo visto eu troco esse agregado (conjunto de dados) aqui
    "filtros": [
        {"operation":"equalTo","field":"DADOS.VL_FILTRO_AVALIACAO","value":"AV22025"}
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

# # B) ESCOLAS por agregado (fetch-schools)
# payload = {
#     "CD_INDICADOR": CD_INDICADOR,
#     "agregado": "4306809",
#     "filtros": [
#         {"operation":"equalTo","field":"DADOS.VL_FILTRO_AVALIACAO","value":"AV22025"},
#         {"operation":"equalTo","field":"DADOS.VL_FILTRO_ETAPA","value":"ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO"},
#         {"operation":"equalTo","field":"DADOS.VL_FILTRO_DISCIPLINA","value":"LÍNGUA PORTUGUESA"}
#     ],
#     "filtrosAdicionais": [
#         {"field":"DADOS.VL_FILTRO_REDE","value":"PÚBLICA","operation":"equalTo"}
#     ],
#     "nivelAbaixo":"1",
#     "ordenacao":[["NM_ENTIDADE","ASC"]],
#     "collectionResultado": None,
#     "CD_INDICADOR_LABEL": [],
#     "TP_ENTIDADE_LABEL":"01",
#     "_ApplicationId":"portal",
#     "_ClientVersion":"js2.19.0",
#     "_InstallationId":"63e7d8d8-a570-42ba-a9af-8ce8bf044cf1",
#     "_SessionToken":"r:e936f6f0d778e4447c34540e4aeb61a8"
# }

# # C) ALUNOS por TURMA (fetch-students-by-class)
# payload = {
#     "CD_INDICADOR": CD_INDICADOR,
#     "agregado": "z8yg99e75f22",  # CD_TURMA
#     "filtros": [
#         {"operation":"equalTo","field":"DADOS.VL_FILTRO_AVALIACAO","value":"AV22025"}
#     ],
#     "filtrosAdicionais": [],
#     "nivelAbaixo":"1",
#     "ordenacao":[["NM_ENTIDADE","ASC"]],
#     "collectionResultado": None,
#     "CD_INDICADOR_LABEL": [],
#     "TP_ENTIDADE_LABEL":"01",
#     "_ApplicationId":"portal",
#     "_ClientVersion":"js2.19.0",
#     "_InstallationId":"63e7d8d8-a570-42ba-a9af-8ce8bf044cf1",
#     "_SessionToken":"r:e936f6f0d778e4447c34540e4aeb61a8"
# }

#  funções seguras para extrair linhas -> OBS!- Preciso entender melhor a estrutura dessas respostas
def extract_rows(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        # 1) Pelo visto essas API's embrulham nesse result aqui -> "result"
        if "result" in obj:
            r = extract_rows(obj["result"])
            if r: return r
        # 2) Chaves se vir em forma de lista
        for k in ("data", "rows", "results", "items"):
            v = obj.get(k)
            if isinstance(v, list):
                return v
        # 3) se for em dict
        for v in obj.values():
            if isinstance(v, (dict, list)):
                r = extract_rows(v)
                if r: return r
    return []

def ensure_columns(df, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]

# Chamada de API
resp = requests.post(URL, json=payload, headers=HEADERS, timeout=60)
print("HTTP:", resp.status_code)
resp.raise_for_status()
full = resp.json()

rows = extract_rows(full)
if not rows:
    print("Não achei a lista de registros. Amostra da resposta:")
    print(json.dumps(full, indent=2, ensure_ascii=False)[:2000])

df = pd.DataFrame(rows)

# Colunas que quero garantir que existam
COLS = [
    "NM_ENTIDADE","DC_ACERTOS","DC_PONTUACAO","TX_ACERTOS",
    "NU_ACERTO_HABILIDADE_1","NU_ACERTO_HABILIDADE_2","NU_ACERTO_HABILIDADE_3","NU_ACERTO_HABILIDADE_4",
    "NU_ACERTO_HABILIDADE_5","NU_ACERTO_HABILIDADE_6","NU_ACERTO_HABILIDADE_7","NU_ACERTO_HABILIDADE_8",
    "VL_FILTRO_DISCIPLINA"
]
if df.empty:
    print("Tabela vazia (sem registros). Verifique 'agregado' e filtros.")
else:
    df = ensure_columns(df, COLS)
    with pd.option_context(
        'display.max_columns', None,
        'display.max_rows', None,
        'display.width', 0,
        'display.max_colwidth', None
    ):
        print(df.to_string(index=False))
    
    df.to_csv("python/tables/tabela.csv", sep=";" ,index=False, encoding="utf-8-sig")
    print("CSV salvo em tabela.csv")

    df.to_excel("python/tables/tabela.xlsx", index=False, sheet_name="Resultados")
    print("Excel salvo em tabela.xlsx")
