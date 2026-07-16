import streamlit as st
import pandas as pd
import plotly.express as px
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
                        # LENDO AS COLUNAS CERTAS: F,G,I,J,Q
                        df_temp = pd.read_excel(
                            f, 
                            sheet_name=0, 
                            header=0, 
                            usecols='F,G,I,J,Q' # Tienda, Fecha, Descripcion, Categoria, Importe
                        )
                        df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor_total']
                    
                    elif nome_arquivo.endswith('.csv'):
                        df_temp = pd.read_csv(
                            f, 
                            sep=';', 
                            usecols=[5,6,8,9,16], # F=5, G=6, I=8, J=9, Q=16
                            names=['loja','data','produto','categoria','valor_total'],
                            header=0,
                            encoding='latin-1',
                            on_bad_lines='skip',
                            engine='python'
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

        # LIMPEZA BRASILEIRA
        df['valor_total'] = df['valor_total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')

        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

        df['ano'] = df['data'].dt.year
        df['id_pedido'] = df.index.astype(str)

        # FILTROS
        st.sidebar.header("🔍 Filtros")
        anos = st.sidebar.multiselect("Ano", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
        df_temp = df[df['ano'].isin(anos)]

        lojas = st.sidebar.multiselect("Loja", options=sorted(df_temp['loja'].unique()), default=sorted(df_temp['loja'].unique()))
        df_temp = df_temp[df_temp['loja'].isin(lojas)]

        categorias = st.sidebar.multiselect("Categoria", options=sorted(df_temp['categoria'].unique()), default=sorted(df_temp['categoria'].unique()))
        df = df_temp[df_temp['categoria'].isin(categorias)]

        st.sidebar.write("Total de registros: " + str(len(df)))

        if len(df) > 0:
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Faturamento Total", "R$ {:,.2f}".format(df['valor_total'].sum()))
            col2.metric("Ticket Médio", "R$ {:,.2f}".format(df['valor_total'].mean()))
            col3.metric("Qtd Itens", "{:,}".format(len(df)))
            col4.metric("Qtd Pedidos", "{:,}".format(df['id_pedido'].nunique()))

            st.divider()
            st.subheader("Top 10 Lojas por Faturamento")
            df_loja = df.groupby('loja')
