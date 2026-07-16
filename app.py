import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from io import BytesIO

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")
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
        except Exception:
            df_temp = pd.read_excel(file, sheet_name=0, header=0)
        lista_df.append(df_temp)
    df = pd.concat(lista_df, ignore_index=True)
    return df

def to_excel(df):
    output = Bytes
