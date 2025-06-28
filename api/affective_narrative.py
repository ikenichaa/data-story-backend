import logging

from fastapi import APIRouter, status
from pydantic import BaseModel

from services.llm_affective_narrative import llm_generate_affective_narrative

router = APIRouter()

logging.basicConfig(level=logging.INFO)
class Agency(BaseModel):
    emotion: str
    intensity_level: int
    word_count: int
    purpose: str

@router.post("/generate-affective-narrative/{session_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_affective_narrative(
    session_id: str, 
    agency: Agency
    ):

    logging.info("Generating affective narrative...")
    logging.info(session_id)
    logging.info(agency)

    await llm_generate_affective_narrative(
        session_id, 
        agency.emotion,
        agency.intensity_level,
        agency.word_count,
        agency.purpose
    )



    return {"status": "processing"}

