import os
import re
import json
from dateutil import parser as dateparser
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

EMAIL_PATH = "../data/emails_internos.txt"

def read_email_file():
    with open(EMAIL_PATH, "r", encoding="utf-8") as f:
        return f.read()


def parse_emails(raw):
    blocks = raw.split("-------------------------------------------------------------------------------")
    emails = []

    for block in blocks:
        b = block.strip()
        if not b:
            continue

        def field(label):
            m = re.search(rf"{label}:\s*(.+)", b)
            return m.group(1).strip() if m else ""

        sender = field("De")
        to = field("Para")
        date_str = field("Data")
        subject = field("Assunto")

        msg = re.search(r"Mensagem:\s*(.*)", b, flags=re.DOTALL)
        body = msg.group(1).strip() if msg else ""

        try:
            timestamp = dateparser.parse(date_str)
        except:
            timestamp = None

        emails.append({
            "from": sender,
            "to": to,
            "date": timestamp.isoformat() if timestamp else None,
            "subject": subject,
            "body": body,
            "raw": b,
        })

    return emails

def get_all_emails():
    return parse_emails(read_email_file())


def get_all_people():
    pessoas = set()
    for e in get_all_emails():
        nome = e["from"].strip()
        if nome:
            pessoas.add(nome)
    return sorted(list(pessoas))


def get_emails_by_person(name):
    emails = get_all_emails()
    return [e for e in emails if name.lower() in e["from"].lower()]


def get_emails_by_date(date_str):
    try:
        target = dateparser.parse(date_str).date()
    except:
        return []

    emails = get_all_emails()
    result = []
    for e in emails:
        if not e["date"]:
            continue
        d = dateparser.parse(e["date"]).date()
        if d == target:
            result.append(e)
    return result

def is_relevant_email(e):
    raw = e["raw"].lower()

    if "para: toby flenderson" in raw or "toby.flenderson@" in raw:
        return False

    if "toby" in raw or "flenderson" in raw:
        return True

    return False


def filter_relevant(emails):
    return [e for e in emails if is_relevant_email(e)]


INTENT_SYSTEM_PROMPT = """
Você é um sistema de classificação de intenção especializado em perguntas sobre
conspiração contra Toby Flenderson.

Você deve analisar a pergunta do usuário e retornar **EXATAMENTE** o JSON:

{{
  "intent": "general" | "by_person" | "by_date" | "by_person_and_date" | "all_emails" | "invalid",
  "person": null or "nome",
  "date": null or "YYYY-MM-DD"
}}

---------------------------------------
REGRAS FUNDAMENTAIS DE ESCOPO
---------------------------------------

1. Toby Flenderson NUNCA deve aparecer no campo "person".
   - Ele é sempre a vítima, nunca um suspeito.

2. Perguntas que envolvem **apenas datas** devem ser classificadas como:
   → "by_date"

3. Perguntas que envolvem **apenas uma pessoa** devem ser:
   → "by_person"

4. Perguntas que envolvem **pessoa + data** devem ser:
   → "by_person_and_date"
   (Mesmo que também apareça a palavra “Toby” no texto.)

   Exemplos:
   - "Angela conspirou contra mim no dia 02 de abril?"
   - "Michael tramou algo no dia 5/4/08?"
   - "Dwight fez algo contra o RH em 02/04/2008?"

5. Perguntas gerais (“alguém está conspirando?”) devem ser:
   → "general"

6. Perguntas solicitando todos os e-mails de uma pessoa devem ser:
   → "all_emails"

7. Se não tiver relação com conspiração / Toby, retorne:
{{
  "intent": "invalid",
  "person": null,
  "date": null
}}

---------------------------------------
CORREÇÃO DE NOMES
---------------------------------------

Lista de pessoas REAIS presentes nos e-mails:
{people}

Use esta lista para identificar nomes mesmo se o usuário escrever errado
(ex: "angel", "angella" → "Angela Martin").

---------------------------------------
REGRAS PARA EXTRAÇÃO DE DATAS
---------------------------------------

- O usuário pode escrever a data em qualquer formato.
- Converta para "YYYY-MM-DD".
- Se não houver data na pergunta, retorne "date": null.

---------------------------------------

Retorne **APENAS** o JSON, sem explicações, sem comentários.
"""


ANALYSIS_PROMPT = """
Você é o auditor oficial da Dunder Mifflin responsável por analisar apenas os e-mails fornecidos
e verificar se existe conspiração contra Toby Flenderson.

REGRAS IMPORTANTES:
- Use SOMENTE os e-mails fornecidos abaixo como fonte de verdade.
- NÃO invente e-mails, eventos, pessoas ou intenções.
- NÃO conclua conspiração se não houver evidências explícitas.
- NÃO inclua nenhuma pessoa que não tenha enviado e-mails conspiratórios diretos.
- NÃO use interpretações além do texto literal.

------------------------------------------------------------
E-MAILS FORNECIDOS:
{emails}
------------------------------------------------------------

Pergunta do usuário:
{question}

------------------------------------------------------------
INSTRUÇÃO CENTRAL:
------------------------------------------------------------

1. Se não houver evidência direta de conspiração nos e-mails fornecidos, responda apenas:

"Não há evidências de conspiração contra Toby nos e-mails fornecidos."

- Não use estrutura.
- Não liste pessoas.
- Não descreva trechos.

2. Se houver evidências, responda SEGUINDO EXATAMENTE ESTA ESTRUTURA:

### Resultado da Investigação
- **Conspiração detectada?**: Sim

### Pessoas Envolvidas
- Lista apenas dos remetentes que realmente enviaram e-mails contendo conspiração.
- Inclua somente os destinatários ou pessoas mencionadas que realmente possam estar envolvidas.

### Evidências Encontradas
Para cada e-mail conspiratório encontrado, liste no formato:

- **De:** <remetente> → **Para:** <destinatário>
  **Trecho:** "<trecho literal que comprova a conspiração>"

(O trecho deve ser COPIADO exatamente do e-mail fornecido.)

### Conclusão Final
- Forneça uma conclusão curta e objetiva baseada apenas nas evidências acima.
- NÃO adicione interpretações externas.

------------------------------------------------------------
AGORA PRODUZA APENAS A RESPOSTA FINAL.
"""


class ConspiracyChatbot:

    def __init__(self, api_key):
        self.llm = ChatGroq(
            api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
        )


    def classify_intent(self, question):
        people_list = json.dumps(get_all_people(), ensure_ascii=False)

        prompt = INTENT_SYSTEM_PROMPT.format(people=people_list)
        prompt += "\nPergunta do usuário:\n" + question

        raw = self.llm.invoke(prompt).content.strip()

        try:
            return json.loads(raw)
        except:
            return {"intent": "invalid", "person": None, "date": None}


    def collect_data(self, intent):
        match intent["intent"]:

            case "general":
                return filter_relevant(get_all_emails())

            case "all_emails":
                return filter_relevant(get_all_emails())

            case "by_person":
                per = get_emails_by_person(intent["person"])
                return filter_relevant(per)

            case "by_date":
                dt = get_emails_by_date(intent["date"])
                return filter_relevant(dt)

            case "by_person_and_date":
                per = get_emails_by_person(intent["person"])
                dt = [e for e in per if e["date"] and dateparser.parse(e["date"]).date() == dateparser.parse(intent["date"]).date()]
                return filter_relevant(dt)

            case _:
                return []

    def analyze(self, question, emails):
        emails_json = json.dumps(emails, ensure_ascii=False, indent=2)
        prompt = ANALYSIS_PROMPT.format(emails=emails_json, question=question)
        return self.llm.invoke(prompt).content.strip()

    def ask(self, question):
        intent = self.classify_intent(question)

        if intent["intent"] == "invalid":
            return "Este chatbot só responde perguntas relacionadas à investigação de conspiração contra Toby."

        emails = self.collect_data(intent)
        if not emails:

            if intent["intent"] == "by_date":
                return (
                    f"Não existem e-mails registrados na data {intent['date']}. "
                    "Portanto, não há evidências de conspiração contra Toby nesse dia."
                )

            if intent["intent"] == "by_person":
                pessoa = intent["person"]
                return (
                    f"Não há qualquer evidência nos e-mails de que {pessoa} "
                    "esteja envolvido(a) em conspiração, sabotagem ou movimentação contra Toby ou o RH."
                )

            return "Não foram encontradas evidências de conspiração contra Toby nos e-mails disponíveis."



        return self.analyze(question, emails)


if __name__ == "__main__":
    api_key = os.getenv("GROQ_API_KEY")
    bot = ConspiracyChatbot(api_key)

    print("Chatbot de Conspiração – Modo Interativo")
    print("-----------------------------------------")

    while True:
        q = input("\nVocê: ")
        if q.lower() in ["sair", "exit", "quit"]:
            break
        print("\nChatbot:", bot.ask(q))
