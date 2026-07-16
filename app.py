import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar
from io import BytesIO

st.set_page_config(page_title="Dashboard Gerencial", layout="wide")

st.markdown("""
<style>
.kpi-box { background-color: #262730; border-left: 4px solid #00FF7F; padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; }
.kpi-label { font-size: 11px; color: #AAAAAA; margin-bottom: 2px; text-transform: uppercase; }
.kpi-value { font-size: 16px; font-weight: bold; color: white; }
.alerta { background-color: #FF4444; padding: 10px; border-radius: 6px; color: white; font-weight: bold; margin-bottom: 10px; }
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
        meta = st.sidebar.number_input(loja, value=valor_padrao, step=5000.0, key="meta_{}".format(i))
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

        periodo = "{}/{}".format(calendar.month_name[meses[0]], anos[0])
        if len(dias) == 1: periodo = "{} de {}".format(int(dias[0]), periodo)
        st.markdown('<h3>{} {} - {}</h3>'.format(cor, status, periodo), unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='kpi-box'><div class='kpi-label'>💰 Faturamento</div><div class='kpi-value'>R$ {:,.0f}</div></div>".format(faturamento), unsafe_allow_html=True)
            st.markdown("<div class='kpi-box'><div class='kpi-label'>🎯 Meta Geral</div><div class='kpi-value'>R$ {:,.0f}</div></div>".format(meta_geral), unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='kpi-box'><div class='kpi-label'>📈 Atingimento</div><div class='kpi-value'>{:.1f}%</div></div>".format(atingimento_geral), unsafe_allow_html=True)
            st.markdown("<div class='kpi-box'><div class='kpi-label'>🧾 Ticket Médio</div><div class='kpi-value'>R$ {:.2f}</div></div>".format(ticket_medio), unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='kpi-box'><div class='kpi-label'>🛒 Qtd. Vendas</div><div class='kpi-value'>{:,}</div></div>".format(qtd_vendas), unsafe_allow_html=True)
            st.markdown("<div class='kpi-box'><div class='kpi-label'>🏆 Melhor Loja</div><div class='kpi-value'>{}</div></div>".format(melhor_loja), unsafe_allow_html=True)

        st.markdown("<div class='kpi-box'><div class='kpi-label'>⭐ Categoria Top</div><div class='kpi-value'>{}</div></div>".format(categoria_top), unsafe_allow_html=True)
        st.progress(min(atingimento_geral/100, 1.0))
        st.divider()

        st.subheader("📊 Performance por Loja")
        df_loja = df.groupby('loja')['valor_total'].sum().reset_index()
        df_metas = pd.DataFrame(metas_loja_lista)
        df_loja = df_loja.merge(df_metas, on='loja', how='left')
        df_loja['Atingimento %'] = (df_loja['valor_total'] / df_loja['Meta'] * 100).round(1)
        df_loja['Status'] = df_loja['Atingimento %'].apply(lambda x: '🟢' if x >= 100 else '🟡' if x >= 80 else '🔴')
        df_loja = df_loja.sort_values('Atingimento %', ascending=False)

        # ALERTA
        lojas_criticas = df_loja[df_loja['Atingimento %'] < 80]
        if not lojas_criticas.empty:
            st.markdown("<div class='alerta'>⚠️ ALERTA: Lojas abaixo de 80% da meta</div>", unsafe_allow_html=True)
            for _, row in lojas_criticas.iterrows():
                st.warning("{}: {}% da meta".format(row['loja'], row['Atingimento %']))

        col_tab, col_graf = st.columns([1, 1.5])
        with col_tab:
            df_show = df_loja.copy()
            df_show['Faturamento'] = df_show['valor_total'].apply(lambda x: "R$ {:,.0f}".format(x))
            df_show['Meta'] = df_show['Meta'].apply(lambda x: "R$ {:,.0f}".format(x))

            st.dataframe(df_show[['Status', 'loja', 'Faturamento', 'Meta', 'Atingimento %']], use_container_width=True, hide_index=True, height=400)

            # BOTÃO EXCEL
            excel_data = to_excel(df_show[['Status', 'loja', 'Faturamento', 'Meta', 'Atingimento %']])
            st.download_button(
                label="📥 Baixar Tabela Excel",
                data=excel_data,
                file_name="performance_lojas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col_graf:
            fig_meta_loja = go.Figure()
            fig_meta_loja.add_trace(go.Bar(x=df_loja['loja'], y=df_loja['Meta'], name='Meta', marker_color='gray', opacity=0.5))
            fig_meta_loja.add_trace(go.Bar(x=df_loja['loja'], y=df_loja['valor_total'], name='Realizado', marker_color='#00FF7F'))
            fig_meta_loja.update_layout(title="Meta vs Realizado por Loja", barmode='group', yaxis_tickprefix='R$ ', height=400)
            st.plotly_chart(fig_meta_loja, use_container_width=True)

        st.divider()
        tab1, tab2 = st.tabs(["📈 Faturamento por Dia", "📦 Top 10 Produtos"])
        with tab1:
            fat_dia = df.groupby('dia')['valor_total'].sum().reset_index()
            fig_dia = px.line(fat_dia, x='dia', y='valor_total', title="Faturamento por Dia", markers=True)
            fig_dia.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig_dia, use_container_width=True)
        with tab2:
            top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index()
            top_produtos['produto'] = top_produtos['produto'].str.wrap(18)
            fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h')
            fig3.update_layout(height=400, margin=dict(l=130))
            fig3.update_traces(texttemplate='R$ %{x:,.0f}', textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
else:
    st.info("👆 Faça upload do arquivo Excel")
