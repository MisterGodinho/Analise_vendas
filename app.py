import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Análise do Negócio BSB", layout="wide")

st.markdown("""
<style>
.main {background-color: #0E1117;}
div[data-testid="stMetric"] {background-color: #262730; padding: 20px; border-radius: 12px;}
div[data-testid="stMetricValue"] {color: #FFFFFF; font-size: 28px;}
h1, h2, h3 {color: #FFFFFF;}
.stSidebar {background-color: #1A1C23;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Análise do Negócio BSB")
st.caption("Performance de Vendas | 2025 - 2026")
st.write("**Selecione os arquivos 2025.zip e 2026.zip:**")
uploaded_files = st.file_uploader("Arquivos ZIP", type=['zip'], accept_multiple_files=True)

@st.cache_data
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
    return pd.concat(lista_df, ignore_index=True)

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor', 'loja'])
    
    df['ano'] = df['data'].dt.year
    df['id'] = df.index.astype(str)
    
    with st.sidebar:
        st.header("🔍 Filtros")
        anos = st.multiselect("Ano", sorted(df['ano'].unique()), sorted(df['ano'].unique()))
        df = df[df['ano'].isin(anos)]
        lojas = st.multiselect("Loja", sorted(df['loja'].unique()), sorted(df['loja'].unique()))
        df = df[df['loja'].isin(lojas)]
        cats = st.multiselect("Categoria", sorted(df['categoria'].unique()), sorted(df['categoria'].unique()))
        df = df[df['categoria'].isin(cats)]
        
        st.divider()
        st.header("
