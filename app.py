import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Dashboard de Análise de Vendas")

uploaded_file = st.sidebar.file_uploader("Envie sua planilha .xlsx", type=['xlsx'])

if uploaded_file is None:
    st.info("Faça upload de uma planilha para começar a análise")
    st.stop()

df = pd.read_excel(uploaded_file, usecols='F,G,I,J,Q')
df.columns = ['loja','data','produto','categoria','valor']
df['data'] = pd.to_datetime(df['data'], errors='coerce')
df = df.dropna(subset=['data'])
df['ano'] = df['data'].dt.year
df['mes_num'] = df['data'].dt.month
df['mes'] = df['data'].dt.month_name()

st.sidebar.header("Filtros")
anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
meses = st.sidebar.multiselect("Mes", df[['mes_num','mes']].drop_duplicates().sort_values('mes_num')['mes'].tolist(), default=df['mes'].unique())
lojas = st.sidebar.multiselect("Loja", sorted(df['loja'].unique()), default=sorted(df['loja'].unique()))
categorias = st.sidebar.multiselect("Categoria", sorted(df['categoria'].unique()), default=sorted(df['categoria'].unique()))

df_filtrado = df[
    (df['ano'].isin(anos)) &
    (df['mes'].isin(meses)) &
    (df['loja'].isin(lojas)) &
    (df['categoria'].isin(categorias))
]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados") # LINHA CORRIGIDA
    st.stop()

st.header("KPIs Gerais")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Faturamento Total", f"R$ {df_filtrado['valor'].sum():,.2f}")
col2.metric("Ticket Medio", f"R$ {df_filtrado['valor'].mean():,.2f}")
col3.metric("Qtd Vendas", f"{len(df_filtrado):,}")
col4.metric("Qtd Produtos", f"{df_filtrado['produto'].nunique():,}")

# ... resto do código igual ao anterior ...
