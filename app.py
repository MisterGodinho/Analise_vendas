import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Dashboard BSB", layout="wide")
st.title("Dashboard Gerencial BSB")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

@st.cache_data(show_spinner="Carregando dados... Aguarde")
def carregar_dados(files):
    lista_df = []
    for zip_file in files:
        with zipfile.ZipFile(zip_file) as z:
            for nome_arquivo in z.namelist():
                if nome_arquivo.endswith('/'): 
                    continue
                with z.open(nome_arquivo) as f:
                    if '.xlsx' in nome_arquivo:
                        df_temp = pd.read_excel(f, sheet_name=0, header=0, usecols='F,G,I,J,Q')
                        df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor']
                    elif '.csv' in nome_arquivo:
                        df_temp = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], names=['loja','data','produto','categoria','valor'], header=0, encoding='latin-1', on_bad_lines='skip')
                    else: 
                        continue
                    lista_df.append(df_temp)
    if len(lista_df) == 0:
        return pd.DataFrame()
    return pd.concat(lista_df, ignore_index=True)

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor', 'loja']) # Adicionei 'loja' aqui
    
    df['ano'] = df['data'].dt.year
    df['id'] = df.index.astype(str)
    
    # SIDEBAR COM FILTROS + METAS
    st.sidebar.header("Filtros")
    anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), sorted(df['ano'].unique()))
    df_f = df[df['ano'].isin(anos)]
    
    lojas = st.sidebar.multiselect("Loja", sorted(df_f['loja'].unique()), sorted(df_f['loja'].unique()))
    df_f = df_f[df_f['loja'].isin(lojas)]
    
    cats = st.sidebar.multiselect("Categoria", sorted(df_f['categoria'].unique()), sorted(df_f['categoria'].unique()))
    df_f = df_f[df_f['categoria'].isin(cats)]
    
    st.sidebar.divider()
    st.sidebar.header("Metas")
    
    # CORREÇÃO 1: step menor que max_value
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 500000000.0, 150000.0, 1000000.0)
    
    # CORREÇÃO 
