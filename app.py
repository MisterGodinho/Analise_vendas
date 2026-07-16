import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")
st.title("Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

@st.cache_data(show_spinner="Carregando 29MB... Aguarde 2 min")
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
                    df_temp['loja'] = df_temp['loja'].astype(str).str.strip()
                    df_temp['produto'] = df_temp['produto'].astype(str).str.strip()
                    df_temp['categoria'] = df_temp['categoria'].astype(str).str.strip()
                    lista_df.append(df_temp)
    if len(lista_df) == 0:
        return pd.DataFrame()
    return pd.concat(lista_df, ignore_index=True)

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor'])
    df = df[df['loja']!= '']
    df['ano'] = df['data'].dt.year

    st.sidebar.header("Filtros")
    anos = st.sidebar.multiselect("Ano", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
    df_f = df[df['ano'].isin(anos)].copy()

    todas_lojas = sorted(df_f['loja'].unique())
    lojas = st.sidebar.multiselect("Loja", options=todas_lojas, default=todas_lojas)
    if len(lojas) > 0:
        df_f = df_f[df_f['loja'].isin(lojas)]

    todas_cats = sorted(df_f['categoria'].unique())
    cats = st.sidebar.multiselect("Categoria", options=todas_cats, default=todas_cats)
    if len(cats) > 0:
        df_f = df_f[df_f['categoria'].isin(cats)]

    st.sidebar.divider()
    st.sidebar.header("Metas")
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 500000.0, 150000.0, 100000.0)

    st.sidebar.subheader("Meta por Loja")
    dict_meta_loja = {}
    for loja in sorted(df['loja'].unique()):
        valor = st.sidebar.number_input(f"Meta {loja}", 0.0, 500000.0, 0.0, 100000.0, key=f"meta_{loja}")
        if valor > 0:
            dict_meta_loja = valor

    st.sidebar.metric("Total registros", f"{len(df_f):,}")
    df = df_f

    if len(df) > 0:
        st.divider()
        c1, c2 = st.columns(2)
        fat = df['valor'].sum()
        c1.metric("Faturamento", f"R$ {fat:,.0f}")
        c2.metric("Ticket Medio", f"R$ {df['valor'].mean():,.2f}")

        st.divider()
        st.subheader("Acompanhamento de Meta")
        ating_geral = (fat / meta_geral) * 100 if meta_geral > 0 else 0
        st.metric("Meta Geral", f"R$ {meta_geral:,.0f}", f"Atingimento: {ating_geral:.2f}%")
        st.progress(min(ating_geral/100, 1.0))

        if len(dict_meta_loja) > 0:
            st.subheader("Performance por Loja com Meta")
            dfm = df.groupby('loja')['valor'].sum().reset_index()
            dfm['Meta'] = dfm['loja'].map(dict_meta_loja).fillna(0)
            dfm = dfm[dfm['Meta'] > 0]
            dfm['% Ating'] = (dfm['valor'] / dfm['Meta']) * 100
            dfm = dfm.sort_values('% Ating', ascending=False)
            st.dataframe(dfm.style.format({'valor':'R$ {:,.2f}','Meta':'R$ {:,.2f}','% Ating':'{:.2f}%'}), use_container_width=True, hide_index=True)

        if len(df['ano'].unique()) > 1:
            st.divider()
            st.subheader("Comparativo Ano a Ano")
            dfa = df.groupby('ano')['valor'].sum().reset_index()
            ano1 = dfa['ano'].max()
            ano0 = dfa['ano'].min()
            f1 = dfa[dfa['ano']==ano1]['valor'].sum()
            f0 = dfa[dfa['ano']==ano0]['valor'].sum()
            cresc = ((f1-f0)/f0)*100 if f0>0 else 0
            x1,x2,x3 = st.columns(3)
            x1.metric(f"Ano {ano1}", f"R$ {f1:,.0f}")
            x2.metric(f"Ano {ano0}", f"R$ {f0:,.0f}")
            x3.metric("Crescimento", f"{cresc:.2f}%")
            fig = px.bar(dfa, x='ano', y='valor')
            fig.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader("Top 10 Produtos por Ano")
            col_ano1, col_ano2 = st.columns
