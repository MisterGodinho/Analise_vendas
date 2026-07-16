import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

# ===== CSS GERENCIAL =====
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    div[data-testid="metric-container"] > label {
        font-size: 14px!important;
        color: #AAAAAA!important;
    }
    div[data-testid="metric-container"] > div {
        font-size: 28px!important;
        font-weight: bold!important;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")
st.title("📊 Dashboard Gerencial de Vendas")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    # MAPEAMENTO DAS COLUNAS
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

    loja = st.sidebar.multiselect("Loja", options=sorted(df_mes['loja'].dropna().unique()))
    categoria = st.sidebar.multiselect("Categoria", options=sorted(df_mes['categoria'].dropna().unique()))

    if loja: df_mes = df_mes[df_mes['loja'].isin(loja)]
    if categoria: df_mes = df_mes[df_mes['categoria'].isin(categoria)]
    df = df_mes

    # ===== META =====
    st.sidebar.divider()
    st.sidebar.subheader("🎯 Meta do Período")
    meta = st.sidebar.number_input("Digite a Meta R$", min_value=0.0, value=500000.0, step=10000.0)

    # ===== KPIs =====
    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        qtd_vendas = df['id_pedido'].nunique()
        atingimento = (faturamento / meta * 100) if meta > 0 else 0

        # SEMAFORO DA META
        if atingimento >= 100:
            cor_meta = "🟢"
            status_meta = "Meta Batida"
        elif atingimento >= 80:
            cor_meta = "🟡"
            status_meta = "Atenção"
        else:
            cor_meta = "🔴"
            status_meta = "Abaixo da Meta"

        st.subheader(f"📅 {', '.join(meses_selecionados_nome)} / {', '.join(map(str, anos_selecionados))} {cor_meta} {status_meta}")

        # LINHA 1: KPIs PRINCIPAIS
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Faturamento", f"R$ {faturamento:,.2f}", delta=f"{atingimento-100:.1f}% vs Meta")
        with col2:
            st.metric("🎯 Meta", f"R$ {meta:,.2f}")
        with col3:
            st.metric("📈 % Atingimento", f"{atingimento:.1f}%")
        with col4:
            st.metric("🧾 Ticket Médio", f"R$ {ticket_medio:,.2f}")

        # LINHA 2: KPIs SECUNDÁRIOS
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("🛒 Qtd. Vendas", f"{qtd_vendas:,}")
        with col6:
            melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax() if len(df['loja'].unique()) > 0 else "-"
            st.metric("🏆 Melhor Loja", melhor_loja)
        with col7:
            categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax() if len(df['categoria'].unique()) > 0 else "-"
            st.metric("⭐ Categoria Top", categoria_top)
        with col8:
            if len(anos_selecionados) == 2:
                ano1, ano2 = sorted(anos_selecionados)
                fat_ano1 = df[df['ano'] == ano1]['valor_total'].sum()
                fat_ano2 = df[df['ano'] == ano2]['valor_total'].sum()
                crescimento = ((fat_ano2 - fat_ano1) / fat_ano1 * 100) if fat_ano1 > 0 else 0
                st.metric("📊 Crescimento YoY", f"{crescimento:.1f}%")

        # BARRA DE PROGRESSO DA META
        st.write("**Evolução da Meta**")
        st.progress(min(atingimento/100, 1.0))
        st.caption(f"Realizado: R$ {faturamento:,.2f} de R$ {meta:,.2f}")

        st.divider()

        # ===== GRÁFICOS =====
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Faturamento por Ano")
            fat_ano = df.groupby('ano')['valor_total'].sum().reset_index()
            fig1 = px.bar(fat_ano, x='ano', y='valor_total', text_auto='.2s', color='ano')
            fig1.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside')
            fig1.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig1, use_container_width=True)

        with col_g2:
            st.subheader("Meta vs Realizado")
            fig_meta = px.bar(x=['Meta', 'Realizado'], y=[meta, faturamento], text_auto='.2s', color=['Meta', 'Realizado'])
            fig_meta.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside')
            fig_meta.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig_meta, use_container_width=True)

        # TOP 10 PRODUTOS
        st.subheader("Top 10 Produtos do Período")
        top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
        top_produtos['produto'] = top_produtos['produto'].str.wrap(25) # Quebra linha
        fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h', text='valor_total')
        fig3.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, margin=dict(l=200, r=80, t=50, b=50))
        fig3.update_traces(texttemplate='R$ %{x:,.2f}', textposition='outside')
        fig3.update_xaxes(tickprefix='R$ ')
        st.plotly_chart(fig3, use_container_width=True)

    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")

else:
    st.info("👆 Faça upload do arquivo Excel para começar")
