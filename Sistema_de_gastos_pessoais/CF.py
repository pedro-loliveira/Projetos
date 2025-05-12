import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import calendar
# Executar pelo terminal com = streamlit run .\Sistema_de_gastos_pessoais\CF.py
# PROX ETAPA 1: ARRUMAR CALCULO DOS CARTÕES DE FUTUROS GASTOS, ETC.
# PROX ETAPA 2: PERSONALIZAR, CORES, TITULOS, ETC.
# PROX ETAPA 3: VERIFICAR POSSIBILISDADES DE COMPARTILHAMENTO, PASTAS, BANCO DE DADOS, ETC.
# CONFIGURAÇÕES INICIAIS
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("📊 Controle Financeiro")

# MESES
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# CONEXÃO SQLITE


def criar_conexao():
    return sqlite3.connect("financeiro.db", check_same_thread=False)


conn = criar_conexao()
cursor = conn.cursor()

# CRIAÇÃO DE TABELAS
cursor.execute('''
CREATE TABLE IF NOT EXISTS tabela_saida (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao_saida TEXT,
    tipo_gasto TEXT,
    forma_pg TEXT,
    categ TEXT,
    valor REAL,
    data_pg DATE,
    parcela INTEGER,
    data_vnc DATE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS tabela_entrada (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT,
    valor REAL,
    data_ent DATE
)
''')
conn.commit()

# FUNÇÕES AUXILIARES


def carregar_saida(tipo):
    return pd.read_sql("SELECT * FROM tabela_saida WHERE tipo_gasto = ?", conn, params=(tipo,))


def filtrar_por_mes(df, coluna_data, mes, ano):
    df[coluna_data] = pd.to_datetime(df[coluna_data])
    return df[(df[coluna_data].dt.month == mes) & (df[coluna_data].dt.year == ano)]

# FUNÇÃO DE FILTRO MENSAL


def selecionar_mes():
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    mes_filtro = st.sidebar.selectbox(
        "Selecione o Mês",
        list(range(1, 13)),
        format_func=lambda x: meses[x-1],
        index=st.session_state.get("mes_filtro", mes_atual) - 1,
        key="mes_filtro"
    )
    ano_filtro = st.sidebar.selectbox(
        "Selecione o Ano",
        list(range(ano_atual - 5, ano_atual + 5)),
        index=st.session_state.get("ano_filtro", ano_atual) - (ano_atual - 5),
        key="ano_filtro"
    )

    return mes_filtro, ano_filtro


def exibir_cadastro():
    st.header("📝 Cadastrar e Atualizar")
    registro_tipo = st.selectbox(
        "Tipo de Registro", ["Entrada", "Gasto Fixo", "Gasto Variável"], key="tipo_registro")

    categorias_predef = ["Assinatura", "Conta", "Casal",
                         "Uber", "Lazer", "Roupa", "Estudo",
                         "Jogos", "Presente", "Mercado", "Necessidade",
                         "Eventuais", "Condominio", "Saúde", "Ifood/Rest."
                         ]

    editando = 'edit_id' in st.session_state
    edit_id = st.session_state.get('edit_id')
    edit_tipo = st.session_state.get('edit_tipo')

    if registro_tipo == "Entrada":
        if editando and edit_tipo == "Entrada":
            dado = pd.read_sql(
                "SELECT * FROM tabela_entrada WHERE id = ?", conn, params=(edit_id,)).iloc[0]
            desc = st.text_input("Descrição", value=dado['descricao'])
            valor = st.number_input(
                "Valor (R$)", min_value=0.0, format="%.2f", value=dado['valor'])
            data = st.date_input(
                "Data", value=pd.to_datetime(dado['data_ent']))
            if st.button("Salvar Alterações", key="alterar_entrada"):
                cursor.execute(
                    "UPDATE tabela_entrada SET descricao=?, valor=?, data_ent=? WHERE id=?", (desc, valor, data, edit_id))
                conn.commit()
                st.success("Entrada atualizada com sucesso!")
                del st.session_state['edit_id']
                del st.session_state['edit_tipo']
                st.rerun()
        else:
            desc = st.text_input("Descrição")
            valor = st.number_input(
                "Valor (R$)", min_value=0.0, format="%.2f")
            data = st.date_input("Data")
            if st.button("Salvar Entrada", key="salvar_entrada"):
                cursor.execute(
                    "INSERT INTO tabela_entrada (descricao, valor, data_ent) VALUES (?, ?, ?)", (desc, valor, data))
                conn.commit()
                st.success("Entrada registrada com sucesso!")
    else:
        tipo_gasto = "Fixos" if registro_tipo == "Gasto Fixo" else "Variaveis"
        if editando and edit_tipo == tipo_gasto:
            dado = pd.read_sql(
                "SELECT * FROM tabela_saida WHERE id = ?", conn, params=(edit_id,)).iloc[0]
            desc = st.text_input(
                "Descrição", value=dado['descricao_saida'])
            forma_pg = st.selectbox("Forma de Pagamento", [
                "Credito", "Debito"], index=0 if dado['forma_pg'] == "Credito" else 1)
            categ = st.selectbox("Categoria", categorias_predef, index=categorias_predef.index(
                dado['categ']) if dado['categ'] in categorias_predef else 0)
            valor = st.number_input(
                "Valor (R$)", min_value=0.0, format="%.2f", value=dado['valor'])
            data_pg = st.date_input(
                "Data de Pagamento", value=pd.to_datetime(dado['data_pg']))

            parcela = st.number_input(
                "Parcelas (opcional)", min_value=0, step=1, value=int(dado['parcela'] or 0))
            data_vnc_usuario = st.date_input(
                "Data de Término (opcional)", value=pd.to_datetime(dado['data_vnc']) if dado['data_vnc'] else None)

            if parcela > 0:
                data_vnc_calculada = (pd.to_datetime(
                    data_pg) + pd.DateOffset(months=parcela - 1)).date()
                data_vnc_final = data_vnc_usuario if data_vnc_usuario else data_vnc_calculada
            else:
                data_vnc_final = data_vnc_usuario

            if st.button("Salvar Alterações", key="alterar_saida"):
                cursor.execute("""
                    UPDATE tabela_saida SET descricao_saida=?, tipo_gasto=?, forma_pg=?, categ=?, valor=?, data_pg=?, parcela=?, data_vnc=? WHERE id=?
                """, (desc, tipo_gasto, forma_pg, categ, valor, data_pg, parcela, data_vnc_final, edit_id))
                conn.commit()
                st.success("Gasto atualizado com sucesso!")
                del st.session_state['edit_id']
                del st.session_state['edit_tipo']
                st.rerun()
        else:
            desc = st.text_input("Descrição")
            forma_pg = st.selectbox("Forma de Pagamento", [
                                    "Credito", "Debito"])
            categ = st.selectbox("Categoria", categorias_predef)
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            data_pg = st.date_input("Data de Pagamento")

            parcela = st.number_input(
                "Parcelas (opcional)", min_value=0, step=1)
            data_vnc_usuario = st.date_input(
                "Data de Término (opcional)", value=None)

            if parcela > 0:
                data_vnc_calculada = (pd.to_datetime(
                    data_pg) + pd.DateOffset(months=parcela - 1)).date()
                data_vnc_final = data_vnc_usuario if data_vnc_usuario else data_vnc_calculada
            else:
                data_vnc_final = data_vnc_usuario if data_vnc_usuario else None

            if st.button("Salvar Gasto", key="salvar_saida"):
                cursor.execute('''
                INSERT INTO tabela_saida (descricao_saida, tipo_gasto, forma_pg, categ, valor, data_pg, parcela, data_vnc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                               (desc, tipo_gasto, forma_pg, categ, valor, data_pg, parcela if parcela else None, data_vnc_final))
                conn.commit()
                st.success("Gasto registrado com sucesso!")


def exibir_visualizacao():
    mes_filtro, ano_filtro = selecionar_mes()
    st.header("📋 Visualização de Registros")

    aba = st.radio("Selecionar Tabela", ["Fixos", "Variaveis", "Entrada"])

    if aba == "Entrada":
        df_entrada = pd.read_sql("SELECT * FROM tabela_entrada", conn)
        df_filtrado = filtrar_por_mes(
            df_entrada, "data_ent", mes_filtro, ano_filtro)

        for index, row in df_filtrado.iterrows():
            with st.expander(f"{row['descricao']} - R$ {row['valor']:.2f}"):
                st.write(
                    f"**Data:** {pd.to_datetime(row['data_ent']).strftime('%d/%m/%Y')}")
                col1, col2 = st.columns(2)
                if col1.button("✏️Editar", key=f"editar_ent_{row['id']}"):
                    st.session_state['edit_id'] = row['id']
                    st.session_state['edit_tipo'] = "Entrada"
                    st.rerun()
                if col2.button("🗑️Excluir", key=f"excluir_ent_{row['id']}"):
                    cursor.execute(
                        "DELETE FROM tabela_entrada WHERE id=?", (row['id'],))
                    conn.commit()
                    st.success("Entrada excluída com sucesso!")
                    st.rerun()

    else:
        df_saida = carregar_saida(aba)
        df_saida["data_pg"] = pd.to_datetime(df_saida["data_pg"])
        df_saida["data_vnc"] = pd.to_datetime(
            df_saida["data_vnc"], errors="coerce")

        # calcula primeiro e último dia do mês selecionado
        primeiro = datetime(ano_filtro, mes_filtro, 1)
        ultimo_dia = calendar.monthrange(ano_filtro, mes_filtro)[1]
        ultimo = datetime(ano_filtro, mes_filtro, ultimo_dia)

        df_filtrado = df_saida[
            (df_saida["data_pg"] <= ultimo) &
            ((df_saida["data_vnc"].isna()) |
             (df_saida["data_vnc"] >= primeiro))
        ]

        for index, row in df_filtrado.iterrows():
            with st.expander(f"{row['descricao_saida']} - R$ {row['valor']:.2f}"):
                st.write(f"**Categoria:** {row['categ']}")
                st.write(f"**Forma de Pagamento:** {row['forma_pg']}")
                st.write(
                    f"**Data de Pagamento:** {row['data_pg'].strftime('%d/%m/%Y')}")
                if aba == "Fixos":
                    st.write(f"**Parcelas:** {row['parcela']}")
                    st.write(
                        f"**Data de Término:** {row['data_vnc'].strftime('%d/%m/%Y') if not pd.isna(row['data_vnc']) else 'Indefinida'}")
                col1, col2 = st.columns(2)
                if col1.button("✏️Editar", key=f"editar_sai_{row['id']}"):
                    st.session_state['edit_id'] = row['id']
                    st.session_state['edit_tipo'] = aba
                    st.rerun()
                if col2.button("🗑️Excluir", key=f"excluir_sai_{row['id']}"):
                    cursor.execute(
                        "DELETE FROM tabela_saida WHERE id=?", (row['id'],))
                    conn.commit()
                    st.success("Registro excluído com sucesso!")
                    st.rerun()


def exibir_graficos():
    mes_filtro, ano_filtro = selecionar_mes()
    st.header("Gráficos")
    st.write(f"📅 Mês selecionado: {meses[mes_filtro - 1]} {ano_filtro}")

    # Carrega e formata dados
    df_entrada = pd.read_sql("SELECT * FROM tabela_entrada", conn)
    df_entrada["data_ent"] = pd.to_datetime(df_entrada["data_ent"])

    df_fixo = carregar_saida("Fixos")
    df_fixo["data_pg"] = pd.to_datetime(df_fixo["data_pg"])
    df_fixo["data_vnc"] = pd.to_datetime(df_fixo["data_vnc"], errors="coerce")

    df_var = carregar_saida("Variaveis")
    df_var["data_pg"] = pd.to_datetime(df_var["data_pg"])

    # Receita e gastos totais e mensais
    total_entradas = df_entrada["valor"].sum()
    entrada_mensal = df_entrada[
        (df_entrada["data_ent"].dt.year == ano_filtro) &
        (df_entrada["data_ent"].dt.month == mes_filtro)
    ]["valor"].sum()

    total_gastos = df_fixo["valor"].sum() + df_var["valor"].sum()
    gasto_mensal = (
        df_fixo[
            (df_fixo["data_pg"].dt.year <= ano_filtro) &
            ((df_fixo["data_vnc"].isna()) | (df_fixo["data_vnc"].dt.year >= ano_filtro)) &
            (df_fixo["data_pg"].dt.month <= mes_filtro) &
            ((df_fixo["data_vnc"].isna()) |
             (df_fixo["data_vnc"].dt.month >= mes_filtro))
        ]["valor"].sum()
        +
        df_var[
            (df_var["data_pg"].dt.year == ano_filtro) &
            (df_var["data_pg"].dt.month == mes_filtro)
        ]["valor"].sum()
    )

    receita_total = total_entradas - total_gastos
    receita_mensal = entrada_mensal - gasto_mensal

    # 1) Cartões de Entrada/Receita
    c1, c2, c3 = st.columns(3)
    c1.metric("Entrada Mensal",  f"R$ {entrada_mensal:,.2f}")
    c2.metric("Receita Mensal",  f"R$ {receita_mensal:,.2f}")
    c3.metric("Receita Total",   f"R$ {receita_total:,.2f}")

    # 2) Cartões Variável/Fixo Anual e Mensal
    df_var_ano = df_var[df_var["data_pg"].dt.year == ano_filtro]
    df_fixo_ano = df_fixo[
        (df_fixo["data_pg"].dt.year <= ano_filtro) &
        ((df_fixo["data_vnc"].isna()) |
         (df_fixo["data_vnc"].dt.year >= ano_filtro))
    ]
    df_var_mes = df_var[
        (df_var["data_pg"].dt.year == ano_filtro) &
        (df_var["data_pg"].dt.month == mes_filtro)
    ]
    df_fixo_mes = df_fixo[
        (df_fixo["data_pg"].dt.year <= ano_filtro) &
        ((df_fixo["data_vnc"].isna()) | (df_fixo["data_vnc"].dt.year >= ano_filtro)) &
        (df_fixo["data_pg"].dt.month <= mes_filtro) &
        ((df_fixo["data_vnc"].isna()) |
         (df_fixo["data_vnc"].dt.month >= mes_filtro))
    ]

    tot_var_ano = df_var_ano["valor"].sum()
    tot_fix_ano = df_fixo_ano["valor"].sum()
    tot_var_mes = df_var_mes["valor"].sum()
    tot_fix_mes = df_fixo_mes["valor"].sum()
    den = tot_var_mes + tot_fix_mes or 1
    pct_var = tot_var_mes / den * 100
    pct_fix = tot_fix_mes / den * 100

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Variável Anual", f"R$ {tot_var_ano:,.2f}")
    d2.metric("Variável Mensal", f"R$ {tot_var_mes:,.2f}")
    d3.metric("Fixo Anual",     f"R$ {tot_fix_ano:,.2f}")
    d4.metric("Fixo Mensal",    f"R$ {tot_fix_mes:,.2f}")

    # 3) Roscas em container escuro
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(
            "<div style='background-color:#333333; padding:1rem; border-radius:0.5rem'>",
            unsafe_allow_html=True
        )
        fig_var = px.pie(
            df_var_mes,
            names='categ',
            values='valor',
            hole=0.5,
            title="Gastos Variáveis"
        )
        fig_var.update_layout(
            annotations=[dict(
                text=f"{pct_var:.1f}%",
                x=0.5, y=0.5, font_size=20, showarrow=False
            )]
        )
        fig_var.update_traces(
            textinfo='label+percent',
            hovertemplate='Categoria: %{label}<br>Valor: R$ %{value:,.2f}'
        )
        st.plotly_chart(fig_var, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with p2:
        st.markdown(
            "<div style='background-color:#333333; padding:1rem; border-radius:0.5rem'>",
            unsafe_allow_html=True
        )
        fig_fix = px.pie(
            df_fixo_mes,
            names='categ',
            values='valor',
            hole=0.5,
            title="Gastos Fixos"
        )
        fig_fix.update_layout(
            annotations=[dict(
                text=f"{pct_fix:.1f}%",
                x=0.5, y=0.5, font_size=20, showarrow=False
            )]
        )
        fig_fix.update_traces(
            textinfo='label+percent',
            hovertemplate='Categoria: %{label}<br>Valor: R$ %{value:,.2f}'
        )
        st.plotly_chart(fig_fix, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 4) Comparativo Crédito vs Débito Mensal
    pg_fixo = df_fixo_mes[["tipo_gasto", "forma_pg", "valor"]]
    pg_var = df_var_mes[["tipo_gasto", "forma_pg", "valor"]]
    frames = [df for df in (pg_fixo, pg_var) if not df.empty]
    if frames:
        df_pg = pd.concat(frames, ignore_index=True)
        df_pg = df_pg.groupby(["tipo_gasto", "forma_pg"],
                              as_index=False)["valor"].sum()
        fig_stack = px.bar(
            df_pg,
            x="valor",
            y="tipo_gasto",
            color="forma_pg",
            orientation="h",
            barmode="stack",
            title="Comparativo Crédito × Débito Mensal"
        )
        fig_stack.update_layout(
            xaxis_title="",
            yaxis_title="",
            showlegend=True,
            height=250,
            bargap=0.2
        )
        fig_stack.update_xaxes(showticklabels=False)
        fig_stack.update_yaxes(showticklabels=True)
        st.plotly_chart(fig_stack, use_container_width=True)
    else:
        st.info("Não há lançamentos de Crédito × Débito para este período.")

    # 5) Evolução Anual
    entr_evo, said_evo = [], []
    for m in range(1, 13):
        e = df_entrada[
            (df_entrada["data_ent"].dt.year == ano_filtro) &
            (df_entrada["data_ent"].dt.month == m)
        ]["valor"].sum()
        s = (
            df_fixo[
                (df_fixo["data_pg"].dt.year <= ano_filtro) &
                ((df_fixo["data_vnc"].isna()) | (df_fixo["data_vnc"].dt.year >= ano_filtro)) &
                (df_fixo["data_pg"].dt.month <= m) &
                ((df_fixo["data_vnc"].isna()) |
                 (df_fixo["data_vnc"].dt.month >= m))
            ]["valor"].sum()
            +
            df_var[
                (df_var["data_pg"].dt.year == ano_filtro) &
                (df_var["data_pg"].dt.month == m)
            ]["valor"].sum()
        )
        entr_evo.append(e)
        said_evo.append(s)

    df_ev = pd.DataFrame({
        "Mês":      meses,
        "Entradas": entr_evo,
        "Gastos":   said_evo
    })
    fig_ev = px.bar(
        df_ev,
        x="Mês",
        y=["Entradas", "Gastos"],
        barmode="group",
        title="Evolução Anual"
    )
    fig_ev.update_layout(
        showlegend=True,
        height=300,
        bargap=0.2,
        xaxis_title=None,
        yaxis_title=None
    )
    # mantém meses no X, remove ticks no Y
    fig_ev.update_yaxes(showticklabels=False)
    st.plotly_chart(fig_ev, use_container_width=True)


# NAVEGAÇÃO MULTIPÁGINA
pagina = st.sidebar.radio("Navegar", ["Cadastros e Visualização", "Gráficos"])

if pagina == "Cadastros e Visualização":
    col1, col2 = st.columns([1, 2])
    with col1:
        exibir_cadastro()
    with col2:
        exibir_visualizacao()

elif pagina == "Gráficos":
    exibir_graficos()

# FECHAR CONEXÃO
conn.close()
