import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análise de Vendas", layout="wide")

# 1. UPLOAD E CARREGAMENTO
uploaded_file = st.sidebar.file_uploader("Envie sua planilha", type=['xlsx', 'csv'])
if uploaded_file:
    df = pd.read_excel(uploaded_file, usecols='F,G,I,J,Q')
    df.columns = ['loja','data','produto','categoria','valor']
    df['data'] = pd.to_datetime(df['data'])
    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month_name()
else:
    st.stop() # Para aqui se não tiver arquivo

# 2. FILTROS
st.sidebar.header("Filtros")
anos = st.sidebar.multiselect("Ano", df['ano'].unique(), default=df['ano'].unique())
lojas = st.sidebar.multiselect("Loja", df['loja'].unique(), default=df['loja'].unique())

df_filtrado = df[
    (df['ano'].isin(anos)) &
    (df['loja'].isin(lojas))
]

# 3. KPIs E GRÁFICOS NORMAIS
st.title("Dashboard de Vendas")
st.metric("Faturamento", f"R$ {df_filtrado['valor'].sum():,.2f}")
# ... resto dos seus graficos

# 4. ANÁLISE DE QUEDA - COLA SÓ AQUI EMBAIXO
if len(df_filtrado['ano'].unique()) > 1:
    st.divider()
    st.subheader("📉 Análise de Queda: Ano Atual vs Ano Anterior")
    # ... cole o código da análise aqui
