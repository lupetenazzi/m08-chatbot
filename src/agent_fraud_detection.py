import csv
import json
import os
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from langchain_groq import ChatGroq

BASE_DIR = Path(__file__).resolve().parent.parent
TRANSACTIONS_PATH = BASE_DIR / "data" / "transacoes_bancarias.csv"
EMAILS_PATH = BASE_DIR / "data" / "emails_internos.txt"
POLICY_PATH = BASE_DIR / "data" / "politica_compliance.txt"

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def _to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


class FraudDetectionAgent:
    """
    Agente responsável por identificar quebras de compliance:
    - Transações que violam diretamente a política.
    - Transações que parecem normais, mas que nos e-mails revelam fraude.
    """

    def __init__(
        self,
        transactions_path: Path = TRANSACTIONS_PATH,
        emails_path: Path = EMAILS_PATH,
        policy_path: Path = POLICY_PATH,
    ):
        self.transactions_path = Path(transactions_path)
        self.emails_path = Path(emails_path)
        self.policy_path = Path(policy_path)

        self.policy_text = self._read_policy()
        self.transactions = self._load_transactions()
        self.emails = self._load_emails()

        self.blacklist_keywords = {
            "Entretenimento inadequado (itens proibidos)": [
                "mágica",
                "ilusionismo",
                "algemas",
                "karaok",
                "discoteca",
                "strip",
            ],
            "Armamento/itens táticos proibidos": [
                "katana",
                "arma",
                "ninja",
                "nunchaku",
                "spray de pimenta",
            ],
            "Conflito de interesses / negócios paralelos": [
                "wuphf",
                "dunder infinity",
                "serenity",
                "vela",
                "startup",
                "tech solutions",
                "sparkl",
            ],
        }

        self.context_rules = [
            {
                "name": "surveillance_spend",
                "email_keywords": ["walkie", "binóculo", "camuflagem"],
                "tx_keywords": ["walkie", "binóculo", "vigilância"],
                "reason": "Compra de equipamentos de espionagem para vigiar Toby, não é gasto de negócio.",
            },
            {
                "name": "wuphf_servers",
                "email_keywords": ["wuphf", "tech solutions", "servidor"],
                "tx_keywords": ["tech solutions", "servidor", "wuphf"],
                "reason": "Uso de verba corporativa para startup pessoal (Seção 3.3a) e valor acima de US$500 exige PO (Seção 1.3).",
            },
            {
                "name": "magic_disguised",
                "email_keywords": ["mágica", "algemas", "ilusionismo"],
                "tx_keywords": ["mágica", "ilusionismo", "algemas"],
                "reason": "Itens de entretenimento proibidos camuflados como treinamento (violação de itens proibidos).",
            },
            {
                "name": "wcs_receipt",
                "email_keywords": ["wcs supplies", "49.50", "recibo"],
                "tx_keywords": ["wcs supplies", "cola"],
                "reason": "Despesa propositalmente abaixo de US$50 para fugir de comprovação (Seção 1.1/controle de recibos).",
            },
            {
                "name": "helicopter_spy",
                "email_keywords": ["helicópteros", "controle remoto", "pilotagem"],
                "tx_keywords": ["helicóptero", "controle remoto", "pilotagem"],
                "reason": "Brinquedo comprado para espionagem, não é despesa de negócio (itens proibidos).",
            },
        ]

    def _read_policy(self) -> str:
        if not self.policy_path.exists():
            return ""
        return self.policy_path.read_text(encoding="utf-8")

    def _load_transactions(self) -> List[Dict]:
        if not self.transactions_path.exists():
            return []

        with self.transactions_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                row["valor"] = _to_float(row.get("valor", "0"))
                data.append(row)
            return data

    def _load_emails(self) -> List[Dict]:
        if not self.emails_path.exists():
            return []

        raw = self.emails_path.read_text(encoding="utf-8")
        blocks = raw.split("-------------------------------------------------------------------------------")
        emails = []

        for block in blocks:
            b = block.strip()
            if not b:
                continue

            def field(label: str) -> str:
                for line in b.splitlines():
                    if line.lower().startswith(f"{label.lower()}:"):
                        return line.split(":", 1)[1].strip()
                return ""

            emails.append(
                {
                    "from": field("De"),
                    "to": field("Para"),
                    "date": field("Data"),
                    "subject": field("Assunto"),
                    "body": b.split("Mensagem:", 1)[1].strip() if "Mensagem:" in b else "",
                    "raw": b,
                    "raw_lower": b.lower(),
                }
            )
        return emails

    def detect_direct_violations(self) -> List[Dict]:
        findings: List[Dict] = []

        for tx in self.transactions:
            motivos: List[str] = []
            desc_lower = tx.get("descricao", "").lower()
            categoria = tx.get("categoria", "").lower()
            valor = tx.get("valor", 0)

            if valor > 500:
                motivos.append("Valor acima de US$500 sem evidência de PO aprovado (Seção 1.3).")
            if 50 < valor <= 500:
                motivos.append("Despesa intermediária requer aprovação prévia de gestão (Seção 1.2) — verifique documentação.")
            if categoria == "diversos" and valor > 5:
                motivos.append("Categoria 'Diversos' não pode ser usada para valores acima de US$5 (Seção 2).")
            if "hooters" in desc_lower:
                motivos.append("Hooters é local restrito e não reembolsável (Seção 2.1).")
            if categoria == "ti" or "servidor" in desc_lower or "licença" in desc_lower:
                if valor > 100:
                    motivos.append("Compras de TI acima de US$100 exigem validação do RH/NY (Seção 2.3).")

            for policy_ref, keywords in self.blacklist_keywords.items():
                if any(k in desc_lower for k in keywords):
                    motivos.append(f"Item proibido ou conflito de interesse ({policy_ref}).")

            if motivos:
                findings.append(
                    {
                        "id_transacao": tx.get("id_transacao"),
                        "data": tx.get("data"),
                        "funcionario": tx.get("funcionario"),
                        "descricao": tx.get("descricao"),
                        "categoria": tx.get("categoria"),
                        "valor": valor,
                        "motivos": sorted(set(motivos)),
                    }
                )

        findings.extend(self._detect_smurfing())
        return findings

    def _detect_smurfing(self) -> List[Dict]:
        grouped: Dict[tuple, List[Dict]] = {}
        for tx in self.transactions:
            key = (tx.get("funcionario"), tx.get("data"))
            grouped.setdefault(key, []).append(tx)

        alerts = []
        for (func, date), txs in grouped.items():
            total = sum(t["valor"] for t in txs)
            max_single = max(t["valor"] for t in txs)
            if len(txs) > 1 and total > 500 and max_single < 500:
                alerts.append(
                    {
                        "id_transacao": ", ".join(t["id_transacao"] for t in txs),
                        "data": date,
                        "funcionario": func,
                        "descricao": "Múltiplas transações no mesmo dia somando > US$500.",
                        "categoria": "Múltiplas",
                        "valor": round(total, 2),
                        "motivos": [
                            "Estruturação suspeita para evitar aprovação de grandes despesas (Seção 1.3)."
                        ],
                    }
                )
        return alerts

    def detect_contextual_fraud(self) -> List[Dict]:
        flags: List[Dict] = []
        for email in self.emails:
            content = email.get("raw_lower", "")
            for rule in self.context_rules:
                if all(keyword in content for keyword in rule["email_keywords"]):
                    matches = self._match_transactions(rule["tx_keywords"])
                    for tx in matches:
                        flags.append(
                            {
                                "id_transacao": tx.get("id_transacao"),
                                "data": tx.get("data"),
                                "funcionario": tx.get("funcionario"),
                                "descricao": tx.get("descricao"),
                                "categoria": tx.get("categoria"),
                                "valor": tx.get("valor"),
                                "motivo": rule["reason"],
                                "evidencia_email": email.get("body", "")[:320],
                                "email_assunto": email.get("subject"),
                                "email_data": email.get("date"),
                            }
                        )
        return flags

    def _match_transactions(self, keywords: List[str]) -> List[Dict]:
        result = []
        for tx in self.transactions:
            desc_lower = tx.get("descricao", "").lower()
            if any(k in desc_lower for k in keywords):
                result.append(tx)
        return result

    def run_full_audit(self) -> Dict:
        return {
            "policy_path": str(self.policy_path),
            "direct_violations": self.detect_direct_violations(),
            "contextual_flags": self.detect_contextual_fraud(),
        }

    def pretty_print(self, report: Dict) -> None:
        print(self._format_direct(report["direct_violations"]))
        print()
        print(self._format_complex(report["contextual_flags"]))

    def _format_direct(self, direct: List[Dict]) -> str:
        if not direct:
            return "Nenhuma quebra direta encontrada nas transações."
        total_rules = sum(len(item["motivos"]) for item in direct)
        lines = [
            f"Quebras diretas: {len(direct)} transações, {total_rules} violações de regra.",
            "----------------------------------------",
        ]
        for item in direct:
            lines.append(
                f"- {item['id_transacao']} | {item['data']} | {item['funcionario']} | ${item['valor']:.2f}"
            )
            lines.append(f"  Descrição: {item['descricao']}")
            lines.append("  Violações:")
            for motivo in item["motivos"]:
                lines.append(f"    • {motivo}")
            lines.append("")
        return "\n".join(lines)

    def _format_complex(self, ctx: List[Dict]) -> str:
        if not ctx:
            return "Nenhuma quebra com contexto de e-mail detectada."
        lines = [
            f"Quebras de compliance com contexto de e-mail: {len(ctx)} transações com evidência.",
            "----------------------------------------",
        ]
        for flag in ctx:
            lines.append(
                f"- {flag['id_transacao']} | {flag['data']} | {flag['funcionario']} | ${flag['valor']:.2f}"
            )
            lines.append(f"  Descrição: {flag['descricao']}")
            lines.append(f"  Motivo: {flag['motivo']}")
            lines.append(f"  Evidência ({flag['email_data']} - {flag['email_assunto']}):")
            lines.append(f"    \"{flag['evidencia_email']}\"")
            lines.append("")
        return "\n".join(lines)


INTENT_PROMPT = """
Você é um roteador de intenções para um chatbot de auditoria financeira.
Classifique a mensagem do usuário em UMA das opções:
- greeting -> saudações ou conversa neutra.
- help -> quando pedir ajuda ou como usar.
- simple -> quando pedir quebras simples/diretas (basta a transação para apontar violação). Inclui termos como "quebra de compliance simples", "fraude simples", "violação direta".
- complex -> quando pedir quebras complexas/contextuais (precisa cruzar e-mail + transação). Inclui termos como "quebra de compliance complexa", "fraude com e-mail", "precisa olhar e-mails".
- all -> quando pedir tudo/relatório completo.
- unknown -> qualquer outra coisa.

Definições para o modelo:
- Quebra simples/direta: a própria transação já mostra violação (item proibido, conflito de interesse, falta de aprovação, categoria errada).
- Quebra complexa/contextual: só é fraude quando existe evidência no e-mail que conecta à transação.

Responda APENAS o JSON:
{{
  "intent": "greeting|help|simple|complex|all|unknown"
}}

Mensagem: \"{msg}\"
"""


class FraudChatRouter:
    def __init__(self, detector: FraudDetectionAgent, model_name: str = "llama-3.3-70b-versatile"):
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY não definida no ambiente.")
        self.detector = detector
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=model_name,
            temperature=0.0,
        )

    def classify(self, message: str) -> str:
        low = message.lower()
        if "quebra" in low or "fraude" in low or "compliance" in low:
            if "simples" in low or "diret" in low:
                return "simple"
            if "complex" in low or "email" in low or "contexto" in low:
                return "complex"

        prompt = INTENT_PROMPT.format(msg=message)
        raw = self.llm.invoke(prompt).content.strip()
        try:
            data = json.loads(raw)
            return data.get("intent", "unknown")
        except Exception:
            return "unknown"

    def ask(self, message: str) -> str:
        intent = self.classify(message)

        if intent == "greeting":
            return (
                "Olá! Sou o agente de auditoria. "
                "Quebra simples = transação sozinha já viola a política. "
                "Quebra complexa = precisa do contexto de e-mail para provar a fraude."
            )
        if intent == "help":
            return (
                "Use: 'quebras simples' para violações diretas (só a transação), "
                "'quebras complexas' para fraudes que exigem cruzar e-mail + transação, "
                "ou 'mostrar tudo' para o relatório completo."
            )
        if intent == "simple":
            return self.detector._format_direct(self.detector.detect_direct_violations())
        if intent == "complex":
            return self.detector._format_complex(self.detector.detect_contextual_fraud())
        if intent == "all":
            direct = self.detector.detect_direct_violations()
            ctx = self.detector.detect_contextual_fraud()
            return self.detector._format_direct(direct) + "\n\n" + self.detector._format_complex(ctx)

        return "Não entendi. Peça por 'quebras simples', 'quebras complexas' ou 'mostrar tudo'."

    def chat(self) -> None:
        print("AGENTE DE FRAUDES: Quebra de compliance")
        print("Diga oi/ajuda ou pergunte por 'quebras simples' ou 'quebras complexas'.")
        while True:
            user = input("\nVocê: ").strip()
            if not user:
                continue
            if user.lower() in {"sair", "exit", "quit"}:
                print("Encerrando.")
                break
            print(self.ask(user))


def create_fraud_agent():
    detector = FraudDetectionAgent()
    router = FraudChatRouter(detector)
    return router.ask


if __name__ == "__main__":
    detector = FraudDetectionAgent()
    router = FraudChatRouter(detector)
    router.chat()
