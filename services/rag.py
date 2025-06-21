import logging
import json


from concurrent.futures import ThreadPoolExecutor

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document

from chromadb.config import Settings
from chromadb import Client


# from ws.websocket import websocket_manager
chroma_client = Client(Settings())

logging.basicConfig(level = logging.INFO)

def convert_stat_to_text(stat_file_path):
    with open(stat_file_path) as json_data:
        stat = json.load(json_data)

        info = []
        for key in stat['data']:
            logging.info(key)
            logging.info(stat['data'][key])
            if key == "fields":
                text = "The dataset includes the following columns:"
                for field_name in stat['data'][key]:
                    text = text + ", " + field_name
                text = text + ". These fields represent the data."
                info.append(text)

            if key == "date":
                text = f"Timespan | Date | Time period = The dataset consists of the data from {stat['data'][key]['start_date']} to {stat['data'][key]['end_date']}" 
                info.append(text)
            
            if key == "stat":
                for field in stat["data"]["stat"]:
                    s = stat["data"]["stat"][field] 
                    text = (f"""For the whole period, This is the summary statistics of the field {field}: """ 
                    f"""the mean value is {s["mean"]}, """
                    f"""the min value is {s["min"]}, """
                    f"""the max value is {s["max"]}, """
                    f"""the median is {s["median"]}, """
                    f"""the sd value is {s["sd"]}""") 

                    info.append(text.rstrip())
            
            if key == "correlation":
                text = "The correlation between each fields are as follow, "
                content = ""
                for field in stat["data"]["correlation"]:
                    c = stat["data"]["correlation"][field]
                    for other_field in c:
                        content = content + f"{field} and {other_field} is {c[other_field]}. "

                info.append(text+content)
            
            if key == "summary_by_month":
                for monthly_stat in stat["data"]["summary_by_month"]:
                    text = f"This is the statistics summary of the month: {monthly_stat['month']}, year: {monthly_stat['year']}. "
                    content = ""
                    for key_field in monthly_stat["metrics"]:
                        content = content + (
                            f"""The {key_field}: max is {monthly_stat["metrics"][key_field]["max"]}, """
                            f"""mean is {monthly_stat["metrics"][key_field]["mean"]}, """ 
                            f"""min is {monthly_stat["metrics"][key_field]["min"]}, """ 
                            f"""sd is {monthly_stat["metrics"][key_field]["std"]}. """ 
                         )
                    
                    info.append(text+content)    
            
            if key == "summary_by_year":
                for yearly_stat in stat["data"]["summary_by_year"]:
                    text = f"This is the statistics summary of the whole year: {yearly_stat['year']}. "
                    content = ""
                    for key_field in yearly_stat["metrics"]:
                        content = content + (
                            f"""The {key_field}: max is {yearly_stat["metrics"][key_field]["max"]}, """
                            f"""mean is {yearly_stat["metrics"][key_field]["mean"]}, """ 
                            f"""min is {yearly_stat["metrics"][key_field]["min"]}, """ 
                            f"""sd is {yearly_stat["metrics"][key_field]["std"]}. """ 
                         )
                    
                    info.append(text+content)
    
    return info
    


async def prepare_rag(csv_file_path, stat_file_path, session_id):
    csv_loader = CSVLoader(file_path=csv_file_path,
        csv_args={
        'delimiter': ','
    })

    
    logging.info("[prepare_rag] Load documents...")
    csv_documents = csv_loader.load()


    logging.info("[prepare_rag] Split to chunks")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=50)
    csv_chunks = text_splitter.split_documents(csv_documents)

    stat_summary_text = convert_stat_to_text(stat_file_path)
    stat_chunks = [
        Document(page_content=text, metadata={"source": "stat.json", "type": "summary"})
        for text in stat_summary_text
    ]

    logging.info("Merge chunks together...")
    # chunks = csv_chunks + stat_chunks
    chunks =  stat_chunks

    logging.info(chunks)

    logging.info("[prepare_rag] Prepare the embedding functions...")
    embedding_function = OllamaEmbeddings(
        model="deepseek-r1:7b",
        base_url="http://host.docker.internal:11434" 
    )


    def generate_embedding(chunk):
        return embedding_function.embed_query(chunk.page_content)
    
    logging.info("[prepare_rag] Generating embeddings...")
    with ThreadPoolExecutor() as executor:
        embeddings = list(executor.map(generate_embedding, chunks))

    logging.info("[prepare_rag] Initialize chroma...")

    try:
        chroma_client.delete_collection(name=session_id)  # Delete existing collection (if any)
    except:
        None
    collection = chroma_client.create_collection(name=session_id)

    logging.info(f"-----> There are a total of {len(chunks)} chunks")
    for idx, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk.page_content], 
            metadatas=[{'id': idx}], 
            embeddings=[embeddings[idx]], 
            ids=[str(idx)]  # Ensure IDs are strings
        )

    