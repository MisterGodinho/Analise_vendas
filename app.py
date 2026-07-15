import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Análise de Vendas Gerenciais")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    mapa = {
        'Fecha':'data',
        'Tienda':'loja',
        'Categoria':'categoria',
        'Descripción artículo':'produto',
        'Importe con IVA':'valor_total',
        'Código Ae':'id_pedido'
    }

    df = df.rename(columns=mapa)
    df = df.dropna(subset=['valor_total', 'data', 'loja', 'produto']) # <-- Adicionei produto aqui
    df = df[df['produto']!= ''] # Remove produto vazio

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df['ano'] = df['data'].dt.year

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
        produto_top = df.groupby('produto')['valor_total'].sum().idxmax() # <-- NOVO
        valor_produto_top = df.groupby('produto')['valor_total'].sum().max() # <-- NOVO

        # CALCULO CRESCIMENTO VS ANO ANTERIOR
        ano_selecionado = df['ano'].max()
        ano_anterior = ano_selecionado - 1
        faturamento_ano_atual = df[df['ano'] == ano_selecionado]['valor_total'].sum()
        faturamento_ano_anterior = df[df['ano'] == ano_anterior]['valor_total'].sum()
        crescimento = ((faturamento_ano_atual - faturamento_ano_anterior) / faturamento_ano_anterior) * 100 if faturamento_ano_anterior > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {faturamento:,.2f}", f"{crescimento:.1f}% vs {ano_anterior}")
        col2.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
        col3.metric("Ano em Análise", int(ano_selecionado))

        col4, col5, col6 = st.columns(3)
        col4.metric("Melhor Loja", melhor_loja)
        col5.metric("Categoria Top", categoria_top, f"R$ {valor_categoria_top:,.2f}")
        col6.metric("Produto Top", produto_top, f"R$ {valor_produto_top:,.2f}") # <-- NOVO KPI

        st.divider()

        # ===== COMPARAÇÃO ANO ANTERIOR =====
        st.subheader("📈 Comparativo Anual")
        faturamento_ano = df.groupby('ano')['valor_total'].sum().reset_index()
        fig_ano = px.bar(faturamento_ano, x='ano', y='valor_total', text_auto='.2s')
        st.plotly_chart(fig_ano, use_container_width=True)

        # ===== GRAFICOS =====
        st.subheader("Top 10 Produtos Mais Vendidos") # <-- JOGUEI PRA CIMA
        top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
        fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h', text_auto='.2s')
        fig3.update_layout(yaxis={'categoryorder':'total ascending'}, height=500) # Gráfico maior
        st.plotly_chart(fig3, use_container_width=True)

        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Vendas por Categoria")
            fig1 = px.bar(df.groupby('categoria')['valor_total'].sum().reset_index(), x='categoria', y='valor_total', text_auto='.2s')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)

        with col_graf2:
            st.subheader("Faturamento ao Longo do Tempo")
            fig2 = px.line(df.groupby('data')['valor_total'].sum().reset_index(), x='data', y='valor_total')
            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados")

else:
    st.info("👆 Faça upload do arquivo Excel para começar")
