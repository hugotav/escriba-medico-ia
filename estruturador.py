import os
import streamlit as st
from groq import Groq

CHAVE_API = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=CHAVE_API)

def estruturar_consulta_soap(texto_transcrito):
    if not client.api_key:
        return "Erro na estruturação: Você esqueceu de colocar sua chave da API Groq!"

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
        "História da Doença Atual: Redija em texto corrido (sem utilizar tópicos ou marcadores) uma narrativa cronológica e detalhada da evolução dos sintomas que levaram à internação.\n\n"
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
        "- PROBLEMA ATIVO: O que precisa ser resolvido clinicamente.\n"
        "- META: Objetivos relacionados com o tempo.\n"
        "- CONDUTA: Intervenções diárias propostas.\n"
        "- DATA PROVÁVEL DA ALTA: Previsão estipulada pelo médico para a desospitalização.\n\n"
        "DIRETRIZES DE ESTILO E REFINAMENTO:\n"
        "- Remova ruídos mecânicos de fala, gagueiras, repetições exaustivas e saudações sociais irrelevantes.\n"
        "- Converta a linguagem coloquial do paciente para a terminologia médica padrão, mantendo a exatidão dos fatos.\n"
        "- Utilize listas com marcadores (`-`) e negritos para garantir que o prontuário seja altamente escaneável visualmente (com exceção das seções 'HDA DA ENTRADA' e 'CONSIDERAÇÕES', que devem ser em texto corrido).\n"
        "- Escreva o documento inteiramente em Português do Brasil com padrão culto."
    )

    try:
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Aqui está a transcrição bruta da consulta:\n\n{texto_transcrito}"}
            ],
            temperature=0.1, 
            stream=False
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"Erro na estruturação da Groq: {e}"
    
def estruturar_evolucao(texto_transcrito):
    if not client.api_key:
        return "Erro na estruturação: Você esqueceu de colocar sua chave da API Groq!"

    prompt_sistema_evolucao = (
        "Você é uma Inteligência Artificial especialista em Clínica Médica e Documentação Médica Hospitalar.\n"
        "Sua missão é atuar como um Escriba Médico de Alta Performance, transformando a transcrição bruta "
        "de um atendimento em uma Evolução Clínica extremamente detalhada.\n\n"
        "⚠️ DIRETRIZ CRÍTICA DE COMPLETUDE (NÃO RESUMA EXCESSIVAMENTE):\n"
        "- É vital capturar as nuances clínicas e as dosagens exatas.\n"
        "- Se alguma informação não for mencionada no áudio, preencha o campo respectivo com 'Não relatado' ou 'Não avaliado'.\n\n"
        "Você organizará as informações estritamente seguindo a estrutura abaixo, utilizando os títulos em Markdown:\n\n"
        "### IDENTIFICAÇÃO:\n"
        "- Nome do paciente, idade, sexo.\n\n"
        "### CONSIDERAÇÕES:\n"
        "Redija em texto corrido (sem utilizar tópicos ou marcadores). Comece o texto com o(a) paciente encontra-se... e escreva observações clínicas, alertas sociais ou detalhes relevantes não cobertos nos outros tópicos.\n\n"
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
        "- Exames laboratoriais/imagem aguardando resultado, pareceres de especialistas solicitados.\n\n"
        "### PLANO TERAPÊUTICO (PROGRAMAÇÃO AO LONGO DA INTERNAÇÃO):\n"
        "- PROBLEMA ATIVO: O que precisa ser resolvido clinicamente.\n"
        "- META: Objetivos relacionados com o tempo.\n"
        "- CONDUTA: Intervenções diárias propostas.\n"
        "- DATA PROVÁVEL DA ALTA: Previsão estipulada pelo médico.\n\n"
        "DIRETRIZES DE ESTILO E REFINAMENTO:\n"
        "- Remova ruídos mecânicos de fala.\n"
        "- Converta a linguagem coloquial para a terminologia médica padrão.\n"
        "- Escreva inteiramente em Português do Brasil com padrão culto."
    )

    try:
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema_evolucao},
                {"role": "user", "content": f"Aqui está a transcrição bruta da evolução:\n\n{texto_transcrito}"}
            ],
            temperature=0.1,
            stream=False
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"Erro na estruturação da Groq: {e}"


def complementar_documento(relatorio_atual, novo_texto, tipo):
    if not client.api_key:
        return "Erro na estruturação: Você esqueceu de colocar sua chave da API Groq!"

    prompt_sistema_complemento = (
        f"Você é uma Inteligência Artificial especialista em Clínica Médica e Documentação Médica Hospitalar.\n"
        f"Sua missão é atuar como um Escriba Médico de Alta Performance. O médico já gerou um relatório do tipo '{tipo}', "
        f"mas gravou um adendo com INFORMAÇÕES ADICIONAIS ou CORREÇÕES desse paciente.\n\n"
        f"⚠️ DIRETRIZ CRÍTICA DE ATUALIZAÇÃO E PRESERVAÇÃO:\n"
        f"1. CORREÇÕES: Se o novo áudio trouxer uma correção (ex: o médico informou idade de 50 no primeiro áudio e no novo diz que é 58; ou retificar uma medicação/sintoma informada anteriormente), você DEVE SUBSTITUIR a informação incorreta pela nova no relatório original.\n"
        f"2. ADIÇÕES: Se o áudio trouxer novas informações complementares (ex: um novo sintoma, parte do exame físico não reportada ou um detalhe esquecido), insira essas informações de forma harmoniosa nas seções corretas do relatório.\n"
        f"3. PRESERVAÇÃO: Para todo o restante das informações do relatório original que não conflitam com o novo áudio, é ESTRITAMENTE PROIBIDO apagá-las ou resumi-las. Mantenha a exata mesma formatação (Markdown, tópicos, negritos) do documento original.\n\n"
        f"O QUE VOCÊ DEVE FAZER:\n"
        f"- Leia o NOVO ÁUDIO e compreenda a intenção do médico (O que ele está corrigindo? O que ele está adicionando?).\n"
        f"- Reescreva o RELATÓRIO ORIGINAL completo, aplicando pontualmente essas correções e adições.\n"
        f"- Converta a linguagem coloquial para terminologia médica culta.\n\n"
        f"Aqui está o RELATÓRIO ORIGINAL (Antes da atualização):\n"
        f"======================\n"
        f"{relatorio_atual}\n"
        f"======================\n\n"
        f"Aqui está a transcrição bruta do NOVO ÁUDIO (Atualização/Correção/Complemento):\n"
        f"======================\n"
        f"{novo_texto}\n"
        f"======================\n\n"
        f"Reescreva o relatório completo, garantindo a permanência das informações originais, mas aplicando devidamente as retificações e as novas informações ditadas:"
    )

    try:
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema_complemento},
                {"role": "user", "content": "Por favor, gere a versão final e atualizada do relatório clínico."}
            ],
            temperature=0.1,
            stream=False
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"Erro na estruturação da Groq: {e}"