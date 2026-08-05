import streamlit as st
import pandas as pd
import zipfile
import plotly.express as px
import gc

st.set_page_config(page_title="Analise BSB", layout="wide")
st.title("📊 Analise do Negocio BSB")
st.warning("⚠️ SÓ SUBA 1 ARQUIVO.zip POR VEZ | 2025.zip OU 2026.zip")

uploaded_file = st.file_uploader("Arraste o arquivo.zip aqui", type=['zip'])

@st.cache_data
def carregar(zip_file):
    with zipfile.ZipFile(zip_file) as z:
        nome = [n for n in z.namelist() if not n.endswith('/')]
        with z.open(nome[0]) as f:
            if '.xlsx' in nome[0]:
                df = pd.read_excel(f, usecols='F,G,I,J,Q')
                df.columns = ['loja', 'data', 'produto', 'categoria', 'valor']
            else:
                df = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], names=['loja','data','produto','categoria','valor'], header=0, encoding='latin-1')
    
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df['mes'] = df['data'].dt.to_period('M').astype(str)
    df = df.dropna(subset=['valor'])
    gc.collect()
    return df

if uploaded_file:
    df = carregar(uploaded_file)
    
    st.success(f"✅ Carregado! {len(df):,} linhas")
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento Total", f"R$ {df['valor'].sum():,.2f}")
    col2.metric("Ticket Médio", f"R$ {df['valor'].mean():,.2f}")
    col3.metric("Qtd Vendas", f"{len(df):,}")
    
    # FILTROS
    st.sidebar.header("Filtros")
    lojas = st.sidebar.multiselect("Selecione a Loja", df['loja'].unique())
    if lojas:
        df = df[df['loja'].isin(lojas)]
    
    # RANKING TOP 10 PRODUTOS
    st.subheader("🏆 Top 10 Produtos que mais venderam")
    top_produtos = df.groupby('produto')['valor'].sum().sort_values(ascending=False).head(10).reset_index()
    fig1 = px.bar(top_produtos, x='valor', y='produto', orientation='h', text='valor')
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)
    
    # GRAFICO POR MES
    st.subheader("📈 Faturamento por Mês")
    vendas_mes = df.groupby('mes')['valor'].sum().reset_index()
    fig2 = px.line(vendas_mes, x='mes', y='valor', markers=True)
    st.plotly_chart(fig2, use_container_width=True)
    
    # TABELA
    st.subheader("Tabela de Dados")
    st.dataframe(df.head(100))
    
else:
    st.info("Faça upload de 2025.zip ou 2026.zip para começar")
