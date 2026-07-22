import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile
import calendar

st.set_page_config(page_title="Analise do Negocio BSB", layout="wide")
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
                        # F=Tienda, G=Fecha, I=Articulo, J=Categoria, O=Importe a, Q=Importe c/Desc, N=Cantidad
                        df_temp = pd.read_excel(f, sheet_name=0, header=0, usecols='F,G,I,J,O,Q,N')
                        df_temp.columns = ['loja', 'data', 'produto', 'categoria', 'valor_cheio', 'valor_desc', 'qtd']
                    elif '.csv' in nome_arquivo:
                        # CSV: F=5, G=6, I=8, J=9, O=14, Q=16, N=13
                        df_temp = pd.read_csv(f, sep=';', usecols=[5,6,8,9,14,16,13], names=['loja','data','produto','categoria','valor_cheio','valor_desc','qtd'], header=0, encoding='latin-1', on_bad_lines='skip')
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
        df = carregar_dados(uploaded_files)

    # CONVERSAO
    df['valor_cheio'] = pd.to_numeric(df['valor_cheio'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['valor_desc'] = pd.to_numeric(df['valor_desc'].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce')
    df['qtd'] = pd.to_numeric(df['qtd'], errors='coerce').fillna(0)
    df['desconto_r$'] = df['valor_cheio'] - df['valor_desc']
    df['desconto_%'] = (df['desconto_r$'] / df['valor_cheio'].replace(0,1)) * 100

    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['data', 'valor_desc'])
    df = df[df['loja']!= '']
    df['ano'] = df['data'].dt.year
    df['mes_num'] = df['data'].dt.month
    df['mes_nome'] = df['data'].dt.month.apply(lambda x: calendar.month_name[x])

    st.sidebar.header("Filtros")
    lista_anos = sorted(df['ano'].unique())
    anos = st.sidebar.multiselect("Ano", options=lista_anos, default=lista_anos)

    lista_meses = sorted(df['mes_num'].unique())
    meses = st.sidebar.multiselect("Mês", options=lista_meses, default=lista_meses, format_func=lambda x: calendar.month_name[x])

    df_f = df[df['ano'].isin(anos)].copy()
    df_f = df_f[df_f['mes_num'].isin(meses)].copy()

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

    st.sidebar.metric("Total registros", f"{len(df_f):,}")
    df = df_f

    if len(df) > 0:
        st.divider()
        c1, c2, c3, c4 = st.columns(4) # 4 KPIs AGORA
        fat_cheio = df['valor_cheio'].sum()
        fat_desc = df['valor_desc'].sum()
        desc_total = df['desconto_r$'].sum()
        perc_desc = (desc_total / fat_cheio) * 100 if fat_cheio > 0 else 0

        c1.metric("Faturamento Cheio", f"R$ {fat_cheio:,.0f}")
        c2.metric("Faturamento Liquido", f"R$ {fat_desc:,.0f}")
        c3.metric("Total Descontos", f"R$ {desc_total:,.0f}")
        c4.metric("% Desconto Médio", f"{perc_desc:.2f}%")

        st.divider()
        st.subheader("Acompanhamento de Meta")
        ating_geral = (fat_desc / meta_geral) * 100 if meta_geral > 0 else 0
        st.metric("Meta Geral", f"R$ {meta_geral:,.0f}", f"Atingimento: {ating_geral:.2f}%")
        st.progress(min(ating_geral/100, 1.0))

        anos_unicos = sorted(df['ano'].unique())
        if len(anos_unicos) > 1:
            st.divider()
            st.subheader("Comparativo Ano a Ano - Valor Líquido")
            dfa = df.groupby('ano')['valor_desc'].sum().reset_index()
            ano1 = anos_unicos[-1]
            ano0 = anos_unicos[-2]
            f1 = dfa[dfa['ano']==ano1]['valor_desc'].sum()
            f0 = dfa[dfa['ano']==ano0]['valor_desc'].sum()
            cresc = ((f1-f0)/f0)*100 if f0>0 else 0
            x1,x2,x3 = st.columns(3)
            x1.metric(f"Ano {ano1}", f"R$ {f1:,.0f}")
            x2.metric(f"Ano {ano0}", f"R$ {f0:,.0f}")
            x3.metric("Crescimento", f"{cresc:.2f}%")
            fig = px.bar(dfa, x='ano', y='valor_desc')
            fig.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader("Ranking Top 10 Lojas - Valor Líquido")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.write(f"**{ano1}**")
                dfl1 = df[df['ano']==ano1].groupby('loja')['valor_desc'].sum().reset_index().sort_values('valor_desc', ascending=False).head(10)
                dfl1['% Total'] = (dfl1['valor_desc'] / dfl1['valor_desc'].sum()) * 100
                st.dataframe(dfl1.style.format({'valor_desc':'R$ {:,.0f}', '% Total':'{:.1f}%'}), use_container_width=True, height=400)
            with col_l2:
                st.write(f"**{ano0}**")
                dfl0 = df[df['ano']==ano0].groupby('loja')['valor_desc'].sum().reset_index().sort_values('valor_desc', ascending=False).head(10)
                dfl0['% Total'] = (dfl0['valor_desc'] / dfl0['valor_desc'].sum()) * 100
                st.dataframe(dfl0.style.format({'valor_desc':'R$ {:,.0f}', '% Total':'{:.1f}%'}), use_container_width=True, height=400)

            # ==============================================================
            # TOP 10 PRODUTOS COM TOGGLE: CHEIO vs LIQUIDO vs QTD
            # ==============================================================
            st.divider()
            st.subheader("Top 10 Produtos por Ano")

            modo_visao = st.radio("Mostrar por:", ["Valor Líquido R$", "Valor Cheio R$", "Quantidade Vendida"], horizontal=True, key="top10_toggle")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.write(f"**{ano1}**")
                df_temp1 = df[df['ano']==ano1]
                if modo_visao == "Valor Líquido R$":
                    dfp1 = df_temp1.groupby('produto').agg({'valor_desc':'sum'}).reset_index().sort_values('valor_desc', ascending=False).head(10)
                    dfp1['label'] = dfp1['valor_desc'].apply(lambda x: f'R$ {x:,.0f}')
                    y_col = 'valor_desc'
                    titulo_eixo = 'Faturamento Líquido R$'
                elif modo_visao == "Valor Cheio R$":
                    dfp1 = df_temp1.groupby('produto').agg({'valor_cheio':'sum'}).reset_index().sort_values('valor_cheio', ascending=False).head(10)
                    dfp1['label'] = dfp1['valor_cheio'].apply(lambda x: f'R$ {x:,.0f}')
                    y_col = 'valor_cheio'
                    titulo_eixo = 'Faturamento Cheio R$'
                else:
                    dfp1 = df_temp1.groupby('produto').agg({'qtd':'sum'}).reset_index().sort_values('qtd', ascending=False).head(10)
                    dfp1['label'] = dfp1['qtd'].apply(lambda x: f'{x:,.0f} un')
                    y_col = 'qtd'
                    titulo_eixo = 'Quantidade Vendida'

                figp1 = go.Figure()
                figp1.add_trace(go.Bar(y=dfp1['produto'], x=dfp1[y_col], orientation='h', text=dfp1['label'], textposition='outside'))
                figp1.update_layout(title=f"Top 10 - {ano1}", yaxis={'categoryorder':'total ascending'}, xaxis_title=titulo_eixo, height=500)
                st.plotly_chart(figp1, use_container_width=True)

            with col_p2:
                st.write(f"**{ano0}**")
                df_temp0 = df[df['ano']==ano0]
                if modo_visao == "Valor Líquido R$":
                    dfp0 = df_temp0.groupby('produto').agg({'valor_desc':'sum'}).reset_index().sort_values('valor_desc', ascending=False).head(10)
                    dfp0['label'] = dfp0['valor_desc'].apply(lambda x: f'R$ {x:,.0f}')
                    y_col = 'valor_desc'
                    titulo_eixo = 'Faturamento Líquido R$'
                elif modo_visao == "Valor Cheio R$":
                    dfp0 = df_temp0.groupby('produto').agg({'valor_cheio':'sum'}).reset_index().sort_values('valor_cheio', ascending=False).head(10)
                    dfp0['label'] = dfp0['valor_cheio'].apply(lambda x: f'R$ {x:,.0f}')
                    y_col = 'valor_cheio'
                    titulo_eixo = 'Faturamento Cheio R$'
                else:
                    dfp0 = df_temp0.groupby('produto').agg({'qtd':'sum'}).reset_index().sort_values('qtd', ascending=False).head(10)
                    dfp0['label'] = dfp0['qtd'].apply(lambda x: f'{x:,.0f} un')
                    y_col = 'qtd'
                    titulo_eixo = 'Quantidade Vendida'

                figp0 = go.Figure()
                figp0.add_trace(go.Bar(y=dfp0['produto'], x=dfp0[y_col], orientation='h', text=dfp0['label'], textposition='outside'))
                figp0.update_layout(title=f"Top 10 - {ano0}", yaxis={'categoryorder':'total ascending'}, xaxis_title=titulo_eixo, height=500)
                st.plotly_chart(figp0, use_container_width=True)

            # ==============================================================
            # NOVA ABA: ANALISE DE DESCONTOS
            # ==============================================================
            st.divider()
            st.header("ANALISE DE DESCONTOS")

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.subheader("Top 10 Produtos + Descontados R$")
                df_desc = df.groupby('produto')['desconto_r$'].sum().reset_index().sort_values('desconto_r$', ascending=False).head(10)
                st.dataframe(df_desc.style.format({'desconto_r$':'R$ {:,.0f}'}), use_container_width=True)
            with col_d2:
                st.subheader("Top 10 Produtos + Descontados %")
                df_desc_perc = df.groupby('produto').agg({'desconto_r$':'sum', 'valor_cheio':'sum'}).reset_index()
                df_desc_perc['% Desconto'] = (df_desc_perc['desconto_r$'] / df_desc_perc['valor_cheio'].replace(0,1)) * 100
                df_desc_perc = df_desc_perc[df_desc_perc['valor_cheio'] > 1000].sort_values('% Desconto', ascending=False).head(10)
                st.dataframe(df_desc_perc[['produto','% Desconto']].style.format({'% Desconto':'{:.2f}%'}), use_container_width=True)

            # ==============================================================
            # ANALISE INTELIGENTE - MES A MES
            # ==============================================================
            st.divider()
            st.header("ANALISE INTELIGENTE: MES A MES")

            mes_selecionado = st.selectbox("Selecione o Mês para Analisar",
                                           options=sorted(df['mes_num'].unique()),
                                           format_func=lambda x: calendar.month_name[x],
                                           index=0)

            tipo_analise = st.radio("Analisar por:", ["Valor Líquido", "Valor Cheio", "Quantidade"], horizontal=True, key="analise_toggle")

            try:
                coluna_analise = 'valor_desc' if tipo_analise == "Valor Líquido" else 'valor_cheio' if tipo_analise == "Valor Cheio" else 'qtd'
                sufixo = 'R$' if tipo_analise!= "Quantidade" else ''

                df_mes0 = df[(df['ano']==ano0) & (df['mes_num']==mes_selecionado)].groupby(['categoria','produto'])[coluna_analise].sum().reset_index()
                df_mes0.columns = ['categoria','produto','Ano_Anterior']

                df_mes1 = df[(df['ano']==ano1) & (df['mes_num']==mes_selecionado)].groupby(['categoria','produto'])[coluna_analise].sum().reset_index()
                df_mes1.columns = ['categoria','produto','Ano_Atual']

                df_analise = pd.merge(df_mes0, df_mes1, on=['categoria','produto'], how='outer').fillna(0)

                df_analise['Diferenca'] = df_analise['Ano_Atual'] - df_analise['Ano_Anterior']
                df_analise['Crescimento %'] = (df_analise['Diferenca'] / df_analise['Ano_Anterior'].replace(0,1)) * 100

                st.subheader(f"1. Categorias em Queda em {calendar.month_name[mes_selecionado]} - {tipo_analise}")
                df_cat_comp = df_analise.groupby('categoria')[['Ano_Anterior','Ano_Atual']].sum()
                df_cat_comp['Diferenca'] = df_cat_comp['Ano_Atual'] - df_cat_comp['Ano_Anterior']
                df_cat_comp['Crescimento %'] = (df_cat_comp['Diferenca'] / df_cat_comp['Ano_Anterior'].replace(0,1)) * 100
                df_queda_cat = df_cat_comp[(df_cat_comp['Ano_Anterior'] > 0) & (df_cat_comp['Crescimento %'] < 0)].sort_values('Diferenca')

                if len(df_queda_cat) > 0:
                    st.warning(f"Categorias que perderam {tipo_analise.lower()} em {calendar.month_name[mes_selecionado]} vs ano anterior")
                    formato = {'Ano_Anterior':f'{sufixo} {{:,.0f}}', 'Ano_Atual':f'{sufixo} {{:,.0f}}', 'Diferenca':f'{sufixo} {{:,.0f}}', 'Crescimento %':'{{:.2f}}%'}
                    st.dataframe(df_queda_cat.style.format(formato), use_container_width=True)
                else:
                    st.success(f"Todas as categorias cresceram em {calendar.month_name[mes_selecionado]} vs ano anterior")

            except Exception as e:
                st.error(f"Erro na Analise Inteligente: {e}")
        else:
            st.info("Selecione 2 anos no filtro lateral para ver a Analise Inteligente")

        st.divider()
        st.markdown("<center>Performance de Vendas | 2025-2026</center>", unsafe_allow_html=True)
else:
    st.info("Upload dos 2.zip")
