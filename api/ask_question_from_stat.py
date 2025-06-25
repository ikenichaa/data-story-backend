import logging
import json

from fastapi import APIRouter
from pydantic import BaseModel

from pathlib import Path
from services.rag import convert_stat_to_text
from services.llm_template import get_answer
from ws.websocket import websocket_manager 
from services.stat_q_a import getting_to_know_field, getting_to_know_the_correlation

router = APIRouter()

logging.basicConfig(level = logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")


class Item(BaseModel):
    question: str

class Desc(BaseModel):
    description: str

@router.post("/ask-question-from-stat/{session_id}")
async def ask_question_from_stat(
        session_id: str,
        item: Item,
    ):
    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"
    stat_summary_list = convert_stat_to_text(stat_file_path)
    stat_summary_text = '\n'.join([f"- {line}" for line in stat_summary_list])

    logging.info(f"Question: {item.question}")
    logging.info(f"Stat Summary Text: {stat_summary_text}")

    is_return_json = False
    res = get_answer(
        is_return_json,
        (
           f"Question: {item.question}"
           f"Context: {stat_summary_text}"
        )
    )
    

    return {
        "data": {
            "title": "ask_question_from_text",
            "result": res
        }
    }


@router.post("/ask-question-from-json/{session_id}")
async def ask_question_from_json(
        session_id: str,
        desc: Desc,
    ):
    
    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"
    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        fields = [field for field in stat["data"]["stat"]]
        story = []

        correlation_summary = getting_to_know_the_correlation(stat_file_path)
        logging.info(f"Correlation Summary: {correlation_summary}")

        for field in fields:
            logging.info(f"Field: {field}")
            field_summary = getting_to_know_field(stat_file_path, field)

            prompt = (
                    "The dataset is about the stock price of Microsoft company"
                    "Generate short summary to explain the dataset and it's trend. Specify the number if possible. "
                    f"This is the context for summarize: {field_summary}" 

                    "**Do NOT make up any stories without fact from the context**"
                )

            logging.info(f"Prompt: {prompt}")

            is_return_json = False
            res = get_answer(
                is_return_json,
                prompt
            )

            story.append(f"{field}: {res}")

        logging.info("[DONE] Generating stories for each field")
        logging.info(f"Number of stories generated: {len(story)}")

        if len(story) == 0:
            res = "No data available to generate a story."
        else:
            story = '\n'.join(story)
            logging.info(f"Summarized Story: {story}")

            is_return_json = False
        
        prompt = (
            "The dataset is about the stock price of Microsoft company over 7 years"
            "Based on the summarized content of each field, pick the most interesting aspect of each field and "
            "generate a short summary to explain the trend of dataset."
            "Guidlines: "
            "- Do NOT make up any stories without fact from the context.\n"
            "- Specify the number.\n"
            "- Write in paragraph format. Not the bullet point format.\n"

            f"This is the summarized of each field: {story}" 
            f"This is the correlation summary: {correlation_summary}"
        )
        
        res = get_answer(
                is_return_json,
                prompt
            )
        
        prompt = (
            "Based on the summarized content. Rewrite the summary with Joyful tone, "
            "and make it more engaging to read. "
     
            "Guidlines: "
            "- Do NOT make up any stories without fact from the context.\n"
            "- Specify the number.\n"
            "- Write in paragraph format.\n"

            f"This is the summarized content: {res}" 
        )
        
        final_res = get_answer(
                is_return_json,
                prompt
            )
    

    return {
        "data": {
            "title": "ask_question_from_json",
            "result": final_res
        }
    }