import logging
import asyncio

from fastapi import APIRouter, status, Response
from pydantic import BaseModel

from services.rag import chroma_client
from services.llm_generate_story import llm_generate_story

router = APIRouter()
class Agency(BaseModel):
    emotion: str
    intensity_level: int
    word_count: int
    purpose: str


@router.post("/generate-story/{session_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_story(
    response: Response,
    session_id: str, 
    agency: Agency):

    logging.info("Generating story..")
    logging.info(session_id)
    logging.info(agency)

    try:
        chroma_client.get_collection(name=session_id)
    except:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"error": f"The chroma vector for session_id: {session_id} is not found"}

    asyncio.create_task(llm_generate_story(
            session_id, 
            agency.emotion, 
            agency.intensity_level,
            agency.word_count,
            agency.purpose
        )
    )

    return {"status": "processing"}