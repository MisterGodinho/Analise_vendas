import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")
st.title("Dashboard Gerencial")

uploaded_files = st.file_uploader(
    "Carregue os arquivos vendas_2025.csv e vendas_2026.csv",
    type=["csv"],
    accept_multiple_files=True # ESSA LINHA LIBERA SUBIR OS 2 JUNTOS
)

@st.cache_data # ESSA LINHA FAZ NÃO TRAVAR COM ARQUIVO GRANDE
def carregar_dados(files):
    lista_df = []
    for file in files:
        df_temp = pd.read_csv(file, sep=',', encoding='utf-8')
        lista_df.append(df_temp)

    # JUNTA OS 2 ARQUIVOS NUM SÓ
    df = pd.concat(lista_df, ignore_index=True)
    return df

if uploaded_files:
    if len(uploaded_files) < 2:
        st.warning("Faz upload dos 2 arquivos: 2025 e 2026")
    else:
        with st.spinner("Carregando e juntando arquivos..."):
            df = carregar_dados(uploaded_files)

        df.columns = df.columns.str.strip()

        # MAPA DAS SUAS COLUNAS PELA FOTO
        mapa = {
            'F':'data', # Coluna F = Data
            'D':'loja', # Coluna D = Loja
            'I':'produto', # Coluna I = Produto
            'L':'valor_total' # Coluna L = Valor
        }
        df = df.rename(columns=mapa)

        # Criar categoria pela primeira palavra do produto
        df['categoria'] = df['produto'].astype(str).str.split().str[0]

        df['id_pedido'] = df.index.astype(str)

        df['data'] = pd.to_datetime(df['data'], format='%d.%m.%Y', errors='coerce')
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
        df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['dia'] = df['data'].dt.day.astype(int)

        # FILTROS
        st.sidebar.header("Filtros
