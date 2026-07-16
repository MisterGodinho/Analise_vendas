import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile

# CONFIGURAÇÃO DA PÁGINA - TEMA DIRETORIA
st.set_page_config(page_title="Dashboard BSB Diretoria", layout="wide", initial_sidebar_state="expanded")

# CSS PERSONALIZADO
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

@st.cache_data(show_spinner="⏳ Carregando dados... Aguarde 2 minutos")
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
    df_completo = pd.concat(lista_df, ignore_index=True)
    return df_completo

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    
    # TRATAMENTO DE DADOS
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor', 'loja'])
    
    df['ano'] = df['data'].dt.year
    df['id'] = df.index.astype(str)
    
    # SIDEBAR
    with st.sidebar:
        st.header("🔍 Filtros Executivos")
        anos = st.multiselect("Ano", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
        df_filtrado = df[df['ano'].isin(anos)]
        
        lojas = st.multiselect("Loja", options=sorted(df_filtrado['loja'].unique()), default=sorted(df_filtrado['loja'].unique()))
        df_filtrado = df_filtrado[df_filtrado['loja'].isin(lojas)]
        
        categorias = st.multiselect("Categoria", options=sorted(df_filtrado['categoria'].unique()), default=sorted(df_filtrado['categoria'].unique()))
        df_filtrado = df_filtrado[df_filtrado['categoria'].isin(categorias)]
        
        st.divider()
        st.header("🎯 Definição de Metas")
        meta_geral = st.number_input("Meta Geral R$", min_value=0.0, max_value=500000000.0, value=150000000.0, step=1000000.0)
        
        st.subheader("Meta por Loja")
        lojas_para_meta = st.multiselect("Selecione lojas para definir meta", options=sorted(df['loja'].unique()))
        dict_meta_loja = {}
        for loja in lojas_para_meta:
            dict_meta_loja = st.number_input(f"Meta {loja}", min_value=0.0, max_value=50000000.0, value=10000000.0, step=100000.0, key=f"meta_{loja}")
        
        st.metric("Total de Registros", f"{len(df_filtrado):,}")
    
    df = df_filtrado
    
    if len(df) > 0:
        # KPIS PRINCIPAIS
        faturamento_total = df['valor'].sum()
        ticket_medio = df['valor'].mean()
        qtd_itens = len(df)
        qtd_pedidos = df['id'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="💰 Faturamento Total", value="R$ {:,.0f}".format(faturamento_total))
        col2.metric(label="🎟️ Ticket Médio", value="R$ {:,.2f}".format(ticket_medio))
        col3.metric(label="📦 Itens Vendidos", value="{:,}".format(qtd_itens))
        col4.metric(label="🧾 Qtd Pedidos", value="{:,}".format(qtd_pedidos))
        
        st.divider()
        
        # SEÇÃO DE META COM GAUGE
        st.subheader("🎯 Acompanhamento de Meta")
        atingimento_geral = (faturamento_total / meta_geral) * 100 if meta_geral > 0 else 0
        diferenca_meta = faturamento_total - meta_geral
        
        col_meta1, col_meta2 = st.columns([2,1])
        with col_meta1:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = atingimento_geral,
                title = {'text': "Atingimento da Meta Geral", 'font': {'color': 'white', 'size': 18}},
                delta = {'reference': 100, 'suffix': "%"},
                gauge = {
                    'axis': {'range': [0, 150], 'tickcolor': "white"},
                    'bar': {'color': "#00C851"},
                    'steps' : [
                        {'range': [0, 80], 'color': "#DC3545"},
                        {'range': [80, 100], 'color': "#FFC107"}],
                    'threshold' : {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 100}
                }
            ))
            fig_gauge.update_layout(height=280, paper_bgcolor="#0E1117", font={'color':"white"})
            st.plotly_chart(fig_gauge, use_container_width=True)
        with col_meta2:
            st.metric("Meta Definida", f"R$ {meta_geral:,.0f}")
            st.metric("Faturamento Atual", f"R$ {faturamento_total:,.0f}")
            st.metric("Diferença", f"R$ {diferenca_meta:,.0f}", delta_color="inverse" if diferenca_meta < 0 else "normal")
        
        # META POR LOJA
        if len(dict_meta_loja) > 0:
            st.subheader("Performance por Loja vs Meta")
            df_meta_loja = df.groupby('loja')['valor'].sum().reset_index()
            df_meta_loja['Meta'] = df_meta_loja['loja'].map(dict_meta_loja).fillna(0)
            df_meta_loja['% Atingimento'] = (df_meta_loja['valor'] / df_meta_loja['Meta']) * 100
            df_meta_loja = df_meta_loja[df_meta_loja['Meta'] > 0].sort_values('% Atingimento', ascending=False)
            
            fig_meta_loja = px.bar(df_meta_loja, x='loja', y='% Atingimento', text='% Atingimento', color='% Atingimento', 
                              color_continuous_scale=['#DC3545', '#FFC107', '#00C851'])
            fig_meta_loja.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_meta_loja.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", font_color="white", yaxis_title="Atingimento %")
            st.plotly_chart(fig_meta_loja, use_container_width=True)
        
        # GRAFICOS
        st.divider()
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            if len(df['ano'].unique()) > 1:
                st.subheader("📈 Comparativo Anual")
                df_ano = df.groupby('ano')['valor'].sum().reset_index()
                fig_ano = px.bar(df_ano, x='ano', y='valor', text_auto='.2s', color='ano', color_discrete_sequence=['#00C851', '#0D6EFD'])
                fig_ano.update_yaxes(tickprefix='R$ ')
                fig_ano.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", font_color="white", showlegend=False)
                st.plotly_chart(fig_ano, use_container_width=True)
        
        with col_graf2:
            st.subheader("🏆 Top 10 Produtos")
            df_produto = df.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
            fig_produto = px.bar(df_produto, x='valor', y='produto', orientation='h', text_auto='.2s', color='valor', color_continuous_scale='Blues')
            fig_produto.update_xaxes(tickprefix='R$ ')
            fig_produto.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", font_color="white")
            st.plotly_chart(fig_produto, use_container_width=True)
        
        st.subheader("🏪 Ranking Top 10 Lojas")
        df_loja = df.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
        fig_loja = px.bar(df_loja, x='loja', y='valor', text_auto='.2s', color='valor', color_continuous_scale='Reds')
        fig_loja.update_yaxes(tickprefix='R$ ')
        fig_loja.update_layout(plot_bgcolor="#0E1117", paper_bgcolor="#0E1117", font_color="white")
        st.plotly_chart(fig_loja, use_container_width=True)
        
else: 
    st.info("👆 Faça upload dos arquivos 2025.zip e 2026.zip para iniciar a apresentação")
