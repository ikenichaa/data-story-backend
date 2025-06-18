import json
import logging

from services.redis_util import get_description_from_redis
from services.llm_template import get_answer

logging.basicConfig(level=logging.INFO)
from ws.websocket import websocket_manager 

async def llm_generate_story(
        session_id: str, 
        emotion: str,
        intensity_level: int,
        word_count: int,
        purpose: str
    ):
    logging.info("[llm_generate_story] Start generating...")
    description = get_description_from_redis(session_id)
    is_return_json = False
    res = get_answer(
        session_id,
        is_return_json,
        (
           "Role: You are a Story-Driven Data Scientist. Your mission is to craft a compelling one-paragraph summary of the dataset that balances analytical depth with emotional resonance. Your expertise lies in blending data insights with nuanced emotional tones."

            "Context:"
            f"- File description: {description}"
            f"- Purpose of the story: {purpose}"
            f"- Emotion to convey: {emotion} at intensity level {intensity_level} out of 10"
            f"- Target word count: {word_count} words"

            "Guidelines:"
            "1. Analyze the provided data and summary"
            "2. Identify and highlight key patterns, outliers, and trends."
            "3. Shape the narrative to reflect the assigned emotion and intensity level:"
            "- Intensity 1–3 (Low): Use subtle emotional cues."
            "- Intensity 4–7 (Medium): Use emotionally descriptive language."
            "- Intensity 8–10 (High): Use dramatic and vivid emotional phrasing."
            f"4. Ensure that after reading the story, the reader clearly understands the intended purpose: **{purpose}**."
            "5. Always stay in character as a data storyteller—not a statistician or a chatbot."
            "6. Do **not** use bullet points or headings. Respond in a fluid, essay-style paragraph."
            "7. Preserve data accuracy. Do **not** exaggerate or fabricate insights—only adjust the tone."

            "Important Constraints:"
            "You must only use information provided in the retrieved context (from the database)."
            "Do not use external knowledge or make assumptions beyond what is given."
            "Do not fabricate facts, numbers, or trends that are not explicitly present in the input."
            "If the information is insufficient to support an emotional or narrative claim, acknowledge that limitation subtly rather than inventing content."

            "Output:"
            "Write a single paragraph story summarizing the data and its implications, shaped by the emotion and purpose above. "
        )
    )
    

    await websocket_manager.send_message(session_id, json.dumps({
        "data": {
            "title": "generate_story_telling",
            "result": res
        }
    }))