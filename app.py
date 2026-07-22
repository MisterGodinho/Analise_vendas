import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Análise de Vendas 2025 vs 2026", layout="wide")
st.title("Dashboard de Analise de Vendas")
st.caption("Faca upload dos arquivos de 2025 e 2026")

def ler_arquivo(uploaded_file, ano_label):
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
        df['mes'] = df['data'].dt.month_name()
        return df
    except Exception as e:
        st.error(f"Erro ao ler arquivo {ano_label}: {e}")
        return pd.DataFrame()

st.sidebar.header("Upload dos Arquivos")
file_2025 = st.sidebar.file_uploader("Arquivo 2025.xlsx ou.zip", type=['xlsx', 'zip'], key="file25")
file_2026 = st.sidebar.file_uploader("Arquivo 2026.xlsx ou.zip", type=['xlsx', 'zip'], key="file26")

if file_2025 is None or file_2026 is None:
    st.info("Envie os 2 arquivos: 2025 e 2026 para comecar")
    st.stop()

df_2025 = ler_arquivo(file_2025, 2025)
df_2026 = ler_arquivo(file_2026, 2026)
df = pd.concat([df_2025, df_2026], ignore_index=True)

st.sidebar.header("Filtros")
lista_meses = df[['mes_num','mes']].drop_duplicates().sort_values('mes_num')['mes'].tolist()
meses = st.sidebar.multiselect("Mes", lista_meses, default=lista_meses)
lojas = st.sidebar.multiselect("Loja", sorted(df['loja'].unique()), default=sorted(df['loja'].unique()))
categorias = st.sidebar.multiselect("Categoria", sorted(df['categoria'].unique()), default=sorted(df['categoria'].unique()))
anos = st.sidebar.multiselect("Ano", [2025, 2026], default=[2025, 2026])

df_filtrado = df[
    (df['ano'].isin(anos)) &
    (df['mes'].isin(meses)) &
    (df['loja'].isin(lojas)) &
    (df['categoria'].isin(categorias))
]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros")
    st.stop()

st.header
