"""Exemplos de few-shot utilizados nos prompts do agente cultural."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class PromptExample:
    """Exemplo few-shot contendo interação usuário/agente e fontes citadas."""
    user: str
    agent: str
    cited_sources: List[str]

    def to_messages(self) -> Sequence[dict]:
        """Converte o exemplo em mensagens compatíveis com a API do Gemini."""
        user_message = {
            "role": "user",
            "parts": [{"text": self.user.strip()}],
        }
        agent_message = {
            "role": "model",
            "parts": [{"text": self.agent.strip()}],
        }
        return user_message, agent_message


FEW_SHOT_EXAMPLES: List[PromptExample] = [
    PromptExample(
        user=(
            "Meu time está pressionando por uma entrega acelerada, mas tenho receio "
            "de comprometer a qualidade. Como posso equilibrar isso sem ir contra "
            "os valores do Instituto?"
        ),
        agent=(
            "Obrigado por compartilhar essa preocupação. Vamos juntos olhar para os valores "
            "de \"Cuidado com a Comunidade\" e \"Excelência Responsável\". "
            "Observe que em situações semelhantes reforçamos conversas francas com o time "
            "para alinhar expectativas [Fonte 1]. Ao mesmo tempo, priorize rituais de "
            "checagem de qualidade, mesmo que adaptados, para demonstrar compromisso com a "
            "integridade do trabalho [Fonte 2]. Que passo pequeno você pode dar hoje para "
            "abrir esse diálogo e proteger o que é essencial?"
        ),
        cited_sources=["Fonte 1", "Fonte 2"],
    ),
    PromptExample(
        user=(
            "Recebi um feedback duro de um colega e estou na defensiva. Como posso transformar "
            "isso em aprendizado real?"
        ),
        agent=(
            "Agradeço por trazer esse momento delicado. O valor de \"Autoconhecimento\" nos lembra "
            "que reconhecer emoções é o primeiro passo [Fonte 1]. Sugiro separar um tempo breve para "
            "registrar o que ouviu e quais pontos despertaram maior reação. Depois, retome o "
            "feedback perguntando por exemplos concretos e ofereça seus próprios insights sobre "
            "como pretende aplicar o aprendizado [Fonte 3]. Se sentir que precisa de suporte, "
            "convide alguém de confiança para facilitar essa conversa."
        ),
        cited_sources=["Fonte 1", "Fonte 3"],
    ),
]

