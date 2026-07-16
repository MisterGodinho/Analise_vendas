import streamlit as st
import pandas as pd
import plotly.express as px
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

st.title("Dashboard Gerencial")

uploaded_file = st.file_uploader("Carregue seu Excel aqui", type=["xlsx"])

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Performance')
    return output.getvalue()

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0, header=0)
    df.columns = df.columns.str.strip()

    mapa = {
        'Fecha':'data',
        'Tienda':'loja',
        'Categoria':'categoria',
        'Descripción artículo':'produto',
        'Importe con IVA':'valor_total'
    }
    df = df.rename(columns=mapa)
    df['id_pedido'] = df.index.astype(str) + df['data'].astype(str)

    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
    df['categoria'] = df['categoria'].fillna('Sem Categoria')
    df = df.dropna(subset=['data', 'valor_total', 'loja', 'produto'])

    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month
    df['dia'] = df['data'].dt.day.astype(int)

    st.sidebar.header("Filtros")

    anos_disponiveis = sorted(df['ano'].unique())
    anos = st.sidebar.multiselect("Ano", anos_disponiveis, default=anos_disponiveis)
    df_temp = df[df['ano'].isin(anos)]

    meses_disponiveis = sorted(df_temp['mes'].unique())
    meses = st.sidebar.multiselect("Mes", meses_disponiveis, format_func=lambda x: calendar.month_name[x], default=meses_disponiveis)
    df_temp = df_temp[df_temp['mes'].isin(meses)]

    dias_disponiveis = sorted(df_temp['dia'].unique())
    dias = st.sidebar.multiselect("Dia", dias_disponiveis, default=dias_disponiveis)
    df_temp = df_temp[df_temp['dia'].isin(dias)]

    lojas_disponiveis = sorted(df_temp['loja'].unique())
    lojas = st.sidebar.multiselect("Loja", lojas_disponiveis, default=lojas_disponiveis)
    df_temp = df_temp[df_temp['loja'].isin(lojas)]

    categorias_disponiveis = sorted(df_temp['categoria'].unique())
    categorias = st.sidebar.multiselect("Categoria", categorias_disponiveis, default=categorias_disponiveis)
    df = df_temp[df_temp['categoria'].isin(categorias)]

    with st.sidebar.expander("Ver selecao atual"):
        st.write("Anos: " + str(len(anos)))
        st.write("Meses: " + str(len(meses)))
        st.write("Dias: " + str(len(dias)))
        st.write("Lojas: " + str(len(lojas)))
        st.write("Categorias: " + str(len(categorias)))

    st.sidebar.divider()
    mostrar_metas = st.sidebar.checkbox("Mostrar Metas", value=True)

    meta_geral = 0
    metas_loja_lista = []
    if mostrar_metas:
        st.sidebar.subheader("Metas")
        meta_geral = st.sidebar.number_input("Meta Geral R$", value=500000.0, step=10000.0)

        st.sidebar.write("Meta por Loja")
        valor_padrao = meta_geral / len(lojas_disponiveis) if len(lojas_disponiveis) > 0 else 0

        for i, loja in enumerate(lojas_disponiveis):
            col1, col2 = st.sidebar.columns([1, 2])
            with col1:
                marcar = st.checkbox(loja, value=True, key=f"check_{i}")
            with col2:
                meta = st.number_input("R$", value=valor_padrao, step=5000.0, key=f"meta_{i}", label_visibility="collapsed")

            if marcar:
                metas_loja_lista.append({'loja': loja, 'Meta': meta})

    if len(df) > 0:
        faturamento = df['valor_total'].sum()
        ticket_medio = df['valor_total'].mean()
        qtd_vendas = df['id_pedido'].nunique()

        atingimento_geral = 0
        if mostrar_metas and meta_geral > 0:
            atingimento_geral = (faturamento / meta_geral * 100)

        melhor_loja = df.groupby('loja')['valor_total'].sum().idxmax()
        categoria_top = df.groupby('categoria')['valor_total'].sum().idxmax()

        periodo = str(len(anos)) + " Ano(s)"
        if len(meses) == 1 and len(anos) == 1:
            periodo = calendar.month_name[meses[0]] + "/" + str(anos[0])
        if len(dias) == 1:
            periodo = str(int(dias[0])) + " de " + periodo

        if mostrar_metas:
            if atingimento_geral >= 100: status = "Meta Batida"
            elif atingimento_geral >= 80: status = "Atencao"
            else: status = "Abaixo da Meta"
            st.markdown("<h3>" + status + " - " + periodo + "</h3>", unsafe_allow_html=True)
        else:
            st.markdown("<h3>Analise - " + periodo + "</h3>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='kpi-box'><div class='kpi-label'>FATURAMENTO</div><div class='kpi-value'>R$ {:,.0f}</div></div>".format(faturamento), unsafe_allow_html=True)
            if mostrar_metas:
                st.markdown("<div class='kpi-box'><div class='kpi-label'>META GERAL</div><div class='kpi-value'>R$ {:,.0f}</div></div>".format(meta_geral), unsafe_allow_html=True)
        with col2:
            if mostrar_metas:
                st.markdown("<div class='kpi-box'><div class='kpi-label'>ATINGIMENTO</div><div class='kpi-value'>{:.1f}%</div></div>".format(atingimento_geral), unsafe_allow_html=True)
            st.markdown("<div class='kpi-box'><div class='kpi-label'>TICKET MEDIO</div><div class='kpi-value'>R$ {:.2f}</div></div>".format(ticket_medio), unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='kpi-box'><div class='kpi-label'>QTD. VENDAS</div><div class='kpi-value'>{:,}</div></div>".format(qtd_vendas), unsafe_allow_html=True)
            st.markdown("<div class='kpi-box'><div class='kpi-label'>MELHOR LOJA</div><div class='kpi-value'>{}</div></div>".format(melhor_loja), unsafe_allow_html=True)

        st.markdown("<div class='kpi-box'><div class='kpi-label'>CATEGORIA TOP</div><div class='kpi-value'>{}</div></div>".format(categoria_top), unsafe_allow_html=True)

        if mostrar_metas:
            st.progress(min(atingimento_geral/100, 1.0))

        st.divider()
        st.subheader("Performance por Loja")
        df_loja = df.groupby('loja')['valor_total'].sum().reset_index()

        if mostrar_metas and len(metas_loja_lista) > 0:
            df_metas = pd.DataFrame(metas_loja_lista)
            df_loja = df_loja.merge(df_metas, on='loja', how='left')
            df_loja['Atingimento %'] = (df_loja['valor_total'] / df_loja['Meta'] * 100).round(1)
            df_loja = df_loja.sort_values('Atingimento %', ascending=False)

            lojas_criticas = df_loja[df_loja['Atingimento %'] < 80]
            if not lojas_criticas.empty:
                st.markdown("<div class='alerta'>ALERTA: Lojas abaixo de 80% da meta</div>", unsafe_allow_html=True)

            col_tab, col_graf = st.columns([1, 1.5])
            with col_tab:
                df_show = df_loja.copy()
                df_show['Faturamento'] = df_show['valor_total'].apply(lambda x: "R$ {:,.0f}".format(x))
                df_show['Meta'] = df_show['Meta'].apply(lambda x: "R$ {:,.0f}".format(x) if pd.notna(x) else "-")
                st.dataframe(df_show[['loja', 'Faturamento', 'Meta', 'Atingimento %']], use_container_width=True, hide_index=True, height=400)
                excel_data = to_excel(df_show[['loja', 'Faturamento', 'Meta', 'Atingimento %']])
                st.download_button(label="Baixar Tabela Excel", data=excel_data, file_name="performance_lojas.xlsx")

            with col_graf:
                fig_meta_loja = px.bar(df_loja, x='loja', y=['Meta', 'valor_total'], title="Meta vs Realizado", barmode='group')
                fig_meta_loja.update_yaxes(tickprefix='R$ ')
                st.plotly_chart(fig_meta_loja, use_container_width=True)
        else:
            df_loja = df_loja.sort_values('valor_total', ascending=False)
            df_show = df_loja.copy()
            df_show['Faturamento'] = df_show['valor_total'].apply(lambda x: "R$ {:,.0f}".format(x))
            st.dataframe(df_show[['loja', 'Faturamento']], use_container_width=True, hide_index=True, height=400)
            fig_simples = px.bar(df_loja, x='loja', y='valor_total', title="Faturamento por Loja")
            fig_simples.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig_simples, use_container_width=True)

        st.divider()
        tab1, tab2 = st.tabs(["Faturamento por Dia", "Top 10 Produtos"])
        with tab1:
            fat_dia = df.groupby('dia')['valor_total'].sum().reset_index()
            fig_dia = px.line(fat_dia, x='dia', y='valor_total', title="Faturamento por Dia", markers=True)
            fig_dia.update_yaxes(tickprefix='R$ ')
            st.plotly_chart(fig_dia, use_container_width=True)
        with tab2:
            top_produtos = df.groupby('produto')['valor_total'].sum().nlargest(10).reset_index().sort_values('valor_total', ascending=True)
            top_produtos['produto'] = top_produtos['produto'].str.wrap(22)

            fig3 = px.bar(top_produtos, x='valor_total', y='produto', orientation='h', title="Top 10 Produtos", text='valor_total')
            fig3.update_layout(height=450, margin=dict(l=160, r=80, t=40, b=40))
            fig3.update_traces(texttemplate='R$ %{x:,.0f}', textposition='outside', cliponaxis=False)
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.error("Nenhum dado encontrado com os filtros selecionados.")
else:
    st.info("Faca upload do arquivo Excel")
