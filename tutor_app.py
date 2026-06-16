import streamlit as st
import google.generativeai as genai
import json
import os
import time

# ==========================================
# 1. LEITURA DINÂMICA CONFIGURAÇÃO DOS PROFESSORES
# ==========================================
FICHEIRO_CONFIG = "config_tutor.json"

# Valores padrão caso o ficheiro de configuração falhe ou não exista
config = {
    "NOME_PROFESSOR": "Celina Baptista",
    "DISCIPLINA": "Aplicações Informáticas",
    "MENSAGEM_BOAS_VINDAS": "Olá! Sou o teu tutor de apoio. Que desafio de lógica vamos explorar hoje?",
    "SYSTEM_PROMPT": "És um tutor socrático especialista em apoiar alunos universitários. Não dês respostas diretas."
}

# Tenta ler o ficheiro JSON editado pelo professor
if os.path.exists(FICHEIRO_CONFIG):
    try:
        with open(FICHEIRO_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        st.error(f"Erro ao ler o ficheiro de configuração: {e}. A usar valores padrão.")

# ==========================================
# 2. CONFIGURAÇÃO DA API DO GOOGLE GEMINI
# ==========================================
# Em vez de colocar a chave diretamente, o Streamlit vai ler do seu cofre seguro
CHAVE_API = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=CHAVE_API)

# Inicializar o modelo com o System Prompt dinâmico do ficheiro JSON
modelo = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=config["SYSTEM_PROMPT"]
)

# ==========================================
# 3. INTERFACE DINÂMICA (STREAMLIT)
# ==========================================
st.set_page_config(page_title=f"Tutor IA - {config['DISCIPLINA']}", page_icon="🎓", layout="centered")

# O título e a legenda mudam automaticamente com base no ficheiro JSON
st.title(f"Tutor Socrático")
st.subheader(f"{config['DISCIPLINA']}")
st.caption(f"Desenvolvido para as aulas de: {config['NOME_PROFESSOR']}")
st.divider()

# Inicializar a memória visual do chat com a mensagem de boas-vindas do JSON
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"role": "assistant", "content": config["MENSAGEM_BOAS_VINDAS"]}
    ]

# Inicializar a sessão de chat nativa do Gemini
if "chat_session" not in st.session_state:
    st.session_state.chat_session = modelo.start_chat(history=[])

# Mostrar as mensagens anteriores no ecrã
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 4. INTERAÇÃO E RESPOSTA DA IA
# ==========================================
if pergunta_aluno := st.chat_input("Escreve aqui a tua dúvida ou raciocínio..."):

    # Mostrar e guardar a pergunta do aluno
    st.session_state.mensagens.append({"role": "user", "content": pergunta_aluno})
    with st.chat_message("user"):
        st.markdown(pergunta_aluno)

    # Processar e mostrar a resposta do Tutor
    with st.chat_message("assistant"):
        resposta_placeholder = st.empty()

        try:
            resposta_ia = st.session_state.chat_session.send_message(pergunta_aluno)
            texto_resposta = resposta_ia.text

            # Efeito visual de digitação gradual
            resposta_completa = ""
            for palavra in texto_resposta.split():
                resposta_completa += palavra + " "
                time.sleep(0.03)
                resposta_placeholder.markdown(resposta_completa + "▌")

            resposta_placeholder.markdown(resposta_completa)
            st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})

        except Exception as e:
            st.error(f"Ocorreu um erro de comunicação com o tutor: {e}")
