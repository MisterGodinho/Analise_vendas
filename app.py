if len(df['ano'].unique()) > 1:
    st.divider()
    st.subheader("📉 Análise de Queda: 2026 vs 2025")

    ano_atual = df['ano'].max()
    ano_ant = df['ano'].min()

    # 1. ANÁLISE POR PRODUTO
    st.write("### Produtos em Queda")
    df_prod_ano = df.groupby(['ano','produto'])['valor'].sum().reset_index()
    df_pivot_prod = df_prod_ano.pivot(index='produto', columns='ano', values='valor').fillna(0)
    df_pivot_prod['Crescimento %'] = ((df_pivot_prod[ano_atual] - df_pivot_prod[ano_ant]) / df_pivot_prod[ano_ant]) * 100
    df_pivot_prod['Diferença R$'] = df_pivot_prod[ano_atual] - df_pivot_prod[ano_ant]

    # Pega só os que venderam no ano anterior e caíram
    df_queda_prod = df_pivot_prod[(df_pivot_prod[ano_ant] > 0) & (df_pivot_prod['Crescimento %'] < 0)].sort_values('Diferença R$')
    df_queda_prod = df_queda_prod.head(20) # Top 20 piores

    if len(df_queda_prod) > 0:
        st.dataframe(df_queda_prod[[ano_ant, ano_atual, 'Diferença R$', 'Crescimento %']].style.format({
            ano_ant:'R$ {:,.2f}', ano_atual:'R$ {:,.2f}', 'Diferença R$':'R$ {:,.2f}', 'Crescimento %':'{:.2f}%'
        }), use_container_width=True)

        fig_queda_prod = px.bar(df_queda_prod.head(10), x='Diferença R$', y=df_queda_prod.head(10).index, orientation='h')
        fig_queda_prod.update_xaxes(tickprefix='R$ ')
        fig_queda_prod.update_layout(yaxis={'categoryorder':'total ascending'}, title="Top 10 Produtos com Maior Queda em R$")
        st.plotly_chart(fig_queda_prod, use_container_width=True)
    else:
        st.success("Nenhum produto em queda forte vs ano anterior")

    # 2. ANÁLISE POR CATEGORIA
    st.write("### Categorias em Queda")
    df_cat_ano = df.groupby(['ano','categoria'])['valor'].sum().reset_index()
    df_pivot_cat = df_cat_ano.pivot(index='categoria', columns='ano', values='valor').fillna(0)
    df_pivot_cat['Crescimento %'] = ((df_pivot_cat[ano_atual] - df_pivot_cat[ano_ant]) / df_pivot_cat[ano_ant]) * 100
    df_pivot_cat['Diferença R$'] = df_pivot_cat[ano_atual] - df_pivot_cat[ano_ant]

    df_queda_cat = df_pivot_cat[(df_pivot_cat[ano_ant] > 0) & (df_pivot_cat['Crescimento %'] < 0)].sort_values('Diferença R$')

    if len(df_queda_cat) > 0:
        st.dataframe(df_queda_cat[[ano_ant, ano_atual, 'Diferença R$', 'Crescimento %']].style.format({
            ano_ant:'R$ {:,.2f}', ano_atual:'R$ {:,.2f}', 'Diferença R$':'R$ {:,.2f}', 'Crescimento %':'{:.2f}%'
        }), use_container_width=True)
    else:
        st.success("Nenhuma categoria em queda vs ano anterior")

    # 3. PRODUTOS QUE VENDEM POUCO - "CAUDA LONGA"
    st.divider()
    st.subheader("📦 Produtos com Baixo Giro")
    df_total_prod = df.groupby('produto')['valor'].sum().reset_index().sort_values('valor')
    total_fat = df_total_prod['valor'].sum()
    df_total_prod['% do Total'] = (df_total_prod['valor'] / total_fat) * 100
    df_total_prod['Qtd Vendida'] = df.groupby('produto')['valor'].count().values # conta quantas vendas

    # Pega os 20% que representam menos de 5% do faturamento
    df_cauda = df_total_prod[df_total_prod['% do Total'] < 0.5].head(50)
    st.write(f"**{len(df_cauda)} produtos** representam menos de 0.5% do faturamento cada. Total: R$ {df_cauda['valor'].sum():,.2f}")
    st.dataframe(df_cauda[['produto','valor','% do Total','Qtd Vendida']].style.format({
        'valor':'R$ {:,.2f}', '% do Total':'{:.3f}%'
    }), use_container_width=True, height=400)

    # 4. INSIGHTS AUTOMÁTICOS
    st.divider()
    st.subheader("💡 Insights para Ação")
    col1, col2 = st.columns(2)
    with col1:
        pior_prod = df_queda_prod.index[0] if len(df_queda_prod)>0 else "N/A"
        pior_cat = df_queda_cat.index[0] if len(df_queda_cat)>0 else "N/A"
        st.metric("Produto com Maior Queda", pior_prod)
        st.metric("Categoria com Maior Queda", pior_cat)
    with col2:
        qtd_prod_baixo = len(df_cauda)
        fat_baixo = df_cauda['valor'].sum()
        st.metric("Produtos com Baixo Giro", qtd_prod_baixo)
        st.metric("Faturamento Perdido na Cauda", f"R$ {fat_baixo:,.0f}")
                
