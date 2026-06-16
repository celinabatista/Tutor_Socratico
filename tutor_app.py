import streamlit as st
import google.generativeai as genai
import json
import base64
import time

# ==========================================
# 1. FUNÇÕES DE CODIFICAÇÃO (LINK MÁGICO)
# ==========================================
# Transforma as configurações do professor num código de texto seguro para links
def codificar_config(config_dict):
    json_str = json.dumps(config_dict)
    return base64.urlsafe_b64encode(json_str.encode()).decode()

# Transforma o código do link de volta nas configurações do professor
def descodificar_config(codigo_str):
    try:
        json_str = base64.urlsafe_b64decode(codigo_str.encode()).decode()
        return json.loads(json_str)
    except:
        return None

# ==========================================
# 2. VERIFICAR MODO (PROFESSOR vs ALUNO)
# ==========================================
# O Streamlit lê os parâmetros do URL (ex: ?c=codigo_encriptado)
parametros_url = st.query_params
config_atual = None

# Se existir o parâmetro 'c' no URL, estamos no Modo Aluno
if "c" in parametros_url:
    config_atual = descodificar_config(parametros_url["c"])

# ==========================================
# 3. INTERFACE - MODO PROFESSOR (CRIADOR)
# ==========================================
if not config_atual:
    st.set_page_config(page_title="Criador de Tutores IA", page_icon="⚙️", layout="centered")
    st.title("⚙️ Plataforma de Tutores Socráticos")
    st.write("Crie um tutor personalizado para a sua disciplina e partilhe o link com os alunos.")
    st.divider()

    with st.form("form_criacao"):
        nome_prof = st.text_input("O seu Nome (ex: Prof.ª Celina Baptista)")
        disciplina = st.text_input("Disciplina ou Módulo")
        boas_vindas = st.text_area("Mensagem Inicial da IA", value="Olá! Sou o teu tutor. Que desafio vamos explorar hoje?")
        prompt_ia = st.text_area("Instruções Pedagógicas (System Prompt)", height=150, 
                                 value="És um tutor socrático. Nunca dês as respostas diretas, orienta o aluno com perguntas lógicas.")
        
        gerar_btn = st.form_submit_button("Gerar o Meu Tutor")

    if gerar_btn and nome_prof and disciplina:
        # Criar o dicionário com os dados
        nova_config = {
            "NOME_PROFESSOR": nome_prof,
            "DISCIPLINA": disciplina,
            "MENSAGEM_BOAS_VINDAS": boas_vindas,
            "SYSTEM_PROMPT": prompt_ia
        }
        
        # Gerar o código e construir o link
        codigo_magico = codificar_config(nova_config)
        
        # AVISO: Substitua 'sua-app.streamlit.app' pelo link real da sua aplicação no Streamlit Cloud
        link_final = f"https://tutorsocratico-vuenltzglqdgwhegtewr2k.streamlit.app/?c={codigo_magico}"
        
        st.success("🎉 O seu tutor foi criado com sucesso!")
        st.write("Copie o link abaixo e partilhe com os seus alunos no Moodle, Teams ou Classroom:")
        st.code(link_final, language="http")
        st.info("Testar: Abra um novo separador no navegador e cole o link para ver o tutor a funcionar.")

# ==========================================
# 4. INTERFACE - MODO ALUNO (O CHAT)
# ==========================================
else:
    # Ler a chave segura guardada no Streamlit Secrets
    try:
        CHAVE_API = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=CHAVE_API)
    except Exception as e:
        st.error("Erro ao ler a Chave API. Verifique os Secrets do Streamlit.")
        st.stop()

    # Inicializar o modelo com o Prompt injetado pelo Link Mágico
    modelo = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=config_atual["SYSTEM_PROMPT"]
    )

    st.set_page_config(page_title=f"Tutor - {config_atual['DISCIPLINA']}", page_icon="🎓", layout="centered")
    st.title("Tutor Socrático")
    st.subheader(config_atual['DISCIPLINA'])
    st.caption(f"Desenvolvido para as turmas de: {config_atual['NOME_PROFESSOR']}")
    st.divider()

    if "mensagens" not in st.session_state:
        st.session_state.mensagens = [{"role": "assistant", "content": config_atual["MENSAGEM_BOAS_VINDAS"]}]

    if "chat_session" not in st.session_state:
        st.session_state.chat_session = modelo.start_chat(history=[])

    for msg in st.session_state.mensagens:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if pergunta_aluno := st.chat_input("Escreve aqui o teu raciocínio..."):
        st.session_state.mensagens.append({"role": "user", "content": pergunta_aluno})
        with st.chat_message("user"):
            st.markdown(pergunta_aluno)
            
        with st.chat_message("assistant"):
            resposta_placeholder = st.empty()
            try:
                resposta_ia = st.session_state.chat_session.send_message(pergunta_aluno)
                texto_resposta = resposta_ia.text
                
                resposta_completa = ""
                for palavra in texto_resposta.split():
                    resposta_completa += palavra + " "
                    time.sleep(0.03)
                    resposta_placeholder.markdown(resposta_completa + "▌")
                    
                resposta_placeholder.markdown(resposta_completa)
                st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                
            except Exception as e:
                st.error(f"Erro de comunicação: {e}")
