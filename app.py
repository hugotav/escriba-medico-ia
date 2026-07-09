import streamlit as st
import os
import bcrypt
import streamlit_authenticator as stauth
from streamlit_mic_recorder import mic_recorder
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime
import time

# ==========================================
# ⚙️ CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(page_title="VoxReport IA", page_icon="📋", layout="centered")

# 💡 CORREÇÃO VISUAL: Evita que o botão de áudio fique cortado na parte inferior
st.markdown("""
<style>
    iframe[title*="mic_recorder"] {
        min-height: 52px !important;
    }
</style>
""", unsafe_allow_html=True)

def obter_conexao():
    # Abre uma conexão super rápida. Autocommit evita locks no banco de dados.
    conn = psycopg2.connect(st.secrets["DB_URI"])
    conn.autocommit = True
    return conn

# 💡 AUTO-REPARAÇÃO: Cria a coluna 'ativo' automaticamente no seu banco de dados se ela não existir
def auto_corrigir_banco():
    try:
        conn = obter_conexao()
        cur = conn.cursor()
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE;")
        cur.close()
        conn.close()
    except Exception:
        pass # Se falhar, o erro real será capturado na função principal abaixo

auto_corrigir_banco()

# ==========================================
# 🚀 FUNÇÕES DE BANCO DE DADOS (COM CACHE ULTRA-RÁPIDO)
# ==========================================
@st.cache_data(ttl=300, show_spinner=False)
def carregar_usuarios_do_banco():
    conn = None
    cur = None
    try:
        conn = obter_conexao()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT username, name, email, password, role, COALESCE(ativo, TRUE) as ativo FROM usuarios")
        usuarios_db = cur.fetchall()
        
        credentials = {"usernames": {}}
        for u in usuarios_db:
            if u.get('ativo', True): # Só carrega para o login se estiver ativo
                credentials["usernames"][u['username']] = {
                    "name": u['name'],
                    "password": u['password'],
                    "email": u['email'],
                    "role": u['role']
                }
        return credentials, usuarios_db
    except Exception as e:
        # 💡 AGORA ELE MOSTRA O ERRO EXATO EM VEZ DE ENTRAR EM LOOP
        return None, str(e)
    finally:
        if cur: cur.close()
        if conn: conn.close()

@st.cache_data(ttl=300, show_spinner=False)
def carregar_metricas():
    conn = None
    cur = None
    try:
        conn = obter_conexao()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT data, usuario, tipo FROM logs_uso ORDER BY data DESC")
        registros = cur.fetchall()
        return registros
    except:
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()

@st.cache_data(ttl=300, show_spinner=False)
def carregar_historico_pessoal(usuario):
    conn = None
    cur = None
    try:
        conn = obter_conexao()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT data, tipo, conteudo FROM historico_relatorios WHERE usuario = %s ORDER BY data DESC LIMIT 50", (usuario,))
        registros = cur.fetchall()
        return registros
    except:
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()

def registrar_log_uso(usuario, tipo):
    try:
        conn = obter_conexao()
        cur = conn.cursor()
        cur.execute("INSERT INTO logs_uso (usuario, tipo) VALUES (%s, %s)", (usuario, tipo))
        cur.close()
        conn.close()
        carregar_metricas.clear() # Limpa o cache para a aba de métricas atualizar na hora
    except Exception:
        pass 

def salvar_historico_db(usuario, tipo, conteudo):
    try:
        conn = obter_conexao()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO historico_relatorios (usuario, tipo, conteudo) VALUES (%s, %s, %s)",
            (usuario, tipo, conteudo)
        )
        cur.close()
        conn.close()
        carregar_historico_pessoal.clear() # Limpa o cache para o histórico atualizar na hora
    except Exception as e:
        st.error(f"⚠️ Erro ao guardar no histórico permanente: {e}")

# ==========================================
# 🔐 SISTEMA DE LOGIN (À PROVA DE FALHAS)
# ==========================================
dados_banco = carregar_usuarios_do_banco()

# Se o banco falhar, o erro exato aparecerá aqui na sua tela
if dados_banco[0] is None:
    st.error(f"🚨 ERRO CRÍTICO NO BANCO DE DADOS: {dados_banco[1]}")
    st.stop()

credentials, lista_usuarios_db = dados_banco

authenticator = stauth.Authenticate(
    credentials,
    "escriba_medico_cookie",
    "chave_secreta_segura",
    cookie_expiry_days=30
)

if not st.session_state.get("authentication_status"):
    st.title("📋 VoxReport IA")

authenticator.login(location="main")

if st.session_state.get("authentication_status") is False:
    st.error('❌ Utilizador inativo ou palavra-passe incorreta')
    st.stop()
elif st.session_state.get("authentication_status") is None:
    st.warning('Por favor, insira as suas credenciais.')
    st.stop()

# ==========================================
# 🚀 ÁREA AUTENTICADA (SISTEMA PRINCIPAL)
# ==========================================
username = st.session_state["username"]
name = st.session_state["name"]

dados_usuario = credentials["usernames"][username]
is_admin = dados_usuario["role"] == "admin"
email_usuario = dados_usuario["email"]

authenticator.logout(button_name="Sair do Sistema", location="sidebar")
st.sidebar.write(f'Bem-vindo(a), *{name}*')

for chave in ["relatorio_soap", "ultimo_audio_id", "ultimo_comp_id", "modo_anterior", "usuario_ativo", "chave_texto", "radio_acao"]:
    if chave not in st.session_state:
        if chave == "relatorio_soap":
            st.session_state[chave] = ""
        elif chave == "chave_texto":
            st.session_state[chave] = str(uuid.uuid4())
        elif chave == "radio_acao":
            st.session_state[chave] = "📋 Admissão"
        else:
            st.session_state[chave] = None
        
if st.session_state["usuario_ativo"] != username:
    st.session_state.relatorio_soap = ""
    st.session_state.chave_texto = str(uuid.uuid4())
    st.session_state.ultimo_audio_id = None
    st.session_state.ultimo_comp_id = None
    st.session_state.usuario_ativo = username
    st.session_state.modo_anterior = None 

st.sidebar.divider()
st.sidebar.markdown("### Navegação")

tela_atual = "Sistema Médico"
if is_admin:
    tela_atual = st.sidebar.radio("Área do Sistema:", ["Sistema Médico", "Gestão de Utilizadores", "Métricas"])
    st.sidebar.divider()
    
modo_medico = "Admissão"
if tela_atual == "Sistema Médico":
    modo_medico = st.sidebar.radio("Menu:", ["📋 Admissão", "📈 Evolução", "📂 Histórico"], key="radio_acao")
    
    if st.session_state.modo_anterior != modo_medico:
        if modo_medico in ["📋 Admissão", "📈 Evolução"] and st.session_state.modo_anterior in ["📋 Admissão", "📈 Evolução"]:
            st.session_state.relatorio_soap = ""
            st.session_state.chave_texto = str(uuid.uuid4())
            st.session_state.ultimo_audio_id = None
            st.session_state.ultimo_comp_id = None
        st.session_state.modo_anterior = modo_medico 

# ==========================================
# TELA: GESTÃO DE UTILIZADORES
# ==========================================
if tela_atual == "Gestão de Utilizadores":
    st.title("👥 Gestão de Utilizadores")
    st.subheader("Utilizadores Ativos")
    
    for u in lista_usuarios_db:
        status = "🟢 Ativo" if u.get('ativo', True) else "🔴 Inativo"
        st.markdown(f"- {status} | **{u['name']}** (`{u['username']}`) | E-mail: {u['email']} | Perfil: {u['role']}")
    st.divider()

    tab_novo, tab_editar = st.tabs(["➕ Novo Acesso", "✏️ Editar / Excluir Utilizador"])
    
    with tab_novo:
        with st.form("form_novo_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                novo_login = st.text_input("Login (ex: dr_joao)")
                novo_nome = st.text_input("Nome Completo")
            with col2:
                novo_email = st.text_input("E-mail")
                nova_senha = st.text_input("Palavra-passe Inicial", type="password")
                
            novo_perfil = st.selectbox("Perfil de Acesso", ["medico", "admin"])
            btn_cadastrar = st.form_submit_button("Cadastrar Utilizador")
            
            if btn_cadastrar:
                if not novo_login or not nova_senha or not novo_nome:
                    st.error("⚠️ Preencha os campos obrigatórios.")
                else:
                    try:
                        hash_senha = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
                        conn = obter_conexao()
                        cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO usuarios (username, name, email, password, role, ativo) VALUES (%s, %s, %s, %s, %s, TRUE)",
                            (novo_login, novo_nome, novo_email, hash_senha, novo_perfil)
                        )
                        cur.close()
                        conn.close()
                        
                        carregar_usuarios_do_banco.clear() 
                        st.success(f"✅ Utilizador {novo_nome} cadastrado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")

    with tab_editar:
        lista_usernames = [u['username'] for u in lista_usuarios_db]
        usuario_selecionado = st.selectbox("Selecione o utilizador que deseja alterar:", lista_usernames)
        
        if usuario_selecionado:
            dados_atuais = next(u for u in lista_usuarios_db if u['username'] == usuario_selecionado)
            
            with st.form("form_editar_usuario"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_login = st.text_input("Login (Username)", value=dados_atuais['username'])
                    edit_nome = st.text_input("Nome Completo", value=dados_atuais['name'])
                    edit_email = st.text_input("E-mail", value=dados_atuais['email'])
                with col2:
                    edit_senha = st.text_input("Nova Palavra-passe (deixe em branco para manter)", type="password")
                    edit_perfil = st.selectbox("Perfil de Acesso", ["medico", "admin"], index=0 if dados_atuais['role'] == "medico" else 1)
                    edit_ativo = st.checkbox("🟢 Acesso Liberado (Desmarque para inativar o usuário)", value=dados_atuais.get('ativo', True))
                
                col_btn_salvar, col_btn_excluir = st.columns(2)
                with col_btn_salvar:
                    btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                with col_btn_excluir:
                    btn_excluir_usuario = st.form_submit_button("🗑️ Excluir Utilizador", use_container_width=True)
                
                if btn_salvar_edicao:
                    if not edit_nome or not edit_login:
                        st.error("⚠️ O Nome e o Login são obrigatórios.")
                    else:
                        try:
                            conn = obter_conexao()
                            cur = conn.cursor()
                            
                            if edit_login != usuario_selecionado:
                                cur.execute("UPDATE historico_relatorios SET usuario=%s WHERE usuario=%s", (edit_login, usuario_selecionado))
                                cur.execute("UPDATE logs_uso SET usuario=%s WHERE usuario=%s", (edit_login, usuario_selecionado))
                            
                            if edit_senha:
                                hash_senha = bcrypt.hashpw(edit_senha.encode(), bcrypt.gensalt()).decode()
                                cur.execute(
                                    "UPDATE usuarios SET username=%s, name=%s, email=%s, role=%s, password=%s, ativo=%s WHERE username=%s",
                                    (edit_login, edit_nome, edit_email, edit_perfil, hash_senha, edit_ativo, usuario_selecionado)
                                )
                            else:
                                cur.execute(
                                    "UPDATE usuarios SET username=%s, name=%s, email=%s, role=%s, ativo=%s WHERE username=%s",
                                    (edit_login, edit_nome, edit_email, edit_perfil, edit_ativo, usuario_selecionado)
                                )
                            cur.close()
                            conn.close()
                            
                            carregar_usuarios_do_banco.clear()
                            carregar_historico_pessoal.clear()
                            carregar_metricas.clear()
                            
                            st.success(f"✅ Utilizador '{edit_nome}' atualizado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {e}")

                if btn_excluir_usuario:
                    if usuario_selecionado == username:
                        st.error("⚠️ Não pode excluir o seu próprio utilizador enquanto estiver logado.")
                    else:
                        try:
                            conn = obter_conexao()
                            cur = conn.cursor()
                            cur.execute("DELETE FROM historico_relatorios WHERE usuario=%s", (usuario_selecionado,))
                            cur.execute("DELETE FROM logs_uso WHERE usuario=%s", (usuario_selecionado,))
                            cur.execute("DELETE FROM usuarios WHERE username=%s", (usuario_selecionado,))
                            cur.close()
                            conn.close()
                            
                            carregar_usuarios_do_banco.clear()
                            carregar_historico_pessoal.clear()
                            carregar_metricas.clear()
                            
                            st.success(f"✅ Utilizador '{usuario_selecionado}' excluído permanentemente!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")

# ==========================================
# TELA: SISTEMA MÉDICO (ADMISSÃO / EVOLUÇÃO)
# ==========================================
elif tela_atual == "Sistema Médico" and modo_medico in ["📋 Admissão", "📈 Evolução"]:
    st.title(modo_medico) 
    st.markdown("Grave a consulta ou envie um ficheiro de áudio.")
    st.divider()

    def processar_audio_e_gerar_relatorio(caminho_arquivo, modo, complementar=False):
        from transcritor import transcrever_audio
        from estruturador import estruturar_consulta_soap, estruturar_evolucao, complementar_documento
        
        sucesso = False
        try:
            with st.spinner("🧠 A transcrever..."):
                texto_transcrito = transcrever_audio(caminho_arquivo)
            
            if texto_transcrito.strip() and not texto_transcrito.startswith("⚠️"):
                acao_msg = "atualizar/complementar" if complementar else "estruturar"
                with st.spinner(f"📝 A {acao_msg} o documento de {modo}..."):
                    
                    if complementar:
                        resultado = complementar_documento(st.session_state.relatorio_soap, texto_transcrito, modo)
                    else:
                        resultado = estruturar_consulta_soap(texto_transcrito) if modo == "Admissão" else estruturar_evolucao(texto_transcrito)
                    
                    if "Erro na estruturação" in resultado:
                        st.error(resultado)
                    else:
                        st.session_state.relatorio_soap = resultado
                        st.session_state.chave_texto = str(uuid.uuid4())
                        
                        tipo_hist = f"{modo} (Complemento)" if complementar else modo
                        salvar_historico_db(username, tipo_hist, resultado)
                        
                        st.success(f"✨ {modo} {'atualizada' if complementar else 'gerada'} com sucesso!")
                        registrar_log_uso(username, modo)
                        sucesso = True
            else:
                st.error("Não foi possível extrair texto ou áudio vazio.")
        except Exception as e:
            st.error(f"Erro inesperado no processamento: {e}")
        finally:
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
        
        if sucesso:
            st.rerun()

    sub_gravar, sub_upload = st.tabs(["🎙️ Gravar", "🗂️ Enviar Ficheiro"])
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
            caminho_temp = f"temp_gravacao_{username}_{uuid.uuid4().hex}.webm"
            with open(caminho_temp, "wb") as f:
                f.write(audio_gravado['bytes'])
            processar_audio_e_gerar_relatorio(caminho_temp, tipo_doc, complementar=False)

    with sub_upload:
        arquivo_audio = st.file_uploader("Anexe o áudio inicial", type=["webm", "mp3", "wav", "m4a", "ogg"], key=f"upload_{tipo_doc}")
        if arquivo_audio is not None and st.button("🚀 Analisar Áudio", key=f"btn_analisar_{tipo_doc}"):
            caminho_temp = f"temp_upload_{username}_{uuid.uuid4().hex}.webm"
            with open(caminho_temp, "wb") as f:
                f.write(arquivo_audio.getbuffer())
            processar_audio_e_gerar_relatorio(caminho_temp, tipo_doc, complementar=False)

    # ==========================================
    # ZONA DO RELATÓRIO FINAL
    # ==========================================
    if st.session_state.relatorio_soap:
        st.divider()
        st.subheader("📋 Documento Final")
        
        def atualizar_texto_editavel():
            st.session_state.relatorio_soap = st.session_state[st.session_state.chave_texto]

        st.text_area(
            "Resultado (Editável):", 
            value=st.session_state.relatorio_soap, 
            key=st.session_state.chave_texto,      
            height=450,
            on_change=atualizar_texto_editavel
        )
        
        st.write("") 

        col_email, col_comp = st.columns(2)
        
        with col_email:
            if email_usuario:
                if st.button("📧 Receber por e-mail", use_container_width=True):
                    try:
                        remetente = st.secrets["EMAIL_USER"]
                        msg = MIMEMultipart()
                        msg['From'] = remetente
                        msg['To'] = email_usuario
                        msg['Subject'] = f"Relatório Gerado ({tipo_doc}) - Escriba Médico IA"
                        msg.attach(MIMEText(st.session_state.relatorio_soap, 'plain'))
                        
                        server = smtplib.SMTP('smtp.mail.yahoo.com', 587)
                        server.starttls()
                        server.login(remetente, st.secrets["EMAIL_PASSWORD"])
                        server.send_message(msg)
                        server.quit()
                        st.success(f"✅ Enviado para {email_usuario}!")
                    except Exception as e:
                        st.error(f"Erro ao enviar: {e}")
            else:
                st.warning("⚠️ E-mail não cadastrado.")

        with col_comp:
            audio_comp = mic_recorder(
                start_prompt="🎙️ Gravar Complemento (Áudio)",
                stop_prompt="⏹️ Encerrar e Atualizar",
                just_once=False,
                use_container_width=True,
                key=f"comp_gravador_{tipo_doc}" 
            )
            
            if audio_comp and audio_comp['id'] != st.session_state.ultimo_comp_id:
                st.session_state.ultimo_comp_id = audio_comp['id']
                caminho_temp = f"temp_comp_grav_{username}_{uuid.uuid4().hex}.webm"
                with open(caminho_temp, "wb") as f:
                    f.write(audio_comp['bytes'])
                processar_audio_e_gerar_relatorio(caminho_temp, tipo_doc, complementar=True)

# ==========================================
# TELA: HISTÓRICO DA SESSÃO
# ==========================================
elif tela_atual == "Sistema Médico" and modo_medico == "📂 Histórico":
    st.title("📂 Histórico de Relatórios")
    st.markdown("Veja todos os prontuários e evoluções gerados por si. Estes dados estão guardados permanentemente na sua conta.")
    st.divider()
    
    def carregar_para_edicao(conteudo_salvo, tipo_salvo):
        tipo_base = "📋 Admissão" if "Admissão" in tipo_salvo else "📈 Evolução"
        st.session_state.radio_acao = tipo_base
        st.session_state.relatorio_soap = conteudo_salvo
        st.session_state.chave_texto = str(uuid.uuid4())
    
    historico_db = carregar_historico_pessoal(username)
    
    if not historico_db:
        st.info("Nenhum relatório foi gerado por si ainda.")
    else:
        for idx, item in enumerate(historico_db):
            data_formatada = item['data'].strftime("%d/%m/%Y %H:%M") if hasattr(item['data'], 'strftime') else item['data']
            
            with st.expander(f"{item['tipo']} - Gerado em: {data_formatada}", expanded=(idx==0)):
                st.text_area("Conteúdo:", item['conteudo'], height=250, key=f"hist_db_{idx}", disabled=True)
                
                st.button(
                    "✏️ Carregar para Edição / Complementar", 
                    key=f"btn_load_{idx}", 
                    use_container_width=True,
                    on_click=carregar_para_edicao,     
                    args=(item['conteudo'], item['tipo']) 
                )

# ==========================================
# TELA: MÉTRICAS
# ==========================================
elif tela_atual == "Métricas":
    st.title("Métricas de Uso")
    
    registros = carregar_metricas()
    
    if not registros:
        st.info("Nenhum registo ainda.")
    else:
        df = pd.DataFrame(registros)
        metricas = df.groupby(['usuario', 'tipo']).size().unstack(fill_value=0)
        st.dataframe(metricas, use_container_width=True)
        st.bar_chart(metricas)