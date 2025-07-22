
import logging

from fastapi import APIRouter, status
from pydantic import BaseModel
import asyncio

from services.llm_summarize_story_v3 import llm_summarize_story_v3

from services.redis_util import get_description_from_redis

router = APIRouter()

logging.basicConfig(level=logging.INFO)
class Agency(BaseModel):
    emotion: str
    intensity_level: str 
    word_count: int
    purpose: str

async def affective_narrative_pipeline_v3(session_id, description, agency: Agency):
    try:
        await llm_summarize_story_v3(session_id, agency, description)
        
    except Exception as e:
        logging.error(f"Error in affective_narrative pipeline: {e}")

@router.post("/v3/generate-affective-narrative/{session_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_affective_narrative(
    session_id: str, 
    agency: Agency
    ):

    logging.info("Generating affective narrative v3...")
    logging.info(session_id)
    logging.info(agency)

    description = get_description_from_redis(session_id) 
    asyncio.create_task(affective_narrative_pipeline_v3(session_id, description, agency))

    return {"status": "processing"}

