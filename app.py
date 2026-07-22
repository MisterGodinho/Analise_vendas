
import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import calendar

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")

# CSS CORPORATIVO
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label {
        color: #e2e8f0!important;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
  .stPills {
        gap: 0.4rem;
    }
  .stPills button {
        border-radius: 20px!important;
        border: 1px solid #475569!important;
        background-color: #334155!important;
        color: #cbd5e1!important;
        font-size: 0.8rem;
        padding: 0.3rem 0.8rem;
    }
  .stPills button[aria-pressed="true"] {
        background-color: #3b82f6!important;
        border: 1px solid #3b82f6!important;
        color: white!important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.title("Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

def carregar_dados(files):
    lista_df = []
    progress = st.progress(0)
    total = len(files)
    for i, zip_file in enumerate(files):
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
        progress.progress((i+1)/total)
    if len(lista_df) == 0:
        return pd.DataFrame()
    return pd.concat(lista_df, ignore_index=True)

if uploaded_files and len(uploaded_files) >= 2:
    with st.spinner("Carregando 29MB..."):
        df = carregar_dados(uploaded_files)

    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor'])
    df = df[df['loja']!= '']
    df['ano'] = df['data'].dt.year
    df['mes_num'] = df['data'].dt.month
    df['mes_nome'] = df['data'].dt.month.apply(lambda x: calendar.month_name[x])

    st.sidebar.markdown("### FILTROS")

    # 1. ANO
    lista_anos = sorted(df['ano'].unique())
    anos = st.sidebar.pills("Ano", options=lista_anos, default=lista_anos, selection_mode="multi", key="pills_ano")

    # 2. MES EM PORTUGUES
    MESES_PT = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 
                7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
    lista_meses = sorted(df['mes_num'].unique())
    meses = st.sidebar.pills("Mês", options=lista_meses, default=lista_meses, 
                             format_func=lambda x: MESES_PT[x], selection_mode="multi", key="pills_mes")

    df_f = df[df['ano'].isin(anos)].copy()
    df_f = df_f[df_f['mes_num'].isin(meses)].copy()

    # 3. LOJA
    lista_lojas = sorted(df_f['loja'].unique())
    lojas = st.sidebar.pills("Loja", options=lista_lojas, default=lista_lojas, selection_mode="multi", key="pills_loja")
    if len(lojas) > 0:
        df_f = df_f[df_f['loja'].isin(lojas)]

    # 4. CATEGORIA
    lista_cats = sorted(df_f['categoria'].unique())
    cats = st.sidebar.pills("Categoria", options=lista_cats, default=lista_cats, selection_mode="multi", key="pills_cat")
    if len(cats) > 0:
        df_f = df_f[df_f['categoria'].isin(cats)]

    # BOTAO LIMPAR
    if st.sidebar.button("Limpar Filtros", use_container_width=True):
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("### METAS")
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 500000.0, 150000.0, 10000.0)

    st.sidebar.metric("Total registros", f"{len(df_f):,}")
    df = df_f

    if len(df) > 0:
        #... aqui continua o resto do seu código normal
        st.divider()
        c1, c2 = st.columns(2)
        fat = df['valor'].sum()
        c1.metric("Faturamento", f"R$ {fat:,.0f}")
        c2.metric("Ticket Medio", f"R$ {df['valor'].mean():,.2f}")
        #... resto
