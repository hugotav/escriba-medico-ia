import streamlit as st
import os
from streamlit_mic_recorder import mic_recorder
from transcritor import transcrever_audio
from estruturador import estruturar_consulta_soap

# Configuração da página profissional
st.set_page_config(
    page_title="Escriba Médico IA", 
    page_icon="🩺", 
    layout="centered"
)

st.title("🩺 Escriba Médico Inteligente")
st.markdown("Grave a consulta em tempo real ou envie um arquivo de áudio para gerar o prontuário SOAP instantaneamente.")

st.divider()

# Inicializa o estado da sessão para manter o relatório editável e estável
if "relatorio_soap" not in st.session_state:
    st.session_state.relatorio_soap = ""

# Função centralizada para processar o áudio (evita repetição de código)
def processar_audio_e_gerar_relatorio(caminho_arquivo):
    try:
        # Passo 1: Transcrição via API da Groq
        with st.spinner("🧠 Transcrevendo o áudio com ultravelocidade na nuvem..."):
            texto_transcrito = transcrever_audio(caminho_arquivo)
        
        # Validação básica
        if texto_transcrito.strip() and not texto_transcrito.startswith("⚠️"):
            
            # Passo 2: Estruturação via API da Groq
            with st.spinner("📝 Analisando o contexto clínico e estruturando o SOAP..."):
                resultado_soap = estruturar_consulta_soap(texto_transcrito)
                st.session_state.relatorio_soap = resultado_soap
                
            st.success("✨ Prontuário gerado com sucesso!")
        else:
            st.error(texto_transcrito if texto_transcrito.strip() else "Não foi possível extrair texto deste áudio.")

    except Exception as e:
        st.error(f"Ocorreu um erro no processamento: {e}")
        
    finally:
        # Garante a eliminação do arquivo temporário
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)

# 🗂️ Criação de Abas para organizar a interface
aba_gravar, aba_upload = st.tabs(["🎤 Gravar Consulta", "📂 Enviar Arquivo"])

# --- ABA 1: GRAVAÇÃO DIRETA ---
with aba_gravar:
    st.markdown("### Gravação Direta no Navegador")
    st.info("Utilize o microfone do seu dispositivo para capturar a consulta.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        audio_gravado = mic_recorder(
            start_prompt="▶️ Iniciar Gravação",
            stop_prompt="⏹️ Encerrar e Gerar Relatório",
            just_once=False,
            use_container_width=True,
            key="gravador_hibrido"
        )
        
    if audio_gravado:
        caminho_temp_gravacao = "consulta_gravada.webm"
        with open(caminho_temp_gravacao, "wb") as f:
            f.write(audio_gravado['bytes'])
            
        processar_audio_e_gerar_relatorio(caminho_temp_gravacao)

# --- ABA 2: UPLOAD DE ARQUIVO ---
with aba_upload:
    st.markdown("### Upload de Arquivo de Áudio")
    arquivo_audio = st.file_uploader(
        "Carregue um arquivo previamente gravado", 
        type=["webm", "mp3", "wav", "m4a", "ogg"],
        help="Formatos aceitos: .webm, .mp3, .wav, .m4a, .ogg"
    )
    
    if arquivo_audio is not None:
        if st.button("🚀 Analisar Áudio Enviado", use_container_width=True):
            caminho_temp_upload = f"temp_{arquivo_audio.name}"
            
            with open(caminho_temp_upload, "wb") as f:
                f.write(arquivo_audio.getbuffer())
                
            processar_audio_e_gerar_relatorio(caminho_temp_upload)

# 📋 ZONA DE EXIBIÇÃO DO RESULTADO (Compartilhada entre as duas abas)
if st.session_state.relatorio_soap:
    st.divider()
    st.subheader("📋 Prontuário SOAP Final (Editável)")
    st.markdown("_Clique dentro da caixa de texto para fazer os ajustes necessários antes de copiar._")
    
    st.session_state.relatorio_soap = st.text_area(
        label="Documento Clínico:",
        value=st.session_state.relatorio_soap,
        height=450,
        key="campo_prontuario_final"
    )
    
    st.info("💡 **Dica de Produtividade:** Clique na caixa acima, aperte `Ctrl + A` para selecionar tudo e `Ctrl + C` para copiar.")
