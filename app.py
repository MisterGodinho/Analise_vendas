import streamlit as st
import pandas as pd
import plotly.express as px
import zipfile
import calendar

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")
st.title("Analise do Negocio BSB")
st.caption("Performance de Vendas | 2025-2026")

uploaded_files = st.file_uploader("1. Selecione 2025.zip e 2026.zip", type=['zip'], accept_multiple_files=True)

@st.cache_data(show_spinner="Carregando 29MB... Aguarde 2 min")
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
                    df_temp['loja'] = df_temp['loja'].astype(str).str.strip()
                    df_temp['produto'] = df_temp['produto'].astype(str).str.strip()
                    df_temp['categoria'] = df_temp['categoria'].astype(str).str.strip()
                    lista_df.append(df_temp)
    if len(lista_df) == 0:
        return pd.DataFrame()
    return pd.concat(lista_df, ignore_index=True) # AQUI ESTAVA CORTADO

if uploaded_files and len(uploaded_files) >= 2:
    df = carregar_dados(uploaded_files)
    df['valor'] = pd.to_numeric(df['valor'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor'])
    df = df[df['loja']!= '']
    df['ano'] = df['data'].dt.year
    df['mes_num'] = df['data'].dt.month
    df['mes_nome'] = df['data'].dt.month.apply(lambda x: calendar.month_name[x]) # NOME DO MÊS

    st.sidebar.header("Filtros")

    lista_anos = sorted(df['ano'].unique())
    anos = st.sidebar.multiselect("Ano", options=lista_anos, default=lista_anos)

    lista_meses = sorted(df['mes_num'].unique()) # FILTRO NOVO DE MÊS
    meses = st.sidebar.multiselect("Mês", options=lista_meses, default=lista_meses, format_func=lambda x: calendar.month_name[x])

    df_f = df[df['ano'].isin(anos)].copy()
    df_f = df_f[df_f['mes_num'].isin(meses)].copy() # APLICA FILTRO DE MÊS

    lista_lojas = sorted(df_f['loja'].unique())
    lojas = st.sidebar.multiselect("Loja", options=lista_lojas, default=lista_lojas)
    if len(lojas) > 0:
        df_f = df_f[df_f['loja'].isin(lojas)]

    lista_cats = sorted(df_f['categoria'].unique())
    cats = st.sidebar.multiselect("Categoria", options=lista_cats, default=lista_cats)
    if len(cats) > 0:
        df_f = df_f[df_f['categoria'].isin(cats)]

    st.sidebar.divider()
    st.sidebar.header("Metas")
    meta_geral = st.sidebar.number_input("Meta Geral R$", 0.0, 500000.0, 150000.0, 100000.0)

    st.sidebar.subheader("Meta por Loja")
    dict_meta_loja = {}
    lista_lojas_meta = sorted(df['loja'].unique())
    for loja in lista_lojas_meta:
        valor = st.sidebar.number_input(f"Meta {loja}", 0.0, 500000.0, 0.0, 100000.0, key=f"meta_{loja}")
        if valor > 0:
            dict_meta_loja = valor

    st.sidebar.metric("Total registros", f"{len(df_f):,}")
    df = df_f

    if len(df) > 0:
        st.divider()
        c1, c2 = st.columns(2)
        fat = df['valor'].sum()
        c1.metric("Faturamento", f"R$ {fat:,.0f}")
        c2.metric("Ticket Medio", f"R$ {df['valor'].mean():,.2f}")

        st.divider()
        st.subheader("Acompanhamento de Meta")
        ating_geral = (fat / meta_geral) * 100 if meta_geral > 0 else 0
        st.metric("Meta Geral", f"R$ {meta_geral:,.0f}", f"Atingimento: {ating_geral:.2f}%")
        st.progress(min(ating_geral/100, 1.0))

        if len(dict_meta_loja) > 0:
            st.subheader("Performance por Loja com Meta")
            dfm = df.groupby('loja')['valor'].sum().reset_index()
            dfm['Meta'] = dfm['loja'].map(dict_meta_loja).fillna(0)
            dfm = dfm[dfm['Meta'] > 0]
            dfm['% Ating'] = (dfm['valor'] / dfm['Meta']) * 100
            dfm = dfm.sort_values('% Ating', ascending=False)
            st.dataframe(dfm.style.format({'valor':'R$ {:,.2f}','Meta':'R$ {:,.2f}','% Ating':'{:.2f}%'}), use_container_width=True, hide_index=True)

        if len(df['ano'].unique()) > 1:
            st.divider()
            st.subheader("Comparativo Ano a Ano")
            dfa = df.groupby('ano')['valor'].sum().reset_index()
            ano1 = dfa['ano'].max()
            ano0 = dfa['ano'].min()
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
            st.subheader("Top 10 Produtos por Ano")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.write(f"**{ano1}**")
                df_temp1 = df[df['ano']==ano1]
                dfp1 = df_temp1.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                figp1 = px.bar(dfp1, x='valor', y='produto', orientation='h', title=f"Top 10 - {ano1}")
                figp1.update_xaxes(tickprefix='R$ ')
                figp1.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(figp1, use_container_width=True)
            with col_p2:
                st.write(f"**{ano0}**")
                df_temp0 = df[df['ano']==ano0]
                dfp0 = df_temp0.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                figp0 = px.bar(dfp0, x='valor', y='produto', orientation='h', title=f"Top 10 - {ano0}")
                figp0.update_xaxes(tickprefix='R$ ')
                figp0.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(figp0, use_container_width=True)

            st.divider()
            st.subheader("Melhor Loja por Ano")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.write(f"**{ano1}**")
                df_temp1 = df[df['ano']==ano1]
                dfl1 = df_temp1.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                melhor1 = dfl1.iloc[0]
                st.success(f"🏆 **{melhor1['loja']}**: R$ {melhor1['valor']:,.0f}")
                figl1 = px.bar(dfl1, x='loja', y='valor', title=f"Top Lojas - {ano1}")
                figl1.update_yaxes(tickprefix='R$ ')
                figl1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(figl1, use_container_width=True)
            with col_l2:
                st.write(f"**{ano0}**")
                df_temp0 = df[df['ano']==ano0]
                dfl0 = df_temp0.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False).head(10)
                melhor0 = dfl0.iloc[0]
                st.success(f"🏆 **{melhor0['loja']}**: R$ {melhor0['valor']:,.0f}")
                figl0 = px.bar(dfl0, x='loja', y='valor', title=f"Top Lojas - {ano0}")
                figl0.update_yaxes(tickprefix='R$ ')
                figl0.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(figl0, use_container_width=True)

            st.divider()
            st.subheader("Ranking Completo: Mais Vendidos → Menos Vendidos")
            tab1, tab2 = st.tabs(["Ranking de Produtos", "Ranking de Lojas"])
            with tab1:
                st.write("**Todos os Produtos ordenados por Faturamento**")
                df_rank_prod = df.groupby('produto')['valor'].sum().reset_index().sort_values('valor', ascending=False)
                df_rank_prod['% do Total'] = (df_rank_prod['valor'] / df_rank_prod['valor'].sum()) * 100
                df_rank_prod['Posição'] = range(1, len(df_rank_prod) + 1)
                st.dataframe(df_rank_prod[['Posição','produto','valor','% do Total']].style.format({'valor':'R$ {:,.2f}','% do Total':'{:.2f}%'}), use_container_width=True, hide_index=True, height=400)
            with tab2:
                st.write("**Todas as Lojas ordenadas por Faturamento**")
                df_rank_loja = df.groupby('loja')['valor'].sum().reset_index().sort_values('valor', ascending=False)
                df_rank_loja['% do Total'] = (df_rank_loja['valor'] / df_rank_loja['valor'].sum()) * 100
                df_rank_loja['Posição'] = range(1, len(df_rank_loja) + 1)
                st.dataframe(df_rank_loja[['Posição','loja','valor','% do Total']].style.format({'valor':'R$ {:,.2f}','% do Total':'{:.2f}%'}), use_container_width=True, hide_index=True, height=400)

            # ==============================================================
            # ACRESCIMO 1: ANALISE DETALHADA ANO ANTERIOR
            # ==============================================================
            st.divider()
            st.header("ANALISE INTELIGENTE: ANO ATUAL vs ANO ANTERIOR")
            df_comp = df.groupby(['ano','categoria','produto'])['valor'].sum().reset_index()
            df_pivot = df_comp.pivot_table(index=['categoria','produto'], columns='ano', values='valor', aggfunc='sum').fillna(0)
            df_pivot['Crescimento %'] = ((df_pivot - df_pivot) / df_pivot.replace(0,1)) * 100
            df_pivot['Diferenca R$'] = df_pivot - df_pivot

            # ==============================================================
            # ACRESCIMO 2: CATEGORIAS EM QUEDA
            # ==============================================================
            st.subheader("1. Categorias em Queda")
            df_cat_comp = df_pivot.reset_index().groupby('categoria')[[ano0, ano1]].sum()
            df_cat_comp['Crescimento %'] = ((df_cat_comp - df_cat_comp) / df_cat_comp.replace(0,1)) * 100
            df_cat_comp['Diferenca R$'] = df_cat_comp - df_cat_comp
            df_queda_cat = df_cat_comp[(df_cat_comp > 0) & (df_cat_comp['Crescimento %'] < 0)].sort_values('Diferenca R$')
            if len(df_queda_cat) > 0:
                st.warning("Foco de Atencao: Categorias que perderam faturamento")
                st.dataframe(df_queda_cat[[ano0, ano1, 'Diferenca R$', 'Crescimento %']].style.format({ano0:'R$ {:,.0f}', ano1:'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.2f}%'}), use_container_width=True)
            else:
                st.success("Nenhuma categoria em queda no periodo filtrado")

            # ==============================================================
            # ACRESCIMO 3: OPORTUNIDADE DE MELHORIA VENDA DOS PRODUTOS
            # ==============================================================
            st.subheader("2. Oportunidade de Melhoria de Venda dos Produtos")
            col_op1, col_op2 = st.columns(2)
            with col_op1:
                st.write("**A. Produtos para Investir: Cresceram Forte**")
                df_investe = df_pivot[(df_pivot['Crescimento %'] > 20) & (df_pivot > 1000)].sort_values('Diferenca R$', ascending=False).head(10)
                if len(df_investe) > 0:
                    st.dataframe(df_investe[[ano0, ano1, 'Diferenca R$', 'Crescimento %']].style.format({ano0:'R$ {:,.0f}', ano1:'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.1f}%'}))
                    st.caption("Acao: Aumentar estoque, divulgar e dar destaque. Ja estao em alta.")
            with col_op2:
                st.write("**B. Produtos para Recuperar: Caiu mas era Forte**")
                df_recupera = df_pivot[(df_pivot > 5000) & (df_pivot['Crescimento %'] < -10)].sort_values('Diferenca R$').head(10)
                if len(df_recupera) > 0:
                    st.dataframe(df_recupera[[ano0, ano1, 'Diferenca R$', 'Crescimento %']].style.format({ano0:'R$ {:,.0f}', ano1:'R$ {:,.0f}', 'Diferenca R$':'R$ {:,.0f}', 'Crescimento %':'{:.1f}%'}))
                    st.caption("Acao: Fazer promocao, bundle, treinar equipe. Potencial de recuperar R$.")

        st.divider()
        st.markdown("<center>Performance de Vendas | 2025-2026</center>", unsafe_allow_html=True)
else:
    st.info("Upload dos 2.zip")
