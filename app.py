import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
import zipfile
from io import BytesIO

st.set_page_config(page_title="Dashboard Gerencial BSB", layout="wide")
st.title("📊 Dashboard Gerencial BSB")

uploaded_files = st.file_uploader(
    "1. Selecione os arquivos 2025.zip e 2026.zip",
    type=['zip'], # AGORA SÓ ACEITA ZIP
    accept_multiple_files=True
)

@st.cache_data(show_spinner="⏳ Descompactando e lendo arquivos... Aguarde 2 min")
def carregar_dados(files):
    lista_df = []
    for zip_file in files:
        with zipfile.ZipFile(zip_file) as z:
            # Pega o primeiro arquivo.xlsx ou.csv dentro do zip
            for nome_arquivo in z.namelist():
                if nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls'):
                    with z.open(nome_arquivo) as f:
                        # LÊ SÓ AS 4 COLUNAS PRA FICAR LEVE
                        df_temp = pd.read_excel(
                            f,
                            sheet_name=0,
                            header=0,
                            usecols='D,F,I,L' # PEGA SÓ COLUNA D, F, I, L
                        )
                        df_temp.columns = ['loja', 'data', 'produto', 'valor_total']
                        lista_df.append(df_temp)
                elif nome_arquivo.endswith('.csv'):
                    with z.open(nome_arquivo) as f:
                        df_temp = pd.read_csv(
                            f,
                            usecols=['D','F','I','L'],
                            names=['loja','data','produto','valor_total'],
                            header=0,
                            encoding='utf-8'
                        )
                        lista_df.append(df_temp)

    df = pd.concat(lista_df, ignore_index=True)
    return df

if uploaded_files:
    if len(uploaded_files) < 2:
        st.warning("⚠️ Faz upload dos 2 arquivos: 2025.zip e 2026.zip")
    else:
        df = carregar_dados(uploaded_files)

        # TRATAMENTO
        df['categoria'] = df['produto'].astype(str).str.split().str[0]
        df['data'] = pd.to_datetime(df['data'], format='%d.%m.%Y', errors='coerce')
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
        df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['id_pedido'] = df.index.astype(str)

        # FILTROS
        st.sidebar.header("🔍 Filtros")
        anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
        df_temp = df[df['ano'].isin(anos)]

        lojas = st.sidebar.multiselect("Loja", sorted(df_temp['loja'].unique()), default=sorted(df_temp['loja'].unique()))
        df_temp = df_temp[df_temp['loja'].isin(lojas)]

        categorias = st.sidebar.multiselect("Categoria", sorted(df_temp['categoria'].unique()), default=sorted(df_temp['categoria'].unique()))
        df = df_temp[df_temp['categoria'].isin(categorias)]

        st.sidebar.write("Total de registros: " + str(len(df)))

        if len(df) > 0:
            # KPIs
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Faturamento Total", "R$ {:,.2f}".format(df['valor_total'].sum()))
            col2.metric("Ticket Médio", "R$ {:,.2f}".format(df['valor_total'].mean()))
            col3.metric("Qtd Itens", "{:,}".format(len(df)))
            col4.metric("Qtd Pedidos", "{:,}".format(df['id_pedido'].nunique()))

            # GRAFICO
            st.divider()
            st.subheader("Top 10 Lojas")
            df_loja = df.groupby('loja')['valor_total'].sum().reset_index().sort_values('valor_total', ascending=False).head(10)
            fig = px.bar(df_loja, x='loja', y='valor_total', text_auto='.2s')
            fig.update_yaxes(tickprefix='R$ ')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("Nenhum dado encontrado com os filtros")

else:
    st.info("👆 Faça upload dos arquivos 2025.zip e 2026.zip")
