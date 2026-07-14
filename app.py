
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Análise de Vendas Gerenciais")

uploaded_file = st.file_uploader("Carregue seu Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # LIMPA E RENOMEIA COLUNAS DO SEU EXCEL
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        'Fecha':'data',
        'Tienda':'loja', 
        'Categoria':'categoria',
        'Importe cc':'valor_total',
        'Código Ae':'id_pedido'
    })
    
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df = df.dropna(subset=['valor_total'])

    # FILTROS
    st.sidebar.header("Filtros")
    data = st.sidebar.date_input("Período", [df['data'].min(), df['data'].max()])
    loja = st.sidebar.multiselect("Loja", df['loja'].unique())
    categoria = st.sidebar.multiselect("Categoria", df['categoria'].unique())
    
    if loja:
        df = df[df['loja'].isin(loja)]
    if categoria:
        df = df[df['categoria'].isin(categoria)]
    if len(data) == 2:
        df = df[(df['data'] >= pd.to_datetime(data[0])) & (df['data'] <= pd.to_datetime(data[1]))]

    # KPIs
    faturamento = df['valor_total'].sum()
    ticket = faturamento / df['id_pedido'].nunique() if df['id_pedido'].nunique() > 0 else 0
    top_loja = df.groupby('loja')['valor_total'].sum().idxmax() if len(df) > 0 else "N/A"
    
    k1,k2,k3 = st.columns(3)
    k1.metric("Faturamento Total", f"R$ {faturamento:,.2f}")
    k2.metric("Ticket Médio", f"R$ {ticket:,.2f}")
    k3.metric("Melhor Loja", top_loja)

    # GRAFICOS
    g1,g2 = st.columns(2)
    g1.plotly_chart(px.bar(df.groupby('categoria')['valor_total'].sum().reset_index(), 
                   x='categoria', y='valor_total', title="Vendas por Categoria"), use_container_width=True)
    g2.plotly_chart(px.bar(df.groupby('loja')['valor_total'].sum().sort_values().reset_index(), 
                   x='valor_total', y='loja', orientation='h', title="Vendas por Loja"), use_container_width=True)
else:
    st.info("Envie um Excel com as colunas: Fecha, Tienda, Categoria, Importe cc, Código Ae")
