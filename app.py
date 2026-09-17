import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gerenciador de Tarefas do Setor", layout="wide")

# 2. CONEXÃO COM SUPABASE
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Erro ao conectar com o Supabase: {e}")
    st.stop()

# 3. FUNÇÕES DE BANCO DE DADOS (Declarações obrigatórias no topo)
def carregar_tarefas():
    try:
        res = supabase.table("tarefas").select("*").order("id", desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Erro ao carregar tarefas: {e}")
        return pd.DataFrame()

def salvar_tarefa(titulo, descricao, responsavel, tema, data_inicio, deadline, prioridade, status="A Fazer"):
    try:
        dados = {
            "titulo": titulo,
            "descricao": descricao,
            "responsavel": responsavel,
            "tema": tema,
            "data_inicio": str(data_inicio),
            "deadline": str(deadline),
            "prioridade": prioridade,
            "status": status,
            "porcentagem": 0
        }
        supabase.table("tarefas").insert(dados).execute()
        st.success("Tarefa cadastrada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar tarefa no banco de dados: {e}")

# 4. INTERFACE DO APLICATIVO
st.title("📋 Gerenciador de Tarefas do Setor")

# Menu de Navegação / Abas
aba1, aba2 = st.tabs(["📌 Painel de Tarefas", "➕ Nova Tarefa"])

# ABA 1: PAINEL DE TAREFAS
with aba1:
    df = carregar_tarefas()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhuma tarefa encontrada ou cadastrada ainda.")

# ABA 2: CADASTRO DE NOVA TAREFA
with aba2:
    st.subheader("Cadastrar Nova Tarefa")
    with st.form("form_nova_tarefa", clear_on_submit=True):
        tit = st.text_input("Título da Tarefa *")
        desc = st.text_area("Descrição")
        col1, col2 = st.columns(2)
        with col1:
            resp = st.text_input("Responsável *")
            d_ini = st.date_input("Data de Início")
            prio = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Urgente"])
        with col2:
            tema = st.text_input("Tema / Projeto")
            d_fim = st.date_input("Prazo (Deadline)")
        
        submitted = st.form_submit_button("Cadastrar Tarefa")
        if submitted:
            if tit and resp:
                # Chamada da função garantida
                salvar_tarefa(tit, desc, resp, tema, d_ini, d_fim, prio, "A Fazer")
                st.rerun()
            else:
                st.error("Por favor, preencha os campos obrigatórios (*).")
