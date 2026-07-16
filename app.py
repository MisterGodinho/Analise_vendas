import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile

# TEMA ESCURO EXECUTIVO
st.set_page_config(page_title="Dashboard BSB Diretoria", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="st-"] {font-family: 'Inter', sans-serif;}
    .main {background-color: #0E1117;}
    div[data-testid="stMetric"] {background-color: #262730; border: 1px solid #333; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);}
    div[data-testid="stMetricLabel"] {color: #FA; font-size: 14px; font-weight: 600;}
    div[data-testid="stMetricValue"] {color: #FFFFFF; font-size: 28px; font-weight: 700;}
    div[data-testid="stMetricDelta"] {font-size: 14px;}
    h1, h2, h3 {color: #FFFFFF;}
    .stSidebar {background-color: #1A1C23;}
    hr {border-color: #333;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Gerencial BSB")
st.caption("Performance de Vendas | 2025 - 2026")

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
    with st.sidebar:
        st.header("🔍 Filtros Executivos")
        anos = st.multiselect("Ano", sorted(df['ano'].unique()), sorted(df['ano'].unique()))
        df_f = df[df['ano'].isin(anos)]
        
        lojas = st.multiselect("Loja", sorted(df_f['loja'].unique()), sorted(df_f['loja'].unique()))
        df_f = df_f[df_f['loja'].isin(lojas)]
        
        cats = st.multiselect("Categoria", sorted(df_f['categoria'].unique()), sorted(df_f['categoria'].unique()))
        df_f = df_f[df_f['categoria'].isin(cats)]
        
        st.divider()
        st.header("🎯 Metas")
        meta_geral = st.number_input("Meta Geral R$", 0.0, 500000.0, 150000.0, 1000000.0)
        
        st.subheader("Meta por Loja")
        lojas_meta = st.multiselect("Selecione lojas", options=sorted(df['loja'].unique()))
        dict_meta_loja = {}
        for loja in lojas_meta:
            dict_meta_loja = st.number_input(f"Meta {loja}", 0.0, 50000000.0, 10000000.0, 100000.0, key=loja)
        
        st.metric("Total Registros", f"{len(df_f):,}")
    df = df_f
    
    if len(df) > 0:
        # KPIS PRINCIPAIS
        fat = df['valor'].sum()
        ticket = df['valor'].mean()
        qtd_itens = len(df)
        qtd_pedidos = df['id'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="💰 Faturamento Total", value="R$ {:,.0f}".format(fat))
        col2.metric(label="🎟️ Ticket Médio", value="R$ {:,.2f}".format(ticket))
        col3.metric(label="📦 Itens Vendidos", value="{:,}".format(qtd_itens))
        col4.metric(label="🧾 Pedidos", value="{:,}".format(qtd_pedidos))
        
        st.divider()
        
        # META COM GAUGE
        st.subheader("🎯 Acompanhamento de Meta")
        ating_geral = (fat / meta_geral) * 100 if meta_geral > 0 else 0
        diferenca = fat - meta_geral
        
        colm1, colm2 = st.columns([2,1])
        with colm1:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = ating_geral,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Atingimento da Meta Geral", 'font': {'color': 'white'}},
                delta = {'reference': 100, 'suffix': "%"},
                gauge = {
                    'axis': {'range': [None, 150], 'tickcolor': "white"},
                    'bar': {'color': "#00C851"},
                    'steps' : [
                        {'range': [0, 80], 'color': "#DC3545"},
                        {'range': [80, 100], 'color': "#FFC107"}],
                    'threshold' : {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 100}})
            fig_gauge.update_layout(height=250, paper_bgcolor="#0E1117", font={'color':"white"})
            st.plotly_chart(fig_gauge, use_container_width=True)
        with colm2:
            st.metric("Meta Definida", f"R$ {meta_geral:,.0f}")
            st.metric("Faturamento Atual", f"R$ {fat:,.0f}")
            st.metric("Diferença", f"R$ {diferenca:,.0f}", delta_color="inverse" if diferenca < 0 else "normal")
        
        # META POR LOJA
        if len(dict_meta_loja) > 0:
            st.subheader("Performance por Loja")
            dfm = df.groupby('loja')['valor'].sum().reset_index()
            dfm['Meta'] = dfm['loja'].map(dict_meta_loja).fillna(0)
            dfm['% Ating'] = (dfm['valor'] / dfm['Meta']) * 100
            dfm = dfm[dfm['Meta'] > 0].sort_values('% Ating', ascending=False)
            fig_meta = px.bar(dfm, x='loja', y='% Ating', text='% Ating', color='% Ating', 
                              color_continuous_scale=['#DC3545', '#FFC107', '#00C851'])
            fig_meta.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_meta.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", font_color="white")
            st.plotly_chart(fig_meta, use_container_width=True)
        
        # GRAFICOS
        st.divider()
        g1, g2 = st.columns(2)
        
        with g1:
            if len(df['ano'].unique()) > 1:
                st.subheader("📈 Comparativo Anual")
                dfa = df.groupby('ano')['valor'].sum().reset_index()
                fig = px.bar(dfa, x='ano', y='valor', text_auto='.2s', color='ano', color_discrete_sequence=['#00C851', '#0D6EFD'])
                fig.update_yaxes(tickprefix='R$ ')
                fig.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", font_color="white", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with g2:
            st.subheader("🏆 Top 10 Produtos")
            dfp = df.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
            figp = px.bar(dfp, x='valor', y='produto', orientation='h', text_auto='.2s', color='valor', color_continuous_scale='Blues')
            figp.update_xaxes(tickprefix='R$ ')
            figp.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", font_color="white")
            st.plotly_chart(figp, use_container_width=True)
        
        st.subheader("🏪 Ranking Top 10 Lojas")
        dfl = df.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
        figl = px.bar(dfl, x='loja', y='valor', text_auto='.2s', color='valor', color_continuous_scale='Reds')
        figl.update_yaxes(tickprefix='R$ ')
        figl.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", font_color="white")
        st.plotly_chart(figl, use_container_width=True)
        
else: 
    st.info("👆 Faça upload dos arquivos 2025.zip e 2026.zip para iniciar a apresentação")
