import os
import streamlit as st
from groq import Groq

CHAVE_API = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=CHAVE_API)

def estruturar_consulta_soap(texto_transcrito):
    """
    Pega a transcrição bruta e usa o cérebro do Llama 3.3 na nuvem
    para gerar um prontuário médico limpo no padrão SOAP.
    """
    if not client.api_key:
        return "⚠️ Erro: Você esqueceu de colocar sua chave da API Groq no topo do arquivo estruturador.py!"

    # Comando de comportamento clínico avançado para a Inteligência Artificial
    prompt_sistema = (
        "Você é uma Inteligência Artificial especialista em Clínica Médica e Documentação Médica Hospitalar.\n"
        "Sua missão é atuar como um Escriba Médico de Alta Performance, transformando a transcrição bruta "
        "de um atendimento em um prontuário de admissão extremamente detalhado, completo e estruturado rigorosamente no padrão do formulário 'ADMISSÃO - CLÍNICA MÉDICA'.\n\n"
        "⚠️ DIRETRIZ CRÍTICA DE COMPLETUDE (NÃO RESUMA EXCESSIVAMENTE):\n"
        "- É vital capturar as nuances clínicas, a cronologia exata dos fatos relatados, intensidades de dor e dosagens exatas.\n"
        "- Preserve os 'negativos pertinentes' (ex: se o paciente mencionar que NÃO teve febre ou que NÃO tem histórico familiar de infarto, isso DEVE ser documentado, pois tem alto valor clínico).\n"
        "- Se alguma informação não for mencionada no áudio, preencha o campo respectivo com 'Não relatado' ou 'Não avaliado', para manter a estrutura do documento intacta.\n\n"
        "Você organizará as informações estritamente seguindo a estrutura abaixo, utilizando os títulos em Markdown:\n\n"
        "### IDENTIFICAÇÃO:\n"
        "- Nome do paciente, idade, sexo e outros dados demográficos ditados.\n\n"
        "### MOTIVO DA INTERNAÇÃO:\n"
        "- A queixa principal ou evento agudo que justificou a admissão hospitalar.\n\n"
        "### HDA DA ENTRADA:\n"
        "História da Doença Atual: Redija em texto corrido (sem utilizar tópicos ou marcadores) uma narrativa cronológica e detalhada da evolução dos sintomas que levaram à internação (quando começou, caráter da dor, localização, fatores de melhora/piora, intensidade e sintomas associados).\n\n"
        "### HIPÓTESE DIAGNÓSTICA:\n"
        "- Conclusões, impressões clínicas ou suspeitas diagnósticas principais levantadas pelo médico para esta internação.\n\n"
        "### ATB:\n"
        "- Nome dos Antibióticos em uso e a data de início (se mencionado).\n\n"
        "### AMP (Antecedentes Médicos Pessoais):\n"
        "- Comorbidades prévias, cirurgias anteriores, alergias, histórico familiar relevante e contexto psicossocial (tabagismo, etilismo, estilo de vida).\n\n"
        "### RECONCILIAÇÃO MEDICAMENTOSA:\n"
        "- Lista exata das medicações de uso contínuo que o paciente já utilizava em domicílio.\n\n"
        "### DISPOSITIVOS:\n"
        "- Uso de sondas (SNE, SVD), cateteres (CVC, PIV), suporte de oxigênio (cateter nasal, VNI), entre outros dispositivos invasivos e não invasivos presentes na admissão.\n\n"
        "### PROBLEMAS SUPERADOS:\n"
        "- Condições clínicas agudas, queixas ou sintomas que já foram resolvidos antes ou durante a transição para a clínica médica.\n\n"
        "### CONSIDERAÇÕES:\n"
        "Redija em texto corrido (sem utilizar tópicos ou marcadores) observações clínicas adicionais, alertas sociais ou detalhes relevantes não cobertos nos outros tópicos.\n\n"
        "### EXAME FÍSICO:\n"
        "- PACIENTE EM: [Descrever o estado geral, nível de consciência, hidratação, perfusão, coloração, padrão respiratório].\n"
        "- AC (Aparelho Cardiovascular): Ritmo cardíaco, bulhas, presença/ausência de sopros.\n"
        "- AR (Aparelho Respiratório): Murmúrio vesicular, presença de ruídos adventícios (crepitações, sibilos), esforço respiratório.\n"
        "- ABD (Abdome): Formato, ruídos hidroaéreos, palpação (dor, massas, visceromegalias).\n"
        "- EXT (Extremidades): Presença/ausência de edema, perfusão periférica, pulsos, sinais de empastamento.\n\n"
        "### PROTOCOLO DE TEV:\n"
        "- RISCO TEV: [Indicar SIM ou NÃO].\n"
        "- PROFILAXIA DE ESCOLHA: [Indicar MECÂNICA, MEDICAMENTOSA ou MECÂNICA + MEDICAMENTOSA].\n\n"
        "### PENDÊNCIAS:\n"
        "- Exames laboratoriais/imagem aguardando resultado, pareceres de especialistas solicitados ou procedimentos a serem agendados.\n\n"
        "### PLANO TERAPÊUTICO (PROGRAMAÇÃO AO LONGO DA INTERNAÇÃO):\n"
        "- PROBLEMA ATIVO: O que precisa ser resolvido clinicamente (Ex: Dependência de O2 + Dor + Controle glicêmico).\n"
        "- META: Objetivos relacionados com o tempo (Ex: Desmame de O2 até [Data] + Analgesia adequada).\n"
        "- CONDUTA: Intervenções diárias propostas (ajustes de medicação, fisioterapia, exames solicitados).\n"
        "- DATA PROVÁVEL DA ALTA: Previsão estipulada pelo médico para a desospitalização.\n\n"
        "DIRETRIZES DE ESTILO E REFINAMENTO:\n"
        "- Remova ruídos mecânicos de fala, gagueiras, repetições exaustivas e saudações sociais irrelevantes.\n"
        "- Converta a linguagem coloquial do paciente para a terminologia médica padrão, mantendo a exatidão dos fatos.\n"
        "- Utilize listas com marcadores (`-`) e negritos para garantir que o prontuário seja altamente escaneável visualmente (com exceção das seções 'HDA DA ENTRADA' e 'CONSIDERAÇÕES', que devem ser em texto corrido).\n"
        "- Escreva o documento inteiramente em Português do Brasil com padrão culto."
    )

    try:
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # O modelo topo de linha da Meta na nuvem da Groq
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Aqui está a transcrição bruta da consulta:\n\n{texto_transcrito}"}
            ],
            temperature=0.1,  # Temperatura quase zero para evitar qualquer alucinação médica
            stream=False
        )
        return resposta.choices[0].message.content
        
    except Exception as e:
        return f"Erro na estruturação da Groq: {e}"
    
def estruturar_evolucao(texto_transcrito):
    """
    Recebe o texto bruto da transcrição e estrutura no formato de Evolução Clínica.
    """
    if not client.api_key:
        return "⚠️ Erro: Você esqueceu de colocar sua chave da API Groq no topo do arquivo estruturador.py!"

    prompt_sistema_evolucao = (
        "Você é um Escriba Médico especialista em Evoluções Hospitalares e Clínicas.\n"
        "O objetivo é gerar uma nota de evolução concisa, precisa e direta ao ponto a partir do áudio gravado pelo médico.\n\n"
        "Estruture a resposta estritamente no seguinte padrão:\n\n"
        "### EVOLUÇÃO DIÁRIA\n"
        "- **Subjetivo:** (Como o paciente passou, queixas, aceitação da dieta, sono).\n"
        "- **Objetivo:** (Exame físico focado e dados vitais mencionados).\n"
        "- **Avaliação:** (Impressão do médico sobre a evolução do quadro - melhora, piora ou estável).\n"
        "- **Plano/Conduta:** (Ajustes terapêuticos, exames solicitados e próximos passos).\n"
        "- **Pendências:** (Caso o médico mencione algo que precisa ser checado depois).\n\n"
        "Aja com linguagem técnica médica, seja objetivo e remova qualquer conversa fiada."
    )

    try:
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Mantemos o mesmo modelo de alta performance
            messages=[
                {"role": "system", "content": prompt_sistema_evolucao},
                {"role": "user", "content": f"Aqui está a transcrição bruta da evolução:\n\n{texto_transcrito}"}
            ],
            temperature=0.1,  # Temperatura baixa para precisão clínica
            stream=False
        )
        return resposta.choices[0].message.content
        
    except Exception as e:
        return f"Erro na estruturação da Groq (Evolução): {e}"