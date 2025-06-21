import logging
import json

from fastapi import APIRouter, Response
from pydantic import BaseModel

from pathlib import Path
from services.rag_v2 import chunking_and_embedding, ask_llm_with_rag
from ws.websocket import websocket_manager 

from chromadb.config import Settings
from chromadb import Client

chroma_client = Client(Settings())
router = APIRouter()

logging.basicConfig(level = logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")


class Item(BaseModel):
    question: str

@router.post("/ask-question-from-rag/{session_id}")
async def ask_question_from_rag(
        session_id: str,
        item: Item,
    ):

    try:
        chroma_client.get_collection(name=session_id)
    except:
        session_dir = UPLOAD_ROOT/session_id
        stat_file_path = session_dir / "stat.json"

        chunking_and_embedding(stat_file_path, session_id)
    

    res = ask_llm_with_rag(session_id, item.question)

    logging.info(f"Response {res}")
    
    return {
        "data": {
            "title": "Asking LLM specific question from RAG (stat info)",
            "result": res
        }
    }