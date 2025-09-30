# app-data-wise

# Resumo do que cada request retorna

A lógica geral é: **o que você coloca em `agregado` + `nivelAbaixo`** define **o nível da entidade** que vem no `result`.

---

## 1) `fetch-classes-by-school` (turmas por escola)
**Objetivo:** listar **turmas** de uma **escola** específica.  
**Como vem no request:**  
- `agregado = <CD_INSTITUICAO>` (código da escola)  
- `nivelAbaixo = "1"`  

**O que retorna (por item em `result`):**  
- `DC_TIPO_ENTIDADE`: **"TURMA"**  
- `CD_ENTIDADE`: código da **turma**  
- `CD_ENTIDADE_SUPERIOR`: **CD da escola**  
- `NM_ENTIDADE` / `NM_TURMA`: nome da turma (ex.: “1º ANO A”)  
- `VL_FILTRO_DISCIPLINA`, `VL_FILTRO_ETAPA`, `VL_FILTRO_AVALIACAO`  
- Indicadores agregados da turma (ex.: `TX_PARTICIPACAO`, `DC_ATIVIDADES`, `TX_ACERTOS`, `NU_N01/N02/N03`, `TX_ACERTO_HABILIDADE_i`)

**Checklist de validação:**  
- `DC_TIPO_ENTIDADE` = **"TURMA"** 
- `CD_ENTIDADE_SUPERIOR` = **CD da escola passada**

**Use quando:** quer ver o **painel de turmas** de uma escola, comparar desempenho **entre turmas**.

---

## 2) `fetch-schools` (escolas por município)
**Objetivo:** listar **escolas** de um **município** (com filtros como etapa, disciplina, rede).  
**Como vem no request:**  
- `agregado = <CD_MUNICIPIO>` (ex.: `4306809`)  
- `nivelAbaixo = "1"`  
- `filtros`: `VL_FILTRO_AVALIACAO`, `VL_FILTRO_ETAPA`, `VL_FILTRO_DISCIPLINA`  
- `filtrosAdicionais`: `VL_FILTRO_REDE` (ex.: “PÚBLICA”)

**O que retorna (por item em `result`):**  
- `DC_TIPO_ENTIDADE`: **"ESCOLA"**  
- `CD_ENTIDADE`: código da **escola**  
- `CD_ENTIDADE_SUPERIOR`: **CD do município**  
- `NM_ENTIDADE` / `NM_INSTITUICAO`: nome da escola  
- Métricas no nível **escola** (ex.: `TX_PARTICIPACAO`, `DC_ATIVIDADES`, `TX_ACERTOS`, `TX_N01/N02/N03`, `TX_ACERTO_HABILIDADE_i`)  
- Confirmações de contexto: `CD_MUNICIPIO`, `NM_MUNICIPIO`, `VL_FILTRO_*`

**Checklist de validação:**  
- `DC_TIPO_ENTIDADE` = **"ESCOLA"** 
- `CD_ENTIDADE_SUPERIOR` = **CD do município**  
- Campos `VL_FILTRO_*` batendo com seus filtros 

**Use quando:** precisa de um **ranking/lista de escolas** dentro do município, para uma **disciplina/etapa** específicos.

---

## 3) `fetch-students-by-classes` (alunos por turma)
**Objetivo:** listar **alunos** de uma **turma** específica (com resultados por disciplina).  
**Como vem no request:**  
- `agregado = <CD_TURMA>` (ex.: `z8yg99e75f22`)  
- `nivelAbaixo = "1"`  

**O que retorna (por item em `result`):**  
- `DC_TIPO_ENTIDADE`: **"ALUNO"**  
- `CD_ENTIDADE`: **ID do aluno**  
- `CD_ENTIDADE_SUPERIOR`: **CD da turma**  
- `NM_ENTIDADE`: nome do aluno  
- **Um registro por disciplina** (LP e MT), com:  
  - `DC_ATIVIDADES` (ex.: “22 de 22”)  
  - `NU_ACERTOS`, `TX_ACERTOS`, `DC_ACERTOS` (“x / 22”)  
  - `VL_PONTUACAO` e `DC_PONTUACAO` (“Adequado”, “Intermediário”, “Defasagem”)  
  - `NU_ACERTO_HABILIDADE_i` (“x / y” por habilidade)  
  - `NU_MODELO_CADERNO` (versão do caderno)

**Checklist de validação:**  
- `DC_TIPO_ENTIDADE` = **"ALUNO"** 
- `CD_ENTIDADE_SUPERIOR` = **CD da turma**   
- Mesmo aluno aparece em **duas linhas** (LP e MT) 

**Use quando:** quer ver o **detalhe individual** por aluno (acertos, habilidades, classificação).

---

## Dicas (Caso Academico):

- Cuidado com a estrutura HTTP:
- headers → linha em branco → body JSON sem comentários.
- Campos sensíveis (_SessionToken, _InstallationId) não devem ir para repositórios públicos.


os indicadores não dependem do nível de agregação, mas sim da avaliação aplicada.

Indicadores = identificam disciplinas + cadernos (LP14, MT14, etc).

Agregado = muda o nível que você quer ver os resultados:

Município → CD_MUNICIPIO

Escola → CD_INSTITUICAO

Turma → CD_TURMA

Aluno → CD_ENTIDADE

Ou seja, os indicadores são sempre os mesmos porque a prova aplicada é a mesma.
O que muda é onde você foca:

No município inteiro,

numa escola,

numa turma,

ou em um aluno.

🔎 Exemplo prático

fetch-schools → pega resultados agregados de várias escolas.

fetch-classes-by-school → pega resultados das turmas de uma escola.

fetch-students-by-class → pega resultados dos alunos de uma turma.

Todos pedem os mesmos indicadores, porque o teste aplicado (LP/MT, cadernos 14–18) é o mesmo.
Mas o "agregado" muda para dizer em que nível da hierarquia você quer enxergar esses indicadores.

👉 Resumindo:

Mesmos indicadores = mesma avaliação aplicada.

Agregado diferente = nível da análise (município, escola, turma, aluno).

- NM_ENTIDADE
- DC_ACERTOS
- DC_PONTUACAO
- TX_ACERTOS
- NU_ACERTO_HABILIDADE_1
- NU_ACERTO_HABILIDADE_2
- NU_ACERTO_HABILIDADE_3
- NU_ACERTO_HABILIDADE_4
- NU_ACERTO_HABILIDADE_5
- NU_ACERTO_HABILIDADE_6
- NU_ACERTO_HABILIDADE_7
- NU_ACERTO_HABILIDADE_8
- VL_FILTRO_DISCIPLINA


Curto e direto: a lógica do Gráfico 1 está correta.

O que ele calcula (exatamente)

Para cada série (1º–5º) e para cada disciplina (LP, MT):

faz uma consulta no nível definido em AGREGADO (município ou escola),

filtra por VL_FILTRO_AVALIACAO = 2024 ou 2025, VL_FILTRO_ETAPA = série, VL_FILTRO_DISCIPLINA = LP/MT, rede = PÚBLICA,

recebe várias linhas (uma por escola naquele nível),

converte TX_ACERTOS para número e tira a média → isso é a altura da barra.

Se 2024 aparece como NaN, não é erro do cálculo — é filtro que não encontrou dados (quase sempre rótulo de avaliação 2024 diferente do que você pôs).

Checklist de validação (3 passos, sem mudar o app)

Pegue 1 ponto do gráfico e confira no .http:

Ex.: LP — 1º ano — 2025 (município 4306809)

POST https://criancaalfabetizada.caeddigital.net/portal/functions/getDadosResultado
content-type: application/json

{
  "CD_INDICADOR": ["12016LP14","12016LP15","12016LP16","12016LP17","12016LP18"],
  "agregado": "4306809",
  "filtros": [
    {"operation":"equalTo","field":"DADOS.VL_FILTRO_AVALIACAO","value":"AV22025"},
    {"operation":"equalTo","field":"DADOS.VL_FILTRO_ETAPA","value":"ENSINO FUNDAMENTAL DE 9 ANOS - 1º ANO"},
    {"operation":"equalTo","field":"DADOS.VL_FILTRO_DISCIPLINA","value":"LÍNGUA PORTUGUESA"}
  ],
  "filtrosAdicionais": [
    {"field":"DADOS.VL_FILTRO_REDE","value":"PÚBLICA","operation":"equalTo"}
  ],
  "nivelAbaixo": "1",
  "ordenacao": [["NM_ENTIDADE","ASC"]],
  "collectionResultado": null,
  "CD_INDICADOR_LABEL": [],
  "TP_ENTIDADE_LABEL": "01",
  "_ApplicationId": "portal",
  "_ClientVersion": "js2.19.0",
  "_InstallationId": "<o seu>",
  "_SessionToken": "<o seu>"
}


O retorno vem com várias escolas; calcule a média de TX_ACERTOS → deve bater com a barra “LP 1º ano 2025”.

Repita para MT 2º ano 2025 e confira a outra faceta.

Para 2024: rode o mesmo request sem o filtro de avaliação; veja quais valores aparecem em VL_FILTRO_AVALIACAO e use o texto exato no app. Se o rótulo estiver errado, as barras de 2024 ficam NaN.

Quando o gráfico “estaria errado”?

Só se a gente:

trocasse o nível (ex.: AGREGADO errado),

usasse outro campo (ex.: DC_ACERTOS em vez de TX_ACERTOS),

não aplicasse os filtros (etapa/disciplina/avaliação/rede).
Nada disso está acontecendo no código.

Se quiser, me manda o rótulo exato de 2024 que você viu no VL_FILTRO_AVALIACAO e eu te confirmo na hora se as barras de 2024 passam a aparecer.