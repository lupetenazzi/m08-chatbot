import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class ComplianceChatbot:

    def __init__(self, policy_file: str | Path = None):

        self.policy_file = Path(policy_file) if policy_file else BASE_DIR / "data" / "politica_compliance.txt"
        self.llm = None
        self.retriever = None
        self.qa_chain = None
        
        self.load_documents()
        self.setup_embeddings()
        self.setup_llm()
        self.create_chain()
    
    def load_documents(self):

        if not self.policy_file.exists():
            raise FileNotFoundError(f"Arquivo de política não encontrado: {self.policy_file}")

        loader = TextLoader(str(self.policy_file), encoding="utf-8")
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )
        self.documents = text_splitter.split_documents(documents)
    
    def setup_embeddings(self):
        
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        self.vector_store = FAISS.from_documents(self.documents, embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
    
    def setup_llm(self):
        
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=800,
        )
    
    def create_chain(self):

        template = """
        Você é um especialista em compliance da Dunder Mifflin Paper Company e deve responder dúvidas sobre a política de compliance da empresa.
        Use APENAS o conteúdo do documento de compliance fornecido para responder.

        Regras obrigatórias:
        1. Se a informação **não** estiver no documento, responda exatamente:
        "Esta informação não está documentada na política de compliance atual."
        2. Sempre cite a **seção** do documento usada para fundamentar a resposta.
        3. Inclua uma evidência retirada do documento.
        4. Seja técnico e objetivo.
        5. Se a pergunta for ambígua, responda com a resposta mais provável baseada no documento e explique brevemente a suposição usada.

        Entrada:
        Contexto do documento:
        {context}

        Pergunta do usuário:
        {question}

        Se não houver resposta no documento, a saída deve ser apenas:
        Esta informação não está documentada na política de compliance atual. """
        
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True,
        )
    
    def ask(self, question: str) -> dict:
       
        result = self.qa_chain.invoke({"query": question})
        return result
    
    def answer(self, result: dict):

        print(result["result"])
        


def main():

    print("DUNDER MIFFLIN - CHATBOT DE COMPLIANCE")
    print("="*60)
    
    try:
        chatbot = ComplianceChatbot()
    except Exception as e:
        print(f"Erro ao inicializar chatbot: {e}")
        return
    
    print("\nDigite suas perguntas. Para encerrar, digite 'sair'.")
    print("Qual sua dúvida?\n")
    
    while True:
        question = input("> Você: ").strip()
        
        if question.lower() in ["sair", "exit", "quit"]:
            break
        
        if not question:
            print("Digite uma pergunta válida.\n")
            continue
        
        try:
            result = chatbot.ask(question)
            
            
            chatbot.answer(result)
            print('-'*60)
            
        except Exception as e:
            print(f"Erro ao processar pergunta: {e}\n")


if __name__ == "__main__":
    main()
