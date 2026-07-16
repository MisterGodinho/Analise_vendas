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

    # ANO - MULTISELECT PRA SELECIONAR 2 ANOS
    anos_disponiveis = sorted(df['ano'].unique())
    anos_selecionados = st.sidebar.multiselect(
        "Ano - Selecione 1 ou 2 para comparar",
        anos_disponiveis,
        default=[anos_disponiveis[-1]] # já vem com o último ano marcado
    )

    if not anos_selecionados:
        st.warning("Selecione pelo menos 1 ano")
        st.stop()

    df_ano = df[df['ano'].isin(anos_selecionados)]

    # MÊS - MULTISELECT TAMBÉM
    meses_disponiveis = sorted(df_ano['mes'].unique())
    nomes_meses = [calendar.month_name[m] for m in meses_disponiveis]
    mes_map = dict(zip(nomes_meses, meses_disponiveis))

    meses_selecionados_nome = st.sidebar.multiselect(
        "Mês",
        nomes_meses,
        default=[nomes_meses[-1]]
    )
    meses_selecionados = [mes_map[m] for m in meses_selecionados_nome]

    df_mes = df_ano[df_ano['mes'].isin(meses_selecionados)]

    # DIAS - CHECKBOX
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

    # ===== KPIs =====
    if len(df) > 0:
        st.subheader(f"📅 Comparando: {', '.join(meses_selecionados_nome)} / {', '.join(map(str, anos_selecionados))}")

        # TABELA DE COMPARAÇÃO POR ANO
        tabela_ano = df.groupby('ano')['valor_total'].agg(['sum', 'mean', 'count']).reset_index()
        tabela_ano.columns = ['Ano', 'Faturamento', 'Ticket Médio', 'Qtd Vendas']
        tabela_ano['Faturamento'] = tabela_ano['Faturamento'].apply(lambda x: f"R$ {x:,.2f}")
        tabela_ano['Ticket Médio'] = tabela_ano['Ticket Médio'].apply(lambda x: f"R$ {x:,.2f}")

        st.dataframe(tabela_ano, use_container_width=True, hide_index=True)

        # GRÁFICO COMPARATIVO POR ANO
        st.subheader("📈 Comparativo de Faturamento por Ano")
        fig_comp = px.bar(tabela_ano, x='Ano', y='Faturamento', text_auto='.2s', color='Ano')
        fig_comp.update_yaxes(tickprefix='R$ ')
        st.plotly_chart(fig_comp, use_container_width=True)

        # GRÁFICO POR MÊS E ANO
        st.subheader("Comparativo Mensal")
        comp_mes_ano = df.groupby(['ano', 'mes'])['valor_total'].sum().reset_index()
        comp_mes_ano['mes_nome'] = comp_mes_ano['mes'].apply(lambda x: calendar.month_name[x][:3])
        fig_mes = px.line(comp_mes_ano, x='mes_nome', y='valor_total', color='ano', markers=True)
        fig_mes.update_yaxes(tickprefix='R$ ')
        st.plotly_chart(fig_mes, use_container_width=True)

        st.divider()
        st.subheader("Top 10 Produtos do Período")
        top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
        fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h')
        fig3.update_layout(yaxis={'categoryorder':'total ascending'})
        fig3.update_traces(texttemplate='R$ %{x:,.2f}', textposition='outside')
        fig3.update_xaxes(tickprefix='R$ ')
        st.plotly_chart(fig3, use_container_width=True)

    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")

else:
    st.info("👆 Faça upload do arquivo Excel para começar")
