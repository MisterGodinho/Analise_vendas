
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Análise de Vendas Gerenciais")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    # MAPA COM TIENDA
    mapa = {
        'Fecha':'data',
        'Tienda':'loja', # <-- Voltou pro código da loja T549
        'Categoria':'categoria',
        'Importe con IVA':'valor_total',
        'Código Ae':'id_pedido'
    }

    df = df.rename(columns=mapa)
    df = df.dropna(subset=['valor_total', 'data', 'loja'])

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')

    # ===== FILTROS =====
    st.sidebar.header("🔍 Filtros")
    min_data, max_data = df['data'].min(), df['data'].max()
    data = st.sidebar.date_input("Periodo", [min_data, max_data])
    loja = st.sidebar.multiselect("Loja", options=sorted(df['loja'].dropna().unique()))
    categoria = st.sidebar.multiselect("Categoria", options=sorted(df['categoria'].dropna().unique()))

    if len(data) == 2:
        df = df[(df['data'] >= pd.to_datetime(data[0])) & (df['data'] <= pd.to_datetime(data[1]))]
    if loja: df = df[df['loja'].isin(loja)]
    if categoria: df = df[df['categoria'].isin(categoria)]

    # ===== KPIs =====
    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax()
        categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax()
        valor_categoria_top = df.groupby('categoria')['valor_total'].sum().max()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Faturamento Total", f"R$ {faturamento:,.2f}")
        col2.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
        col3.metric("Melhor Loja", melhor_loja)
        col4.metric("Categoria Top", categoria_top, f"R$ {valor_categoria_top:,.2f}")

        st.divider()

        # ===== GRAFICOS =====
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Vendas por Categoria")
            fig1 = px.bar(df.groupby('categoria')['valor_total'].sum().reset_index(),
                          x='categoria', y='valor_total', text_auto='.2s')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)

        with col_graf2:
            st.subheader("Faturamento ao Longo do Tempo")
            fig2 = px.line(df.groupby('data')['valor_total'].sum().reset_index(),
                           x='data', y='valor_total')
            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados")

else:
    st.info("👆 Faça upload do arquivo Excel para começar")
