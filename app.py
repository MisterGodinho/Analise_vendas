import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar

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
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    mapa = {'Fecha':'data','Tienda':'loja','Categoria':'categoria','Descripción artículo':'produto','Importe con IVA':'valor_total','Código Ae':'id_pedido'}
    df = df.rename(columns=mapa)
    if 'id_pedido' not in df.columns: df['id_pedido'] = df.index

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month
    df['dia'] = df['data'].dt.day.astype(int)

    # ===== FILTROS =====
    st.sidebar.header("🔍 Filtros")
    anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), default=[df['
