import logging
import uuid
import json

import pandas as pd

from fastapi import APIRouter, UploadFile, File, Form, Response, status, BackgroundTasks

from pathlib import Path
from redis_manager import RedisManager
from services.generate_stat import generate_descriptive_stats

router = APIRouter()

logging.basicConfig(level = logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")

def generate_stat_file(df: pd.DataFrame, session_dir):
    res = generate_descriptive_stats(df)
    file_path = session_dir / "stat.json"

    with open(file_path, "w") as f:
        f.write(json.dumps(res, indent=4))

    print(res)

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
    file_path = session_dir / "data.csv"

    ## Save to temp folder
    with open(file_path, "wb") as f:
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
    background_tasks.add_task(generate_stat_file,pd.read_csv(file_path), session_dir)

    return {
        "session_id": session_id,
    }