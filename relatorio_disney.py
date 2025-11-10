import streamlit as st
import pandas as pd
from io import BytesIO

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

    # Combinar colunas de marca
    df['MARCA'] = df[['LICENÇA', 'FRANQUIA']].astype(str).agg(' '.join, axis=1)
    df_disney = df[df['MARCA'].str.contains('disney', case=False, na=False)].copy()

    # Excluir cancelados (colunas J e K)
    cancel_keywords = ['cancel', 'cancelado', 'reprovado', 'negado', 'excluído']
    mask_cancel = df_disney[['PEDIDO GERAL', 'POR PRODUTO']].astype(str).apply(
        lambda col: col.str.lower().str.contains('|'.join(cancel_keywords))
    ).any(axis=1)
    df_disney = df_disney[~mask_cancel]

    # Calcular FOB total
    df_disney['FOB TOTAL'] = df_disney['FOB'] * df_disney['QTD EMBARQUE']

    # Sidebar para filtros
    st.sidebar.header("🔍 Filtros")

    # Filtro de anos
    anos_unicos = sorted(df_disney['ANO'].dropna().unique().tolist())
    anos_sel = st.sidebar.multiselect("📅 Selecione anos", anos_unicos, default=anos_unicos)

    # Filtro de clientes
    clientes_unicos = sorted(df_disney['CLIENTE'].dropna().unique().tolist())
    clientes_sel = st.sidebar.multiselect("👤 Selecione clientes", clientes_unicos, default=clientes_unicos)

    # Aplicar filtros
    df_filtrado = df_disney[
        df_disney['ANO'].isin(anos_sel) & df_disney['CLIENTE'].isin(clientes_sel)
    ].copy()

    # Agrupar por código pai
    df_codpai = df_filtrado.groupby(['ANO', 'CLIENTE', 'CÓD BBR', 'DESCRIÇÃO SISTEMA'], as_index=False).agg(
        {'QTD EMBARQUE': 'sum', 'FOB': 'mean', 'FOB TOTAL': 'sum'}
    )

    # Ordenar
    criterio = st.sidebar.radio("📈 Ordenar por:", ["FOB TOTAL", "QTD EMBARQUE"], horizontal=False)
    df_codpai = df_codpai.sort_values(criterio, ascending=False).reset_index(drop=True)

    # Totais
    total_fob = df_codpai['FOB TOTAL'].sum()
    total_qtd = df_codpai['QTD EMBARQUE'].sum()

    st.markdown(f"### 💰 Total FOB: **US$ {total_fob:,.2f}**")
    st.markdown(f"### 📦 Total Quantidade: **{total_qtd:,.0f} unidades**")

    # Exibir tabela
    st.subheader("📋 Tabela de Performance Disney (filtrada)")
    st.dataframe(
        df_codpai[['ANO', 'CLIENTE', 'CÓD BBR', 'DESCRIÇÃO SISTEMA',
                   'QTD EMBARQUE', 'FOB', 'FOB TOTAL']].style.format({
            'FOB': '{:,.2f}',
            'FOB TOTAL': '{:,.2f}',
        }),
        use_container_width=True
    )

    # --- Exportar Excel (.xlsx) ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_codpai.to_excel(writer, index=False, sheet_name='Relatório Disney')

        # Formatar planilha
        workbook = writer.book
        worksheet = writer.sheets['Relatório Disney']
        fmt_money = workbook.add_format({'num_format': '#,##0.00'})
        fmt_int = workbook.add_format({'num_format': '#,##0'})

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:D', 35)
        worksheet.set_column('E:E', 15, fmt_int)
        worksheet.set_column('F:G', 18, fmt_money)

        # Cabeçalho em negrito
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#EAEAEA'})
        for col_num, value in enumerate(df_codpai.columns.values):
            worksheet.write(0, col_num, value, header_fmt)

    excel_data = output.getvalue()

    st.download_button(
        label="💾 Baixar relatório completo (Excel)",
        data=excel_data,
        file_name=f"Relatorio_Disney_{'_'.join(map(str, anos_sel))}.xlsx",
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

else:
    st.info("⬆️ Envie o arquivo Excel para gerar o relatório.")
