import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
import numpy as np

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

st.markdown("""
<style>
 .kpi-box { background-color: #262730; border-left: 4px solid #00FF7F; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; }
 .kpi-label { font-size: 11px; color: #AAAAAA; margin-bottom: 2px; text-transform: uppercase; }
 .kpi-value { font-size: 16px; font-weight: bold; color: white; }
  h3 { font-size: 18px!important; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Gerencial")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
        df.columns = df.columns.str.strip()

        mapa = {'Fecha':'data','Tienda':'loja','Categoria':'categoria','Descripción artículo':'produto','Importe con IVA':'valor_total','Código Ae':'id_pedido'}
        df = df.rename(columns=mapa)
        if 'id_pedido' not in df.columns: df['id_pedido'] = df.index

        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')

        # CORREÇÃO 1: TIRAR LINHAS SEM DATA OU VALOR
        df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['dia'] = df['data'].dt.day.astype(int) # Força pra int pra não dar NaN

        # ===== FILTROS DINÂMICOS =====
        st.sidebar.header("🔍 Filtros")
        anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), default=[df['ano'].max()])
        df_filtro = df[df['ano'].isin(anos)]

        meses_disponiveis = sorted(df_filtro['mes'].unique())
        meses = st.sidebar.multiselect("Mês", meses_disponiveis, format_func=lambda x: calendar.month_name[x], default=[meses_disponiveis[-1]])
        df_filtro = df_filtro[df_filtro['mes'].isin(meses)]

        dias_disponiveis = sorted(df_filtro['dia'].unique())
        dias = st.sidebar.multiselect("Dia", dias_disponiveis, default=dias_disponiveis)

        # CORREÇÃO 2: SE NÃO SELECIONAR NADA, PEGA TUDO
        if not dias: dias = dias_disponiveis
        df_filtro = df_filtro[df_filtro['dia'].isin(dias)]

        lojas_disponiveis = sorted(df_filtro['loja'].unique())
        lojas = st.sidebar.multiselect("Loja", lojas_disponiveis, default=lojas_disponiveis)
        if not lojas: lojas = lojas_disponiveis
        df_filtro = df_filtro[df_filtro['loja'].isin(lojas)]

        df = df_filtro
        st.sidebar.divider()
        meta = st.sidebar.number_input("🎯 Meta R$", value=500000.0, step=10000.0)

        if len(df) > 0:
