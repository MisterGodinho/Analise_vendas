import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from io import BytesIO

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 24px; }
h1 { font-size: 26px!important; }
h3 { font-size: 18px!important; }
</style>
""", unsafe_allow_html=True)

st.title("Dashboard Gerencial")

uploaded_files = st.file_uploader(
    "1. Selecione os arquivos 2025 e 2026 da pasta dashboard",
    type=None,
    accept_multiple_files=True
)

@st.cache_data(show_spinner="Carregando e juntando arquivos grandes... Aguarde 1 min")
def carregar_dados(files):
    lista_df = []
    for file in files:
        try:
            df_temp = pd.read_csv(file, sep=',', encoding='utf-8', on_bad_lines='skip')
        except:
            df_temp = pd.read_excel(file, sheet_name=0, header=0)
        lista_df.append(df_temp)

    df = pd.concat(lista_df, ignore_index=True)
    return df

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Performance')
    return output.getvalue()

if uploaded_files:
    if len(uploaded_files) < 2:
        st.warning("⚠️ Faz upload dos 2 arquivos: 2025 e 2026")
    else:
        df = carregar_dados(uploaded_files)

        df.columns = df.columns.str.strip()

        # MAPA DAS SUAS COLUNAS
        mapa = {
            'F':'data',
            'D':'loja',
            'I':'produto',
            'L':'valor_total'
        }
        df = df.rename(columns=mapa)

        df['categoria'] = df['produto'].astype(str).str.split().str[0]
        df['categoria'] = df['categoria'].fillna('Sem Categoria')

        df['id_pedido'] = df.index.astype(str) + df['data'].astype(str)

        df['data'] = pd.to_datetime(df['data'], format='%d.%m.%Y', errors='coerce')
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
        df = df.dropna(subset=['data', 'valor_total', '
