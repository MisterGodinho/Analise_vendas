import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")

st.title("Analise do Negocio BSB")
st.write("Selecione os arquivos 2025.zip e 2026.zip:")
uploaded_files = st.file_uploader("Upload", type=['zip'], accept_multiple_files=True)

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
    if len(lista_df) == 0:
        return pd.DataFrame()
    return pd.concat(lista_df, ignore_index=True)

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(files=uploaded_files) # CORRIGIDO AQUI
    
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor', 'loja'])
    
    df['ano'] = df['data'].dt.year
    
    st.sidebar.header("Filtros")
    anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), sorted(df['ano'].unique()))
    df = df[df['ano'].isin(anos)]
    
    fat = df['valor'].sum()
    ticket = df['valor'].mean()
    
    col1, col2 = st.columns(2)
    col1.metric("Faturamento Total", f"R$ {fat:,.0f}")
    col2.metric("Ticket Medio", f"R$ {ticket:,.2f}")
    
    st.subheader("Top 10 Produtos")
    dfp = df.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
    figp = px.bar(dfp, x='valor', y='produto', orientation='h')
    st.plotly_chart(figp, use_container_width=True)
    
    st.subheader("Top 10 Lojas")
    dfl = df.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
    figl = px.bar(dfl, x='loja', y='valor')
    st.plotly_chart(figl, use_container_width=True)
    
else: 
    st.info("Faca upload dos arquivos 2025.zip e 2026.zip")
