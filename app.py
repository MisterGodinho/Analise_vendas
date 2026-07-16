import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

# CSS PRA DEIXAR GERENCIAL
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
        font-size: 14px !important;
        color: #AAAAAA !important;
    }
    div[data-testid="metric-container"] > div {
        font-size: 28px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")
st.title("📊 Dashboard Gerencial de Vendas")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    # ... todo seu código de leitura e filtros continua igual ...
    
    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        qtd_vendas = df['id_pedido'].nunique()
        atingimento = (faturamento / meta * 100) if meta > 0 else 0
        
        melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax() if len(df['loja'].unique()) > 0 else "-"
        categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax() if len(df['categoria'].unique()) > 0 else "-"

        # CABEÇALHO GERENCIAL
        st.subheader(f"📅 {', '.join(meses_selecionados_nome)} / {', '.join(map(str, anos_selecionados))}")
        
        # LINHA 1: KPIs PRINCIPAIS
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            delta_meta = f"{atingimento-100:.1f}%" if meta > 0 else None
            st.metric("💰 Faturamento", f"R$ {faturamento:,.2f}", delta=delta_meta)
        with col2:
            st.metric("🎯 Meta", f"R$ {meta:,.2f}")
        with col3:
            st.metric("📈 % Atingimento", f"{atingimento:.1f}%", delta=f"{atingimento-100:.1f}%")
        with col4:
            st.metric("🧾 Ticket Médio", f"R$ {ticket_medio:,.2f}")

        # LINHA 2: KPIs SECUNDÁRIOS
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("🛒 Qtd. Vendas", f"{qtd_vendas:,}")
        with col6:
            st.metric("🏆 Melhor Loja", melhor_loja)
        with col7:
            st.metric("⭐ Categoria Top", categoria_top)
        with col8:
            if len(anos_selecionados) == 2:
                ano1, ano2 = sorted(anos_selecionados)
                fat_ano1 = df[df['ano'] == ano1]['valor_total'].sum()
                fat_ano2 = df[df['ano'] == ano2]['valor_total'].sum()
                crescimento = ((fat_ano2 - fat_ano1) / fat_ano1 * 100) if fat_ano1 > 0 else 0
                st.metric("📊 Crescimento YoY", f"{crescimento:.1f}%")

        st.divider()

        # BARRA DE PROGRESSO DA META
        st.write("**Evolução da Meta**")
        st.progress(min(atingimento/100, 1.0))
        st.caption(f"Realizado: R$ {faturamento:,.2f} de R$ {meta:,.2f}")

        # ... resto dos gráficos continua igual ...
