import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")
st.title("📊 Dashboard Gerencial")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    try: # BLOCO DE ERRO PRA VER O QUE TA ACONTECENDO
        df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
        
        st.success(f"Arquivo carregado! {len(df)} linhas encontradas.")
        st.write("Colunas do seu Excel:", df.columns.tolist()) # MOSTRA AS COLUNAS
        
        df.columns = df.columns.str.strip()
        mapa = {'Fecha':'data','Tienda':'loja','Categoria':'categoria','Descripción artículo':'produto','Importe con IVA':'valor_total','Código Ae':'id_pedido'}
        
        # VERIFICA SE AS COLUNAS EXISTEM
        colunas_faltando = [k for k in mapa.keys() if k not in df.columns]
        if colunas_faltando:
            st.error(f"⚠️ ERRO: Faltam essas colunas no Excel: {colunas_faltando}")
            st.stop()
            
        df = df.rename(columns=mapa)
        if 'id_pedido' not in df.columns: df['id_pedido'] = df.index

        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
        df['categoria'] = df['categoria'].fillna('Sem Categoria')
        df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['dia'] = df['data'].dt.day.astype(int)

        st.sidebar.header("🔍 Filtros")
        anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
        df = df[df['ano'].isin(anos)]

        st.sidebar.divider()
        
        if len(df) > 0:
            faturamento = df['valor_total'].sum()
            st.metric("💰 Faturamento", f"R$ {faturamento:,.0f}")
            
            st.dataframe(df.head(10)) # MOSTRA OS 10 PRIMEIROS DADOS
            
        else:
            st.warning("Nenhum dado após aplicar filtros")
            
    except Exception as e:
        st.error("❌ DEU ERRO AO CARREGAR")
        st.code(str(e)) # MOSTRA O ERRO EXATO AQUI
else:
    st.info("👆 Faça upload do arquivo Excel")
