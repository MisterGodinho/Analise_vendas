import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Dashboard de Análise de Vendas")

def ler_arquivo(uploaded_file, ano_label):
    """Função para ler xlsx ou zip e já adicionar coluna do ano"""
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
        df['ano'] = ano_label # Força o ano que você selecionou
        df['mes_num'] = df['data'].dt.month
        df['mes'] = df['data'].dt.month_name()
        return df
    except Exception as e:
        st.error(f"Erro ao ler arquivo {ano_label}: {e}")
        return pd.DataFrame()

# 1. DOIS UPLOADS NA SIDEBAR
st.sidebar.header("📂 Upload dos Arquivos")
file_2025 = st.sidebar.file_uploader("Upload 2025.xlsx ou.zip", type=['xlsx', 'zip'], key="file25")
file_2026 = st.sidebar.file_uploader("Upload 2026.xlsx ou.zip", type=['xlsx', 'zip'], key="file26")

if file_2025 is None or file_2026 is None:
    st.info("Envie os 2 arquivos: 2025 e 2026 para começar a análise comparativa")
    st.stop()

# 2. LER E JUNTAR OS 2 ANOS
df_2025 = ler_arquivo(file_2025, 2025)
df_2026 = ler_arquivo(file_2026, 2026)
df = pd.concat([df_2025, df_2026], ignore_index=True)

# 3. FILTROS
st.sidebar.header("🔍 Filtros")
meses = st.sidebar.multiselect("Mês", df[['mes_num','mes']].drop_duplicates().sort_values('mes_num')['mes'].tolist(), default=df['mes'].
