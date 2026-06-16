import streamlit as st
import google.generativeai as genai
import json
import base64
import time
import os

# ==========================================
# 1. FUNÇÕES DE CODIFICAÇÃO (LINK MÁGICO)
# ==========================================
def codificar_config(config_dict):
    json_str = json.dumps(config_dict)
    return base64.urlsafe_b64encode(json_str.encode()).decode()

def descodificar_config(codigo_str):
    try:
        json_str = base64.urlsafe_b64decode(codigo_str.encode()).decode()
        return json.loads(json_str)
    except:
        return None

# ==========================================
# 2. LER O TEMPLATE PEDAGÓGICO DO JSON
# ==========================================
FICHEIRO_CONFIG = "config_tutor.json"
TEMPLATE_BASE = "És um tutor socrático da disciplina de {disciplina}. Nunca dês respostas diretas, faz perguntas orientadoras."

if os.path.exists(FICHEIRO_CONFIG):
    try:
        with open(FICHEIRO_CONFIG, "r", encoding="utf-8") as f:
            dados_json = json.load(f)
            TEMPLATE_BASE = dados_json.get("TEMPLATE_SYSTEM_PROMPT", TEMPLATE_BASE)
    except Exception as e:
        st.warning(f"Aviso: Não foi possível ler o ficheiro JSON. A usar template padrão.")

# ==========================================
# 3. VERIFICAR MODO (PROFESSOR vs ALUNO)
# ==========================================
parametros_url = st.query_params
config_atual = None

if "c" in parametros_url:
    config_atual = descodificar_config(parametros_url["c"])

# ==========================================
# 4. INTERFACE - MODO PROFESSOR (CRIADOR)
# ==========================================
if not config_atual:
    st.set_page_config(page_title="Criador de Tutores IA", page_icon="⚙️", layout="centered")
    st.title("⚙️ Plataforma de Tutores Socráticos")
    st.write("Crie um tutor personalizado para a sua disciplina.")
    st.divider()

    with st.form("form_criacao"):
        nome_prof = st.text_input("O seu Nome (ex: Prof.ª Maria Silva)")
        disciplina = st.text_input("Disciplina ou Módulo (ex: Biologia e Geologia)")
        boas_vindas = st.text_area("Mensagem Inicial da IA", value="Olá! Sou o teu tutor. Que desafio vamos explorar hoje?")
        
        # O campo do System Prompt foi removido daqui!
        gerar_btn = st.form_submit_button("Gerar o Meu Tutor")

    if gerar_btn and nome_prof and disciplina:
        # Injetar a disciplina preenchida no template lido do JSON
        prompt_final = TEMPLATE_BASE.replace("{disciplina}", disciplina)
        
        nova_config = {
            "NOME_PROFESSOR": nome_prof,
            "DISCIPLINA": disciplina,
            "MENSAGEM_BOAS_VINDAS": boas_vindas,
            "SYSTEM_PROMPT": prompt_final # O prompt final e blindado vai aqui
        }
        
        codigo_magico = codificar_config(nova_config)
        
        # URL definitivo da sua aplicação
        link_final = f"https://tutorsocratico-vuenltzglqdgwhegtewr2k.streamlit.app/?c={codigo_magico}"
        
        st.success("🎉 O seu tutor foi criado com sucesso!")
        st.write("Copie o link abaixo e partilhe com os seus alunos:")
        st.code(link_final, language="http")

# ==========================================
# 5. INTERFACE - MODO ALUNO (O CHAT)
# ==========================================
else:
    try:
        CHAVE_API = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=CHAVE_API)
    except Exception as e:
        st.error("Erro ao ler a Chave API. Verifique os Secrets do Streamlit.")
        st.stop()

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
                    
                resposta_placeholder.markdown(resposta_completa)
                st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                
            except Exception as e:
                st.error(f"Erro de comunicação: {e}")
