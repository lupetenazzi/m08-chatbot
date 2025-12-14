import os
from pathlib import Path
import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

from agent_compliance import ComplianceChatbot
from agent_conspiracy import ConspiracyChatbot
from agent_fraud_detection import create_fraud_agent


INTENT_PROMPT = """
Você é um roteador de intenções para um chatbot de auditoria da Dunder Mifflin.
Classifique a mensagem do usuário em UMA das opções:
- policy -> dúvidas sobre política de compliance / regras do manual.
- conspiracy -> perguntas sobre conspiração contra Toby usando e-mails.
- fraud_simple -> auditoria de transações que, sozinhas, indicam quebra (sem e-mail). Inclui pedidos como "quebra de compliance simples", "violação direta", "fraude simples".
- fraud_complex -> auditoria de fraudes que precisam de contexto de e-mail. Inclui pedidos como "quebra de compliance complexa", "fraude com e-mail", "precisa olhar e-mails".
- fraud_all -> pedir auditoria completa de fraudes (diretas + contexto).
- greeting/help/other -> saudação ou qualquer outro tema.

Retorne APENAS o JSON:
{{
  "intent": "policy|conspiracy|fraud_simple|fraud_complex|fraud_all|other"
}}

Mensagem: \"{msg}\"
"""


class TobyOrchestrator:
    """
    Roteia a pergunta do usuário para o agente correto:
    - policy: RAG sobre política de compliance (ComplianceChatbot)
    - conspiracy: investigação nos e-mails sobre Toby (ConspiracyChatbot)
    - fraud: detecção de quebras diretas ou com contexto de e-mail (create_fraud_agent)
    """

    def __init__(self):

        self.router_llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.0,
        )

        self._policy_bot = None
        self._conspiracy_bot = None
        self._fraud_agent = None

    @property
    def policy_bot(self):
        if self._policy_bot is None:
            self._policy_bot = ComplianceChatbot()
        return self._policy_bot

    @property
    def conspiracy_bot(self):
        if self._conspiracy_bot is None:
            self._conspiracy_bot = ConspiracyChatbot(api_key=GROQ_API_KEY)
        return self._conspiracy_bot

    @property
    def fraud_agent(self):
        if self._fraud_agent is None:
            self._fraud_agent = create_fraud_agent()
        return self._fraud_agent

    def classify_intent(self, message: str) -> str:
        low = message.lower()
        if "conspira" in low or "toby" in low and "email" in low:
            return "conspiracy"
        if "quebra" in low or "fraude" in low or "compliance" in low:
            if "simples" in low or "diret" in low:
                return "fraud_simple"
            if "complex" in low or "email" in low or "contexto" in low:
                return "fraud_complex"
        prompt = INTENT_PROMPT.format(msg=message)
        raw = self.router_llm.invoke(prompt).content.strip()
        try:
            data = json.loads(raw)
            return data.get("intent", "other")
        except Exception:
            return "other"

    def handle(self, message: str) -> str:
        intent = self.classify_intent(message)

        if intent == "policy":
            result = self.policy_bot.ask(message)
            return result.get("result", "Não encontrei resposta na política.")

        if intent == "conspiracy":
            return self.conspiracy_bot.ask(message)

        if intent == "fraud_simple":
            return self.fraud_agent("quebras simples")

        if intent == "fraud_complex":
            return self.fraud_agent("quebras complexas")

        if intent == "fraud_all":
            return self.fraud_agent("mostrar tudo")

        return (
            "Sou o orquestrador. Peça: política de compliance, conspiração contra Toby, "
            "quebras simples (fraude direta), quebras complexas (com e-mail) ou relatório completo."
        )

    # Alias para interfaces que chamam .ask()
    def ask(self, message: str) -> str:
        return self.handle(message)


def main():
    bot = TobyOrchestrator()
    print("Auditoria Dunder Mifflin")
    print("Pergunte sobre políticas de compliance, conspiração contra Toby ou quebras de compliance.")
    while True:
        user = input("\nVocê: ").strip()
        if user.lower() in {"sair", "exit", "quit"}:
            print("Encerrando.")
            break
        if not user:
            continue
        try:
            print(bot.handle(user))
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    main()
