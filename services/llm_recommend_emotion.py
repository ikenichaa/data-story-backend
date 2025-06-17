import re
import json
import logging

from langchain_chroma import Chroma
from chromadb import Client
from chromadb.config import Settings

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from redis_manager import RedisManager

logging.basicConfig(level=logging.INFO)
from ws.websocket import manager 

positive_emotions = [
   "empathy", 
   "surprise", 
   "joy", 
   "amusement", 
   "contentment", 
   "tenderness", 
   "excitement"
]

negative_emotions = [
   "seriousness", 
   "awe", 
   "sadness", 
   "anger", 
   "fear", 
   "disgust"
]

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

def get_description_from_redis(session_id):
    redis_client = RedisManager.get_client()
    res = redis_client.get(session_id)
    logging.info(f"Get data from redis: {res}")

    json_res = json.loads(res)

    return json_res["description"]


async def get_appropriate_emotion(session_id):
    logging.info("[prepare_rag] Initialize retriever using Ollama embeddings for queries...")
    embedding_function = OllamaEmbeddings(
        model="deepseek-r1:7b",
        base_url="http://host.docker.internal:11434" 
    )

    client = Client(Settings())
    retriever = Chroma(collection_name=session_id, client=client, embedding_function=embedding_function).as_retriever()

    llm = OllamaLLM(
        model="deepseek-r1:7b",
        base_url="http://host.docker.internal:11434" 
    ) 

    def retrieve_context(question):
        results = retriever.invoke(question)

        context = "\n\n".join([doc.page_content for doc in results])
        return context
    
    def query_deepseek(question, context):
        # Format the input prompt
        formatted_prompt = f"Question: {question}\n\nContext: {context}"
        # Query DeepSeek-R1 using Ollama
        response = llm.invoke(formatted_prompt)
        # Clean and return the response
        response_content = response
        final_answer = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
        return final_answer

    def ask_question(question):
        # Retrieve context and generate an answer using RAG
        context = retrieve_context(question)
        answer = query_deepseek(question, context)
        return answer
    
    description = get_description_from_redis(session_id)
    
    logging.info("[prepare_rag] Asking Question...")
    res = ask_question(
        (
            f"You are a data story-teller. Your goal is to recommend the best emotion from the list provided to generate data storytelling that help user to understand and recall data more based on the provided dataset and description"
            f"Description of the dataset: {description}"
            "First, choose either POSITIVE or NEGATIVE emotion that suit the input"
            f"Then, If you choose POSITIVE then pick ONE of the POSTIVIE emotions in the list {positive_emotions} that suit the data narrative for the input best"
            f"If you choose NEGTIVE then pick ONE of the POSTIVIE emotions in the list {negative_emotions} that suit the data narrative for the input best"
            f"Give reasoning in ONE sentence"
            "The response should be in json format: {'feeling': 'positive | negative', 'emotion': '...', 'reason': '....'}"
        )
    )

    logging.info(f"Response from LLM: {res}")

    json_response = extract_json_response(res)
    logging.info(f"Json Response: {json_response}")

    return json_response

    # await manager.send_message(session_id, json_response)