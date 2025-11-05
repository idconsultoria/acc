"""Serviço para classificar conversas em tópicos usando Gemini."""
import google.generativeai as genai
from typing import Optional


class TopicClassifier:
    """Serviço para classificar conversas em tópicos usando Gemini Flash 2.5."""
    
    def __init__(self, api_key: str):
        """
        Inicializa o classificador de tópicos.
        
        Args:
            api_key: Chave da API do Google Gemini
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def classify_conversation(
        self,
        user_query: str,
        agent_response: str,
        existing_topics: list[str]
    ) -> str:
        """
        Classifica uma conversa em um tópico existente ou retorna um novo tópico.
        
        Args:
            user_query: A pergunta original do usuário
            agent_response: A primeira resposta do agente
            existing_topics: Lista de nomes de tópicos já existentes
            
        Returns:
            Nome do tópico (priorizando existentes, ou criando novo se necessário)
        """
        # Constrói a lista de tópicos existentes
        topics_list = "\n".join([f"- {topic}" for topic in existing_topics]) if existing_topics else "Nenhum tópico existente ainda."
        
        # Prompt para o Gemini
        prompt = f"""Você é um classificador de conversas. Sua tarefa é classificar a conversa abaixo em um tópico.

REGRAS IMPORTANTES:
1. PRIMEIRO, verifique se algum dos tópicos existentes abaixo se aplica à conversa. Sempre priorize usar um tópico existente.
2. Se nenhum tópico existente se aplicar, retorne APENAS o nome do novo tópico (em português, curto e descritivo).
3. Retorne APENAS o nome do tópico, nada mais. Sem explicações, sem pontuação extra, apenas o nome.
4. Evite nomes de tópicos genéricos preferindo nomes mais específicos. Alguns exemplos seriam "Feedbacks", "Sentimentos de Inadequação", "Progressão de Carreira", "Conflitos com Pares", "Conflitos com Líderes", "Conflitos com Liderados", etc.

TÓPICOS EXISTENTES:
{topics_list}

CONVERSA:
Usuário: {user_query}

Agente: {agent_response}

TÓPICO (apenas o nome, priorizando existente):"""

        try:
            response = self.model.generate_content(prompt)
            
            if hasattr(response, 'text'):
                topic_name = response.text.strip()
            elif hasattr(response, 'parts') and response.parts:
                topic_name = response.parts[0].text.strip()
            else:
                topic_name = str(response).strip()
            
            # Remove pontuação extra e normaliza
            topic_name = topic_name.strip('.,!?;:')
            
            # Se o tópico retornado está na lista de existentes, retorna ele
            # Caso contrário, pode ser um novo tópico ou uma variação
            # Vamos verificar se há correspondência aproximada
            for existing in existing_topics:
                if existing.lower() in topic_name.lower() or topic_name.lower() in existing.lower():
                    return existing
            
            # Se não encontrou correspondência, retorna o tópico retornado (novo)
            return topic_name if topic_name else "Geral"
            
        except Exception as e:
            # Em caso de erro, loga e retorna um tópico padrão
            print(f"Erro ao classificar tópico: {e}")
            import traceback
            traceback.print_exc()
            return "Geral"

