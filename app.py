import streamlit as st
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import bcrypt
from streamlit_mic_recorder import mic_recorder
from transcritor import transcrever_audio
from estruturador import estruturar_consulta_soap, estruturar_evolucao

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import csv
from datetime import datetime

def registrar_log_uso(usuario, tipo):
    with open('logs_uso.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, tipo])

import pandas as pd

def registrar_log_uso(usuario, tipo):
    with open('logs_uso.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Formato: Data, Usuário, Tipo (Admissão ou Evolução)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario, tipo])

# Configuração da página (apenas uma vez)
st.set_page_config(page_title="Escriba Médico IA", page_icon="📋", layout="centered")

# --- SISTEMA DE LOGIN ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login()

# Verifica o status da autenticação
if st.session_state["authentication_status"] is False:
    st.error('❌ Usuário ou senha incorretos')
elif st.session_state["authentication_status"] is None:
    st.warning('🔒 Por favor, insira seu usuário e senha para acessar o sistema.')
elif st.session_state["authentication_status"]:
    
    # === 🛡️ BLINDAGEM DE PRIVACIDADE (TROCA DE USUÁRIO) ===
    if "usuario_ativo" not in st.session_state or st.session_state["usuario_ativo"] != st.session_state["username"]:
        st.session_state.relatorio_soap = ""
        st.session_state.ultimo_audio_id = None
        st.session_state.usuario_ativo = st.session_state["username"]
        st.session_state.modo_anterior = None # Reseta também a aba ao trocar de usuário
    
    # === TUDO AQUI DENTRO SÓ APARECE PARA QUEM ESTÁ LOGADO ===    
    authenticator.logout("Sair do Sistema", "sidebar")
    st.sidebar.write(f'Bem-vindo(a), *{st.session_state["name"]}*')

    # Variáveis e Permissões do usuário logado
    username = st.session_state.get("username")
    is_admin = username and 'admin' in config['credentials']['usernames'].get(username, {}).get('roles', [])
    
    # ==========================================
    # 🎛️ NAVEGAÇÃO LATERAL (SIDEBAR)
    # ==========================================
    st.sidebar.divider()
    st.sidebar.markdown("### Navegação")
    
    tela_atual = "Sistema Médico"
    
    # Se for admin, pode escolher entre o sistema e a gestão
    if is_admin:
        tela_atual = st.sidebar.radio("Área do Sistema:", ["Sistema Médico", "Gestão de Usuários", "📊 Métricas"])
        st.sidebar.divider()
        
    # Se estiver no modo Médico, escolhe o documento
    modo_medico = "Admissão"
    if tela_atual == "Sistema Médico":
        modo_medico = st.sidebar.radio("Tipo de Documento:", ["📋 Admissão", "📈 Evolução"])
        
        # === 🧹 RASTREADOR DE ABAS (LIMPEZA DE TELA) ===
        # Registra qual era a aba na primeira vez
        if "modo_anterior" not in st.session_state:
            st.session_state.modo_anterior = modo_medico
            
        # Se o médico clicou em uma aba diferente da anterior, limpa o relatório
        if st.session_state.modo_anterior != modo_medico:
            st.session_state.relatorio_soap = ""
            st.session_state.ultimo_audio_id = None
            st.session_state.modo_anterior = modo_medico # Atualiza para a nova aba

    # ==========================================
    # TELA 1: GESTÃO DE USUÁRIOS (SÓ ADMIN)
    # ==========================================
    if tela_atual == "Gestão de Usuários":
        st.title("👥 Gestão de Usuários")
        st.markdown("Cadastre novos médicos ou gerencie os acessos ativos.")
        
        st.subheader("Usuários Ativos")
        for usr, dados in config['credentials']['usernames'].items():
            perfil = "Administrador" if "admin" in dados.get('roles', []) else "Médico"
            st.markdown(f"- **{dados['name']}** (`{usr}`) | E-mail: {dados['email']} | Nível: {perfil}")
            
        st.divider()

        tab_novo, tab_editar = st.tabs(["➕ Novo Acesso", "✏️ Editar Usuário"])
        
        with tab_novo:
            with st.form("form_novo_usuario"):
                col1, col2 = st.columns(2)
                with col1:
                    novo_login = st.text_input("Login do Sistema (ex: dr_joao)")
                    novo_nome = st.text_input("Nome Completo")
                with col2:
                    novo_email = st.text_input("E-mail")
                    nova_senha = st.text_input("Senha Temporária", type="password")
                    
                novo_perfil = st.selectbox("Perfil de Acesso", ["medico", "admin"])
                btn_cadastrar = st.form_submit_button("Cadastrar Usuário")
                
                if btn_cadastrar:
                    if not novo_login or not nova_senha or not novo_nome:
                        st.error("⚠️ Preencha os campos obrigatórios (Login, Nome e Senha).")
                    elif novo_login in config['credentials']['usernames']:
                        st.error(f"⚠️ O login '{novo_login}' já existe no sistema.")
                    else:
                        hash_senha = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
                        config['credentials']['usernames'][novo_login] = {
                            'email': novo_email,
                            'failed_login_attempts': 0,
                            'logged_in': False,
                            'name': novo_nome,
                            'password': hash_senha,
                            'roles': [novo_perfil]
                        }
                        with open('config.yaml', 'w') as file:
                            yaml.dump(config, file, default_flow_style=False)
                        st.success(f"✅ Médico(a) {novo_nome} cadastrado com sucesso!")
                        st.rerun() 
                        
        with tab_editar:
            lista_usuarios = list(config['credentials']['usernames'].keys())
            usuario_selecionado = st.selectbox("Selecione o usuário que deseja alterar:", lista_usuarios)
            
            if usuario_selecionado:
                dados_atuais = config['credentials']['usernames'][usuario_selecionado]
                
                with st.form("form_editar_usuario"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_login = st.text_input("Login (Usuário)", value=usuario_selecionado)
                        edit_nome = st.text_input("Nome Completo", value=dados_atuais.get('name', ''))
                    with col2:
                        edit_email = st.text_input("E-mail", value=dados_atuais.get('email', ''))
                        edit_senha = st.text_input("Nova Senha (deixe em branco para manter a atual)", type="password")
                        
                    perfil_atual = "admin" if "admin" in dados_atuais.get('roles', []) else "medico"
                    edit_perfil = st.selectbox("Perfil de Acesso", ["medico", "admin"], index=0 if perfil_atual == "medico" else 1)
                    
                    btn_salvar_edicao = st.form_submit_button("Salvar Alterações")
                    
                    if btn_salvar_edicao:
                        if not edit_login or not edit_nome:
                            st.error("⚠️ Login e Nome são obrigatórios.")
                        elif edit_login != usuario_selecionado and edit_login in config['credentials']['usernames']:
                            st.error(f"⚠️ O login '{edit_login}' já está em uso por outra pessoa.")
                        else:
                            novos_dados = {
                                'email': edit_email,
                                'failed_login_attempts': dados_atuais.get('failed_login_attempts', 0),
                                'logged_in': dados_atuais.get('logged_in', False),
                                'name': edit_nome,
                                'roles': [edit_perfil]
                            }
                            
                            if edit_senha:
                                novos_dados['password'] = bcrypt.hashpw(edit_senha.encode(), bcrypt.gensalt()).decode()
                            else:
                                novos_dados['password'] = dados_atuais['password']
                                
                            if edit_login != usuario_selecionado:
                                del config['credentials']['usernames'][usuario_selecionado]
                                
                            config['credentials']['usernames'][edit_login] = novos_dados
                            
                            with open('config.yaml', 'w') as file:
                                yaml.dump(config, file, default_flow_style=False)
                                
                            st.success(f"✅ Usuário '{edit_nome}' atualizado com sucesso!")
                            st.rerun()

    # ==========================================
    # TELA 2: SISTEMA MÉDICO 
    # ==========================================
    elif tela_atual == "Sistema Médico":
        
        st.title(modo_medico) 
        st.markdown("Grave a consulta em tempo real ou envie um arquivo de áudio para gerar o documento instantaneamente.")
        st.divider()

        # --- 🧠 GESTÃO DE ESTADO ---
        if "relatorio_soap" not in st.session_state:
            st.session_state.relatorio_soap = ""
        if "ultimo_audio_id" not in st.session_state:
            st.session_state.ultimo_audio_id = None

        # --- FUNÇÃO CENTRALIZADA DE PROCESSAMENTO ---
        def processar_audio_e_gerar_relatorio(caminho_arquivo, modo):
            try:
                with st.spinner("🧠 Transcrevendo..."):
                    texto_transcrito = transcrever_audio(caminho_arquivo)
                
                if texto_transcrito.strip() and not texto_transcrito.startswith("⚠️"):
                    with st.spinner(f"📝 Estruturando documento de {modo}..."):
                        
                        if modo == "Admissão":
                            resultado = estruturar_consulta_soap(texto_transcrito)
                        else:
                            resultado = estruturar_evolucao(texto_transcrito)
                            
                        st.session_state.relatorio_soap = resultado
                    st.success(f"✨ {modo} gerada com sucesso!")
                    registrar_log_uso(st.session_state["username"], modo)
                else:
                    st.error("Não foi possível extrair texto do áudio.")
            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                if os.path.exists(caminho_arquivo):
                    os.remove(caminho_arquivo)
            st.rerun()

        # 🗂️ Abas para Gravação ou Upload
        sub_gravar, sub_upload = st.tabs(["🎙️ Gravar", "🗂️ Enviar Arquivo"])
        
        tipo_doc = "Admissão" if modo_medico == "📋 Admissão" else "Evolução"
        
        with sub_gravar:
            audio_gravado = mic_recorder(
                start_prompt="⏺️ Iniciar Gravação",
                stop_prompt="⏹️ Encerrar e Gerar Documento",
                just_once=False,
                use_container_width=True,
                key=f"gravador_{tipo_doc}" 
            )
            
            if audio_gravado and audio_gravado['id'] != st.session_state.get("ultimo_audio_id"):
                st.session_state.ultimo_audio_id = audio_gravado['id']
                caminho_temp = f"temp_gravacao.webm"
                with open(caminho_temp, "wb") as f:
                    f.write(audio_gravado['bytes'])
                processar_audio_e_gerar_relatorio(caminho_temp, tipo_doc)

        with sub_upload:
            arquivo_audio = st.file_uploader("Anexe o áudio", type=["webm", "mp3", "wav", "m4a", "ogg"], key=f"upload_{tipo_doc}")
            if arquivo_audio is not None and st.button("🚀 Analisar Áudio", key=f"btn_analisar_{tipo_doc}"):
                caminho_temp = f"temp_upload.webm"
                with open(caminho_temp, "wb") as f:
                    f.write(arquivo_audio.getbuffer())
                processar_audio_e_gerar_relatorio(caminho_temp, tipo_doc)

        # 📋 ZONA DE EXIBIÇÃO E ENVIO DE E-MAIL
        if st.session_state.relatorio_soap:
            st.divider()
            st.subheader("📋 Documento Clínico Final")
            st.text_area("Resultado:", st.session_state.relatorio_soap, height=450)
            
            st.divider()

            username_logado = st.session_state.get("username")
            email_usuario = config['credentials']['usernames'].get(username_logado, {}).get('email')

            if email_usuario:
                if st.button("📧 Receber relatório por e-mail"):
                    try:
                        remetente = st.secrets["EMAIL_USER"]
                        senha_app = st.secrets["EMAIL_PASSWORD"]
                        
                        msg = MIMEMultipart()
                        msg['From'] = remetente
                        msg['To'] = email_usuario
                        msg['Subject'] = f"Relatório Gerado ({tipo_doc}) - Escriba Médico IA"
                        msg.attach(MIMEText(st.session_state.relatorio_soap, 'plain'))
                        
                        server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
                        server.starttls()
                        server.login(remetente, senha_app)
                        server.send_message(msg)
                        server.quit()
                        
                        st.success(f"✅ Enviado para {email_usuario}!")
                    except Exception as e:
                        st.error(f"Erro ao enviar: {e}")
            else:
                st.warning("⚠️ E-mail não encontrado no cadastro. Verifique seu config.yaml.")

    elif tela_atual == "📊 Métricas":
        st.title("📊 Métricas de Uso")
        
        if not os.path.exists('logs_uso.csv'):
            st.info("Nenhum dado de uso registrado ainda. Gere um relatório para começar.")
        else:
            # Importa o pandas apenas aqui para garantir que ele está disponível
            import pandas as pd 
            
            # Lê o arquivo
            df = pd.read_csv('logs_uso.csv', names=['Data', 'Usuario', 'Tipo'])
            
            if df.empty:
                st.info("Arquivo de log vazio.")
            else:
                # Agrupa os dados
                metricas = df.groupby(['Usuario', 'Tipo']).size().unstack(fill_value=0)
                
                st.subheader("Relatórios Gerados por Médico")
                st.dataframe(metricas, use_container_width=True)
                
                st.subheader("Resumo Visual")
                st.bar_chart(metricas)