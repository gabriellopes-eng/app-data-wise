import streamlit as st

st.set_page_config(page_title="Relatório Criança Alfabetizada", layout="wide")

st.title("❖ Relatório - Criança Alfabetizada")
st.markdown("◆ Selecione abaixo a Análise que deseja visualizar:")

st.page_link("home.py", label="Home", icon="🏠")
st.page_link("pages/analise1.py", label="Análise 1 - Evolução 2024×2025", icon="1️⃣")
st.page_link("pages/analise2.py", label="Análise 2 - Tabela de Desempenho dos Alunos em Matemática e Português", icon="2️⃣")
st.page_link("pages/analise3.py", label="Análise 3 - Escola específica", icon="3️⃣")
st.page_link("pages/analise4.py", label="Análise 4 - Turma específica", icon="4️⃣")
