import streamlit as st

st.set_page_config(page_title="Relatório Criança Alfabetizada", layout="wide")

st.title("Relatório — Criança Alfabetizada")
st.markdown("Selecione abaixo a análise que deseja visualizar:")

st.page_link("app.py", label="Home", icon="🏠")
st.page_link("pages/grafico1.py", label="📊 Gráfico 1 — Evolução 2024×2025", icon="1️⃣")
st.page_link("pages/grafico2.py", label="📶 Gráfico 2 — Tabela de Desempenho dos Alunos", icon="2️⃣")
st.page_link("pages/grafico3.py", label="🧑‍🏫 Gráfico 3 — Escola específica", icon="3️⃣")
st.page_link("pages/grafico4.py", label="🧑🎓 Gráfico 4 — Turma específica", icon="4️⃣")
