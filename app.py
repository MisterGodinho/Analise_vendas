import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from io import BytesIO

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

    anos_disponiveis = sorted(df['ano'].unique())
    anos_selecionados = st.sidebar.multiselect("Ano - Selecione 1 ou 2", anos_disponiveis, default=[anos_disponiveis[-1]])

    if not anos_selecionados:
        st.warning("Selecione pelo menos 1 ano")
        st.stop()

    df_ano = df[df['ano'].isin(anos_selecionados)]

    meses_disponiveis = sorted(df_ano['mes'].unique())
    nomes_meses = [calendar.month_name[m] for m in meses_disponiveis]
    mes_map = dict(zip(nomes_meses, meses_disponiveis))
    meses_selecionados_nome = st.sidebar.multiselect("Mês", nomes_meses, default=[nomes_meses[-1]])
    meses_selecionados = [mes_map[m] for m in meses_selecionados_nome]

    df_mes = df_ano[df_ano['mes'].isin(meses_selecionados)]

    st.sidebar.write("**Dias:**")
    dias_disponiveis = sorted(df_mes['dia'].unique())
    col_dias = st.sidebar.columns(7)
    dias_selecionados = []
    for i, dia in enumerate(dias_disponiveis):
        if col_dias[i % 7].checkbox(str(dia), key=f"dia_{dia}"):
            dias_selecionados.append(dia)

    if dias_selecionados:
        df_mes = df_mes[df_mes['dia'].isin(dias_selecionados)]

    loja = st.sidebar.multiselect("Loja", options=sorted(df_mes['loja'].dropna().unique()))
    categoria = st.sidebar.multiselect("Categoria", options=sorted(df_mes['categoria'].dropna().unique()))

    if loja: df_mes = df_mes[df_mes['loja'].isin(loja)]
    if categoria: df_mes = df_mes[df_mes['categoria'].isin(categoria)]
    df = df_mes

    # ===== META =====
    st.sidebar.divider()
    st.sidebar.subheader("🎯 Meta")
    meta = st.sidebar.number_input("Digite a Meta do Período R$", min_value=0.0, value=10000.0, step=1000.0)

    # ===== KPIs =====
    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        atingimento = (faturamento / meta * 100) if meta > 0 else 0

        st.subheader(f"📅 {', '.join(meses_selecionados_nome)} / {', '.join(map(str, anos_selecionados))}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Faturamento", f"R$ {faturamento:,.2f}")
        col2.metric("Meta", f"R$ {meta:,.2f}")
        col3.metric("% Atingimento", f"{atingimento:.1f}%", delta=f"{atingimento-100:.1f}%")
        col4.metric("Ticket Médio", f"R$ {df['valor_total'].mean():,.2f}")

        # ===== % CRESCIMENTO ENTRE 2 ANOS =====
        if len(anos_selecionados) == 2:
            ano1, ano2 = sorted(anos_selecionados)
            fat_ano1 = df[df['ano'] == ano1]['valor_total'].sum()
            fat_ano2 = df[df['ano'] == ano2]['valor_total'].sum()
            crescimento = ((fat_ano2 - fat_ano1) / fat_ano1 * 100) if fat_ano1 > 0 else 0
            st.success(f"📈 Crescimento de {ano1} para {ano2}: **{crescimento:.1f}%**")

        st.divider()

        # ===== GRÁFICOS =====
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Faturamento por Ano")
            fat_ano = df.groupby('ano')['valor_total'].sum().reset_index()
            fig1 = px.bar(fat_ano, x='ano', y='valor_total', text_auto='.2s', color='ano')
            fig1.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig1, use_container_width=True)

        with col_g2:
            st.subheader("Meta vs Realizado")
            fig_meta = px.bar(x=['Meta', 'Realizado'], y=[meta, faturamento], text_auto='.2s')
            fig_meta.update_traces(texttemplate='R$ %{y:,.2f}')
            fig_meta.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig_meta, use_container_width=True)

        st.subheader("Top 10 Produtos")
        top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
        fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h')
        fig3.update_layout(yaxis={'categoryorder':'total ascending'})
        fig3.update_traces(texttemplate='R$ %{x:,.2f}', textposition='outside')
        fig3.update_xaxes(tickprefix='R$ ')
        st.plotly_chart(fig3, use_container_width=True)

        # ===== BOTÃO EXPORTAR =====
        st.divider()
        if st.button("📄 Exportar Dados em Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Dados Filtrados', index=False)
                fat_ano.to_excel(writer, sheet_name='Resumo Ano', index=False)
            st.download_button(
                label="⬇️ Baixar Excel",
                data=output.getvalue(),
                file_name="relatorio_vendas.xlsx",
                mime="application/vnd.ms-excel"
            )

    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")

else:
    st.info("👆 Faça upload do arquivo Excel para começar")
