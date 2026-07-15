
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Análise de Vendas Gerenciais")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip()

    # MAPA DAS COLUNAS DO SEU EXCEL
    mapa = {
        'Fecha':'data',
        'Tienda':'loja',
        'Categoria':'categoria',
        'Importe con IVA':'valor_total',
        'Código Ae':'id_pedido'
    }

    df = df.rename(columns=mapa)

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df = df.dropna(subset=['valor_total', 'data', 'loja'])

    # ===== FILTROS NA BARRA LATERAL =====
    st.sidebar.header("🔍 Filtros")

    min_data, max_data = df['data'].min(), df['data'].max()
    data = st.sidebar.date_input("Periodo", [min_data, max_data])

    loja = st.sidebar.multiselect("Loja", options=sorted(df['loja'].dropna().unique()))
    categoria = st.sidebar.multiselect("Categoria", options=sorted(df['categoria'].dropna().unique()))

    # Aplica filtros
    if len(data) == 2:
        df = df[(df['data'] >= pd.to_datetime(data[0])) & (df['data'] <= pd.to_datetime(data[1]))]
    if loja:
        df = df[df['loja'].isin(loja)]
    if categoria:
        df = df
