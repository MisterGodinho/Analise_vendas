import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

# CSS PRA DEIXAR COMPACTO
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #262730;
        border: 1px solid #444;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 5px;
    }
    div[data-testid="metric-container"] > label { font-size: 12px!important; }
    div[data-testid="metric-container"] > div { font-size: 20px!important; font-weight: bold!important; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Gerencial")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    mapa = {'Fecha':'data','Tienda':'loja','Categoria':'categoria','Descripción artículo':'produto','Importe con IVA':'valor_total','Código Ae':'id_pedido'}
    df = df.rename(columns=mapa)
    if 'id_pedido' not in df.columns: df['id_pedido'] = df.index
    df = df.dropna(subset=['valor_total', 'data', 'loja', 'produto'])
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month

    # ===== FILTROS =====
    st.sidebar.header("🔍 Filtros")
    anos = st.sidebar.multiselect("Ano", sorted(df['ano'].dropna().unique()), default=[df['ano'].max()])
    df = df[df['ano'].isin(anos)]
    meses = st.sidebar.multiselect("Mês", sorted(df['mes'].dropna().unique()), format_func=lambda x: calendar.month_name[x], default=[df['mes'].max()])
    df = df[df['mes'].isin(meses)]
    meta = st.sidebar.number_input("🎯 Meta R$", value=500000.0, step=10000.0)

    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        qtd_vendas = df['id_pedido'].nunique()
        atingimento = (faturamento / meta * 100) if meta > 0 else 0
        melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax()
        categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax()

        # SEMAFORO
        if atingimento >= 100: cor, status = "🟢", "Meta Batida"
        elif atingimento >= 80: cor, status = "🟡", "Atenção"
        else: cor, status = "🔴", "Abaixo da Meta"

        st.subheader(f"{cor} {status} - {calendar.month_name[meses[0]]}/{anos[0]}")

        # ===== AGRUPADO EM 2 COLUNAS =====
        col1, col2 = st.columns(2)

        with col1:
            st.metric("💰 Faturamento", f"R$ {faturamento:,.2f}")
            st.metric("📈 % Atingimento", f"{atingimento:.1f}%")
            st.metric("🛒 Qtd. Vendas", f"{qtd_vendas:,}")

        with col2:
            st.metric("🎯 Meta", f"R$ {meta:,.2f}")
            st.metric("🧾 Ticket Médio", f"R$ {ticket_medio:,.2f}")
            st.metric("🏆 Melhor Loja", melhor_loja)

        st.progress(min(atingimento/100, 1.0))
        st.caption(f"Realizado: R$ {faturamento:,.2f} de R$ {meta:,.2f} | Categoria Top: {categoria_top}")

        st.divider()

        # ===== TUDO EM ABAS PRA NÃO FICAR GRANDE =====
        tab1, tab2, tab3 = st.tabs(["📈 Vendas", "📦 Produtos", "🏬 Lojas"])

        with tab1:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fat_ano = df.groupby('ano')['valor_total'].sum().reset_index()
                fig1 = px.bar(fat_ano, x='ano', y='valor_total', title="Faturamento por Ano")
                fig1.update_yaxes(tickprefix='R$ ')
                st.plotly_chart(fig1, use_container_width=True)
            with col_g2:
                fig_meta = px.bar(x=['Meta', 'Realizado'], y=[meta, faturamento], title="Meta vs Realizado")
                fig_meta.update_yaxes(tickprefix='R$ ')
                st.plotly_chart(fig_meta, use_container_width=True)

        with tab2:
            st.subheader("Top 10 Produtos")
            top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
            top_produtos['produto'] = top_produtos['produto'].str.wrap(20)
            fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h')
            fig3.update_layout(height=400, margin=dict(l=150))
            fig3.update_traces(texttemplate='R$ %{x:,.0f}', textposition='outside')
            fig3.update_xaxes(tickprefix='R$ ')
            st.plotly_chart(fig3, use_container_width=True)

        with tab3:
            st.subheader("Top 5 Lojas")
            top_lojas = df.groupby('loja')['valor_total'].sum().nlargest(5).reset_index()
            fig4 = px.bar(top_lojas, x='loja', y='valor_total')
            fig4.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig4, use_container_width=True)

    else:
        st.warning("Nenhum dado encontrado.")

else:
    st.info("👆 Faça upload do arquivo Excel")
