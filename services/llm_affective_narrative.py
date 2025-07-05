import logging
import json

from langchain_core.prompts import PromptTemplate 
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

from ws.websocket import websocket_manager

from services.redis_util import get_description_instruction, get_core_concept, get_description_from_redis

from pathlib import Path
from langchain.globals import set_debug

set_debug(True)

logging.basicConfig(level=logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")
model = OllamaLLM(
    model="llama3.1:8b",
    base_url="http://host.docker.internal:11434" 
)

async def llm_generate_affective_narrative(
    session_id: str, 
    emotion: str, 
    intensity_level: int,
    word_count: int,
    purpose: str,
    story_file: str
):
    """
    Generate an affective narrative based on the provided parameters.
    """
    logging.info("Generating affective narrative...")

    # Load the core concept from Redis
    core_concept = get_core_concept(session_id)
    if not isinstance(core_concept, str):
        core_concept = get_description_from_redis(session_id) 

    user_instruction = get_description_instruction(session_id)
    if user_instruction is None:
        logging.info("No core concept found for the session.")
    
    session_dir = UPLOAD_ROOT/session_id
    story_file_path = session_dir / story_file
    with open(story_file_path) as f:
        story_content = f.read()
        
    
    # Prepare the prompt
    prompt_template = (
        "You are a data storyteller. Your goal is to add emotion to the summarized data\n"
        "This is the summarized data: {story_content}\n"
        
        
        "Guideline:\n"
        "- Generate a narrative that evokes the emotion {emotion} with the intensity level {intensity_level}.\n"
        "- The closer the intensity level is to 10, the more intense the emotion should be.\n"
        "- The narrative should be approximately {word_count} words long.\n"
        "- Ensure that the narrative aligns with the purpose of {purpose}.\n"
        "- Focus on representing facts and data in a way that evokes subtle specified emotion.\n"
        "- The narrative should be engaging and coherent. \n"
        
        
        "Output format:\n"
        "- Provide a single paragraph narrative."
    )

    prompt = PromptTemplate(
        input_variables=["core_concept", "emotion", "intensity_level", "word_count", "purpose"],
        template=prompt_template
    )

    affective_narrative_chain = prompt | model | StrOutputParser()
    affective_narrative_result = await affective_narrative_chain.ainvoke({
        "story_content": story_content,
        "user_instruction": user_instruction,
        "core_concept": core_concept,
        "emotion": emotion,
        "intensity_level": intensity_level,
        "word_count": word_count,
        "purpose": purpose,
    })

    logging.info(f"Affective Narrative Result: {affective_narrative_result}")

    await websocket_manager.send_message(session_id, json.dumps({
        "data": {
            "title": "affective_narrative",
            "result": affective_narrative_result
        }
    }))


 