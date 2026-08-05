import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import calendar
import gc

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")

# CSS PRA FICAR IGUAL POWER BI - TAGS VERMELHAS
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1e293b; }
[data-testid="stSidebar"] label { color: #e2e8f0!important; font-weight: 600; text-transform: uppercase; font-size: 0.8rem; }
div[data-baseweb="tag"] { background-color: #ef4444!important; border-radius: 16px!important; } /* Vermelho */
div[data-baseweb="tag"] span { color: white!important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

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

    # OTIMIZAÇÃO PESADA
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce').astype('float32')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df['loja'] = df['loja'].astype(str).str.strip().astype('category')
    df['produto'] = df['produto'].astype(str).str.strip().astype('category')
    df['categoria'] = df['categoria'].astype(str).str.strip().astype('category')
    df = df.dropna(subset=['data', 'valor'])
    df = df[df['loja']!= '']
    df['ano'] = df['data'].dt.year.astype('int16')
    df['mes_num'] = df['data'].dt.month.astype('int8')
    df['mes_nome'] = df['mes_num'].map({1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'})
    return df

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    st.success(f"Carregado! {len(df):,} linhas | Memória: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

    st.sidebar.header("FILTROS")

    # FILTROS DINAMICOS ESTILO POWER BI
    anos = st.sidebar.multiselect("ANO", options=sorted(df['ano'].unique()), default=sorted(df['ano'].unique()))
    df_ano = df[df['ano'].isin(anos)] if anos else df

    meses_nome = st.sidebar.multiselect("MÊS", options=sorted(df['mes_nome'].unique()), default=sorted(df['mes_nome'].unique()))
    df_mes = df_ano[df_ano['mes_nome'].isin(meses_nome)] if meses_nome else df_ano

    # FILTRO EM CASCATA: Loja e Categoria só mostram o que tem nos filtros acima
    lojas = st.sidebar.multiselect("LOJA", options=sorted(df_mes['loja'].unique()), default=sorted(df_mes['loja'].unique()))
    df_loja = df_mes[df_mes['loja'].isin(lojas)] if lojas else df_mes

    cats = st.sidebar.multiselect("CATEGORIA", options=sorted(df_loja['categoria'].unique()), default=sorted(df_loja['categoria'].unique()))
    df_f = df_loja[df_loja['categoria'].isin(cats)] if cats else df_loja

    # Converte mes_nome de volta pra mes_num pra filtrar
    df_f = df_f[df_f['mes_num'].isin(df_f[df_f['mes_nome'].isin(meses_nome)]['mes_num'].unique())] if meses_nome else df_f

    st.sidebar.divider()
    st.sidebar.header("METAS")
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 500000.0, 150000.0, 10000.0)
    st.sidebar.metric("TOTAL REGISTROS", f"{len(df_f):,}")

    if len(df_f) > 0:
        st.divider()
        c1, c2 = st.columns(2)
        fat = df_f['valor'].sum()
        c1.metric("Faturamento", f"R$ {fat:,.0f}")
        c2.metric("Ticket Medio", f"R$ {df_f['valor'].mean():,.2f}")

        st.divider()
        st.subheader("Acompanhamento de Meta")
        ating_geral = (fat / meta_geral) * 100 if meta_geral > 0 else 0
        st.metric("Meta Geral", f"R$ {meta_geral:,.0f}", f"Atingimento: {ating_geral:.2f}%")
        st.progress(min(ating_geral/100, 1.0))

        anos_unicos = sorted(df_f['ano'].unique())
        if len(anos_unicos) > 1:
            ano1 = anos_unicos[-1]
            ano0 = anos_unicos[-2]

            st.divider()
            st.subheader("Comparativo Ano a Ano")
            dfa = df_f.groupby('ano')['valor'].sum().reset_index()
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
                dfl1 = df_f[df_f['ano']==ano1].groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                dfl1['% Total'] = (dfl1['valor'] / dfl1['valor'].sum()) * 100 if dfl1['valor'].sum() > 0 else 0
                st.dataframe(dfl1.style.format({'valor':'R$ {:,.0f}', '% Total':'{:.1f}%'}), use_container_width=True, height=400)
            with col_l2:
                st.write(f"**{ano0}**")
                dfl0 = df_f[df_f['ano']==ano0].groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                dfl0['% Total'] = (dfl0['valor'] / dfl0['valor'].sum()) * 100 if dfl0['valor'].sum() > 0 else 0
                st.dataframe(dfl0.style.format({'valor':'R$ {:,.0f}', '% Total':'{:.1f}%'}), use_container_width=True, height=400)

            st.divider()
            st.subheader("Top 10 Produtos por Ano")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.write(f"**{ano1}**")
                df_temp1 = df_f[df_f['ano']==ano1]
                dfp1 = df_temp1.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                # ADICIONADO: coluna de valor formatado
                dfp1['Valor R$'] = dfp1['valor'].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(dfp1[['produto', 'Valor R$']].rename(columns={'produto':'Produto'}), use_container_width=True, height=400)
                figp1 = px.bar(dfp1, x='valor', y='produto', orientation='h', text='Valor R$', title=f"Top 10 - {ano1}")
                figp1.update_traces(textposition='outside')
                figp1.update_xaxes(tickprefix='R$ ')
                figp1.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(figp1, use_container_width=True)
            with col_p2:
                st.write(f"**{ano0}**")
                df_temp0 = df_f[df_f['ano']==ano0]
                dfp0 = df_temp0.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                # ADICIONADO: coluna de valor formatado
                dfp0['Valor R$'] = dfp0['valor'].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(dfp0[['produto', 'Valor R$']].rename(columns={'produto':'Produto'}), use_container_width=True, height=400)
                figp0 = px.bar(dfp0, x='valor', y='produto', orientation='h', text='Valor R$', title=f"Top 10 - {ano0}")
                figp0.update_traces(textposition='outside')
                figp0.update_xaxes(tickprefix='R$ ')
                figp0.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(figp0, use_container_width=True)

            st.divider()
            st.header("ANALISE INTELIGENTE: MES A MES")
            mes_selecionado = st.selectbox("Selecione o Mês para Analisar", options=sorted(df_f['mes_num'].unique()), format_func=lambda x: calendar.month_name[x], index=0)

            try:
                df_mes0 = df_f[(df_f['ano']==ano0) & (df_f['mes_num']==mes_selecionado)].groupby(['categoria','produto'])['valor'].sum().reset_index()
                df_mes0.columns = ['categoria','produto','Ano_Anterior']
                df_mes1 = df_f[(df_f['ano']==ano1) & (df_f['mes_num']==mes_selecionado)].groupby(['categoria','produto'])['valor'].sum().reset_index()
                df_mes1.columns = ['categoria','produto','Ano_Atual']
                df_analise = pd.merge(df_mes0, df_mes1, on=['categoria','produto'], how='outer').fillna(0)
                df_analise['Diferenca R$'] = df_analise['Ano_Atual'] - df_analise['Ano_Anterior']
                df_analise['Crescimento %'] = (df_analise['Diferenca R$'] / df_analise['Ano_Anterior'].replace(0,1)) * 100

                st.subheader(f"1. Categorias em Queda em {calendar.month_name[mes_selecionado]}")
                df_cat_comp = df_analise.groupby('categoria')[['Ano_Anterior','Ano_Atual']].sum()
                df_cat_comp['Diferenca R$'] = df_cat_comp['Ano_Atual'] - df_cat_comp['Ano_Anterior']
                df_cat_comp['Crescimento %'] = (df_cat_comp['Diferenca R$'] / df_cat_comp['Ano_Anterior'].replace(0,1)) * 100
                df_queda_cat = df_cat_comp[(df_cat_comp['Ano_Anterior'] > 0) & (df_cat_comp['Crescimento %'] < 0)].sort_values('Diferenca R$')
                if len(df_queda_cat) > 0:
                    st.warning(f"Categorias que perderam faturamento em {calendar.month_name[mes_selecionado]} vs ano anterior")
                    st.dataframe(df_queda_cat.style.format({'Ano_Anterior':'R$ {:,.0f}', 'Ano_Atual':'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.2f}%'}), use_container_width=True)
                else:
                    st.success(f"Todas as categorias cresceram em {calendar.month_name[mes_selecionado]} vs ano anterior")

            except Exception as e:
                st.error(f"Erro na Analise Inteligente: {e}")
        else:
            st.info("Selecione 2 anos no filtro lateral para ver a Analise Inteligente")
    else:
        st.warning("Nenhum dado com os filtros selecionados")
else:
    st.info("Upload dos 2.zip")
