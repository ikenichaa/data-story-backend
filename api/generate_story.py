import logging
import asyncio

from fastapi import APIRouter, status 
from pydantic import BaseModel

from services.llm_generate_story import llm_generate_story

router = APIRouter()
class Agency(BaseModel):
    emotion: str
    intensity_level: int
    word_count: int
    purpose: str


@router.post("/generate-story/{session_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_story(
    session_id: str, 
    agency: Agency):

    logging.info("Generating story..")
    logging.info(session_id)
    logging.info(agency)

    asyncio.create_task(llm_generate_story(
            session_id, 
            agency.emotion, 
            agency.intensity_level,
            agency.word_count,
            agency.purpose
        )
    )

    return {"status": "processing"}