import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import io

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Dashboard de Análise de Vendas")

# 1. UPLOAD ACEITA XLSX OU ZIP
uploaded_file = st.sidebar.file_uploader("Envie sua planilha.xlsx ou.zip", type=['xlsx', 'zip'])

if uploaded_file is None:
    st.info("Faça upload de uma planilha ou arquivo.zip para começar")
    st.stop()

# 2. LER DENTRO DO ZIP SE PRECISAR
try:
    if uploaded_file.name.endswith('.zip'):
        st.write("📦 Detectado arquivo.zip. Lendo planilha de dentro...")
        with zipfile.ZipFile(uploaded_file, 'r') as z:
            # Pega o primeiro.xlsx que achar dentro do zip
            file_name = [f for f in z.namelist() if f.endswith('.xlsx')][0]
            with z.open(file_name) as f:
                df = pd.read_excel(f, usecols='F,G,I,J,Q')
    else:
        # Se for xlsx normal
        df = pd.read_excel(uploaded_file, usecols='F,G,I,J,Q')

    df.columns = ['loja','data','produto','categoria','valor']
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    df['ano'] = df['data'].dt.year
    df['mes_num'] = df['data'].dt.month
    df['mes'] = df['data'].dt.month_name()

except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.error("Verifique se dentro do.zip tem 1 planilha.xlsx com as colunas F,G,I,J,Q")
    st.stop()


# 3. FILTROS
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
    st.warning("Nenhum dado encontrado com os filtros selecionados")
    st.stop()

# 4. KPIs
st.header("KPIs Gerais")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Faturamento Total", f"R$ {df_filtrado['valor'].sum():,.2f}")
col2.metric("Ticket Medio", f"R$ {df_filtrado['valor'].mean():,.2f}")
col3.metric("Qtd Vendas", f"{len(df_filtrado):,}")
col4.metric("Qtd Produtos", f"{df_filtrado['produto'].nunique():,}")

# 5. ANALISE DE QUEDA
if len(df_filtrado['ano'].unique()) > 1:
    st.divider()
    st.header("📉 Análise de Queda: Ano Atual vs Ano Anterior")
    ano_atual = df_filtrado['ano'].max()
    ano_ant = df_filtrado['ano'].min()

