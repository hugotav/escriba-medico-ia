import os
from groq import Groq

CHAVE_API = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=CHAVE_API)

def transcrever_audio(caminho_audio):
    """
    Envia o áudio gravado para a API da Groq usando o modelo Whisper.
    Transcreve minutos de conversa em poucos segundos.
    """
    if not client.api_key:
        return "⚠️ Erro: Você esqueceu de colocar sua chave da API Groq no topo do arquivo transcritor.py!"

    if not os.path.exists(caminho_audio):
        return f"⚠️ Erro: O arquivo '{caminho_audio}' não foi gerado pelo navegador."

    try:
        # Abre o arquivo de áudio bruto gerado pelo Streamlit
        with open(caminho_audio, "rb") as arquivo:
            transcricao = client.audio.transcriptions.create(
                file=(os.path.basename(caminho_audio), arquivo.read()),
                model="whisper-large-v3-turbo",  # Modelo ultra-rápido e preciso da Groq
                response_format="text",
                language="pt"  # Força o algoritmo a focar no Português do Brasil
            )
        return transcricao
        
    except Exception as e:
        return f"Erro na transcrição da Groq: {e}"
