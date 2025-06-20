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
            logging.info("JSON decode error:", e)
            return full_response
    else:
        logging.info("No JSON block found.")
        return full_response
    
def get_answer(is_return_json: bool, question: str):

    llm = OllamaLLM(
        model="deepseek-r1:7b",
        base_url="http://host.docker.internal:11434" 
    ) 

    def query_deepseek(question):
        response = llm.invoke(question)
        final_answer = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        return final_answer
    
    logging.info("[prepare_rag] Asking Question...")
    res = query_deepseek(question)

    logging.info(f"Response from LLM: {res}")

    if is_return_json:
        json_response = extract_json_response(res)
        logging.info(f"Json Response: {json_response}")
        return json_response

    return res