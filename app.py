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
                # IGNORA PASTAS DENTRO DO ZIP
                if nome_arquivo.endswith('/'):
                    continue

                with z.open(nome_arquivo) as f:
                    # DETECTA SE É EXCEL OU CSV
                    if nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls'):
                        df_temp = pd.read_excel(
                            f,
                            sheet_name=0,
                            header=0,
                            usecols='D,F,I,L' # PEGA SÓ 4 COLUNAS
                        )
                        df_temp.columns = ['loja', 'data', 'produto', 'valor_total']

                    elif nome_arquivo.endswith('.csv'):
                        df_temp = pd.read_csv(
                            f,
                            usecols=[3,5,8,11], # D=3, F=5, I=8, L=11
                            names=['loja','data','produto','valor_total'],
                            header=0,
                            encoding='latin-1', # Mudei pra latin-1 pq as vezes utf-8 quebra
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
        df = carregar_dados(uploaded_files)

        # TRATAMENTO
        df['categoria'] = df['produto'].astype(str).str.split().str[0]
        df['data'] = pd.to_datetime(df['data'], format='%d.%m.%Y', errors='coerce')
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
        df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

        df['ano'] = df['data'].dt.year

        # FILTROS
        st.sidebar.header("🔍 Filtros")
        anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
        df = df[df['ano'].isin(anos)]

        st.sidebar.write("Total de registros: " + str(len(df)))

        # KPIs
        st.metric("Faturamento Total", "R$ {:,.2f}".format(df['valor_total'].sum()))

        # GRAFICO
        st.subheader("Top
