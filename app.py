import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile

st.set_page_config(page_title="Análise do Negócio BSB", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="st-"] {font-family: 'Inter', sans-serif;}
    .main {background-color: #0E1117;}
    div[data-testid="stMetric"] {background-color: #262730; border: 1px solid #333; padding: 20px; border-radius: 12px;}
    div[data-testid="stMetricLabel"] {color: #FA; font-size: 14px; font-weight: 600;}
    div[data-testid="stMetricValue"] {color: #FFFFFF; font-size: 28px; font-weight: 700;}
    h1, h2, h3 {color: #FFFFFF;}
    .stSidebar {background-color: #1A1C23;}
    hr {border-color: #333;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Análise do Negócio BSB")
st.caption("Performance de Vendas | 2025 - 2026")
st.write("**Selecione os arquivos 2025.zip e 2026.zip abaixo:**")

uploaded_files = st.file_uploader(
    label=" ",
    type=['zip'], 
    accept_multiple_files=True
)

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
    return pd.concat(lista_df, ignore_index=True)

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor', 'loja'])
    
    df['ano'] = df['data'].dt.year
    df['id'] = df.index.astype(str)
    
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
            dict_meta_loja[loja] = st.number_input(f"Meta {loja}", min_value=0.0, max_value=50000000.0, value=10000000.0, step=100000.0, key=f"meta_{loja}")
        
        st.metric("Total de Registros", f"{len(df_filtrado):,}")
    
    df = df_filtrado
    
    if len(df) > 0:
        fat = df['valor'].sum()
        ticket = df['valor'].mean()
        qtd_itens = len(df)
        qtd_pedidos = df['id'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="💰 Faturamento Total", value="R$ {:,.0f}".format(fat))
        col2.metric(label="🎟️ Ticket Médio", value="R$ {:,.2f}".format(ticket))
        col3.metric(label="📦 Itens Vendidos", value="{:,}".format(qtd_itens))
        col4.metric(label="🧾 Qtd Pedidos", value="{:,}".format(qtd_pedidos))
        
        st.divider()
        
        st.subheader("🎯 Acompanhamento de Meta")
        ating_geral = (fat / meta_geral) * 100 if meta_geral > 0 else 0
        diferenca = fat - meta_geral
        
        colm1, colm2 = st.columns([2,1])
        with colm1:
            # CORREÇÃO: padronizei todas as aspas para aspas simples
            fig_gauge = go.Figure(go.Indicator(
                mode = 'gauge+number+delta', 
                value = ating_geral,
                title = {'text': 'Atingimento da Meta Geral', 'font': {'color': 'white', 'size': 18}},
                delta = {'reference': 100, 'suffix': '%'},
                gauge = {
                    'axis': {'range': [0, 150], 'tickcolor': 'white'},
                    'bar': {'color': '#00C851'},
                    'steps' : [
                        {'range': [0, 80], 'color': '#DC3545'}, 
                        {'range': [80, 100], 'color': '#FFC107'}
                    ],
                    'threshold' : {'line': {'color': 'white', 'width': 4}, 'thickness': 0.75, 'value': 100}
                }
            ))
            fig_gauge.update_layout(height=280, paper_bgcolor='#0E1117', font={'color':'white'})
            st.plotly_chart(fig_gauge, use_container_width=True)
        with colm2:
            st.metric("Meta Definida", f"R$ {meta_geral:,.0f}")
            st.metric("Faturamento Atual", f"R$ {fat:,.0f}")
            st.metric("Diferença", f"R$ {diferenca:,.0f}", delta_color="inverse" if diferenca < 0 else "normal")
        
        if len(dict_meta_loja) > 0:
            st.subheader("Performance por Loja vs Meta")
            dfm = df.groupby('loja')['valor'].sum().reset_index()
            dfm['Meta'] = dfm['loja'].map(dict_meta_loja).fillna(0)
            dfm['% Atingimento'] = (dfm['valor'] / dfm['Meta']) * 100
            dfm = dfm[dfm['Meta'] > 0].sort_values('% Atingimento', ascending=False)
            fig_meta = px.bar(dfm, x='loja', y='% Atingimento', text='% Atingimento', color='% Atingimento', 
                              color_continuous_scale=['#DC3545', '#FFC107', '#00C851'])
            fig_meta.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_meta.update_layout(plot_bgcolor='#0E1117', paper_bgcolor='#0E1117', font_color='white')
            st.plotly_chart(fig_meta, use_container_width=True)
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            if len(df['ano'].unique()) > 1:
                st.subheader("📈 Comparativo Anual")
                dfa = df.groupby('ano')['valor'].sum().reset_index()
                fig = px.bar(dfa, x='ano', y='valor', text_auto='.2s', color='ano', color_discrete_sequence=['#00C851', '#0D6EFD'])
                fig.update_yaxes(tickprefix='R$ ')
                fig.update_layout(plot_bgcolor='#0E1117', paper_bgcolor='#0E1117', font_color='white', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.subheader("🏆 Top 10 Produtos")
            dfp = df.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
            figp = px.bar(dfp, x='valor', y='produto', orientation='h', text_auto='.2s', color='valor', color_continuous_scale='Blues')
            figp.update_xaxes(tickprefix='R$ ')
            figp.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='#0E1117', paper_bgcolor='#0E1117', font_color='white')
            st.plotly_chart(figp, use_container_width=True)
        
        st.subheader("🏪 Ranking Top 10 Lojas")
        dfl = df.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
        figl = px.bar(dfl, x='loja', y='valor', text_auto='.2s', color='valor', color_continuous_scale='Reds')
        figl.update_yaxes(tickprefix='R$ ')
        figl.update_layout(plot_bgcolor='#0E1117', paper_bgcolor='#0E1117', font_color='white')
        st.plotly_chart(figl, use_container_width=True)
        
else: 
    st.info("👆 Faça upload dos arquivos 2025.zip e 2026.zip para iniciar")
