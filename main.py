# Importamos as funções que criamos nos arquivos anteriores
from transcritor import transcrever_audio
from estruturador import estruturar_consulta_soap
import os

def executar_sistema_completo():
    # 1. Defina aqui o nome do SEU arquivo de áudio real
    arquivo_audio = "consulta_teste.ogg" 
    
    if not os.path.exists(arquivo_audio):
        print(f"⚠️ Erro: O arquivo '{arquivo_audio}' não foi encontrado na pasta.")
        return

    print("=== PASSO 1: Iniciando Transcrição do Seu Áudio ===")
    # O Whisper lê o seu áudio e transforma no seu texto real
    texto_real_da_consulta = transcrever_audio(arquivo_audio)
    
    print("\n=== PASSO 2: Enviando Seu Texto Real para a IA Estruturar ===")
    # O Llama 3 lê o seu texto real e cria o prontuário SOAP
    relatorio_soap = estruturar_consulta_soap(texto_real_da_consulta)
    
    print("\n================ RELATÓRIO SOAP REAL GERADO =================\n")
    print(relatorio_soap)

if __name__ == "__main__":
    executar_sistema_completo()