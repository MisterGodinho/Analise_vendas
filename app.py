if df_filtrado.empty:
    st.warning("Faça upload de um arquivo para começar")
else:
    # ... todo seu código atual de KPIs, gráficos ...

    # COLE AQUI EMBAIXO - ANÁLISE DE QUEDA
    if len(df_filtrado['ano'].unique()) > 1:
        st.divider()
        st.subheader("📉 Análise de Queda: Ano Atual vs Ano Anterior")

        ano_atual = df_filtrado['ano'].max()
        ano_ant = df_filtrado['ano'].min()

        # 1. PRODUTOS EM QUEDA
        st.write("### Produtos em Queda")
        df_prod_ano = df_filtrado.groupby(['ano','produto'])['valor'].sum().reset_index()
        df_pivot_prod = df_prod_ano.pivot(index='produto', columns='ano', values='valor').fillna(0)
        df_pivot_prod['Crescimento %'] = ((df_pivot_prod[ano_atual] - df_pivot_prod[ano_ant]) / df_pivot_prod[ano_ant].replace(0,1)) * 100
        df_pivot_prod['Diferença R$'] = df_pivot_prod[ano_atual] - df_pivot_prod[ano_ant]

        df_queda_prod = df_pivot_prod[(df_pivot_prod[ano_ant] > 0) & (df_pivot_prod['Crescimento %'] < 0)].sort_values('Diferença R$').head(20)

        if len(df_queda_prod) > 0:
            st.dataframe(df_queda_prod[[ano_ant, ano_atual, 'Diferença R$', 'Crescimento %']].style.format({
                ano_ant:'R$ {:,.2f}', ano_atual:'R$ {:,.2f}', 'Diferença R$':'R$ {:,.2f}', 'Crescimento %':'{:.2f}%'
            }), use_container_width=True)
        else:
            st.success(f"Nenhum produto em queda de {ano_ant} para {ano_atual}")

        # 2. CATEGORIAS EM QUEDA
        st.write("### Categorias em Queda")
        df_cat_ano = df_filtrado.groupby(['ano','categoria'])['valor'].sum().reset_index()
        df_pivot_cat = df_cat_ano.pivot(index='categoria', columns='ano', values='valor').fillna(0)
        df_pivot_cat['Crescimento %'] = ((df_pivot_cat[ano_atual] - df_pivot_cat[ano_ant]) / df_pivot_cat[ano_ant].replace(0,1)) * 100
        df_pivot_cat['Diferença R$'] = df_pivot_cat[ano_atual] - df_pivot_cat[ano_ant]
        df_queda_cat = df_pivot_cat[(df_pivot_cat[ano_ant] > 0) & (df_pivot_cat['Crescimento %'] < 0)].sort_values('Diferença R$')

        if len(df_queda_cat) > 0:
            st.dataframe(df_queda_cat[[ano_ant, ano_atual, 'Diferença R$', 'Crescimento %']].style.format({
                ano_ant:'R$ {:,.2f}', ano_atual:'R$ {:,.2f}', 'Diferença R$':'R$ {:,.2f}', 'Crescimento %':'{:.2f}%'
            }), use_container_width=True)
        
        # 3. BAIXO GIRO
        st.write("### Produtos com Baixo Giro")
        df_total_prod = df_filtrado.groupby('produto')['valor'].sum().reset_index().sort_values('valor')
        total_fat = df_total_prod['valor'].sum()
        df_total_prod['% do Total'] = (df_total_prod['valor'] / total_fat.replace(0,1)) * 100
        df_cauda = df_total_prod[df_total_prod['% do Total'] < 0.5].head(50)
        st.dataframe(df_cauda[['produto','valor','% do Total']].style.format({'valor':'R$ {:,.2f}', '% do Total':'{:.3f}%'}), use_container_width=True)
