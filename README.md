# ChatBot Auditoria do Toby - M08

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

Colocar arquitetura aqui


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