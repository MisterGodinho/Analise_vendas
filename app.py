import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import calendar

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1e293b; }
    [data-testid="stSidebar"] label { color: #e2e8f0!important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; }
.stPills button { border-radius: 20px!important; border: 1px solid #475569!important; background-color: #334155!important; color: #cbd5e1!important; }
.stPills button[aria-pressed="true"] { background-color: #3b82f6!important; border: 1px solid #3b82f6!important; color: white!important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

@st.cache_data
def carregar_dados(files):
    lista_df = []
    for zip_file in files:
        with zipfile.ZipFile(zip_file) as z:
            for nome_arquivo in z.namelist():
                if nome_arquivo.endswith('/'): continue
                with z.open(nome_arquivo) as f:
                    if '.xlsx' in nome_arquivo:
                        df_temp = pd.read_excel(f, sheet_name=0, header=0, usecols='F,G,I,J,Q')
                        df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor']
                    elif '.csv' in nome_arquivo:
                        df_temp = pd.read_csv(f, sep=';', usecols=[5,6,8,9,16], names=['loja','data','produto','categoria','valor'], header=0, encoding='latin-1', on_bad_lines='skip')
                    else: continue
                    lista_df.append(df_temp)
    return pd.concat(lista_df, ignore_index=True) if lista_df else pd.DataFrame()

if uploaded_files and len(uploaded_files) >= 2:
    with st.spinner("Carregando 29MB..."):
        df = carregar_dados(uploaded_files)

    # LIMPEZA
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df['loja'] = df['loja'].astype(str).str.strip()
    df['produto'] = df['produto'].astype(str).str.strip()
    df['categoria'] = df['categoria'].astype(str).str.strip()
    df = df.dropna(subset=['data', 'valor', 'loja'])
    df['ano'] = df['data'].dt.year
    df['mes_num'] = df['data'].dt.month

    st.sidebar.header("FILTROS")
    MESES_PT = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}

    # PASSO 1: Pega Ano e Mes
    anos = st.sidebar.pills("ANO", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()), selection_mode="multi")
    meses = st.sidebar.pills("MÊS", options=sorted(df['mes_num'].unique()), default=sorted(df['mes_num'].unique()), format_func=lambda x: MESES_PT[x], selection_mode="multi")

    # PASSO 2: Cria df_base só com Ano e Mes pra gerar as listas de Loja e Categoria
    df_base = df[df['ano'].isin(anos) & df['mes_num'].isin(meses)].copy()

    # PASSO 3: Gera as listas a partir do df_base
    lista_lojas = sorted(df_base['loja'].unique())
    lista_cats = sorted(df_base['categoria'].unique())

    # PASSO 4: Pega Loja e Categoria
    lojas = st.sidebar.pills("LOJA", options=lista_lojas, default=lista_lojas, selection_mode="multi")
    cats = st.sidebar.pills("CATEGORIA", options=lista_cats, default=lista_cats, selection_mode="multi")

    # PASSO 5: Aplica TODOS os filtros no df_final
    df_final = df_base[df_base['loja'].isin(lojas) & df_base['categoria'].isin(cats)].copy()

    st.sidebar.metric("Total registros", f"{len(df_final):,}")

    if len(df_final) > 0:
        st.divider()
        fat = df_final['valor'].sum()
        st.metric("Faturamento", f"R$ {fat:,.0f}")

        anos_unicos = sorted(df_final['ano'].unique())
        if len(anos_unicos) > 1:
            ano1 = anos_unicos[-1]
            ano0 = anos_unicos[-2]

            st.divider()
            st.subheader("Ranking Top 10 Lojas")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.write(f"**{ano1}**")
                dfl1 = df_final[df_final['ano']==ano1].groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                dfl1['% Total'] = (dfl1['valor'] / dfl1['valor'].sum()) * 100 if dfl1['valor'].sum() > 0 else 0
                st.dataframe(dfl1.style.format({'valor':'R$ {:,.0f}', '% Total':'{:.1f}%'}), use_container_width=True)
            with col_l2:
                st.write(f"**{ano0}**")
                dfl0 = df_final[df_final['ano']==ano0].groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                dfl0['% Total'] = (dfl0['valor'] / dfl0['valor'].sum()) * 100 if dfl0['valor'].sum() > 0 else 0
                st.dataframe(dfl0.style.format({'valor':'R$ {:,.0f}', '% Total':'{:.1f}%'}), use_container_width=True)
        else:
            st.warning("Selecione 2 anos para ver o Ranking")
else:
    st.info("Upload dos 2.zip")
