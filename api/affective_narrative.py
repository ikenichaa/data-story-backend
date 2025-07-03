import logging

from fastapi import APIRouter, status
from pydantic import BaseModel
import asyncio

from services.llm_affective_narrative import llm_generate_affective_narrative
from services.llm_extract_description import extract_description
from services.llm_summarize_story import llm_summarize_story

from services.redis_util import get_description_from_redis

router = APIRouter()

logging.basicConfig(level=logging.INFO)
class Agency(BaseModel):
    emotion: str
    intensity_level: int
    word_count: int
    purpose: str

async def affective_narrative_pipeline(session_id, description, agency: Agency):
    try:
        await extract_description(session_id, description)
        await llm_summarize_story(session_id)
        await llm_generate_affective_narrative(
            session_id, 
            agency.emotion,
            agency.intensity_level,
            agency.word_count,
            agency.purpose
        )
    except Exception as e:
        logging.error(f"Error in affective_narrative pipeline: {e}")

@router.post("/generate-affective-narrative/{session_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_affective_narrative(
    session_id: str, 
    agency: Agency
    ):

    logging.info("Generating affective narrative...")
    logging.info(session_id)
    logging.info(agency)

    description = get_description_from_redis(session_id) 
    asyncio.create_task(affective_narrative_pipeline(session_id, description, agency))

    return {"status": "processing"}

