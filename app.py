import streamlit as st

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")

st.title("📊 Analise do Negocio BSB")
st.success("✅ App abriu! Agora vamos subir o resto")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

if uploaded_files:
    st.info("Recebi " + str(len(uploaded_files)) + " arquivos")
    st.warning("Proxima etapa: ler os arquivos")
else:
    st.info("📤 Faça upload dos arquivos 2025.zip e 2026.zip")
