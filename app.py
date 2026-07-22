import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Análise de Vendas 2025 vs 2026", layout="wide")
st.title("📊 Dashboard de Análise de Vendas")
st.caption("Faça upload dos arquivos de 2025 e 2026 para ver queda, crescimento e baixo giro")

def ler_arquivo(uploaded_file, ano_label):
    """Lê xlsx ou zip e retorna DataFrame com coluna do ano"""
    if uploaded_file is None:
        return pd.DataFrame()
    
    try:
        if uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(uploaded_file, 'r') as z:
                file_name = [f for f in z.namelist() if f.endswith('.xlsx')][0]
                with z.open(file_name) as f:
                    df = pd.read_excel(f, usecols='F,G,I,J,Q')
        else:
            df = pd.read_excel(uploaded_file, usecols='F,G,I,J,Q')
        
        df.columns = ['loja','data','produto','categoria','valor']
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df = df.dropna(subset=['data'])
        df['ano'] = ano_label
        df['mes_num'] = df['data'].dt.month
        df['mes'] = df['data'].dt.month_name(locale='pt_BR')
        return df
    except Exception as e:
        st.error(f
