import pandas as pd
import mysql.connector
import decimal
import streamlit as st

def bd_phoenix(vw_name):
    # Parametros de Login AWS
    config = {
    'user': 'user_automation_jpa',
    'password': 'luck_jpa_2024',
    'host': 'comeia.cixat7j68g0n.us-east-1.rds.amazonaws.com',
    'database': 'test_phoenix_maceio'
    }
    # Conexão as Views
    conexao = mysql.connector.connect(**config)
    cursor = conexao.cursor()

    request_name = f'SELECT * FROM {vw_name}'

    # Script MySql para requests
    cursor.execute(
        request_name
    )
    # Coloca o request em uma variavel
    resultado = cursor.fetchall()
    # Busca apenas o cabecalhos do Banco
    cabecalho = [desc[0] for desc in cursor.description]

    # Fecha a conexão
    cursor.close()
    conexao.close()

    # Coloca em um dataframe e muda o tipo de decimal para float
    df = pd.DataFrame(resultado, columns=cabecalho)
    df = df.applymap(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)
    return df

def definir_html(df_ref):

    html=df_ref.to_html(index=False)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                text-align: center;  /* Centraliza o texto */
            }}
            table {{
                margin: 0 auto;  /* Centraliza a tabela */
                border-collapse: collapse;  /* Remove espaço entre as bordas da tabela */
            }}
            th, td {{
                padding: 8px;  /* Adiciona espaço ao redor do texto nas células */
                border: 1px solid black;  /* Adiciona bordas às células */
                text-align: center;
            }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """

    return html

def criar_output_html(nome_html, html, titulo_inclusos, titulo_vendas, titulo_total):

    with open(nome_html, "w", encoding="utf-8") as file:

        file.write(f'<p style="font-size:40px;">{titulo_inclusos}</p>\n\n')

        file.write(f'<p style="font-size:40px;">{titulo_vendas}</p>\n\n')

        file.write(f'<p style="font-size:40px;">{titulo_total}</p>\n\n')
        
        file.write(html)

st.set_page_config(layout='wide')

if 'mapa_router' not in st.session_state:

    st.session_state.mapa_router = bd_phoenix('vw_router')

    st.session_state.sales_ranking = bd_phoenix('vw_sales_ranking')

st.title('Ranking Vendedores')

st.divider()

row0 = st.columns(2)

with row0[1]:

    container_dados = st.container()

    atualizar_dados = container_dados.button('Carregar Dados do Phoenix', use_container_width=True)

if atualizar_dados:

    st.session_state.mapa_router = bd_phoenix('vw_router')

    st.session_state.sales_ranking = bd_phoenix('vw_sales_ranking')

with row0[0]:

    data_inicial = st.date_input('Data Inicial', value=None ,format='DD/MM/YYYY', key='data_inicial')

    data_final = st.date_input('Data Final', value=None ,format='DD/MM/YYYY', key='data_final')

if data_inicial and data_final:

    df_router_filtrado = st.session_state.mapa_router[(st.session_state.mapa_router['Data Execucao'] >= data_inicial) & 
                                                      (st.session_state.mapa_router['Data Execucao'] <= data_final) & 
                                                      (st.session_state.mapa_router['Tipo de Servico'] == 'TOUR')].reset_index(drop=True)
    
    df_router_filtrado['Total ADT | CHD'] = df_router_filtrado['Total ADT'] + df_router_filtrado['Total CHD']
    
    df_sales_filtrado = st.session_state.sales_ranking[(st.session_state.sales_ranking['Data de Execucao'] >= data_inicial) & 
                                                            (st.session_state.sales_ranking['Data de Execucao'] <= data_final) & 
                                                            (st.session_state.sales_ranking['Tipo de Servico'] == 'TOUR')]\
                                                                .reset_index(drop=True)
    
    df_vendedores = pd.merge(df_router_filtrado, df_sales_filtrado[['Codigo da Reserva', '1 Vendedor', 'Data de Execucao', 'Servico']], 
                             how='left', left_on=['Reserva', 'Data Execucao', 'Servico'], 
                             right_on=['Codigo da Reserva', 'Data de Execucao', 'Servico'])
    
    lista_servicos = df_vendedores['Servico'].unique().tolist()

    with row0[1]:

        container_passeios = st.container(border=True)

        container_passeios.write('Passeios')

        servico = container_passeios.multiselect('', sorted(lista_servicos))

    st.divider()

    row2 = st.columns(1)

    container_2 = st.container(border=True)

    if servico:

        df_mapa_filtrado_servico = df_vendedores[df_vendedores['Servico'].isin(servico)].reset_index(drop=True)

        df_mapa_filtrado_servico['Total ADT | CHD'] = df_mapa_filtrado_servico['Total ADT'] + df_mapa_filtrado_servico['Total CHD']

        df_ranking = df_mapa_filtrado_servico.groupby('1 Vendedor').agg({'Total ADT | CHD': 'sum'})\
            .sort_values(by='Total ADT | CHD', ascending=False).reset_index()
        
        total_paxs = df_router_filtrado[df_router_filtrado['Servico'].isin(servico)]['Total ADT | CHD'].sum()

        total_paxs_vendedores = df_ranking['Total ADT | CHD'].sum()

        st.session_state.titulo_inclusos = f'Incluso = {int(total_paxs-total_paxs_vendedores)}'

        st.session_state.titulo_vendas = f'Vendas = {int(total_paxs_vendedores)}'

        st.session_state.titulo_total = f'Total = {int(total_paxs)}'

        container_2.write(st.session_state.titulo_inclusos)

        container_2.write(st.session_state.titulo_vendas)

        container_2.write(st.session_state.titulo_total)

        df_ranking = df_ranking.rename(columns={'1 Vendedor': 'Vendedor', 'Total ADT | CHD': 'Paxs'})  

        df_ranking['Paxs'] = pd.to_numeric(df_ranking['Paxs'], errors='coerce').fillna(0).astype(int) 

        container_2.dataframe(df_ranking, hide_index=True, use_container_width=True)

        st.session_state.df_ranking = df_ranking

        st.session_state.nome_html = f"{servico[0].split(' ')[0]}.html"

if 'df_ranking' in st.session_state:

    html = definir_html(st.session_state.df_ranking)

    criar_output_html(st.session_state.nome_html, html, st.session_state.titulo_inclusos, st.session_state.titulo_vendas, 
                        st.session_state.titulo_total)
    
    with open(st.session_state.nome_html, "r", encoding="utf-8") as file:

        html_content = file.read()

    st.download_button(
        label="Baixar Arquivo HTML",
        data=html_content,
        file_name=st.session_state.nome_html,
        mime="text/html"
    )