import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

st.set_page_config(page_title="Análise de Vendas", layout="wide")
st.title("📊 Análise de Vendas Gerenciais")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    mapa = {
        'Fecha':'data',
        'Tienda':'loja',
        'Categoria':'categoria',
        'Descripción artículo':'produto',
        'Importe con IVA':'valor_total',
        'Código Ae':'id_pedido'
    }

    df = df.rename(columns=mapa)
    df = df.dropna(subset=['valor_total', 'data', 'loja', 'produto'])
    df = df[df['produto']!= '']

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month
    df['mes_nome'] = df['data'].dt.month_name()
    df['dia'] = df['data'].dt.day

    # ===== FILTROS COM BOTÕES NA TELA =====
    st.subheader("🔍 Filtros Rápidos")

    # GUARDAR SELEÇÃO
    if 'ano_sel' not in st.session_state:
        st.session_state.ano_sel = df['ano'].max()
    if 'mes_sel' not in st.session_state:
        st.session_state.mes_sel = df['mes'].max()
    if 'dias_sel' not in st.session_state:
        st.session_state.dias_sel = []

    # BOTÕES DE ANO
    st.write("**Ano:**")
    col_anos = st.columns(len(df['ano'].unique()))
    for i, ano in enumerate(sorted(df['ano'].unique())):
        if col_anos[i].button(f"{ano}", key=f"ano_{ano}", use_container_width=True):
            st.session_state.ano_sel = ano
            st.session_state.mes_sel = df[df['ano']==ano]['mes'].max()

    # BOTÕES DE MÊS
    st.write("**Mês:**")
    df_ano = df[df['ano'] == st.session_state.ano_sel]
    meses_disponiveis = sorted(df_ano['mes'].unique())
    col_meses = st.columns(6) # 6 botões por linha
    for i, mes in enumerate(meses_disponiveis):
        nome_mes = calendar.month_name[mes][:3] # Jan, Fev, Mar
        if col_meses[i % 6].button(nome_mes, key=f"mes_{mes}", use_container_width=True):
            st.session_state.mes_sel = mes

    # BOTÕES DE DIAS
    st.write("**Dias:**")
    df_mes = df_ano[df_ano['mes'] == st.session_state.mes_sel]
    dias_disponiveis = sorted(df_mes['dia'].unique())

    col_dias = st.columns(7) # 7 dias por linha
    for i, dia in enumerate(dias_disponiveis):
        if col_dias[i % 7].button(f"{dia}", key=f"dia_{dia}", use_container_width=True):
            if dia in st.session_state.dias_sel:
                st.session_state.dias_sel.remove(dia) # desmarca
            else:
                st.session_state.dias_sel.append(dia) # marca

    if st.button("Limpar Dias"):
        st.session_state.dias_sel = []

    # APLICAR FILTROS
    df_filtrado = df_ano[df_ano['mes'] == st.session_state.mes_sel]
    if st.session_state.dias_sel:
        df_filtrado = df_filtrado[df_filtrado['dia'].isin(st.session_state.dias_sel)]

    df = df_filtrado

    # ===== KPIs =====
    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax() if len(df['loja'].unique()) > 0 else "-"
        categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax() if len(df['categoria'].unique()) > 0 else "-"
        valor_categoria_top = df.groupby('categoria')['valor_total'].sum().max() if len(df['categoria'].unique()) > 0 else 0
