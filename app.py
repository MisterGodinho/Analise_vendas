import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import calendar
import gc

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")
st.markdown("""<style>[data-testid="stSidebar"] { background-color: #1e293b; } div[data-baseweb="tag"] { background-color: #ef4444!important; }</style>""", unsafe_allow_html=True)

st.title("Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")
uploaded_file = st.file_uploader("SOBE 2025.zip OU 2026.zip - SÓ 1 POR VEZ", type=['zip'])

@st.cache_data(show_spinner="Carregando...")
def carregar_dados(zip_file):
    lista_df = []
    with zipfile.ZipFile(zip_file) as z:
        for nome_arquivo in z.namelist():
            if nome_arquivo.endswith('/'): continue
            with z.open(nome_arquivo) as f:
                if '.xlsx' in nome_arquivo:
                    df_temp = pd.read_excel(f, usecols='F,G,I,J,Q', dtype={'F':str, 'I':str, 'J':str})
                    df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor']
                else:
                    df_temp = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], names=['loja','data','produto','categoria','valor'], header=0, encoding='latin-1', dtype={'loja':str, 'produto':str, 'categoria':str})
                lista_df.append(df_temp)
    df = pd.concat(lista_df, ignore_index=True); gc.collect()
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce').astype('float32')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df['loja'] = df['loja'].astype(str).str.strip().astype('category')
    df['categoria'] = df['categoria'].astype(str).str.strip().astype('category')
    df['ano'] = df['data'].dt.year.astype('int16')
    df['mes_num'] = df['data'].dt.month.astype('int8')
    df['mes_nome'] = df['mes_num'].map({1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'})
    return df.dropna(subset=['data', 'valor'])

if uploaded_file:
    df = carregar_dados(uploaded_file)
    st.success(f"Carregado! {len(df):,} linhas")
    
    st.sidebar.header("FILTROS POWER BI")
    anos = st.sidebar.multiselect("ANO", sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
    meses = st.sidebar.multiselect("MÊS", sorted(df['mes_nome'].unique()), default=sorted(df['mes_nome'].unique())[:3])
    lojas = st.sidebar.multiselect("LOJA", sorted(df['loja'].unique()), default=sorted(df['loja'].unique())[:10])
    
    df_f = df[df['ano'].isin(anos) & df['mes_nome'].isin(meses) & df['loja'].isin(lojas)]
    st.sidebar.metric("TOTAL", f"{len(df_f):,}")
    
    if len(df_f) > 0:
        st.metric("Faturamento", f"R$ {df_f['valor'].sum():,.0f}")
        # Cole aqui seu Ranking e Analise Inteligente
    else:
        st.warning("Nenhum dado. Marque menos filtros.")
