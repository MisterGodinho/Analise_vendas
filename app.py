import streamlit as st
import pandas as pd
import plotly.express as px
import locale

# Tenta colocar o mês em PT-BR
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    pass

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Dashboard de Análise de Vendas")

# 1. UPLOAD DO ARQUIVO
uploaded_file = st.sidebar.file_uploader("Envie sua planilha .xlsx", type=['xlsx'])

if uploaded_file is None:
    st.info("👆 Faça upload de uma planilha para começar a análise")
    st.stop()

# 2. CARREGAR E TRATAR DADOS
try:
    df = pd.read_excel(uploaded_file, usecols='F,G,I,J,Q')
    df.columns = ['loja','data','produto','categoria','valor']
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    df['ano'] = df['data'].dt.year
    df['mes_num'] = df['data'].dt.month
    df['mes'] = df['data'].dt.strftime('%B').str.capitalize() # Mes em PT
except Exception as e:
    st.error(f"Erro ao ler a planilha: {e}")
    st.stop()

# 3. FILTROS NA SIDEBAR
st.sidebar.header("🔍 Filtros")
anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
meses = st.sidebar.multiselect("Mês", df[['mes_num','mes']].drop_duplicates().sort_values('mes_num')['mes'].tolist(), default=df['mes'].unique())
lojas = st.sidebar.multiselect("Loja", sorted(df['loja'].unique()), default=sorted(df['loja'].unique()))
categorias = st.sidebar.multiselect("Categoria", sorted(df['categoria'].unique()), default=sorted(df['categoria'].unique()))

df_filtrado = df[
    (df['ano'].isin(anos)) &
    (df['mes'].isin(meses)) &
    (df['loja'].isin(lojas)) &
    (df['categoria'].isin(categorias))
]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os
