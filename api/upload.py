import logging
import json
import asyncio

import pandas as pd

from fastapi import APIRouter, UploadFile, File, Form, Response, status
from pathlib import Path

from redis_manager import RedisManager
from services.generate_stat import generate_descriptive_stats
from services.llm_recommend_emotion import llm_emotion_recommendation
from services.llm_extract_description import extract_description
from services.llm_summarize_story import llm_summarize_story

router = APIRouter()

logging.basicConfig(level = logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")


async def prepare_stat(df: pd.DataFrame, stat_file_path):
    res = generate_descriptive_stats(df)
    
    with open(stat_file_path, "w") as f:
        f.write(json.dumps(res, indent=4))

    
async def upload_pipeline(df, session_dir, session_id, description):
    stat_file_path = session_dir / "stat.json"

    try:
        await prepare_stat(df, stat_file_path) 
        await llm_emotion_recommendation(session_id, description)
        await extract_description(session_id, description)
        await llm_summarize_story(session_id)
    except Exception as e:
        logging.error(f"Error in upload pipeline: {e}")



@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file_and_description(
    response: Response,
    description: str = Form(None),
    session_id: str = Form(None),
    file: UploadFile = File(None)
):
    ## Check the input
    if file is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "missing file"}
    if description is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "missing description"}
    if session_id is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "missing description"}
    if file.content_type != "text/csv":
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "accept only CSV file"}
    

    session_dir = UPLOAD_ROOT/session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    csv_file_path = session_dir / "data.csv"

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
    redis_client.expire(session_id, 20*60)  # Set expiration time to 20 minutes

    logging.info("[API] Upload the file and description")

    df = pd.read_csv(csv_file_path)
    asyncio.create_task(upload_pipeline(df, session_dir, session_id, description))
    
    return {
        "status": "processing"
    }