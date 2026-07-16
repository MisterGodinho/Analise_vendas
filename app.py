import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile

st.set_page_config(page_title="Dashboard BSB", layout="wide", initial_sidebar_state="expanded")

# CSS PARA DEIXAR GERENCIAL
st.markdown("""
<style>
    .big-card {padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background: white;}
    .metric-card {border-left: 5px solid #FF4B4B;}
    .meta-card {border-left: 5px solid #00C851;}
    div[data-testid="metric-container"] {background-color: #F8F9FA; border-radius: 10px; padding: 15px;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Gerencial BSB")
st.caption("Análise de Vendas 2025 - 2026")

uploaded_files = st.file_uploader("Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True, label_visibility="collapsed")

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
    
    # SIDEBAR
    st.sidebar.header("🔍 Filtros")
    anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), sorted(df['ano'].unique()))
    df_f = df[df['ano'].isin(anos)]
    
    lojas = st.sidebar.multiselect("Loja", sorted(df_f['loja'].unique()), sorted(df_f['loja'].unique()))
    df_f = df_f[df_f['loja'].isin(lojas)]
    
    cats = st.sidebar.multiselect("Categoria", sorted(df_f['categoria'].unique()), sorted(df_f['categoria'].unique()))
    df_f = df_f[df_f['categoria'].isin(cats)]
    
    st.sidebar.divider()
    st.sidebar.header("🎯 Metas")
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 500000.0, 150000.0, 1000000.0)
    
    st.sidebar.subheader("Meta por Loja")
    lojas_meta = st.sidebar.multiselect("Selecione lojas", options=sorted(df['loja'].unique()))
    dict_meta_loja = {}
    for loja in lojas_meta:
        dict_meta_loja[loja] = st.sidebar.number_input(f"Meta {loja}", 0.0, 50000000.0, 10000000.0, 100000.0, key=loja)
    
    st.sidebar.metric("Total Registros", f"{len(df_f):,}")
    df = df_f
    
    if len(df) > 0:
        # KPIS PRINCIPAIS - CARDS MAIORES
        st.subheader("Visão Geral")
        fat = df['valor'].sum()
        ticket = df['valor'].mean()
        qtd_itens = len(df)
        qtd_pedidos = df['id'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="💰 Faturamento Total", value="R$ {:,.2f}".format(fat))
        with col2:
            st.metric(label="🎟️ Ticket Médio", value="R$ {:,.2f}".format(ticket))
        with col3:
            st.metric(label="📦 Qtd Itens", value="{:,}".format(qtd_itens))
        with col4:
            st.metric(label="🧾 Qtd Pedidos", value="{:,}".format(qtd_pedidos))
        
        st.divider()
        
        # META COM BARRA DE PROGRESSO
        st.subheader("🎯 Acompanhamento de Meta")
        ating_geral = (fat / meta_geral) * 100 if meta_geral > 0 else 0
        diferenca = fat - meta_geral
        
        colm1, colm2 = st.columns([2,1])
        with colm1:
            st.metric("Meta Geral", f"R$ {meta_geral:,.2f}", f"{ating_geral:.2f}%")
            st.progress(min(ating_geral/100, 1.0)) # BARRA DE PROGRESSO
        with colm2:
            st.metric("Diferença", f"R$ {diferenca:,.2f}", delta_color="inverse" if diferenca < 0 else "normal")
        
        # META POR LOJA COM CORES
        if len(dict_meta_loja) > 0:
            st.subheader("Performance por Loja")
            dfm = df.groupby('loja')['valor'].sum().reset_index()
            dfm['Meta'] = dfm['loja'].map(dict_meta_loja).fillna(0)
            dfm['% Ating'] = (dfm['valor'] / dfm['Meta']) * 100
            dfm = dfm[dfm['Meta'] > 0].sort_values('valor', ascending=False)
            
            def cor_ating(val):
                if val >= 100: return 'background-color: #d4edda' # verde
                elif val >= 80: return 'background-color: #fff3cd' # amarelo
                else: return 'background-color: #f8d7da' # vermelho
            
            st.dataframe(
                dfm.style.format({'valor':'R$ {:,.2f}','Meta':'R$ {:,.2f}','% Ating':'{:.2f}%'}).applymap(cor_ating, subset=['% Ating']),
                use_container_width=True, hide_index=True
            )
        
        # GRAFICOS EM 2 COLUNAS
        st.divider()
        g1, g2 = st.columns(2)
        
        with g1:
            if len(df['ano'].unique()) > 1:
                st.subheader("📈 Comparativo Anual")
                dfa = df.groupby('ano')['valor'].sum().reset_index()
                fig = px.bar(dfa, x='ano', y='valor', text_auto='.2s', color='ano', color_discrete_sequence=px.colors.sequential.Reds)
                fig.update_yaxes(tickprefix='R$ ')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with g2:
            st.subheader("🏆 Top 10 Produtos")
            dfp = df.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
            figp = px.bar(dfp, x='valor', y='produto', orientation='h', text_auto='.2s', color='valor', color_discrete_sequence=px.colors.sequential.Reds)
            figp.update_xaxes(tickprefix='R$ ')
            figp.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(figp, use_container_width=True)
        
        st.subheader("🏪 Top 10 Lojas")
        dfl = df.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
        figl = px.bar(dfl, x='loja', y='valor', text_auto='.2s', color='valor', color_discrete_sequence=px.colors.sequential.Reds)
        figl.update_yaxes(tickprefix='R$ ')
        st.plotly_chart(figl, use_container_width=True)
        
else: 
    st.info("👆 Faça upload dos arquivos 2025.zip e 2026.zip para começar")
