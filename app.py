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
    df['dia'] = df['data'].dt.day

    # ===== FILTROS NA SIDEBAR =====
    st.sidebar.header("🔍 Filtros")

    # ANO - BOTÃO RADIO PEQUENO
    anos_disponiveis = sorted(df['ano'].unique())
    ano_selecionado = st.sidebar.radio("Ano", anos_disponiveis, horizontal=True)

    df_ano = df[df['ano'] == ano_selecionado]

    # MÊS - BOTÃO RADIO PEQUENO
    meses_disponiveis = sorted(df_ano['mes'].unique())
    nomes_meses = [calendar.month_name[m][:3] for m in meses_disponiveis] # Jan, Fev, Mar
    mes_selecionado_idx = st.sidebar.radio("Mês", range(len(meses_disponiveis)),
                                          format_func=lambda x: nomes_meses[x], horizontal=True)
    mes_selecionado = meses_disponiveis[mes_selecionado_idx]

    df_mes = df_ano[df_ano['mes'] == mes_selecionado]

    # DIAS - CHECKBOX EM COLUNAS PEQUENAS
    st.sidebar.write("**Dias:**")
    dias_disponiveis = sorted(df_mes['dia'].unique())
    col_dias = st.sidebar.columns(7) # 7 colunas = 1 semana

    dias_selecionados = []
    for i, dia in enumerate(dias_disponiveis):
        if col_dias[i % 7].checkbox(str(dia), key=f"dia_{dia}"):
            dias_selecionados.append(dia)

    if dias_selecionados:
        df_mes = df_mes[df_mes['dia'].isin(dias_selecionados)]

    # OUTROS FILTROS
    loja = st.sidebar.multiselect("Loja", options=sorted(df_mes['loja'].dropna().unique()))
    categoria = st.sidebar.multiselect("Categoria", options=sorted(df_mes['categoria'].dropna().unique()))

    if loja: df_mes = df_mes[df_mes['loja'].isin(loja)]
    if categoria: df_mes = df_mes[df_mes['categoria'].isin(categoria)]

    df = df_mes

    # ===== KPIs =====
    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax() if len(df['loja'].unique()) > 0 else "-"
        categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax() if len(df['categoria'].unique()) > 0 else "-"
        valor_categoria_top = df.groupby('categoria')['valor_total'].sum().max() if len(df['categoria'].unique()) > 0 else 0
        produto_top = df.groupby('produto')['valor_total'].sum().idxmax() if len(df['produto'].unique()) > 0 else "-"
        valor_produto_top = df.groupby('produto')['valor_total'].sum().max() if len(df['produto'].unique()) > 0 else 0

        ano_anterior = ano_selecionado - 1
        faturamento_ano_atual = df[df['ano'] == ano_selecionado]['valor_total'].sum()
        faturamento_ano_anterior = df[df['ano'] == ano_anterior]['valor_total'].sum()
        crescimento = ((faturamento_ano_atual - faturamento_ano_anterior) / faturamento_ano_anterior) * 100 if faturamento_ano_anterior > 0 else 0

        st.subheader(f"📅 {calendar.month_name[mes_selecionado]} / {ano_selecionado}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {faturamento:,.2f}", f"{crescimento:.1f}% vs {ano_anterior}")
        col2.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
        col3.metric("Registros", f"{len(df):,}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Melhor Loja", melhor_loja)
        col5.metric("Categoria Top", categoria_top, f"R$ {valor_categoria_top:,.2f}")
        col6.metric("Produto Top", produto_top, f"R$ {valor_produto_top:,.2f}")

        st.divider()

        st.subheader("Top 10 Produtos Mais Vendidos")
        top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
        if len(top_produtos) > 0:
            fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h')
            fig3.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
            fig3.update_traces(texttemplate='R$ %{x:,.2f}', textposition='outside')
            fig3.update_xaxes(tickprefix='R$ ')
            st.plotly_chart(fig3, use_container_width=True)

        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Vendas por Categoria")
            cat_df = df.groupby('categoria')['valor_total'].sum().reset_index()
            if len(cat_df) > 0:
                fig1 = px.bar(cat_df, x='categoria', y='valor_total')
                fig1.update_layout(xaxis_tickangle=-45)
                fig1.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside')
                fig1.update_yaxes(tickprefix='R$ ')
                st.plotly_chart(fig1, use_container_width=True)

        with col_graf2:
            st.subheader("Faturamento por Dia")
            dia_df = df.groupby('data')['valor_total'].sum().reset_index()
            if len(dia_df) > 0:
                fig2 = px.line(dia_df, x='data', y='valor_total')
                fig2.update_yaxes(tickprefix='R$ ')
                st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados. Marque alguns dias.")

else:
    st.info("👆 Faça upload do arquivo Excel para começar")
