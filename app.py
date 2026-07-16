import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Dashboard Gerencial BSB", layout="wide")
st.title("📊 Dashboard Gerencial BSB")

uploaded_files = st.file_uploader(
    "1. Selecione os arquivos 2025.zip e 2026.zip",
    type=['zip'],
    accept_multiple_files=True
)

@st.cache_data(show_spinner="⏳ Descompactando e lendo arquivos... Aguarde 2 min")
def carregar_dados(files):
    lista_df = []
    for zip_file in files:
        with zipfile.ZipFile(zip_file) as z:
            for nome_arquivo in z.namelist():
                if nome_arquivo.endswith('/'):
                    continue
                with z.open(nome_arquivo) as f:
                    if nome_arquivo.endswith('.xlsx') or nome_arquivo.endswith('.xls'):
                        df_temp = pd.read_excel(f, sheet_name=0, header=0, usecols='F,G,I,J,Q')
                        df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor_total']
                    elif nome_arquivo.endswith('.csv'):
                        df_temp = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], names=['loja','data','produto','categoria','valor_total'], header=0, encoding='latin-1', on_bad_lines='skip', engine='python')
                    else:
                        continue
                    lista_df.append(df_temp)
    df = pd.concat(lista_df, ignore_index=True)
    return df

if uploaded_files:
    if len(uploaded_files) < 2:
        st.warning("⚠️ Faz upload dos 2 arquivos: 2025.zip e 2026.zip")
    else:
        df = carregar_dados(uploaded_files)

        df['valor_total'] = df['valor_total'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

        df['ano'] = df['data'].dt.year
        df['id_pedido'] = df.index.astype(str)

        st.sidebar.header("🔍 Filtros")
        anos = st.sidebar.multiselect("Ano", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
        df_temp = df[df['ano'].isin(anos)]

        lojas = st.sidebar.multiselect("Loja", options=sorted(df_temp['loja'].unique()), default=sorted(df_temp['loja'].unique()))
        df_temp = df_temp[df_temp['loja'].isin(lojas)]

        categorias = st.sidebar.multiselect("Categoria", options=sorted(df_temp['categoria'].unique()), default=sorted(df_temp['categoria'].unique()))
        df = df_temp[df_temp['categoria'].isin(categorias)]

        st.sidebar.write("Total de registros: " + str(len(df)))

        if len(df) > 0:
            st.divider()
            
            col1, col2, col3, col4 = st.columns(4)
            faturamento_total = df['valor_total'].sum()
            col1.metric("Faturamento Total", "R$ {:,.2f}".format(faturamento_total))
            col2.metric("Ticket Médio", "R$ {:,.2f}".format(df['valor_total'].mean()))
            col3.metric("Qtd Itens", "{:,}".format(len(df)))
            col4.metric("Qtd Pedidos", "{:,}".format(df['id_pedido'].nunique()))

            # META GERAL E POR LOJA - CORRIGIDO
            st.divider()
            st.subheader("🎯 Meta de Faturamento")
            meta_geral = st.number_input("Digite a Meta Geral R$", min_value=0.0, value=150000000.0, step=1000000.0, format="%.2f")
            atingimento = (faturamento_total / meta_geral) * 100 if meta_geral > 0 else 0
            diferenca = faturamento_total - meta_geral
            st.metric("Atingimento da Meta Geral", f"{atingimento:.2f}%", f"R$ {diferenca:,.2f}")

            st.subheader("Performance por Loja vs Meta")
            df_meta_loja = df.groupby('loja')['valor_total'].sum().reset_index().sort_values('valor_total', ascending=False)
            qtd_lojas = len(df_meta_loja)
            meta_por_loja = meta_geral / qtd_lojas if qtd_lojas > 0 else 0
            df_meta_loja['Meta Loja'] = meta_por_loja
            df_meta_loja['% Atingimento'] = (df_meta_loja['valor_total'] / df_meta_loja['Meta Loja']) * 100
            st.dataframe(df_meta_loja.style.format({'valor_total': 'R$ {:,.2f}', 'Meta Loja': 'R$ {:,.2f}', '% Atingimento': '{:.2f}%'}), use_container_width=True)

            # COMPARATIVO ANO ANTERIOR
            st.divider()
            st.subheader("📈 Comparativo Ano vs Ano Anterior")
            if len(df['ano'].unique()) > 1:
                df_ano = df.groupby('ano')['valor_total'].sum().reset_index()
                ano_atual = df['ano'].max()
                ano_anterior = ano_atual - 1
                fat_atual = df_ano[df_ano['ano'] == ano_atual]['valor_total'].sum()
                fat_anterior = df_ano[df_ano['ano'] == ano_anterior]['valor_total'].sum()
                crescimento = ((fat_atual - fat_anterior) / fat_anterior) * 100 if fat_anterior > 0 else 0
                col_a, col_b, col_c = st.columns(3)
                col_a.metric(f"Faturamento {ano_atual}", f"R$ {fat_atual:,.2f}")
                col_b.metric(f"Faturamento {ano_anterior}", f"R$ {fat_anterior:,.2f}")
                col_c.metric("Crescimento", f"{crescimento:.2f}%")
                fig_ano = px.bar(df_ano, x='ano', y='valor_total', text_auto='.2s')
                fig_ano.update_yaxes(tick
