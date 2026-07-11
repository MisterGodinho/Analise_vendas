import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise Vendas", layout="wide")
st.title("📊 Análise de Vendas Gerencial")

uploaded_file = st.file_uploader("Carregue seu Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['data'] = pd.to_datetime(df['data'])
    
    # FILTROS
    c1,c2,c3 = st.columns(3)
    data = c1.date_input("Período", [df['data'].min(), df['data'].max()])
    loja = c2.multiselect("Loja", df['loja'].unique(), default=df['loja'].unique())
    cat = c3.multiselect("Categoria", df['categoria'].unique(), default=df['categoria'].unique())

    df = df[(df['data'] >= pd.to_datetime(data[0])) & (df['data'] <= pd.to_datetime(data[1]))]
    df = df[df['loja'].isin(loja) & df['categoria'].isin(cat)]

    # KPIs
    fat = df['valor_total'].sum()
    ticket = fat / df['id_pedido'].nunique() if df['id_pedido'].nunique() > 0 else 0
    top_loja = df.groupby('loja')['valor_total'].sum().idxmax() if len(df) > 0 else "N/A"
    
    k1,k2,k3 = st.columns(3)
    k1.metric("Faturamento Total", f"R$ {fat:,.2f}")
    k2.metric("Ticket Médio", f"R$ {ticket:,.2f}")
    k3.metric("Melhor Loja", top_loja)

    # GRAFICOS
    g1,g2 = st.columns(2)
    g1.plotly_chart(px.bar(df.groupby('categoria')['valor_total'].sum().reset_index(), x='categoria', y='valor_total', title="Vendas por Categoria"), use_container_width=True)
    g2.plotly_chart(px.bar(df.groupby('loja')['valor_total'].sum().sort_values().reset_index(), x='valor_total', y='loja', orientation='h', title="Vendas por Loja"), use_container_width=True)
else:
    st.info("Envie um Excel com as colunas: data, id_pedido, loja, categoria, valor_total")
