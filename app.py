import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import calendar
import gc # Pra limpar memória

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")
st.markdown("""<style>[data-testid="stSidebar"] { background-color: #1e293b; } [data-testid="stSidebar"] label { color: #e2e8f0!important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; }.stPills button { border-radius: 20px!important; border: 1px solid #475569!important; background-color: #334155!important; color: #cbd5e1!important; }.stPills button[aria-pressed="true"] { background-color: #3b82f6!important; border: 1px solid #3b82f6!important; color: white!important; font-weight: 600; }</style>""", unsafe_allow_html=True)

st.title("Analise do Negocio BSB")
uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

@st.cache_data(show_spinner="Carregando e otimizando 29MB...")
def carregar_dados(files):
    lista_df = []
    for zip_file in files:
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
    df = pd.concat(lista_df, ignore_index=True) if lista_df else pd.DataFrame()
    del lista_df
    gc.collect()
    
    # OTIMIZAÇÃO PESADA DE MEMÓRIA
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce').astype('float32')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df['loja'] = df['loja'].astype(str).str.strip().astype('category') # category usa 10x menos memoria
    df['produto'] = df['produto'].astype(str).str.strip().astype('category')
    df['categoria'] = df['categoria'].astype(str).str.strip().astype('category')
    df = df.dropna(subset=['data', 'valor', 'loja'])
    df['ano'] = df['data'].dt.year.astype('int16')
    df['mes_num'] = df['data'].dt.month.astype('int8')
    return df

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    st.success(f"Carregado! {len(df):,} linhas | Memória: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

    st.sidebar.header("FILTROS")
    MESES_PT = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    anos = st.sidebar.pills("ANO", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()), selection_mode="multi")
    meses = st.sidebar.pills("MÊS", options=sorted(df['mes_num'].unique()), default=sorted(df['mes_num'].unique()), format_func=lambda x: MESES_PT[x], selection_mode="multi")
    lista_lojas = sorted(df['loja'].unique())
    lista_cats = sorted(df['categoria'].unique())
    lojas = st.sidebar.pills("LOJA", options=lista_lojas, default=lista_lojas, selection_mode="multi")
    cats = st.sidebar.pills("CATEGORIA", options=lista_cats, default=lista_cats, selection_mode="multi")

    df_final = df[df['ano'].isin(anos) & df['mes_num'].isin(meses) & df['loja'].isin(lojas) & df['categoria'].isin(cats)].copy()
    st.sidebar.metric("Total registros", f"{len(df_final):,}")

    if len(df_final) > 0:
        fat = df_final['valor'].sum()
        st.metric("Faturamento", f"R$ {fat:,.0f}")
        #... resto do seu código aqui
else:
    st.info("Upload dos 2.zip")
