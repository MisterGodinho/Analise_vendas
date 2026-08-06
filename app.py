import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import gc

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1e293b; }
[data-testid="stSidebar"] label { color: #e2e8f0!important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; }
div[data-baseweb="tag"] { background-color: #ef4444!important; border-radius: 16px!important; }
div[data-baseweb="tag"] span { color: white!important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)
MESES_PT = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}

@st.cache_data(show_spinner="Carregando e otimizando 29MB...")
def carregar_dados(files):
    lista_df = []
    progress = st.progress(0)
    total = len(files)
    for i, zip_file in enumerate(files):
        with zipfile.ZipFile(zip_file) as z:
            for nome_arquivo in z.namelist():
                if nome_arquivo.endswith('/'): continue
                with z.open(nome_arquivo) as f:
                    if '.xlsx' in nome_arquivo:
                        df_temp = pd.read_excel(f, sheet_name=0, header=0, usecols='F,G,I,J,Q', dtype={'F':str, 'I':str, 'J':str})
                        df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor']
                    elif '.csv' in nome_arquivo:
                        df_temp = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], names=['loja','data','produto','categoria','valor'], header=0, encoding='latin-1', on_bad_lines='skip', dtype={'loja':str, 'produto':str, 'categoria':str})
                    else: continue
                    lista_df.append(df_temp)
        progress.progress((i+1)/total)
    if len(lista_df) == 0: return pd.DataFrame()

    df = pd.concat(lista_df, ignore_index=True); del lista_df; gc.collect()
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce').astype('float32')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df['loja'] = df['loja'].astype(str).str.strip()
    df['produto'] = df['produto'].astype(str).str.strip()
    df['categoria'] = df['categoria'].astype(str).str.strip()
    df = df.dropna(subset=['data', 'valor'])
    df = df[df['loja']!= '']
    df['ano'] = df['data'].dt.year.astype('int16')
    df['mes_num'] = df['data'].dt.month.astype('int8')
    df['dia'] = df['data'].dt.day.astype('int8') # NOVO
    df['mes_nome'] = df['mes_num'].map(MESES_PT)
    df['loja'] = df['loja'].astype('category')
    df['produto'] = df['produto'].astype('category')
    df['categoria'] = df['categoria'].astype('category')
    return df

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    st.success(f"✅ Carregado! {len(df):,} linhas | Memória: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

    st.sidebar.header("FILTROS GERAIS")
    anos = st.sidebar.multiselect("ANO", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
    df_ano = df[df['ano'].isin(anos)] if anos else df
    meses_nome = st.sidebar.multiselect("MÊS", options=sorted(df['mes_nome'].unique(), key=lambda x: list(MESES_PT.values()).index(x)), default=sorted(df['mes_nome'].unique(), key=lambda x: list(MESES_PT.values()).index(x)))
    df_mes = df_ano[df_ano['mes_nome'].isin(meses_nome)] if meses_nome else df_ano
    lojas = st.sidebar.multiselect("LOJA", options=sorted(df_mes['loja'].unique()), default=sorted(df_mes['loja'].unique()))
    df_loja = df_mes[df_mes['loja'].isin(lojas)] if lojas else df_mes
    cats = st.sidebar.multiselect("CATEGORIA", options=sorted(df_loja['categoria'].unique()), default=sorted(df_loja['categoria'].unique()))
    df_f = df_loja[df_loja['categoria'].isin(cats)] if cats else df_loja

    st.sidebar.divider()
    st.sidebar.header("METAS")
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 5000000.0, 1500000.0, 100000.0)
    st.sidebar.metric("TOTAL REGISTROS", f"{len(df_f):,}")

    if len(df_f) > 0:
        st.divider()
        c1, c2, c3 = st.columns(3)
        fat = df_f['valor'].sum()
        c1.metric("💰 Faturamento", f"R$ {fat:,.0f}")
        c2.metric("📦 Ticket Medio", f"R$ {df_f['valor'].mean():,.2f}")
        c3.metric("🧾 Qtd Vendas", f"{len(df_f):,}")

        anos_unicos = sorted(df_f['ano'].unique())
        if len(anos_unicos) > 1:
            ano1 = anos_unicos[-1]
            ano0 = anos_unicos[-2]

            st.divider()
            st.header("🧠 ANALISE INTELIGENTE: DIA A DIA")

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                mes_selecionado = st.selectbox("1. Selecione o Mês", options=sorted(df_f['mes_num'].unique()), format_func=lambda x: MESES_PT[x], index=0)
            with col_m2:
                # NOVO FILTRO DE DIA
                dias_disponiveis = sorted(df_f[df_f['mes_num']==mes_selecionado]['dia'].unique())
                dia_selecionado = st.selectbox("2. Selecione o Dia", options=dias_disponiveis, index=len(dias_disponiveis)-1) # Pega o último dia por padrão
                st.caption(f"Comparando: {dia_selecionado}/{mes_selecionado}/{ano0} vs {dia_selecionado}/{mes_selecionado}/{ano1}")

            try:
                df_temp = df_f.copy()
                df_temp['categoria'] = df_temp['categoria'].astype(str)
                df_temp['produto'] = df_temp['produto'].astype(str)

                # FILTRO POR DIA AGORA
                df_mes0 = df_temp[(df_temp['ano']==ano0) & (df_temp['mes_num']==mes_selecionado) & (df_temp['dia']==dia_selecionado)].groupby(['categoria','produto'])['valor'].sum().reset_index()
                df_mes0.columns = ['categoria','produto','Ano_Anterior']
                df_mes1 = df_temp[(df_temp['ano']==ano1) & (df_temp['mes_num']==mes_selecionado) & (df_temp['dia']==dia_selecionado)].groupby(['categoria','produto'])['valor'].sum().reset_index()
                df_mes1.columns = ['categoria','produto','Ano_Atual']
                df_analise = pd.merge(df_mes0, df_mes1, on=['categoria','produto'], how='outer').fillna(0)
                df_analise['Diferenca R$'] = df_analise['Ano_Atual'] - df_analise['Ano_Anterior']
                df_analise['Crescimento %'] = (df_analise['Diferenca R$'] / df_analise['Ano_Anterior'].replace(0,1)) * 100

                # 1. CATEGORIAS
                st.subheader(f"1. Categorias no dia {dia_selecionado} de {MESES_PT[mes_selecionado]}")
                df_cat_comp = df_analise.groupby('categoria')[['Ano_Anterior','Ano_Atual']].sum()
                df_cat_comp['Diferenca R$'] = df_cat_comp['Ano_Atual'] - df_cat_comp['Ano_Anterior']
                df_cat_comp['Crescimento %'] = (df_cat_comp['Diferenca R$'] / df_cat_comp['Ano_Anterior'].replace(0,1)) * 100

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown("#### 🔴 Em Queda")
                    df_queda_cat = df_cat_comp[(df_cat_comp['Ano_Anterior'] > 0) & (df_cat_comp['Crescimento %'] < 0)].sort_values('Diferenca R$')
                    if len(df_queda_cat) > 0:
                        st.dataframe(df_queda_cat.style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.2f}%'}), use_container_width=True, height=300)
                    else:
                        st.success("Nenhuma em queda")
                with col_c2:
                    st.markdown("#### 🟢 Em Alta")
                    df_cresce_cat = df_cat_comp[(df_cat_comp['Ano_Anterior'] > 0) & (df_cat_comp['Crescimento %'] > 0)].sort_values('Diferenca R$', ascending=False)
                    if len(df_cresce_cat) > 0:
                        st.dataframe(df_cresce_cat.style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.2f}%'}), use_container_width=True, height=300)
                    else:
                        st.warning("Nenhuma em alta")

                # 2. PRODUTOS COM FILTRO DE CATEGORIA
                st.divider()
                st.subheader(f"2. Análise de Produtos no dia {dia_selecionado}")

                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    cat_filtro_prod = st.multiselect(
                        "Filtrar por Categoria",
                        options=sorted(df_analise['categoria'].unique()),
                        default=sorted(df_analise['categoria'].unique()),
                        key="filtro_cat_prod_dia"
                    )
                with col_f2:
                    st.metric("Categorias Selecionadas", len(cat_filtro_prod))

                df_analise_filtrado = df_analise[df_analise['categoria'].isin(cat_filtro_prod)] if cat_filtro_prod else df_analise

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.markdown("#### 🔴 Top 20 Produtos em Queda")
                    df_queda_prod = df_analise_filtrado[(df_analise_filtrado['Ano_Anterior'] > 0) & (df_analise_filtrado['Crescimento %'] < 0)].sort_values('Diferenca R$').head(20)
                    if len(df_queda_prod) > 0:
                        st.dataframe(df_queda_prod[['categoria', 'produto', 'Ano_Anterior', 'Ano_Atual', 'Diferenca R$', 'Crescimento %']]
                               .rename(columns={'categoria':'Categoria', 'produto':'Produto'})
                               .style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.2f}%'}),
                                     use_container_width=True, height=400)
                    else:
                        st.info("Nenhum produto em queda")

                with col_p2:
                    st.markdown("#### 🟢 Top 20 Produtos em Alta")
                    df_cresce_prod = df_analise_filtrado[(df_analise_filtrado['Ano_Anterior'] > 0) & (df_analise_filtrado['Crescimento %'] > 0)].sort_values('Diferenca R$', ascending=False).head(20)
                    if len(df_cresce_prod) > 0:
                        st.dataframe(df_cresce_prod[['categoria', 'produto', 'Ano_Anterior', 'Ano_Atual', 'Diferenca R$', 'Crescimento %']]
                               .rename(columns={'categoria':'Categoria', 'produto':'Produto'})
                               .style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.2f}%'}),
                                     use_container_width=True, height=400)
                    else:
                        st.info("Nenhum produto em alta")

            except Exception as e:
                st.error(f"Erro na Analise Inteligente: {e}")

        else:
            st.info("Selecione 2 anos no filtro lateral para ver a Analise Inteligente")
    else:
        st.warning("⚠️ Nenhum dado com os filtros selecionados")
else:
    st.info("📤 Upload dos 2.zip")
