import streamlit as st
import pandas as pd
import zipfile

st.title("Analise BSB - MODO LEVE")
uploaded_file = st.file_uploader("SOBE SÓ 2026.zip")

if uploaded_file:
    # Lê em pedaços de 10.000 linhas
    with zipfile.ZipFile(uploaded_file) as z:
        nome = [n for n in z.namelist() if not n.endswith('/')]
        with z.open(nome[0]) as f:
            df = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], chunksize=10000)
            df = pd.concat(df)
    
    df.columns = ['loja','data','produto','categoria','valor']
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    st.success(f"Carregou {len(df)} linhas")
    st.dataframe(df.head())
