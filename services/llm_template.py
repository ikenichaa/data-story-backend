import re
import logging
import json

from langchain_chroma import Chroma
from chromadb.config import Settings
from chromadb import Client

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from services.rag import convert_stat_to_text

logging.basicConfig(level=logging.INFO)
from pathlib import Path

UPLOAD_ROOT = Path("uploaded_files")

def extract_json_response(full_response: str):
    match = re.search(r"```json(.*?)```", full_response, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            return None
    else:
        print("No JSON block found.")
        return None
    
def get_answer(session_id: str, is_return_json: bool, question: str):
    embedding_function = OllamaEmbeddings(
        model="deepseek-r1:7b",
        base_url="http://host.docker.internal:11434" 
    )
    # chroma_client = Client(Settings())
    
    # logging.info("[prepare_rag] Initialize retriever using Ollama embeddings for queries...")
    # retriever = Chroma(collection_name=session_id, client=chroma_client, embedding_function=embedding_function).as_retriever()

    llm = OllamaLLM(
        model="deepseek-r1:7b",
        base_url="http://host.docker.internal:11434" 
    ) 

    # def retrieve_context(question):
    #     results = retriever.invoke(question)

    #     context = "\n\n".join([doc.page_content for doc in results])
    #     logging.info(f"----> There are {len(results)} being retrieved....")
    #     return context
    
    def query_deepseek(question, context):
        # Format the input prompt
        logging.info(f"-----> Retrieved Context: {context}")
        # formatted_prompt = f"Question: {question}\n\nContext: {context}"
        formatted_prompt = question
        # Query DeepSeek-R1 using Ollama
        response = llm.invoke(formatted_prompt)
        # Clean and return the response
        response_content = response
        final_answer = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
        return final_answer

    def ask_question(question):
        # Retrieve context and generate an answer using RAG
        # context = retrieve_context(question)
        
        answer = query_deepseek(question, "")
        return answer
    
    
    
    logging.info("[prepare_rag] Asking Question...")
    # await websocket_manager.send_message(session_id, json.dumps({"status": "Generating emotion recommendation"}))
    res = ask_question(question)

    logging.info(f"Response from LLM: {res}")

    if is_return_json:
        json_response = extract_json_response(res)
        logging.info(f"Json Response: {json_response}")
        return json_response

    return res