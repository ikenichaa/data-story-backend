import json
import logging
import os
import base64

from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ws.websocket import websocket_manager

logging.basicConfig(level=logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")

os.environ.get("OPENAI_API_KEY")

model = ChatOpenAI(
    model="gpt-4.1-nano",
    temperature=1,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def summarize_the_story_of_each_field(session_id: str, field, description):
    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"
    focus_summary = []

    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        yearly_summarize =  stat["data"]["summary_by_year"]
        for year in yearly_summarize:
            field_summary = year["metrics"][field]
            new_summary = {
                "year": year["year"],
                "value": field_summary
            }

            focus_summary.append(new_summary)

    graph_file_path = session_dir/"graph"/f"{field}.png"
    image_data = encode_image(graph_file_path)

    field_summary_generator = data_story_chain_generator_with_image()
    field_summary = field_summary_generator.invoke({
        "description": description,
        "stat_summary": focus_summary,
        "image_data": image_data
    })

    logging.info("Stat----->")
    logging.info(focus_summary)
    logging.info("Field Summary---->")
    logging.info(field_summary)

    return field_summary


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def data_story_chain_generator_with_image():
    chat_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a data storyteller. Your goal is to generate a data story from the provided text and image of a graph.\n"
                    "The dataset is about {description}.\n"
                    "Guideline:\n"
                    "- Tell the story by analyzing the trend and using the data shown in the graph image.\n"
                    "- Only use the numeric data provided in the description.\n"
                    "- Specify interesting trend such as  the peak and the drop in the graph.\n"
                    "- Do NOT make up any stories without facts from the context and the image.\n"
                    "- Write in a paragraph format, not bullet points.\n"
                ),
            ),
            (
                "human",
                [
                    {
                        "type": "text",
                        "text": (
                            "Here is a text description for additional context: {stat_summary}"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": "data:image/png;base64,{image_data}",
                    },
                ],
            ),
        ]
    )

    return chat_template | model | StrOutputParser()

def data_story_chain_generator_v3():
    data_story_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a data storyteller. Your goal is to generate a data story from the provided text.\n"
                    "Guideline:\n"
                    "- Generate a narrative that evokes the emotion {emotion} with the intensity level {intensity_level}.\n"
                    "- There are 3 intensity level: Low, Medium, and High. \n"
                    "- The narrative should be approximately {word_count} words long.\n"
                    "- Ensure that the narrative aligns with the purpose of {purpose}.\n"
                    "- Tell the story by summarize and pick the interesting information from each field combine\n"
                    "- Do NOT make up any stories without fact from the context.\n"
                    "- Write in paragraph format. Not the bullet point format.\n"
                ),
            ),
            (
                "human",
                [
                    {
                        "type": "text",
                        "text": (
                            "The dataset is about {description}\n"
                            "This is the summary of each field: {q_and_a}\n" 
                            "When writing the story, beaware that the data may not be in the full year. For example, the weather data may lack data for the whole year, which may tamper with the descriptive stats for the last or the first year\n"
                        ),
                    }
                ],
            ),
        ]
    )

    return data_story_prompt | model | StrOutputParser()


class Agency(BaseModel):
    emotion: str
    intensity_level: str
    word_count: int
    purpose: str

# Summarize story by Q and A, without having to summarize story for each field first
async def llm_summarize_story_v3(session_id: str, agency: Agency, description: str):
    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"

    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        fields = [field for field in stat["data"]["correlation"]]
        summarize_data = []
        for field in fields:
            summary = summarize_the_story_of_each_field(session_id, field, description)
            summarize_data.append({
                "Field": field,
                "Summary": summary
            })
        
        logging.info(f"Summarize data: {summarize_data}")

        # Instantiate the chain
        data_story_chain = data_story_chain_generator_v3()
        data_story_result = await data_story_chain.ainvoke({
            "description": description,
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
