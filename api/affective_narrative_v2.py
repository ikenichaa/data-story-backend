"""
V2 use Q and A that summarize the mean of each field by year
"""

import logging

from fastapi import APIRouter, status
from pydantic import BaseModel
import asyncio

from services.llm_summarize_story import llm_summarize_story_v2

from services.redis_util import get_description_from_redis

router = APIRouter()

logging.basicConfig(level=logging.INFO)
class Agency(BaseModel):
    emotion: str
    intensity_level: int
    word_count: int
    purpose: str

async def affective_narrative_pipeline_v2(session_id, description, agency: Agency):
    try:
        await llm_summarize_story_v2(session_id, agency)
        
    except Exception as e:
        logging.error(f"Error in affective_narrative pipeline: {e}")

@router.post("/v2/generate-affective-narrative/{session_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_affective_narrative(
    session_id: str, 
    agency: Agency
    ):

    logging.info("Generating affective narrative v2...")
    logging.info(session_id)
    logging.info(agency)

    description = get_description_from_redis(session_id) 
    asyncio.create_task(affective_narrative_pipeline_v2(session_id, description, agency))

    return {"status": "processing"}

