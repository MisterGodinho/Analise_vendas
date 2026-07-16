import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
from io import BytesIO

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

# CSS PRA DEIXAR BONITO E COMPACTO
st.markdown("""
<style>
.kpi-box { background-color: #262730; border-left: 4px solid #00FF7F; padding: 10px 15px; border-radius: 8px; margin-bottom: 10px; }
.kpi-label { font-size: 12px; color: #AAAAAA; margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { font-size: 20px; font-weight: bold; color: white; }
.alerta { background-color: #FF4444; padding: 12px; border-radius: 8px; color: white; font-weight: bold; margin-bottom: 15px; }
h1 { font-size: 26px!important; }
h3 { font-size: 18px!important; }
[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

st.title("Dashboard Gerencial")

uploaded_files = st.file_uploader(
    "1. Selecione os arquivos 2025 e 2026 da pasta dashboard",
    type=None, # ACEITA QUALQUER ARQUIVO PQ O WINDOWS ESCONDE O.CSV
    accept_multiple_files=True
)

@st.cache_data(show_spinner="Carregando e juntando arquivos grandes... Aguarde 1 min")
def carregar_dados(files):
    lista_df = []
    for file in files:
        # Tenta ler como CSV primeiro
        try:
            df_temp = pd.read_csv(file, sep=',', encoding='utf-8', on_bad_lines='skip')
        except:
            # Se der erro tenta como Excel
            df_temp = pd.read_excel(file, sheet_name=0, header=0)
        lista_df.append(df_temp)

    # JUNTA OS 2 ARQUIVOS NUMA TABELA SÓ
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

        # MAPA DAS SUAS COLUNAS PELA FOTO QUE VC MANDOU
        mapa = {
            'F':'data', # Coluna F = 14.07.2026
            'D':'loja', # Coluna D = GISELE DA CAJERO/V T816
            'I':'produto', # Coluna I = Fandango, Mentos St, COCA COL
            'L':'valor_total' # Coluna L = 19,9
        }
        df = df.rename(columns=mapa)

        # Criar categoria pela primeira palavra do produto
        df['categoria'] = df['produto'].astype(str).str.split().str[0]
        df['categoria'] = df['categoria'].fillna('Sem Categoria')

        df['id_pedido'] = df.index.astype(str) + df['data'].astype(str)

        df['data'] = pd.to_datetime(df['data'], format='%d.%m.%Y', errors='coerce')
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
        df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['dia'] = df['data'].dt.day.astype(int)
        df['mes_nome'] = df['data'].dt.month_name()

        # FILTROS NA LATERAL
        st.sidebar.header("Filtros")

        anos_disponiveis = sorted(df['ano'].unique())
        anos = st.sidebar.multiselect("Ano", anos_disponiveis, default=anos_disponiveis)
        df_temp = df[df['ano'].isin(anos)]

        meses_disponiveis = sorted(df_temp['mes'].unique())
        meses = st.sidebar.multiselect("Mes", meses_disponiveis, format_func=lambda x: calendar.month_name[x], default=meses_disponiveis)
        df_temp = df_temp[df_temp['mes'].isin(meses)]

        dias_disponiveis = sorted(df_temp['dia'].unique())
        dias = st.sidebar.multiselect("Dia", dias_dis
