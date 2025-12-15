# ChatBot Auditoria do Toby - M08

## Video Demonstração
<div align="center">
  <a href="https://www.youtube.com/watch?v=4vCLRgi4TYg" target="_blank">
    <img src="https://img.youtube.com/vi/4vCLRgi4TYg/0.jpg" alt="Demonstração - Auditoria do Toby" width="560">
  </a>
</div>

Chatbot investigativo para a Dunder Mifflin que responde sobre:

- Política de compliance (RAG sobre o manual)
- Conspiração contra Toby (e-mails internos)
- Quebras de compliance financeiras (transações diretas e fraudes com contexto de e-mail)

## Estrutura de pastas (resumo)

```
├── data/
│   ├── politica_compliance.txt
│   ├── transacoes_bancarias.csv
│   └── emails_internos.txt
├── src/
│   ├── agent_compliance.py
│   ├── agent_conspiracy.py
│   ├── agent_fraud_detection.py
│   ├── agent_orchestrator.py
│   └── webapp/
│       ├── app.py
│       ├── index.html
│       ├── chat.js
│       └── style.css
├── requirements.txt
└── README.md
```

## Como rodar:

1. Criar e ativar o venv:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Definir `GROQ_API_KEY` no `.env` na raiz (mesmo nível de `src/` e `data/`):
   ```
   GROQ_API_KEY=...sua-chave...
   ```
4. Rodar orquestrador via CLI:
   ```bash
   cd src
   python agent_orchestrator.py
   ```
5. Rodar via webapp:
   ```bash
   cd src
   python webapp/app.py
   # acessar http://127.0.0.1:5000
   ```

## Arquitetura

Abaixo, segue arquitetura geral do sistema com a descrição de seus principais componentes e funcionalidades.

```
┌─────────────────────────────────────────────────────────┐
│                       USUÁRIO                           │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│            ORQUESTRADOR (agent_orchestrator.py)         │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │    Identifica qual agente deve responder       │     │
│  │       conforme o contexto da mensagem          │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌───────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  AGENTE DE    │  │   AGENTE DE     │  │   AGENTE DE     │
│  COMPLIANCE   │  │  CONSPIRAÇÃO    │  │    FRAUDES      │
└───────────────┘  └─────────────────┘  └─────────────────┘
        ↓                   ↓                   ↓
┌───────────────┐  ┌─────────────────┐  ┌───────────────────────────┐
│  Sistema RAG  │  │  Parser Emails  │  │ Verifica Irregularidades  │
│     FAISS     │  │   + Analisador  │  │     e valida Dados        │
└───────────────┘  └─────────────────┘  └───────────────────────────┘ 
        ↓                   ↓                   ↓
┌─────────────────────────────────────────────────────────┐
│                    FONTES DE DADOS                      │
│  • politica_compliance.txt                              │
│  • emails_internos.txt                                  │
│  • transacoes_bancarias.csv                             │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              MODELO DE LINGUAGEM (LLM)                  │
│                        Groq API                         │
└─────────────────────────────────────────────────────────┘

```

### Principais funcionalidades e componentes:

**Orquestrador (agent_orchestrator.py)**

Decide por meio do contexto da pergunta do usuário qual agentee específico deve processar a perguntar para retornar uma resposta coerente. É responsável por analisar a inteção da pergunta do usuário, encaminhar para o agente correto, coordenar as respostas e gerenciar esse contexto de conversa.


**Agentes Especializados** 

- Agente de Compliance (agent_compliance.py) especialista em responder dúvidas sobre a política de compliance da empresa. Utiliza das seguintes tecnologias:

   RAG (Retrieval-Augmented Generation)

   FAISS (banco de vetores)

   HuggingFace Embeddings

   LangChain RetrievalQA

- Agente de Conspiração (agent_conspiracy.py) é um investigador que analisa emails internos procurando evidências de conspirações. Utiliza das seguintes tecnologias:

   Parser de emails

   Sistema de filtros inteligentes
   
   Análise contextual com LLM

- Agente de Fraudes (agent_fraud_detection.py) é um auditor que detecta violações de compliance em transações financeiras. Utiliza das seguintes tecnologias:

   Analisador CSV de transações

   Sistema de regras de validação

   Cruzamento de dados emails + transações

   Detecção de padrões suspeitos


**Modelo de Linguagem** 

Via Groq API usado por todos os agentes para:

Classificação de intenções
Geração de respostas contextualizadas
Análise de conteúdo textual
Correlação de evidências



## Integrantes da equipe

<div align="center">

<table style="border-collapse: collapse; width: 100%; max-width: 1700px;">
  <tr>
    <td align="center" style="padding: 15px; border: 1px solid #464646;">
        <img src="assets/luiza.jpeg" alt="" style="width:150px; height:150px; object-fit:cover; border-radius:8px;" /><br>
        <sub><b>Luiza Faria Petenazzi</b></sub><br><br>
         <a href="https://www.linkedin.com/in/luizapetenazzi/"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white" /></a>
         <a href="https://github.com/lupetenazzi"><img src="https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white" /></a>
    </td>
    <td align="center" style="padding: 15px; border: 1px solid #464646;">
        <img src="assets/claret.jpeg" alt="" style="width:150px; height:150px; object-fit:cover; border-radius:8px;" /><br>
        <sub><b>Miguel Claret</b></sub><br><br>
        <a href="https://www.linkedin.com/in/miguelclaret"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white" /></a>
        <a href="https://github.com/MiguelClaret"><img src="https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white" /></a>
    </td>
    <td align="center" style="padding: 15px; border: 1px solid #464646;">
        <img src="assets/yasmim.jpeg" alt="" style="width:150px; height:150px; object-fit:cover; border-radius:8px;" /><br>
        <sub><b>Yasmim Passos</b></sub><br><br>
         <a href="https://www.linkedin.com/in/yasmim-passos/"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white" /></a>
        <a href="https://github.com/yasmimpassos"><img src="https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white" /></a>
    </td>    
  </tr>
</table>

</div>
