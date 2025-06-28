import logging
import json

from langchain_core.prompts import PromptTemplate 
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableParallel
from langchain_ollama import OllamaLLM

from redis_manager import RedisManager
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
model = OllamaLLM(
    model="llama3.1:8b",
    base_url="http://host.docker.internal:11434" 
)
redis_client = RedisManager.get_client()

class core_concept(BaseModel):
    core_concept: str = Field(description="the core concept of the dataset")

class summary_instruction(BaseModel):
    is_there_any_instruction: bool = Field(description="whether there is any instruction for LLM to follow")
    instruction: str = Field(description="the instruction for LLM to follow")

def dataset_topic_chain_generator():
    core_concept_parser = JsonOutputParser(pydantic_object=core_concept)
    core_concept_template = (
        "You are a data storyteller. Your goal is to extract the core concept (what is the dataset is about) based on the provided description.\n"
        "Description of the dataset: {description}\n"
        "Guideline:\n"
        "- The core concept should be a short phrase that captures the essence of the dataset on what the dataset is about.\n"
        "- It should be concise and easy to understand.\n"
        "- It should NOT include any specific data points or statistics.\n"
        "- It should be relevant to the overall theme of the dataset.\n"

        "Output format:\n"
        "- You MUST respond **only with a valid JSON object** matching the schema below.\n"
        "- Do NOT include explanations, apologies, commentary, or markdown formatting.\n"
        "- Return ONLY the JSON object, no surrounding text.\n"

        "{format_instructions}\n"
    )

    core_concept_prompt = PromptTemplate(
        input_variables=["description"],
        template=core_concept_template,
        partial_variables={"format_instructions": core_concept_parser.get_format_instructions()},
    )

    return core_concept_prompt | model | core_concept_parser

def instruction_chain_generator():
    summary_instruction_parser = JsonOutputParser(pydantic_object=summary_instruction)
    summary_instruction_template = (
        "You are a data storyteller. Your goal is to extract the instruction that the user wants story to be based on the provided description.\n"
        "Description of the dataset: {description}\n"
        "Guideline:\n"
        "- First, check if there is any instruction on theme of the story or not.\n"
        "- If there is no instruction, respond that there is no instruction\n"
        "- If there is instruction, provide the instruction in a short phrase that captures the theme and tone that the user wants the story to talk about.\n"

        "Output format:\n"
        "- You MUST respond **only with a valid JSON object** matching the schema below.\n"
        "- Do NOT include explanations, apologies, commentary, or markdown formatting.\n"
        "- Return ONLY the JSON object, no surrounding text.\n"

        "{format_instructions}\n"
    )

    summary_instruction_prompt = PromptTemplate(
        input_variables=["description"],
        template=summary_instruction_template,
        partial_variables={"format_instructions": summary_instruction_parser.get_format_instructions()},
    )

    return summary_instruction_prompt | model | summary_instruction_parser


async def extract_description(session_id: str, description: str):
    logging.info("Extracting description from the description...")

    topic_chain = dataset_topic_chain_generator()
    instruction_chain = instruction_chain_generator()

    runnable = RunnableParallel(
        topic=topic_chain,
        instruction=instruction_chain
    )

    res = runnable.invoke({
        "description": description
    })

    logging.info(f"Extracted Topic------>: {res}")

    if "properties" in res['topic']:
        topic_result = res['topic']["properties"]
    else:
        topic_result = res['topic']

    redis_topic_key = f"{session_id}_topic"
    redis_client.set(redis_topic_key, json.dumps(topic_result))
    redis_client.expire(redis_topic_key, 20*60)

    if "properties" in res['instruction']:
        instruction_result = res['instruction']["properties"]
    else:
        instruction_result = res['instruction']
    
    redis_topic_key = f"{session_id}_instruction"
    redis_client.set(redis_topic_key, json.dumps(instruction_result))
    redis_client.expire(redis_topic_key, 20*60)

    
