import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile

# CONFIGURAÇÃO DA PÁGINA - TEMA DIRETORIA
st.set_page_config(page_title="Análise do Negócio BSB", layout="wide", initial_sidebar_state="expanded")

# CSS PERSONALIZADO
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="st-"] {font-family: 'Inter', sans-serif;}
    .main {background-color: #0E1117;}
    div[data-testid="stMetric"] {background-color: #262730; border: 1px solid #333; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);}
    div[data-testid="stMetricLabel"] {color: #FA; font-size: 14px; font-weight: 600;}
    div[data-testid="stMetricValue"] {color: #FFFFFF; font-size: 28px; font-weight: 700;}
    h1, h2, h3 {color: #FFFFFF;}
    .stSidebar {background-color: #1A1C23;}
    hr {border-color: #333;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Análise do Negócio BSB") # NOME TROCADO
st.caption("Performance de Vendas | 2025 - 2026")

uploaded_files = st.file_uploader("Selecione os arquivos 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

@st.cache_data(show_spinner="⏳ Carregando dados... Aguarde 2 minutos")
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
    df_completo = pd.concat(lista_df, ignore_index=True)
    return df_completo

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    
    # TRATAMENTO DE DADOS
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor', 'loja'])
    
    df['ano'] = df['data'].dt.year
    df['id'] = df.index.astype(str)
    
    # SIDEBAR
    with st.sidebar:
        st.header("🔍 Filtros Executivos")
        anos = st.multiselect("Ano", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
        df_filtrado = df[df['ano'].isin(anos)]
        
        lojas = st.multiselect("Loja", options=sorted(df_filtrado['loja'].unique()), default=sorted(df_filtrado['loja'].unique()))
        df_filtrado = df_filtrado[df_filtrado['loja'].isin(lojas)]
        
        categorias = st.multiselect("Categoria", options=sorted(df_filtrado['categoria'].unique()), default=sorted(df_filtrado['categoria'].unique()))
        df_f
