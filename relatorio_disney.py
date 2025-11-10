import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Relatório Disney", layout="wide")

st.title("📊 Relatório de Performance - Produtos Disney")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("📤 Envie o arquivo Excel de embarques", type=["xlsx"])

if uploaded_file:
    # Ler o arquivo
    df = pd.read_excel(uploaded_file, header=1)
    df.columns = df.columns.str.strip().str.upper()

    # Selecionar colunas relevantes
    cols = ['CLIENTE', 'CÓD BBR', 'DESCRIÇÃO SISTEMA', 'STATUS INSPEÇÃO', 
            'STATUS PLATE', 'FOB', 'QTD EMBARQUE', 'LICENÇA']
    df = df[[c for c in cols if c in df.columns]]

    # Filtrar apenas produtos Disney
    df_disney = df[df['LICENÇA'].str.contains('disney', case=False, na=False)].copy()

    # Excluir status cancelados/reprovados
    cancel_keywords = ['cancel', 'cancelado', 'reprovado', 'negado', 'excluído']
    mask_cancel = df_disney[['STATUS INSPEÇÃO', 'STATUS PLATE']].apply(
        lambda x: x.astype(str).str.lower().str.contains('|'.join(cancel_keywords)).any(), axis=1
    )
    df_disney = df_disney[~mask_cancel]

    # Calcular FOB total
    df_disney['FOB TOTAL'] = df_disney['FOB'] * df_disney['QTD EMBARQUE']

    # Filtro de cliente
    clientes = ['Todos'] + sorted(df_disney['CLIENTE'].dropna().unique().tolist())
    cliente_sel = st.selectbox("👤 Selecione o cliente", clientes)

    if cliente_sel != 'Todos':
        df_disney = df_disney[df_disney['CLIENTE'] == cliente_sel]

    # Agrupar por código pai
    df_codpai = df_disney.groupby(['CÓD BBR', 'DESCRIÇÃO SISTEMA'], as_index=False).agg(
        {'QTD EMBARQUE': 'sum', 'FOB': 'mean', 'FOB TOTAL': 'sum'}
    )

    # Ordenação
    criterio = st.radio("📈 Ordenar por:", ["FOB TOTAL", "QTD EMBARQUE"], horizontal=True)
    df_codpai = df_codpai.sort_values(criterio, ascending=False).reset_index(drop=True)

    # Curvas ABC
    df_codpai['% FOB'] = df_codpai['FOB TOTAL'] / df_codpai['FOB TOTAL'].sum()
    df_codpai['ACUM FOB'] = df_codpai['% FOB'].cumsum()
    df_codpai['CURVA FOB'] = pd.cut(df_codpai['ACUM FOB'], bins=[0, 0.8, 0.95, 1], labels=['A', 'B', 'C'], include_lowest=True)

    df_codpai['% QTD'] = df_codpai['QTD EMBARQUE'] / df_codpai['QTD EMBARQUE'].sum()
    df_codpai['ACUM QTD'] = df_codpai['% QTD'].cumsum()
    df_codpai['CURVA QTD'] = pd.cut(df_codpai['ACUM QTD'], bins=[0, 0.8, 0.95, 1], labels=['A', 'B', 'C'], include_lowest=True)

    # Exibir tabela
    st.subheader("📋 Tabela de Performance Disney")
    st.dataframe(df_codpai.style.format({
        'FOB': '{:,.2f}',
        'FOB TOTAL': '{:,.2f}',
        '% FOB': '{:.2%}',
        '% QTD': '{:.2%}'
    }))

    # Gráfico Pareto
    st.subheader("📊 Gráfico de Pareto - Curva ABC (por FOB Total)")
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()

    ax1.bar(df_codpai['CÓD BBR'], df_codpai['FOB TOTAL'], color='skyblue')
    ax2.plot(df_codpai['CÓD BBR'], df_codpai['ACUM FOB'] * 100, color='red', marker='o')

    ax1.set_xlabel('Código Pai (CÓD BBR)')
    ax1.set_ylabel('FOB Total (US$)')
    ax2.set_ylabel('% Acumulado')

    ax1.tick_params(axis='x', rotation=90)
    ax2.axhline(80, color='gray', linestyle='--')
    ax2.axhline(95, color='gray', linestyle='--')

    st.pyplot(fig)

    # Exportar para Excel
    csv = df_codpai.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="💾 Baixar relatório completo (Excel/CSV)",
        data=csv,
        file_name=f"Relatorio_Disney_{cliente_sel.replace(' ', '_')}.csv",
        mime='text/csv'
    )

else:
    st.info("⬆️ Envie o arquivo Excel para gerar o relatório.")
