import re
import time
import logging
import json


from concurrent.futures import ThreadPoolExecutor

from services.rag import convert_stat_to_text

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.schema import Document

from chromadb.config import Settings
from chromadb import Client

chroma_client = Client(Settings())
embedding_function = OllamaEmbeddings(
    model="deepseek-r1:7b",
    base_url="http://host.docker.internal:11434" 
)

def chunking_and_embedding(stat_file_path, session_id): 
    stat_summary_text = convert_stat_to_text(stat_file_path)
    stat_chunks = [
        Document(page_content=text, metadata={"source": "stat.json", "type": "summary"})
        for text in stat_summary_text
    ]

    logging.info("Stat chunks: ", stat_chunks)
    logging.info("[prepare_rag] Prepare the embedding functions...")

    def generate_embedding(chunk):
        return embedding_function.embed_query(chunk.page_content)
    
    logging.info("[prepare_rag] Generating embeddings...")
    with ThreadPoolExecutor() as executor:
        embeddings = list(executor.map(generate_embedding, stat_chunks))

    logging.info("[prepare_rag] Initialize chroma...")
    
    try:
        chroma_client.delete_collection(name=session_id)  # Delete existing collection (if any)
    except:
        None
    collection = chroma_client.create_collection(name=session_id)

    for idx, chunk in enumerate(stat_chunks):
        collection.add(
            documents=[chunk.page_content], 
            metadatas=[{'id': idx}], 
            embeddings=[embeddings[idx]], 
            ids=[str(idx)]  # Ensure IDs are strings
        )
    


def ask_llm_with_rag(session_id, question):
    logging.info("[ask_llm_with_rag] Initialize retriever using Ollama embeddings for queries...")
    start = time.time()
    retriever = Chroma(collection_name=session_id, client=chroma_client, embedding_function=embedding_function).as_retriever()
    logging.info(f"Retriever processing time => {time.time() - start}")

    def retrieve_context(question):
        results = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in results])
        return context
    

    logging.info("[prepare_rag] Start LLM...")
    llm = OllamaLLM(
        model="deepseek-r1:7b",
        base_url="http://host.docker.internal:11434" 
    ) 

    def query_deepseek(question, context):
        formatted_prompt = f"Question: {question}\n\nContext: {context}"

        response = llm.invoke(formatted_prompt)

        response_content = response
        logging.info(f"Full response from deepseek: {response_content}")
        final_answer = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()

        return final_answer

    def ask_question(question):
        context = retrieve_context(question)
        logging.info(f"Context from RAG retrival: {context}")
        answer = query_deepseek(question, context)
        return answer
    
    logging.info(f"Asking Question: {question} .......")
    res = ask_question(question)
    logging.info(res)

    return res