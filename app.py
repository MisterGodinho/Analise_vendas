import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

# CSS EXECUTIVO
st.markdown("""
<style>
  .kpi-box {
        background-color: #262730;
        border-left: 4px solid #00FF7F;
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
  .kpi-label { font-size: 11px; color: #AAAAAA; margin-bottom: 2px; text-transform: uppercase; }
  .kpi-value { font-size: 16px; font-weight: bold; color: white; }
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
    df['dia'] = df['data'].dt.day

    # ===== FILTROS DINÂMICOS =====
    st.sidebar.header("🔍 Filtros")

    anos = st.sidebar.multiselect("Ano", sorted(df['ano'].dropna().unique()), default=[df['ano'].max()])
    df_filtro = df[df['ano'].isin(anos)]

    meses_disponiveis = sorted(df_filtro['mes'].dropna().unique())
    meses = st.sidebar.multiselect("Mês", meses_disponiveis, format_func=lambda x: calendar.month_name[x], default=[meses_disponiveis[-1]])
    df_filtro = df_filtro[df_filtro['mes'].isin(meses)]

    # FILTRO NOVO 1: DIA
    dias_disponiveis = sorted(df_filtro['dia'].dropna().unique())
    dias = st.sidebar.multiselect("Dia", dias_disponiveis, default=dias_disponiveis)
    df_filtro = df_filtro[df_filtro['dia'].isin(dias)]

    # FILTRO NOVO 2: LOJA
    lojas_disponiveis = sorted(df_filtro['loja'].dropna().unique())
    lojas = st.sidebar.multiselect("Loja", lojas_disponiveis, default=lojas_disponiveis)
    df_filtro = df_filtro[df_filtro['loja'].isin(lojas)]

    categoria = st.sidebar.multiselect("Categoria", options=sorted(df_filtro['categoria'].dropna().unique()))

    if categoria: df_filtro = df_filtro[df_filtro['categoria'].isin(categoria)]
    df = df_filtro

    st.sidebar.divider()
    meta = st.sidebar.number_input("🎯 Meta R$", value=500000.0, step=10000.0)

    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        q
