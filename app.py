import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
import zipfile

st.set_page_config(page_title="Dashboard Gerencial BSB", layout="wide")
st.title("📊 Dashboard Gerencial BSB")

uploaded_files = st.file_uploader(
    "1. Selecione os arquivos 2025.zip e 2026.zip",
    type=['zip'],
    accept_multiple_files=True
)

@st.cache_data(show_spinner="⏳ Descompactando e lendo arquivos... Aguarde 2 min")
def carregar_dados(files):
    lista_df = []
    for zip_file in files:
        with zipfile.ZipFile(zip_file) as z:
            for nome_arquivo in z.namelist():
                if nome_arquivo.endswith('/'):
                    continue
                with z.open(nome_arquivo) as f:
                    if nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls'):
                        df_temp = pd.read_excel(
                            f,
                            sheet_name=0,
                            header=0,
                            usecols='D,F,I,L'
                        )
                        df_temp.columns = ['loja', 'data', 'produto', 'valor_total']
                    elif nome_arquivo.endswith('.csv'):
                        df_temp = pd.read_csv(
                            f,
                            usecols=[3,5,8,11],
                            names=['loja','data','produto','valor_total'],
                            header=0,
                            encoding='latin-1',
                            on_bad_lines='skip'
                        )
                    else:
                        continue
                    lista_df.append(df_temp)

    df = pd.concat(lista_df, ignore_index=True)
    return df

if uploaded_files:
    if len(uploaded_files) < 2:
        st.warning("⚠️ Faz upload dos 2 arquivos: 2025.zip e 2026.zip")
    else:
        df = carregar
