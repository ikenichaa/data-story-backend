import logging

from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logging.basicConfig(level = logging.INFO)

async def prepare_rag(csv_file_path, session_id):
    csv_loader = CSVLoader(file_path=csv_file_path,
        csv_args={
        'delimiter': ','
    })
    
    logging.info("[prepare_rag] Load documents...")
    csv_documents = csv_loader.load()

    logging.info("[prepare_rag] Split to chunks")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=50)
    csv_chunks = text_splitter.split_documents(csv_documents)

    logging.info(csv_chunks)

    logging.info("[prepare_rag] Prepare the embedding functions...")
    embedding_function = OllamaEmbeddings(
        model="deepseek-r1:7b",
        base_url="http://host.docker.internal:11434" 
    )


    def generate_embedding(chunk):
        return embedding_function.embed_query(chunk.page_content)
    
    logging.info("[prepare_rag] Generating embeddings...")
    with ThreadPoolExecutor() as executor:
        embeddings = list(executor.map(generate_embedding, csv_chunks))

    logging.info("[prepare_rag] Initialize chroma...")

    try:
        chroma_client.delete_collection(name=session_id)  # Delete existing collection (if any)
    except:
        None
    collection = chroma_client.create_collection(name=session_id)

    logging.info(f"-----> There are a total of {len(csv_chunks)} chunks")
    for idx, chunk in enumerate(csv_chunks):
        collection.add(
            documents=[chunk.page_content], 
            metadatas=[{'id': idx}], 
            embeddings=[embeddings[idx]], 
            ids=[str(idx)]  # Ensure IDs are strings
        )