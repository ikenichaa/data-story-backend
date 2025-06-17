import logging
import uuid
import json
import asyncio

import pandas as pd

from fastapi import APIRouter, UploadFile, File, Form, Response, status, BackgroundTasks

from pathlib import Path
from redis_manager import RedisManager
from services.generate_stat import generate_descriptive_stats
from services.rag import prepare_rag
from ws.websocket import manager 


router = APIRouter()

logging.basicConfig(level = logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")

# TODO: Delete this API
@router.post("/test-rag-json")
async def test_rag_json():
   await manager.send_message("xxxx", "test send message...")

        

async def prepare_stat_and_rag(df: pd.DataFrame, session_dir, session_id):
    res = generate_descriptive_stats(df)
    json_file_path = session_dir / "stat.json"

    with open(json_file_path, "w") as f:
        f.write(json.dumps(res, indent=4))

    csv_file_path = session_dir/ "data.csv" 
    return await prepare_rag(csv_file_path, json_file_path, session_id) 


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file_and_description(
    response: Response,
    background_tasks: BackgroundTasks,
    description: str = Form(None),
    file: UploadFile = File(None)
):
    ## Check the input
    if file is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "missing file"}
    if description is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "missing description"}
    if file.content_type != "text/csv":
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "accept only CSV file"}
    
    ## Create session id
    session_id = str(uuid.uuid4())

    session_dir = UPLOAD_ROOT/session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    csv_file_path = session_dir / "data.csv"
    json_file_path = session_dir / "stat.json"

    ## Save to temp folder
    with open(csv_file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    value = {
        "status": "processing",
        "description": description
    }
    redis_client = RedisManager.get_client()
    redis_client.set(session_id, json.dumps(value))

    logging.info("[API] Upload the file and description")

    # Add some background tasks
    background_tasks.add_task(lambda: asyncio.create_task(
        prepare_stat_and_rag(pd.read_csv(csv_file_path), session_dir, session_id)
    ))

    r = await(prepare_stat_and_rag(pd.read_csv(csv_file_path), session_dir, session_id))
    
    return {
        "session_id": session_id,
        "emotion": r
    }