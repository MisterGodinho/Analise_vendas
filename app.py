import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import calendar

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")

# ========== SLICERS PROFISSIONAIS IGUAL POWER BI ==========
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1e293b; }
    [data-testid="stSidebar"] label { color: #e2e8f0!important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; }
.stPills button { border-radius: 20px!important; border: 1px solid #475569!important; background-color: #334155!important; color: #cbd5e1!important; }
.stPills button[aria-pressed="true"] { background-color: #3b82f6!important; border: 1px solid #3b82f6!important; color: white!important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)
# ==========================================================

st.title("Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

@st.cache_data
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
    with st.spinner("Carregando 29MB... Isso pode levar 2-3 min na primeira vez"):
        df_original = carregar_dados(uploaded_files) # NOME MUDOU PARA NAO CONFUNDIR

    df_original['valor'] = pd.to_numeric(df_original['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df_original['data'] = pd.to_datetime(df_original['data'], dayfirst=True, errors='coerce')
    df_original = df_original.dropna(subset=['data', 'valor'])
    df_original = df_original[df_original['loja']!= '']
    df_original['ano'] = df_original['data'].dt.year
    df_original['mes_num'] = df_original['data'].dt.month
    df_original['mes_nome'] = df_original['data'].dt.month.apply(lambda x: calendar.month_name[x])

    st.sidebar.header("FILTROS")
    
    MESES_PT = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho',
                7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}

    lista_anos = sorted(df_original['ano'].unique())
    anos = st.sidebar.pills("ANO", options=lista_anos, default=lista_anos, selection_mode="multi")
    if not anos: anos = lista_anos

    lista_meses = sorted(df_original['mes_num'].unique())
    meses = st.sidebar.pills("MÊS", options=lista_meses, default=lista_meses, format_func=lambda x: MESES_PT[x], selection_mode="multi")
    if not meses: meses = lista_meses

    # APLICA FILTROS EM CIMA DO ORIGINAL
    df_filtrado = df_original[df_original['ano'].isin(anos)].copy()
    df_filtrado = df_filtrado[df_filtrado['mes_num'].isin(meses)].copy()

    lista_lojas = sorted(df_filtrado['loja'].unique())
    lojas = st.sidebar.pills("LOJA", options=lista_lojas, default=lista_lojas, selection_mode="multi")
    if not lojas: lojas = lista_lojas
    
    lista_cats = sorted(df_filtrado['categoria'].unique())
    cats = st.sidebar.pills("CATEGORIA", options=lista_cats, default=lista_cats, selection_mode="multi")
    if not cats: cats = lista_cats

    df_filtrado = df_filtrado[df_filtrado['loja'].isin(lojas)]
    df_filtrado = df_filtrado[df_filtrado['categoria'].isin(cats)]

    st.sidebar.divider()
    st.sidebar.header("METAS")
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 500000.0, 150000.0, 10000.0)

    st.sidebar.metric("Total registros", f"{len(df_filtrado):,}")

    # USAR SEMPRE df_filtrado DAQUI PRA BAIXO
    if len(df_filtrado) > 0:
        st.divider()
        c1, c2 = st.columns(2)
        fat = df_filtrado['valor'].sum()
        c1.metric("Faturamento", f"R$ {fat:,.0f}")
        c2.metric("Ticket Medio", f"R$ {df_filtrado['valor'].mean():,.2f}")

        st.divider()
        st.subheader("Acompanhamento de Meta")
        ating_geral = (fat / meta_geral) * 100 if meta_geral > 0 else 0
        st.metric("Meta Geral", f"R$ {meta_geral:,.0f}", f"Atingimento: {ating_geral:.2f}%")
        st.progress(min(ating_geral/100, 1.0))

        anos_unicos = sorted(df_filtrado['ano'].unique())
        if len(anos_unicos) > 1:
            st.divider()
            st.subheader("Comparativo Ano a Ano")
            dfa = df_filtrado.groupby('ano')['valor'].sum().reset_index()
            ano1 = anos_unicos[-1]
            ano0 = anos_unicos[-2]
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
            st.subheader("Ranking Top 10 Lojas")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.write(f"**{ano1}**")
                dfl1 = df_filtrado[df_filtrado['ano']==ano1].groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10) # AQUI ERA O ERRO
                dfl1['% Total'] = (dfl1['valor'] / dfl1['valor'].sum()) * 100
                st.dataframe(dfl1.style.format({'valor':'R$ {:,.0f}', '% Total':'{:.1f}%'}), use_container_width=True, height=400)
            with col_l2:
                st.write(f"**{ano0}**")
                dfl0 = df_filtrado[df_filtrado['ano']==ano0].groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10) # AQUI ERA O ERRO
                dfl0['% Total'] = (dfl0['valor'] / dfl0['valor'].sum()) * 100
                st.dataframe(dfl0.style.format({'valor':'R$ {:,.0f}', '% Total':'{:.1f}%'}), use_container_width=True, height=400)

            st.divider()
            st.subheader("Top 10 Produtos por Ano")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.write(f"**{ano1}**")
                df_temp1 = df_filtrado[df_filtrado['ano']==ano1]
                dfp1 = df_temp1.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                figp1 = px.bar(dfp1, x='valor', y='produto', orientation='h', title=f"Top 10 - {ano1}")
                figp1.update_xaxes(tickprefix='R$ ')
                figp1.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(figp1, use_container_width=True)
            with col_p2:
                st.write(f"**{ano0}**")
                df_temp0 = df_filtrado[df_filtrado['ano']==ano0]
                dfp0 = df_temp0.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                figp0 = px.bar(dfp0, x='valor', y='produto', orientation='h', title=f"Top 10 - {ano0}")
                figp0.update_xaxes(tickprefix='R$ ')
                figp0.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(figp0, use_container_width=True)

            # ANALISE INTELIGENTE
            st.divider()
            st.header("ANALISE INTELIGENTE: MES A MES")
            mes_selecionado = st.selectbox("Selecione o Mês para Analisar",
                                           options=sorted(df_filtrado['mes_num'].unique()),
                                           format_func=lambda x: MESES_PT[x],
                                           index=0)
            try:
                df_mes0 = df_filtrado[(df_filtrado['ano']==ano0) & (df_filtrado['mes_num']==mes_selecionado)].groupby(['categoria','produto'])['valor'].sum().reset_index()
                df_mes0.columns = ['categoria','produto','Ano_Anterior']
                df_mes1 = df_filtrado[(df_filtrado['ano']==ano1) & (df_filtrado['mes_num']==mes_selecionado)].groupby(['categoria','produto'])['valor'].sum().reset_index()
                df_mes1.columns = ['categoria','produto','Ano_Atual']
                df_analise = pd.merge(df_mes0, df_mes1, on=['categoria','produto'], how='outer').fillna(0)
                df_analise['Diferenca R$'] = df_analise['Ano_Atual'] - df_analise['Ano_Anterior']
                df_analise['Crescimento %'] = (df_analise['Diferenca R$'] / df_analise['Ano_Anterior'].replace(0,1)) * 100
                df_cat_comp = df_analise.groupby('categoria')[['Ano_Anterior','Ano_Atual']].sum()
                df_cat_comp['Diferenca R$'] = df_cat_comp['Ano_Atual'] - df_cat_comp['Ano_Anterior']
                df_cat_comp['Crescimento %'] = (df_cat_comp['Diferenca R$'] / df_cat_comp['Ano_Anterior'].replace(0,1)) * 100

                st.subheader(f"1. Categorias em Queda em {MESES_PT[mes_selecionado]}")
                df_queda_cat = df_cat_comp[(df_cat_comp['Ano_Anterior'] > 0) & (df_cat_comp['Crescimento %'] < 0)].sort_values('Diferenca R$')
                if len(df_queda_cat) > 0:
                    st.error(f"{len(df_queda_cat)} categoria(s) perderam faturamento")
                    st.dataframe(df_queda_cat.style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.2f}%'}), use_container_width=True)
                else:
                    st.success(f"Todas as categorias cresceram")

                st.subheader(f"2. Categorias que Cresceram em {MESES_PT[mes_selecionado]}")
                df_cresce_cat = df_cat_comp[(df_cat_comp['Ano_Anterior'] > 0) & (df_cat_comp['Crescimento %'] > 0)].sort_values('Diferenca R$', ascending=False)
                if len(df_cresce_cat) > 0:
                    st.success(f"{len(df_cresce_cat)} categoria(s) cresceram")
                    st.dataframe(df_cresce_cat.head(10).style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.2f}%'}), use_container_width=True)

                st.subheader("3. Produtos para Investir vs Recuperar no Mês")
                col_op1, col_op2 = st.columns(2)
                with col_op1:
                    st.write("**A. Cresceram Forte >20%**")
                    df_investe = df_analise[(df_analise['Crescimento %'] > 20) & (df_analise['Ano_Atual'] > 500)].sort_values('Diferenca R$', ascending=False).head(10)
                    if len(df_investe) > 0:
                        st.dataframe(df_investe[['categoria','produto','Ano_Anterior','Ano_Atual','Diferenca R$','Crescimento %']].style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.1f}%'}), use_container_width=True)
                with col_op2:
                    st.write("**B. Caiu mas era Forte**")
                    df_recupera = df_analise[(df_analise['Ano_Anterior'] > 2000) & (df_analise['Crescimento %'] < -10)].sort_values('Diferenca R$').head(10)
                    if len(df_recupera) > 0:
                        st.dataframe(df_recupera[['categoria','produto','Ano_Anterior','Ano_Atual','Diferenca R$','Crescimento %']].style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.1f}%'}), use_container_width=True)
            except Exception as e:
                st.error(f"Erro na Analise Inteligente: {e}")
        else:
            st.info("Selecione 2 anos no filtro lateral para ver a Analise Inteligente")

        st.divider()
        st.markdown("<center>Performance de Vendas | 2025-2026</center>", unsafe_allow_html=True)
else:
    st.info("Upload dos 2.zip")
