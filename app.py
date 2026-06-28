import streamlit as st
import os
from streamlit_mic_recorder import mic_recorder
from transcritor import transcrever_audio
from estruturador import estruturar_consulta_soap

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuração da página profissional
st.set_page_config(
    page_title="Prontuário IA", 
    page_icon="📋", 
    layout="centered"
)

st.title("📋 Prontuário Inteligente")
st.markdown("Grave a consulta em tempo real ou envie um arquivo de áudio para gerar o prontuário instantaneamente.")

st.divider()

# --- 🧠 GESTÃO DE ESTADO (MEMÓRIA DO APP) ---
# Inicializa o relatório
if "relatorio_soap" not in st.session_state:
    st.session_state.relatorio_soap = ""

# Inicializa o rastreador de novas gravações
if "ultimo_audio_id" not in st.session_state:
    st.session_state.ultimo_audio_id = None

# Função centralizada para processar o áudio
def processar_audio_e_gerar_relatorio(caminho_arquivo):
    try:
        with st.spinner("🧠 Transcrevendo o áudio com ultravelocidade na nuvem..."):
            texto_transcrito = transcrever_audio(caminho_arquivo)
        
        if texto_transcrito.strip() and not texto_transcrito.startswith("⚠️"):
            with st.spinner("📝 Analisando o contexto clínico e estruturando o relatório..."):
                resultado_soap = estruturar_consulta_soap(texto_transcrito)
                
                # Atualiza a memória global (que agora atualiza a caixa de texto automaticamente)
                st.session_state.relatorio_soap = resultado_soap
                
            st.success("✨ Prontuário gerado com sucesso!")
        else:
            st.error(texto_transcrito if texto_transcrito.strip() else "Não foi possível extrair texto deste áudio.")

    except Exception as e:
        st.error(f"Ocorreu um erro no processamento: {e}")
        
    finally:
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)

# 🗂️ Criação de Abas
aba_gravar, aba_upload = st.tabs(["🎙️ Gravar Consulta", "🗂️ Enviar Arquivo"])

# --- ABA 1: GRAVAÇÃO DIRETA ---
with aba_gravar:
    
    # OPÇÃO DE IMAGEM REAL: Se você baixar a foto de um gravador digital (ex: gravador.png), 
    # salve na mesma pasta do projeto e remova o '#' da linha abaixo para exibir:
    # st.image("gravador.png", width=120)
    
    st.markdown("### ⏺️ Gravador Digital")
    st.info("Utilize o gravador integrado para registrar o áudio da consulta.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        audio_gravado = mic_recorder(
            start_prompt="⏺️ Iniciar Gravação", # Ícone clássico de botão de gravar (REC)
            stop_prompt="⏹️ Encerrar e Gerar Relatório",
            just_once=False,
            use_container_width=True,
            key="gravador_hibrido"
        )
        
    if audio_gravado and audio_gravado['id'] != st.session_state.ultimo_audio_id:
        st.session_state.ultimo_audio_id = audio_gravado['id']
        
        caminho_temp_gravacao = "consulta_gravada.webm"
        with open(caminho_temp_gravacao, "wb") as f:
            f.write(audio_gravado['bytes'])
            
        processar_audio_e_gerar_relatorio(caminho_temp_gravacao)

# --- ABA 2: UPLOAD DE ARQUIVO ---
with aba_upload:
    st.markdown("### 📂 Importar Áudio")
    arquivo_audio = st.file_uploader(
        "Anexe o arquivo de áudio do gravador ou dispositivo móvel", 
        type=["webm", "mp3", "wav", "m4a", "ogg"],
        help="Formatos aceitos: .webm, .mp3, .wav, .m4a, .ogg"
    )
    
    if arquivo_audio is not None:
        if st.button("🚀 Analisar Áudio Enviado", use_container_width=True):
            caminho_temp_upload = f"temp_{arquivo_audio.name}"
            
            with open(caminho_temp_upload, "wb") as f:
                f.write(arquivo_audio.getbuffer())
                
            processar_audio_e_gerar_relatorio(caminho_temp_upload)

# 📋 ZONA DE EXIBIÇÃO DO RESULTADO
if st.session_state.relatorio_soap:
    st.divider()
    st.subheader("📋 Prontuário de Admissão Final (Editável)")
    st.markdown("_Clique dentro da caixa de texto para fazer os ajustes necessários antes de colar no sistema da clínica._")
    
    st.text_area(
        label="Documento Clínico:",
        height=450,
        key="relatorio_soap" 
    )
    
    st.info("💡 **Dica de Produtividade:** Clique na caixa acima, aperte `Ctrl + A` para selecionar tudo e `Ctrl + C` para copiar.")
    
    # --- NOVA SEÇÃO: ENVIO POR E-MAIL ---
    st.divider()
    st.markdown("### 📧 Enviar Prontuário por E-mail")
    
    # Cria duas colunas: uma maior para o texto, uma menor para o botão
    col_email, col_botao = st.columns([3, 1])
    
    with col_email:
        email_destino = st.text_input(
            "E-mail do médico:", 
            placeholder="digite.o.email@exemplo.com", 
            label_visibility="collapsed"
        )
        
    with col_botao:
        enviar_email = st.button("🚀 Enviar", use_container_width=True)
        
    if enviar_email:
        if email_destino:
            try:
                # Configuração do e-mail (usando Gmail como exemplo)
                remetente = st.secrets["EMAIL_USER"]
                senha_app = st.secrets["EMAIL_PASSWORD"]
                
                # Montando a mensagem
                msg = MIMEMultipart()
                msg['From'] = remetente
                msg['To'] = email_destino
                msg['Subject'] = "Prontuário de Admissão - Escriba Médico IA"
                
                # O corpo do e-mail é o texto que está na text_area
                corpo_email = st.session_state.relatorio_soap
                msg.attach(MIMEText(corpo_email, 'plain'))
                
                # Conectando ao servidor do Yahoo e enviando
                server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
                server.starttls()
                server.login(remetente, senha_app)
                server.send_message(msg)
                server.quit()
                
                st.success(f"✅ Prontuário enviado com sucesso para {email_destino}!")
            except Exception as e:
                st.error(f"❌ Erro ao enviar e-mail. Verifique as configurações. Detalhes: {e}")
        else:
            st.warning("⚠️ Por favor, informe um endereço de e-mail válido antes de enviar.")