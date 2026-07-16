import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import base64

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

st.markdown("""
<style>
.kpi-box { background-color: #262730; border-left: 4px solid #00FF7F; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; }
.kpi-label { font-size: 11px; color: #AAAAAA; margin-bottom: 2px; text-transform: uppercase; }
.kpi-value { font-size: 16px; font-weight: bold; color: white; }
.alerta { background-color: #FF4444; padding: 10px; border-radius: 6px; color: white; font-weight: bold; }
h3 { font-size: 18px!important; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Gerencial")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Performance')
    return output.getvalue()

def create_pdf(faturamento, atingimento, melhor_loja, df_loja):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 50, "Relatório Gerencial")
    c.setFont("Helvetica", 10)
    c.drawString(30, height - 70, f"Faturamento: R$ {faturamento:,.0f}")
    c.drawString(30, height - 85, f"Atingimento Geral: {atingimento:.1f}%")
    c.drawString(30, height - 100, f"Melhor Loja: {melhor_loja}")
    y = height - 130
    c.drawString(30, y, "Performance por Loja:")
    y -= 20
    for index, row in df_loja.iterrows():
        c.drawString(30, y, f"{row['loja']}: R$ {row['valor_total']:,.0f} | Meta: R$ {row['Meta']:,.0f} | {row['Atingimento %']}%")
        y -= 15
        if y < 50: break
    c.save()
    return buffer.getvalue()

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    mapa = {'Fecha':'data','Tienda':'loja','Categoria':'categoria','Descripción artículo':'produto','Importe con IVA':'valor_total','Código Ae':'id_pedido'}
    df = df.rename(columns=mapa)
    if 'id_pedido' not in df.columns: df['id_pedido'] = df.index

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month
    df['dia'] = df['data'].dt.day.astype(int)

    st.sidebar.header("🔍 Filtros")
    anos = st.sidebar.multiselect("Ano", sorted(df['ano'].unique()), default=[df['ano'].max()])
    df_filtro = df[df['ano'].isin(anos)]

    meses_disponiveis = sorted(df_filtro['mes'].unique())
    meses = st.sidebar.multiselect("Mês", meses_disponiveis, format_func=lambda x: calendar.month_name[x], default=[meses_disponiveis[-1]])
    df_filtro = df_filtro[df_filtro['mes'].isin(meses)]

    dias_disponiveis = sorted(df_filtro['dia'].unique())
    dias = st.sidebar.multiselect("Dia", dias_disponiveis, default=dias_disponiveis)
    if len(dias) == 0: dias = dias_disponiveis
    df_filtro = df_filtro[df_filtro['dia'].isin(dias)]

    lojas_disponiveis = sorted(df_filtro['loja'].unique())
    lojas = st.sidebar.multiselect("Loja", lojas_disponiveis, default=lojas_disponiveis)
    if len(lojas) == 0: lojas = lojas_disponiveis
    df_filtro = df_filtro[df_filtro['loja'].isin(lojas)]
    df = df_filtro

    st.sidebar.divider()
    st.sidebar.subheader("🎯 Metas")
    meta_geral = st.sidebar.number_input("Meta Geral R$", value=500000.0, step=10000.0)

    st.sidebar.write("**Meta por Loja**")
    metas_loja_lista = []
    valor_padrao = meta_geral / len(lojas_disponiveis) if len(lojas_disponiveis) > 0 else 0
    for i, loja in enumerate(lojas_disponiveis):
        meta = st.sidebar.number_input(loja, value=valor_padrao, step=5000.0, key=f"meta_{i}")
        metas_loja_lista.append({'loja': loja, 'Meta': meta})

    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        qtd_vendas = df['id_pedido'].nunique()
        atingimento_geral = (faturamento / meta_geral * 100) if meta_geral > 0 else 0

        melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax()
        categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax()

        if atingimento_geral >= 100: cor, status = "🟢", "Meta Batida"
        elif atingimento_geral >= 80: cor, status = "🟡", "Atenção"
        else: cor, status = "🔴", "Abaixo da Meta"

        periodo = f"{calendar.month_name[meses[0]]}/{anos[0]}"
        if len(dias) == 1: periodo = f"{int(dias[0])} de {periodo}"
        st.markdown(f"<h3>{cor} {status} - {periodo}</h3>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='kpi-box'><div class='kpi-label'>💰 Faturamento</div><div class='kpi-value'>R$ {faturamento:,.0f}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-box'><div class='kpi-label'>🎯 Meta Geral</div><div class='kpi-value'>R$ {meta_geral:,.0f}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"
