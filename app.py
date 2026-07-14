import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Análise de Vendas Gerenciais")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    st.write("Colunas encontradas no seu Excel:", df.columns.tolist())
    
    df.columns = df.columns.str.strip()
    
    mapa = {
        'Fecha':'data',
        'Tienda':'loja', 
        'Categoria':'categoria',
        'Importe cc':'valor_total',
        'Código Ae':'id_pedido'
    }
    
    df = df.rename(columns=mapa)
    
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df = df.dropna(subset=['valor_total'])
    
    st.sidebar.header("Filtros")
    data = st.sidebar.date_input("Periodo", [df['data'].min(), df['data'].max()])
    loja = st.sidebar.multiselect("Loja", df['loja'].unique())
    categoria = st.sidebar.multiselect("Categoria", df['categoria'].unique())
    
    if loja: df = df[df['loja'].isin(loja)]
    if categoria: df = df[df['categoria'].isin(categoria)]
    
    faturamento = df['valor_total'].sum()
    ticket_medio = df['valor_total'].mean()
    melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento Total", f"R$ {faturamento:,.2f}")
    col2.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
    col3.metric("Melhor Loja", melhor_loja)
    
    fig1 = px.bar(df.groupby('categoria')['valor_total'].sum().reset_index(), x='categoria', y='valor_total', title='Vendas por Categoria')
    fig2 = px.line(df.groupby('data')['valor_total'].sum().reset_index(), x='data', y='valor_total', title='Faturamento ao Longo do Tempo')
    
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
