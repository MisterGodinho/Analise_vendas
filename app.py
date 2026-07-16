import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

# CSS EXECUTIVO - FONTE PEQUENA E ORGANIZADA
st.markdown("""
<style>
   .kpi-box {
        background-color: #262730;
        border-left: 4px solid #00FF7F;
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
   .kpi-label {
        font-size: 11px;
        color: #AAAAAA;
        margin-bottom: 2px;
        text-transform: uppercase;
    }
   .kpi-value {
        font-size: 16px;
        font-weight: bold;
        color: white;
    }
    h3 { font-size: 18px!important; }
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
        if atingimento >= 100: cor, status, cor_barra = "🟢", "Meta Batida", "#00FF7F"
        elif atingimento >= 80: cor, status, cor_barra = "🟡", "Atenção", "#FFD700"
        else: cor, status, cor_barra = "🔴", "Abaixo da Meta", "#FF4500"

        st.markdown(f"<h3>{cor} {status} - {calendar.month_name[meses[0]]}/{anos[0]}</h3>", unsafe_allow_html=True)

        # ===== 3 COLUNAS - FONTE PEQUENA =====
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='kpi-box'><div class='kpi-label'>💰 Faturamento</div><div class='kpi-value'>R$ {faturamento:,.0f}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-box'><div class='kpi-label'>🎯 Meta</div><div class='kpi-value'>R$ {meta:,.0f}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='kpi-box'><div class='kpi-label'>📈 Atingimento</div><div class='kpi-value'>{atingimento:.1f}%</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-box'><div class='kpi-label'>🧾 Ticket Médio</div><div class='kpi-value'>R$ {ticket_medio:.2f}</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='kpi-box'><div class='kpi-label'>🛒 Qtd. Vendas</div><div class='kpi-value'>{qtd_vendas:,}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-box'><div class='kpi-label'>🏆 Melhor Loja</div><div class='kpi-value'>{melhor_loja}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='kpi-box'><div class='kpi-label'>⭐ Categoria Top</div><div class='kpi-value'>{categoria_top}</div></div>", unsafe_allow_html=True)
        st.progress(min(atingimento/100, 1.0))

        st.divider()

        # ===== ABAS =====
        tab1, tab2 = st.tabs(["📈 Performance", "📦 Top 10 Produtos"])

        with tab1:
            fat_ano = df.groupby('ano')['valor_total'].sum().reset_index()
            fig1 = px.bar(fat_ano, x='ano', y='valor_total', title="Faturamento por Ano")
            fig1.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig1, use_container_width=True)

        with tab2:
            top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
            top_produtos['produto'] = top_produtos['produto'].str.wrap(18)
            fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h')
            fig3.update_layout(height=400, margin=dict(l=130))
            fig3.update_traces(texttemplate='R$ %{x:,.0f}', textposition='outside')
            fig3.update_xaxes(tickprefix='R$ ')
            st.plotly_chart(fig3, use_container_width=True)

    else:
        st.warning("Nenhum dado encontrado.")

else:
    st.info("👆 Faça upload do arquivo Excel")
