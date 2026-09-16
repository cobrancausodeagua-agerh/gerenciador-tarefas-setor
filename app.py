import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gerenciador de Tarefas do Setor", layout="wide", page_icon="📋")

# 2. CONEXÃO COM O SUPABASE
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 3. FUNÇÕES DE BANCO DE DADOS
def carregar_tarefas():
    res = supabase.table("tarefas").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def salvar_tarefa(titulo, descricao, responsavel, tema, data_ini, deadline, prioridade, status):
    dados = {
        "titulo": titulo,
        "descricao": descricao,
        "responsavel": responsavel,
        "tema": tema,
        "data_inicio": str(data_ini),
        "deadline": str(deadline),
        "prioridade": prioridade,
        "status": status,
        "porcentagem": 0,
        "historico": f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Tarefa criada."
    }
    supabase.table("tarefas").insert(dados).execute()

def atualizar_tarefa(id_tarefa, novo_status, nova_porcentagem, novo_comentario, historico_atual):
    novo_historico = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Status: {novo_status} ({nova_porcentagem}%). {novo_comentario}\n" + str(historico_atual or "")
    dados = {
        "status": novo_status,
        "porcentagem": nova_porcentagem,
        "historico": novo_historico
    }
    supabase.table("tarefas").update(dados).eq("id", id_tarefa).execute()

# --- INTERFACE ---
st.title("📋 Gerenciador de Tarefas do Setor")

df = carregar_tarefas()

if not df.empty:
    df['deadline'] = pd.to_datetime(df['deadline']).dt.date
    hoje = date.today()

    # METRICAS
    tot = len(df)
    atrasadas = len(df[(df['deadline'] < hoje) & (df['status'] != 'Concluído')])
    em_andamento = len(df[df['status'] == 'Em Andamento'])
    concluidas = len(df[df['status'] == 'Concluído'])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Tarefas", tot)
    c2.metric("Em Andamento", em_andamento)
    c3.metric("Atrasadas 🚨", atrasadas)
    c4.metric("Concluídas ✅", concluidas)

st.divider()

# ABAS DE NAVEGAÇÃO
aba1, aba2, aba3 = st.tabs(["📌 Painel de Tarefas", "✍️ Atualizar Andamento", "➕ Nova Tarefa"])

with aba1:
    st.subheader("Painel Geral de Demandas")
    if not df.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_resp = st.multiselect("Filtrar por Responsável", options=df['responsavel'].unique())
        with col_f2:
            filtro_status = st.multiselect("Filtrar por Status", options=df['status'].unique())

        df_filtrado = df.copy()
        if filtro_resp:
            df_filtrado = df_filtrado[df_filtrado['responsavel'].isin(filtro_resp)]
        if filtro_status:
            df_filtrado = df_filtrado[df_filtrado['status'].isin(filtro_status)]

        # Tabela exibida
        colunas_visiveis = ['id', 'titulo', 'responsavel', 'tema', 'deadline', 'prioridade', 'status', 'porcentagem']
        st.dataframe(df_filtrado[colunas_visiveis], use_container_width=True)

with aba2:
    st.subheader("Atualizar Andamento da Tarefa")
    if not df.empty:
        lista_tarefas = df['id'].astype(str) + " - " + df['titulo'] + " (" + df['responsavel'] + ")"
        tarefa_sel = st.selectbox("Selecione a Tarefa para Atualizar", options=lista_tarefas)

        if tarefa_sel:
            id_sel = int(tarefa_sel.split(" - ")[0])
            dados_t = df[df['id'] == id_sel].iloc[0]

            with st.form("form_atualiza"):
                c_st, c_porc = st.columns(2)
                with c_st:
                    status_opcoes = ["A Fazer", "Em Andamento", "Aguardando Validação", "Concluído"]
                    index_atual = status_opcoes.index(dados_t['status']) if dados_t['status'] in status_opcoes else 0
                    n_status = st.selectbox("Novo Status", options=status_opcoes, index=index_atual)
                with c_porc:
                    n_porc = st.slider("Porcentagem de Conclusão (%)", 0, 100, int(dados_t['porcentagem']))

                n_coment = st.text_area("Adicionar Comentário/Andamento")
                
                if st.form_submit_button("Salvar Atualização"):
                    atualizar_tarefa(id_sel, n_status, n_porc, n_coment, dados_t['historico'])
                    st.success("Andamento atualizado com sucesso!")
                    st.rerun()

            with st.expander("📜 Ver Histórico de Andamentos"):
                st.text(dados_t['historico'])

with aba3:
    st.subheader("Cadastrar Nova Tarefa")
    with st.form("form_nova_tarefa"):
        tit = st.text_input("Título da Tarefa*")
        desc = st.text_area("Descrição Detalhada")
        c_r, c_t = st.columns(2)
        with c_r:
            resp = st.text_input("Responsável*")
        with c_t:
            tema = st.text_input("Tema / Categoria")

        c_d1, c_d2, c_p = st.columns(3)
        with c_d1:
            d_ini = st.date_input("Data de Início", value=date.today())
        with c_d2:
            d_fim = st.date_input("Prazo Final (Deadline)", value=date.today())
        with c_p:
            prio = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"])

        if st.form_submit_button("Cadastrar Tarefa"):
            if tit and resp:
                salvar_tarefa(tit, desc, resp, tema, d_ini, d_fim, prio, "A Fazer")
                st.success("Tarefa cadastrada com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, preencha os campos obrigatórios (*).")
