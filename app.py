import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Dashboard BSB", layout="wide")
st.title("📊 Dashboard Gerencial BSB")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

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
    return pd.concat(lista_df, ignore_index=True)

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor'])
    
    df['ano'] = df['data'].dt.year
    df['id'] = df.index.astype(str)
    
    # SIDEBAR COM FILTROS + METAS
    st.sidebar.header("🔍 Filtros")
    anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), sorted(df['ano'].unique()))
    df_f = df[df['ano'].isin(anos)]
    
    lojas = st.sidebar.multiselect("Loja", sorted(df_f['loja'].unique()), sorted(df_f['loja'].unique()))
    df_f = df_f[df_f['loja'].isin(lojas)]
    
    cats = st.sidebar.multiselect("Categoria", sorted(df_f['categoria'].unique()), sorted(df_f['categoria'].unique()))
    df_f = df_f[df_f['categoria'].isin(cats)]
    
    st.sidebar.divider()
    st.sidebar.header("🎯 Metas")
    
    # 1. META GERAL - CAMPO PARA DIGITAR
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 500000.0, 150000.0, 1000000.0)
    
    # 2. META POR LOJA - SELECIONAVEL
    st.sidebar.subheader("Meta por Loja")
    lojas_meta = st.sidebar.multiselect("Selecione lojas para meta", options=sorted(df['loja'].unique()))
    
    dict_meta_loja = {}
    for loja in lojas_meta:
        dict_meta_loja[loja] = st.sidebar.number_input(f"Meta {loja}", 0.0, 50000000.0, 10000000.0, 100000.0, key=loja)
    
    st.sidebar.write("Total registros: " + str(len(df_f)))
    df = df_f
    
    if len(df) > 0:
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        fat = df['valor'].sum()
        c1.metric("Faturamento", "R$ {:,.2f}".format(fat))
        c2.metric("Ticket Médio", "R$ {:,.2f}".format(df['valor'].mean()))
        c3.metric("Qtd Itens", "{:,}".format(len(df)))
        c4.metric("Qtd Pedidos", "{:,}".format(df['id'].nunique()))
        
        st.divider()
        st.subheader("🎯 Acompanhamento de Meta")
        
        # META GERAL
        ating_geral = (fat / meta_geral) * 100 if meta_geral > 0 else 0
        st.metric("Meta Geral", f"R$ {meta_geral:,.2f}", f"Atingimento: {ating_geral:.2f}%")
        
        # META POR LOJA
        if len(dict_meta_loja) > 0:
            st.subheader("Performance por Loja com Meta")
            dfm = df.groupby('loja')['valor'].sum().reset_index()
            dfm['Meta'] = dfm['loja'].map(dict_meta_loja).fillna(0)
            dfm['% Ating'] = (dfm['valor'] / dfm['Meta']) * 100
            dfm = dfm[dfm['Meta'] > 0].sort_values('valor', ascending=False)
            st.dataframe(dfm.style.format({'valor':'R$ {:,.2f}','Meta':'R$ {:,.2f}','% Ating':'{:.2f}%'}), use_container_width=True)
        else:
            st.info("Selecione lojas na sidebar para ver meta por loja")
        
        if len(df['ano'].unique()) > 1:
            st.divider()
            st.subheader("📈 Comparativo Ano a Ano")
            dfa = df.groupby('ano')['valor'].sum().reset_index()
            ano1 = dfa['ano'].max()
            ano0 = ano1 - 1
            f1 = dfa[dfa['ano']==ano1]['valor'].sum()
            f0 = dfa[dfa['ano']==ano0]['valor'].sum()
            cresc = ((f1-f0)/f0)*100 if f0>0 else 0
            x1,x2,x3 = st.columns(3)
            x1.metric(f"Ano {ano1}", f"R$ {f1:,.2f}")
            x2.metric(f"Ano {ano0}", f"R$ {f0:,.2f}")
            x3.metric("Crescimento", f"{cresc:.2f}%")
            fig = px.bar(dfa, x='ano', y='valor', text_auto='.2s')
            fig.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.subheader("🏆 Top 10 Produtos")
        dfp = df.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
        figp = px.bar(dfp, x='produto', y='valor', text_auto='.2s')
        figp.update_yaxes(tickprefix='R$ ')
        figp.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(figp, use_container_width=True)
        
        st.divider()
        st.subheader("🏪 Top 10 Lojas")
        dfl = df.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
        figl = px.bar(dfl, x='loja', y='valor', text_auto='.2s')
        figl.update_yaxes(tickprefix='R$ ')
        figl.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(figl, use_container_width=True)
else: 
    st.info("👆 Upload dos 2 .zip")
