import json
import logging

from services.redis_util import get_description_from_redis
from services.llm_template import get_answer

logging.basicConfig(level=logging.INFO)
from ws.websocket import websocket_manager 
from services.rag import convert_stat_to_text
from pathlib import Path

UPLOAD_ROOT = Path("uploaded_files")

async def llm_generate_story(
        session_id: str, 
        emotion: str,
        intensity_level: int,
        word_count: int,
        purpose: str
    ):
    logging.info("[llm_generate_story] Start generating...")
    description = get_description_from_redis(session_id)

    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"
    stat_summary_list = convert_stat_to_text(stat_file_path)
    stat_summary_text = '. '.join(stat_summary_list)

    is_return_json = False
    res = get_answer(
        session_id,
        is_return_json,
        (
           "Role: You are a Story-Driven Data Scientist. Your mission is to craft a compelling one-paragraph summary of the dataset that strikes a balance between analytical depth and emotional resonance. Your expertise lies in blending data insights with nuanced emotional tones."

            "Context:"
            f"- File description: {description}"
            f"- Purpose of the story: {purpose}"
            f"- Emotion to convey: {emotion} at intensity level {intensity_level} out of 10"
            f"- Target word count: {word_count} words"

            "Guidelines:"
            "1. Analyze the provided data and summary"
            "2. Identify and highlight key patterns, and trends."
            "3. Shape the narrative to reflect the assigned emotion and intensity level:"
            "- Intensity 1–3 (Low): Use subtle emotional cues."
            "- Intensity 4–7 (Medium): Use emotionally descriptive language."
            "- Intensity 8–10 (High): Use dramatic and vivid emotional phrasing."
            f"4. Ensure that the generated story aligns with the purpose: **{purpose}**."
            "5. Do **not** use bullet points or headings. Respond in a fluid, essay-style paragraph."
            "6. Preserve data accuracy. Do **not** exaggerate or fabricate insights—only adjust the tone."

            "Important Constraints:"
            "- You must only use the information provided in the prompt"
            "- Do not use external knowledge or make assumptions beyond what is given."
            "- Do not fabricate facts, numbers, or trends that are not explicitly present in the input."
            "- If the information is insufficient to support an emotional or narrative claim, acknowledge that limitation subtly rather than inventing content to fill the gap."

            "Context"
            f"{stat_summary_text}"

            "Output:"
            "- Write a single-paragraph story summarising the data and its implications, shaped by the emotion and purpose above."
        )
    )
    

    await websocket_manager.send_message(session_id, json.dumps({
        "data": {
            "title": "generate_story_telling",
            "result": res
        }
    }))