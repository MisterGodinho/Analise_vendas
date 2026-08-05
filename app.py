import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import calendar
import gc

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")

# CSS PRA FICAR IGUAL POWER BI - TAGS VERMELHAS
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1e293b; }
[data-testid="stSidebar"] label { color: #e2e8f0!important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; }
div[data-baseweb="tag"] { background-color: #ef4444!important; border-radius: 16px!important; }
div[data-baseweb="tag"] span { color: white!important; font-weight: 600; }
.stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

@st.cache_data(show_spinner="Carregando e otimizando...")
def carregar_dados(files):
    lista_df = []
    progress = st.progress(0)
    total = len(files)
    for i, zip_file in enumerate(files):
        with zipfile.ZipFile(zip_file) as z:
            for nome_arquivo in z.namelist():
                if nome_arquivo.endswith('/'): continue
                with z.open(nome_arquivo) as f:
                    if '.xlsx' in nome_arquivo:
                        df_temp = pd.read_excel(f, sheet_name=0, header=0, usecols='F,G,I,J,Q', dtype={'F':str, 'I':str, 'J':str})
                        df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor']
                    elif '.csv' in nome_arquivo:
                        df_temp = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], names=['loja','data','produto','categoria','valor'], header=0, encoding='latin-1', on_bad_lines='skip', dtype={'loja':str, 'produto':str, 'categoria':str})
                    else: continue
                    lista_df.append(df_temp)
        progress.progress((i+1)/total)
    if len(lista_df) == 0: return pd.DataFrame()

    df = pd.concat(lista_df, ignore_index=True); del lista_df; gc.collect()

    # OTIMIZAÇÃO PESADA
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce').astype('float32')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df['loja'] = df['loja'].astype(str).str.strip().astype('category')
    df['produto'] = df['produto'].astype(str).str.strip().astype('category')
    df['categoria'] = df['categoria'].astype(str).str.strip().astype('category')
    df = df.dropna(subset=['data', 'valor'])
    df = df[df['loja']!= '']
    df['ano'] = df['data'].dt.year.astype('int16')
    df['mes_num'] = df['data'].dt.month.astype('int8')
    df['mes_nome'] = df['mes_num'].map({1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'})
    return df

if uploaded_files:
    df = carregar_dados(uploaded_files)
    st.success(f"✅ Carregado! {len(df):,} linhas | Memória: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

    st.sidebar.header("FILTROS")

    anos = st.sidebar.multiselect("ANO", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
    df_ano = df[df['ano'].isin(anos)] if anos else df

    meses_nome = st.sidebar.multiselect("MÊS", options=sorted(df['mes_nome'].unique()), default=sorted(df['mes_nome'].unique()))
    df_mes = df_ano[df_ano['mes_nome'].isin(meses_nome)] if meses_nome else df_ano

    lojas = st.sidebar.multiselect("LOJA", options=sorted(df_mes['loja'].unique()), default=sorted(df_mes['loja'].unique()))
    df_loja = df_mes[df_mes['loja'].isin(lojas)] if lojas else df_mes

    cats = st.sidebar.multiselect("CATEGORIA", options=sorted(df_loja['categoria'].unique()), default=sorted(df_loja['categoria'].unique()))
    df_f = df_loja[df_loja['categoria'].isin(cats)] if cats else df_loja

    st.sidebar.divider()
    st.sidebar.header("METAS")
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 10000000.0, 1500000.0, 100000.0)
    st.sidebar.metric("
