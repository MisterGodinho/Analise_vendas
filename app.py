import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

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
    df = df.dropna(subset=['valor_total', 'data', 'loja', 'produto'])
    df = df[df['produto']!= '']

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month
    df['mes_nome'] = df['data'].dt.month_name()
    df['dia'] = df['data'].dt.day

    # ===== FILTROS COM BOTÕES =====
    st.sidebar.header("🔍 Filtros")

    # FILTRO 1: ANO
    anos_disponiveis = sorted(df['ano'].unique())
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)
    df_ano = df[df['ano'] == ano_selecionado]

    # FILTRO 2: MÊS COM BOTÃO
    meses_disponiveis = sorted(df_ano['mes'].unique())
    nomes_meses = [calendar.month_name[m] for m in meses_disponiveis]
    mes_map = dict(zip(nomes_meses, meses_disponiveis))

    mes_selecionado_nome = st.sidebar.selectbox("Selecione o Mês", nomes_meses)
    mes_selecionado = mes_map[mes_selecionado_nome]
    df_mes = df_ano[df_ano['mes'] == mes_selecionado]

    # FILTRO 3: DIAS DO MÊS COM EXPANDER
    with st.sidebar.expander("📅 Filtrar por Dias Específicos"):
        dias_do_mes = sorted(df_mes['dia'].unique())
        dias_selecionados = st.multiselect(
            "Selecione os Dias",
            options=dias_do_mes,
            default=dias_do_mes # vem marcado todos
        )
        if dias_selecionados:
            df_mes = df_mes[df_mes['dia'].isin(dias_selecionados)]

    # OUTROS FILTROS
    loja = st.sidebar.multiselect("Loja", options=sorted(df_mes['loja'].dropna().unique()))
    categoria = st.sidebar.multiselect("Categoria", options=sorted(df_mes['categoria'].dropna().unique()))

    if loja: df_mes = df_mes[df_mes['loja'].isin(loja)]
    if categoria: df_mes = df_mes[df_mes['categoria'].isin(categoria)]

    df = df_mes # df final já filtrado

    # ===== KPIs =====
    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax()
        categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax()
        valor_categoria_top = df.groupby('categoria')['valor_total'].sum().max()
        produto_top = df.groupby('produto')['valor_total'].sum().idxmax()
        valor_produto_top = df.groupby('produto')['valor_total'].sum().max()

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
        col6.metric("Produto Top", produto_top, f"R$ {valor_produto_top:,.2f}")

        st.divider()

        # ===== COMPARAÇÃO ANO ANTERIOR =====
        st.subheader("📈 Comparativo Anual")
        faturamento_ano = df.groupby('ano')['valor_total'].sum().reset_index()
        fig_ano = px.bar(faturamento_ano, x='ano', y='valor_total', text_auto='.2s')
        fig_ano.update_layout(yaxis_tickprefix='R$ ')
        st.plotly_chart(fig_ano, use_container_width=True)

        # ===== GRAFICOS =====
        st.subheader("Top 10 Produtos Mais Vendidos")
        top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
        fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h', text_auto='.2s')
        fig3.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
        fig3.update_traces(texttemplate='R$ %{x:,.2f}')
        fig3.update_xaxes(tickprefix='R$ ')
        st.plotly_chart(fig3,
