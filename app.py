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

# 3. FUNÇÕES DE BANCO DE DADOS
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

def atualizar_tarefa(id_tarefa, novo_status, nova_porcentagem, novo_historico=""):
    try:
        dados_atualizados = {
            "status": novo_status,
            "porcentagem": int(nova_porcentagem)
        }
        if novo_historico:
            dados_atualizados["historico"] = novo_historico

        supabase.table("tarefas").update(dados_atualizados).eq("id", id_tarefa).execute()
        st.success(f"Tarefa #{id_tarefa} atualizada com sucesso!")
    except Exception as e:
        st.error(f"Erro ao atualizar tarefa: {e}")

# 4. INTERFACE DO APLICATIVO
st.title("📋 Gerenciador de Tarefas do Setor")

# Menu de Navegação / Abas
aba1, aba2, aba3 = st.tabs(["📌 Painel de Tarefas", "➕ Nova Tarefa", "✏️ Atualizar Progresso"])

# ABA 1: PAINEL DE TAREFAS (COM FILTROS)
with aba1:
    df = carregar_tarefas()
    if not df.empty:
        # --- SEÇÃO DE FILTROS ---
        st.subheader("🔍 Filtros e Busca")
        
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            # Busca por palavra-chave no título ou descrição
            busca = st.text_input("🔎 Buscar palavra-chave", placeholder="Ex: relatório, reunião...")
        
        with col_f2:
            # Filtro por Responsável
            lista_responsaveis = ["Todos"] + sorted(list(df["responsavel"].dropna().unique()))
            filtro_resp = st.selectbox("👤 Responsável", lista_responsaveis)
            
        with col_f3:
            # Filtro por Prioridade
            lista_prioridades = ["Todas", "Baixa", "Média", "Alta", "Urgente"]
            filtro_prio = st.selectbox("⚡ Prioridade", lista_prioridades)

        with col_f4:
            # Filtro por Status
            lista_status = ["Todos", "A Fazer", "Em Andamento", "Pendente / Bloqueada", "Concluída"]
            filtro_status = st.selectbox("📌 Status", lista_status)

        # Aplicação dos filtros no DataFrame
        df_filtrado = df.copy()

        if busca:
            termo = busca.lower()
            mascara_titulo = df_filtrado["titulo"].fillna("").str.lower().str.contains(termo)
            mascara_desc = df_filtrado["descricao"].fillna("").str.lower().str.contains(termo)
            df_filtrado = df_filtrado[mascara_titulo | mascara_desc]

        if filtro_resp != "Todos":
            df_filtrado = df_filtrado[df_filtrado["responsavel"] == filtro_resp]

        if filtro_prio != "Todas":
            df_filtrado = df_filtrado[df_filtrado["prioridade"] == filtro_prio]

        if filtro_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]

        st.markdown("---")

        # --- CARDS DE MÉTRICAS (Refletem os filtros ativos) ---
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Exibindo", len(df_filtrado))
        col_m2.metric("A Fazer / Pendentes", len(df_filtrado[df_filtrado["status"].isin(["A Fazer", "Pendente / Bloqueada"])]))
        col_m3.metric("Em Andamento", len(df_filtrado[df_filtrado["status"] == "Em Andamento"]))
        col_m4.metric("Concluídas", len(df_filtrado[df_filtrado["status"] == "Concluída"]))
        
        st.markdown("---")

        # --- TABELA DE DADOS ---
        col_config = {
            "porcentagem": st.column_config.ProgressColumn(
                "Progresso (%)",
                help="Porcentagem de execução da tarefa",
                format="%d%%",
                min_value=0,
                max_value=100,
            )
        }
        
        st.dataframe(df_filtrado, use_container_width=True, column_config=col_config)
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
                salvar_tarefa(tit, desc, resp, tema, d_ini, d_fim, prio, "A Fazer")
                st.rerun()
            else:
                st.error("Por favor, preencha os campos obrigatórios (*).")

# ABA 3: ATUALIZAR STATUS E PROGRESSO
with aba3:
    st.subheader("Atualizar Progresso de Tarefa Existente")
    df_atualizar = carregar_tarefas()
    
    if not df_atualizar.empty:
        opcoes_tarefas = {
            f"#{row['id']} | {row['titulo']} ({row['responsavel']})": row 
            for _, row in df_atualizar.iterrows()
        }
        
        tarefa_selecionada_label = st.selectbox(
            "Selecione a tarefa que deseja atualizar:",
            options=list(opcoes_tarefas.keys())
        )
        
        if tarefa_selecionada_label:
            dados_tarefa = opcoes_tarefas[tarefa_selecionada_label]
            
            st.info(f"**Descrição atual:** {dados_tarefa.get('descricao', 'Sem descrição')}")
            
            with st.form("form_atualizar_tarefa"):
                c1, c2 = st.columns(2)
                
                with c1:
                    status_opcoes = ["A Fazer", "Em Andamento", "Pendente / Bloqueada", "Concluída"]
                    status_index = status_opcoes.index(dados_tarefa['status']) if dados_tarefa['status'] in status_opcoes else 0
                    
                    novo_status = st.selectbox("Status Atual", options=status_opcoes, index=status_index)
                
                with c2:
                    val_porcentagem = int(dados_tarefa['porcentagem']) if pd.notnull(dados_tarefa['porcentagem']) else 0
                    nova_porcentagem = st.slider("Porcentagem de Conclusão", min_value=0, max_value=100, value=val_porcentagem, step=5)
                
                novo_historico = st.text_area("Observações / Histórico de Progresso", value=dados_tarefa.get('historico', '') or '')
                
                if st.form_submit_button("Salvar Atualizações"):
                    atualizar_tarefa(dados_tarefa['id'], novo_status, nova_porcentagem, novo_historico)
                    st.rerun()
    else:
        st.info("Nenhuma tarefa disponível para atualização.")
