import streamlit as st
st.title("Analise BSB - Teste")
st.write("Subiu com sucesso!")
uploaded_file = st.file_uploader("Teste upload zip")
if uploaded_file:
    st.success("Arquivo recebido!")
