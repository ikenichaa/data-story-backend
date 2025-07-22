import json
import logging
import os

from langchain_core.prompts import PromptTemplate 
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM
from pydantic import BaseModel
from ws.websocket import websocket_manager
from langchain_openai import ChatOpenAI

from services.stat_q_a import data_change_through_out_year

from services.redis_util import get_description_from_redis
from services.redis_util import get_core_concept

from pathlib import Path

logging.basicConfig(level=logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")
# model = OllamaLLM(
#     model="llama3.1:8b",
#     base_url="http://host.docker.internal:11434" 
# )

os.environ.get("OPENAI_API_KEY")

model = ChatOpenAI(
    model="gpt-4.1-nano",
    temperature=1,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# This V2 is trying to avoid Calculation in LLM
def data_story_chain_generator_v2():
    data_story_template = (
        "You are a data storyteller. Your goal is to generate a data story from given Q and A of each field.\n"
        "The dataset is about {core_concept}\n"
        "This is the Q and A  of each field: {q_and_a}\n" 

        "Guideline:\n"
        "- Generate a narrative that evokes the emotion {emotion} with the intensity level {intensity_level}.\n"
        "- The closer the intensity level is to 10, the more intense the emotion should be.\n"
        "- The narrative should be approximately {word_count} words long.\n"
        "- Ensure that the narrative aligns with the purpose of {purpose}.\n"
        "- Tell the story by using the trend and using the number provided in the Q and A.\n"
        "- Do NOT make up any stories without fact from the context.\n"
        "- Write in paragraph format. Not the bullet point format.\n"
    )

    data_story_prompt = PromptTemplate(
        input_variables=["core_concept", "q_and_a", "emotion", "intensity_level", "word_count", "purpose"],
        template=data_story_template,
    )

    return data_story_prompt | model | StrOutputParser()


class Agency(BaseModel):
    emotion: str
    intensity_level: int
    word_count: int
    purpose: str

# Summarize story by Q and A, without having to summarize story for each field first
async def llm_summarize_story_v2(session_id: str, agency: Agency):
    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"

    core_concept = get_core_concept(session_id)
    if not isinstance(core_concept, str):
        core_concept = get_description_from_redis(session_id)

    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        fields = [field for field in stat["data"]["correlation"]]
        summarize_data = []
        for field in fields:
            summarize_data.append(data_change_through_out_year(stat["data"]["summary_by_year"], field))
        
        logging.info(f"Summarize data: {summarize_data}")

        data_story_chain = data_story_chain_generator_v2()
        data_story_result = await data_story_chain.ainvoke({
            "core_concept": core_concept,
            "q_and_a": summarize_data,
            "emotion": agency.emotion,
            "intensity_level": agency.intensity_level,
            "word_count": agency.word_count,
            "purpose": agency.purpose
        })

        logging.info(f"Data Story Result: {data_story_result}")

        await websocket_manager.send_message(session_id, json.dumps({
            "data": {
                "title": "affective_narrative",
                "result": data_story_result
            }
        }))
