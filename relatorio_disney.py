import streamlit as st
import pandas as pd

st.set_page_config(page_title="Relatório Disney", layout="wide")

st.title("📊 Relatório de Performance - Produtos Disney")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("📤 Envie o arquivo Excel de embarques", type=["xlsx"])

if uploaded_file:
    # Ler a planilha
    df = pd.read_excel(uploaded_file, header=1)
    df.columns = df.columns.str.strip().str.upper()

    # Selecionar colunas relevantes
    cols = ['ANO', 'CLIENTE', 'CÓD BBR', 'DESCRIÇÃO SISTEMA',
            'PEDIDO GERAL', 'POR PRODUTO', 'FOB', 'QTD EMBARQUE',
            'LICENÇA', 'FRANQUIA']
    df = df[[c for c in cols if c in df.columns]]

    # Filtrar Disney (considerando LICENÇA ou FRANQUIA)
    df['MARCA'] = df[['LICENÇA', 'FRANQUIA']].astype(str).agg(' '.join, axis=1)
    df_disney = df[df['MARCA'].str.contains('disney', case=False, na=False)].copy()

    # Excluir cancelados (colunas J e K = PEDIDO GERAL e POR PRODUTO)
    cancel_keywords = ['cancel', 'cancelado', 'reprovado', 'negado', 'excluído']
    mask_cancel = df_disney[['PEDIDO GERAL', 'POR PRODUTO']].astype(str).apply(
        lambda col: col.str.lower().str.contains('|'.join(cancel_keywords))
    ).any(axis=1)
    df_disney = df_disney[~mask_cancel]

    # Calcular FOB total
    df_disney['FOB TOTAL'] = df_disney['FOB'] * df_disney['QTD EMBARQUE']

    # === FILTRO DE ANOS (múltipla seleção) ===
    anos_unicos = sorted(df_disney['ANO'].dropna().unique().tolist())
    anos_sel = st.multiselect("📅 Selecione um ou mais anos", anos_unicos, default=anos_unicos)
    if anos_sel:
        df_disney = df_disney[df_disney['ANO'].isin(anos_sel)]

    # === FILTRO DE CLIENTES (múltipla seleção) ===
    clientes_unicos = sorted(df_disney['CLIENTE'].dropna().unique().tolist())
    clientes_sel = st.multiselect("👤 Selecione um ou mais clientes", clientes_unicos, default=clientes_unicos)
    if clientes_sel:
        df_disney = df_disney[df_disney['CLIENTE'].isin(clientes_sel)]

    # Agrupar por código pai
    df_codpai = df_disney.groupby(['CÓD BBR', 'DESCRIÇÃO SISTEMA'], as_index=False).agg(
        {'QTD EMBARQUE': 'sum', 'FOB': 'mean', 'FOB TOTAL': 'sum'}
    )

    # Ordenação
    criterio = st.radio("📈 Ordenar por:", ["FOB TOTAL", "QTD EMBARQUE"], horizontal=True)
    df_codpai = df_codpai.sort_values(criterio, ascending=False).reset_index(drop=True)

    # Calcular percentuais
    df_codpai['% FOB'] = df_codpai['FOB TOTAL'] / df_codpai['FOB TOTAL'].sum()
    df_codpai['% QTD'] = df_codpai['QTD EMBARQUE'] / df_codpai['QTD EMBARQUE'].sum()

    # Totais
    total_fob = df_codpai['FOB TOTAL'].sum()
    total_qtd = df_codpai['QTD EMBARQUE'].sum()

    st.markdown(f"### 💰 Total FOB: **US$ {total_fob:,.2f}**")
    st.markdown(f"### 📦 Total Quantidade: **{total_qtd:,.0f} unidades**")

    # Exibir tabela
    st.subheader("📋 Tabela de Performance Disney")
    st.dataframe(
        df_codpai[['CÓD BBR', 'DESCRIÇÃO SISTEMA', 'QTD EMBARQUE', 'FOB', 'FOB TOTAL', '% FOB', '% QTD']].style.format({
            'FOB': '{:,.2f}',
            'FOB TOTAL': '{:,.2f}',
            '% FOB': '{:.2%}',
            '% QTD': '{:.2%}'
        })
    )

    # Exportar CSV
    csv = df_codpai.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="💾 Baixar relatório completo (Excel/CSV)",
        data=csv,
        file_name=f"Relatorio_Disney_{'_'.join(map(str, anos_sel))}_{'_'.join(clientes_sel)}.csv",
        mime='text/csv'
    )

else:
    st.info("⬆️ Envie o arquivo Excel para gerar o relatório.")
