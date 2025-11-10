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

    # Verificar se coluna ANO existe
    if 'ANO' not in df.columns:
        st.error("A coluna 'ANO' não foi encontrada na planilha. Verifique se está na primeira coluna (A).")
    else:
        # Selecionar colunas relevantes
        cols = ['ANO', 'CLIENTE', 'CÓD BBR', 'DESCRIÇÃO SISTEMA', 
                'PEDIDO GERAL', 'POR PRODUTO', 'FOB', 'QTD EMBARQUE', 'LICENÇA']
        df = df[[c for c in cols if c in df.columns]]

        # Filtrar apenas produtos Disney
        df_disney = df[df['LICENÇA'].str.contains('disney', case=False, na=False)].copy()

        # --- FILTRO CORRIGIDO: excluir itens e embarques cancelados ---
        df_disney = df_disney[
            ~(
                (df_disney['PEDIDO GERAL'].astype(str).str.strip().str.lower() == 'cancelado') |
                (df_disney['POR PRODUTO'].astype(str).str.strip().str.lower().isin(['item embarque cancelado', 'item cancelado']))
            )
        ]

        # Calcular FOB total
        df_disney['FOB TOTAL'] = df_disney['FOB'] * df_disney['QTD EMBARQUE']

        # Filtro de ano
        anos = sorted(df_disney['ANO'].dropna().unique().tolist())
        ano_sel = st.selectbox("📅 Selecione o ano", anos, index=len(anos)-1)
        df_disney = df_disney[df_disney['ANO'] == ano_sel]

        # Filtro de cliente
        clientes = ['Todos'] + sorted(df_disney['CLIENTE'].dropna().unique().tolist())
        cliente_sel = st.selectbox("👤 Selecione o cliente", clientes)

        if cliente_sel != 'Todos':
            df_disney = df_disney[df_disney['CLIENTE'] == cliente_sel]

        # Agrupar por código pai
        df_codpai = df_disney.groupby(['CÓD BBR', 'DESCRIÇÃO SISTEMA'], as_index=False).agg(
            {'QTD EMBARQUE': 'sum', 'FOB': 'mean', 'FOB TOTAL': 'sum'}
        )

        # Ordenar por FOB ou quantidade
        criterio = st.radio("📈 Ordenar por:", ["FOB TOTAL", "QTD EMBARQUE"], horizontal=True)
        df_codpai = df_codpai.sort_values(criterio, ascending=False).reset_index(drop=True)

        # Curvas ABC
        df_codpai['% FOB'] = df_codpai['FOB TOTAL'] / df_codpai['FOB TOTAL'].sum()
        df_codpai['ACUM FOB'] = df_codpai['% FOB'].cumsum()
        df_codpai['CURVA FOB'] = pd.cut(df_codpai['ACUM FOB'], bins=[0, 0.8, 0.95, 1],
                                        labels=['A', 'B', 'C'], include_lowest=True)

        df_codpai['% QTD'] = df_codpai['QTD EMBARQUE'] / df_codpai['QTD EMBARQUE'].sum()
        df_codpai['ACUM QTD'] = df_codpai['% QTD'].cumsum()
        df_codpai['CURVA QTD'] = pd.cut(df_codpai['ACUM QTD'], bins=[0, 0.8, 0.95, 1],
                                        labels=['A', 'B', 'C'], include_lowest=True)

        # Exibir tabela
        st.subheader(f"📋 Tabela de Performance Disney ({ano_sel})")
        st.dataframe(df_codpai.style.format({
            'FOB': '{:,.2f}',
            'FOB TOTAL': '{:,.2f}',
            '% FOB': '{:.2%}',
            '% QTD': '{:.2%}'
        }))

        # Exportar
        csv = df_codpai.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="💾 Baixar relatório completo (Excel/CSV)",
            data=csv,
            file_name=f"Relatorio_Disney_{ano_sel}_{cliente_sel.replace(' ', '_')}.csv",
            mime='text/csv'
        )

else:
    st.info("⬆️ Envie o arquivo Excel para gerar o relatório.")
