import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
from io import BytesIO

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

st.markdown("""
<style>
.kpi-box { background-color: #262730; border-left: 4px solid #00FF7F; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; }
.kpi-label { font-size: 11px; color: #AAAAAA; margin-bottom: 2px; text-transform: uppercase; }
.kpi-value { font-size: 16px; font-weight: bold; color: white; }
.alerta { background-color: #FF4444; padding: 10px; border-radius: 6px; color: white; font-weight: bold; margin-bottom: 10px; }
h3 { font-size: 18px!important; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Gerencial")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Performance')
    return output.getvalue()

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    # MAPA ATUALIZADO COM AS COLUNAS DO SEU EXCEL
    mapa = {
        'Fecha':'data',
        'Tienda':'loja',
        'Categoria':'categoria',
        'Descripción artículo':'produto',
        'Importe con IVA':'valor_total'
    }
    df = df.rename(columns=mapa)

    # CORREÇÃO: Como não tem id_pedido, vamos criar um com a linha
    df['id_pedido'] = df.index.astype(str) + df['data'].astype(str)

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df['categoria'] = df['categoria'].fillna('Sem Categoria')
    df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month
    df['dia'] = df['data'].dt.day.astype(int)

    st.sidebar.header("🔍 Filtros")

    anos_disponiveis = sorted(df['ano'].unique())
    anos = st.sidebar.multiselect("Ano", anos_disponiveis, default=anos_disponiveis)
    df_temp = df[df['ano'].isin(anos)]

    meses_disponiveis = sorted(df_temp['mes'].unique())
    meses = st.sidebar.multiselect("Mês", meses_disponiveis, format_func=lambda x: calendar.month_name[x], default=meses_disponiveis)
    df_temp = df_temp[df_temp['mes'].isin(meses)]

    dias_disponiveis = sorted(df_temp['dia'].unique())
    dias = st.sidebar.multiselect("Dia", dias_disponiveis, default=dias_disponiveis)
    df_temp = df_temp[df_temp['dia'].isin(dias)]

    lojas_disponiveis = sorted(df_temp['loja'].unique())
    lojas = st.sidebar.multiselect("Loja", lojas_disponiveis, default=lojas_disponiveis)
    df_temp = df_temp[df_temp['loja'].isin(lojas)]

    categorias_disponiveis = sorted(df_temp['categoria'].unique())
    categorias = st.sidebar.multiselect("Categoria", categorias_disponiveis, default=categorias_disponiveis)
    df = df_temp[df_temp['categoria'].isin(categorias)]

    with st.sidebar.expander("👁️ Ver seleção atual"):
        st.write(f"**Anos:** {len(anos)} selecionado(s)")
        st.write(f"**Meses
