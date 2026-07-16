import streamlit as st, pandas as pd, plotly.express as px, zipfile
st.set_page_config(page_title="Dashboard BSB", layout="wide")
st.title("📊 Dashboard Gerencial BSB")
uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)
@st.cache_data(show_spinner="⏳ Carregando...")
def carregar_dados(files):
    lista_df = []
    for zip_file in files:
        with zipfile.ZipFile(zip_file) as z:
            for nome_arquivo in z.namelist():
                if nome_arquivo.endswith('/'): continue
                with z.open(nome_arquivo) as f:
                    if nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls'):
                        df_temp = pd.read_excel(f, sheet_name=0, header=0, usecols='F,G,I,J,Q')
                        df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor_total']
                    elif nome_arquivo.endswith('.csv'):
                        df_temp = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], names=['loja','data','produto','categoria','valor_total'], header=0, encoding='latin-1', on_bad_lines='skip', engine='python')
                    else: continue
                    lista_df.append(df_temp)
    return pd.concat(lista_df, ignore_index=True)
if uploaded_files:
    if len(uploaded_files) < 2: st.warning("⚠️ Faz upload dos 2 arquivos")
    else:
        df = carregar_dados(uploaded_files)
        df['valor_total'] = pd.to_numeric(df['valor_total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce')
        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['data', 'valor_total'])
        df['ano'] = df['data'].dt.year
        df['id_pedido'] = df.index.astype(str)
        st.sidebar.header("🔍 Filtros")
        anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), sorted(df['ano'].unique()))
        df_temp = df[df['ano'].isin(anos)]
        lojas = st.sidebar.multiselect("Loja", sorted(df_temp['loja'].unique()), sorted(df_temp['loja'].unique()))
        df_temp = df_temp[df_temp['loja'].isin(lojas)]
        categorias = st.sidebar.multiselect("Categoria", sorted(df_temp['categoria'].unique()), sorted(df_temp['categoria'].unique
