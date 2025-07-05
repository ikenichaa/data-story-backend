import json
import logging
import asyncio

from langchain_core.prompts import PromptTemplate 
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM
from pydantic import BaseModel
from ws.websocket import websocket_manager

from services.stat_q_a import getting_to_know_field, getting_to_know_the_correlation, data_change_through_out_year

from services.redis_util import get_description_from_redis
from services.redis_util import get_core_concept

from pathlib import Path

logging.basicConfig(level=logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")
model = OllamaLLM(
    model="llama3.1:8b",
    base_url="http://host.docker.internal:11434" 
)

def field_narrative_chain_generator():
    field_narrative_template = (
        "You are a data storyteller. Your goal is to generate a short summary from a given stat.\n"
        "The dataset is about {core_concept}\n"
        "This is the summarized stat: {summarized_stat}" 

        "Guideline:\n"
        "- Generate short summary to explain the dataset and it's trend.\n"
        "- Do NOT make up any stories without fact from the context.\n"
        "- Specify the number.\n"
        "- Write in paragraph format. Not the bullet point format.\n"
    )

    field_narrative_prompt = PromptTemplate(
        input_variables=["core_concept", "summarized_stat"],
        template=field_narrative_template,
    )

    return field_narrative_prompt | model | StrOutputParser()

def data_story_chain_generator():
    data_story_template = (
        "You are a data storyteller. Your goal is to generate a data story from given summary of each field.\n"
        "The dataset is about {core_concept}\n"
        "This is the summary of each field: {fields_summary}\n" 
        "This is the correlation summary: {correlation_summary}\n"

        "Guideline:\n"
        "- Pick interesting aspects of each field and generate a summary of 500 words to explain the trend of dataset.\n"
        "- Use the correlation summary to enhance the story.\n"
        "- Do NOT make up any stories without fact from the context.\n"
        "- Specify the number.\n"
        "- Write in paragraph format. Not the bullet point format.\n"
    )

    data_story_prompt = PromptTemplate(
        input_variables=["core_concept", "fields_summary", "correlation_summary"],
        template=data_story_template,
    )

    return data_story_prompt | model | StrOutputParser()


async def process_field(stat_file_path, field, core_concept):
    field_summary = getting_to_know_field(stat_file_path, field)
    field_narrative_chain = field_narrative_chain_generator()

    logging.info(f"Processing field: {field}")
    logging.info(f"Core Concept: {core_concept}")
    logging.info(f"Field Summary: {field_summary}")

    result = await field_narrative_chain.ainvoke({
        "core_concept": core_concept,
        "summarized_stat": field_summary
    })

    logging.info(f"Field Narrative Result: {result}")

    return f"{field}: {result}"

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
        "- DO NOT specify the number. DO NOT calculate value.\n"
        "- Just tell the story by using the trend.\n"
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
                "title": "affective_narrative_v2",
                "result": data_story_result
            }
        }))

async def llm_summarize_story(session_id: str):
    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"

    core_concept = get_core_concept(session_id)
    if not isinstance(core_concept, str):
        core_concept = get_description_from_redis(session_id)

    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        fields = [field for field in stat["data"]["correlation"]]
        logging.info(f"Fields in the dataset: {fields}")
        story = []

        correlation_summary = getting_to_know_the_correlation(stat_file_path)
        logging.info(f"Correlation Summary: {correlation_summary}")

        logging.info("Starting to generate stories for each field...")
        tasks = [
            process_field(stat_file_path, field, core_concept)
            for field in fields
        ]


        logging.info("Before calling asyncio...")

        story = await asyncio.gather(*tasks)
        logging.info("[DONE] Generating stories for each field")
        logging.info(f"Number of stories generated: {len(story)}")

        story = '\n'.join(story)
        logging.info(f"Summarized Story: {story}")

        # if not story:
            # TODO: Handle the case where no story is generated

        data_story_chain = data_story_chain_generator()
        data_story_result = await data_story_chain.ainvoke({
            "core_concept": core_concept,
            "fields_summary": story,
            "correlation_summary": correlation_summary
        })

        logging.info(f"Data Story Result: {data_story_result}")

        story_file_path = session_dir / "story.txt"
        with open(story_file_path, "w") as f:
            f.write(str(data_story_result))