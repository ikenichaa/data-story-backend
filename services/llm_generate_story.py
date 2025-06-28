import json
import logging

from services.redis_util import get_description_from_redis
from services.llm_template import get_answer

from ws.websocket import websocket_manager 
from pathlib import Path
from services.stat_q_a import generate_stat_q_and_a

UPLOAD_ROOT = Path("uploaded_files")
logging.basicConfig(level=logging.INFO)

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
    # Before
    # stat_summary_list = convert_stat_to_text(stat_file_path)
    # stat_summary_text = '. '.join(stat_summary_list)

    # After
    # Using Q and A form
    q_a = generate_stat_q_and_a(stat_file_path)
    logging.info(f"Q and A: {q_a}")

    if intensity_level <=3:
        tone = "Low Emotion Intensity Level. Use subtle emotional cues."
    elif intensity_level <=6:
        tone = "Medium Emotion Intensity Level. Use emotionally descriptive language."
    else:
        tone = "High Emotion Intensity Level. Use dramatic and vivid emotional phrasing."

    prompt = (
           "Role: You are a Story-Driven Data Scientist. "
           "Your mission is to craft a one-paragraph summary of the dataset that strikes a balance between analytical depth and emotional resonance."
           "Your expertise lies in blending data insights with nuanced emotional tones."

            "Context:"
            f"- Purpose of the story: {purpose}"
            f"- Emotion to convey: {emotion}"
            f"- Target word count: {word_count} words"

            "Guidelines:"
            f"1. Analyze the provided data and summary according to the user input {description} with emotion of {emotion}"
            "2. Identify and highlight key patterns, and trends."
            f"3. Shape the narrative to reflect the {tone}"
            f"4. Ensure that the generated story aligns with the purpose: **{purpose}**."
            "5. Do **not** use bullet points or headings. Respond in a fluid, essay-style paragraph."
            "6. Preserve data accuracy. Do **not** exaggerate or fabricate insights—only adjust the tone."

            "Important Constraints:"
            "- You must only use the information provided in the prompt"
            "- Do not use external knowledge or make assumptions beyond what is given."
            "- Do not fabricate facts, numbers, or trends that are not explicitly present in the input."
            "- If the information is insufficient to support an emotional or narrative claim, acknowledge that limitation subtly rather than inventing content to fill the gap."

            "Context"
            f"{q_a}"

            "Output:"
            "- Write a single-paragraph story summarising the data and its implications, shaped by the emotion and purpose above."
        )
    
    logging.info(f"Prompt: {prompt}")
    is_return_json = False
    res = get_answer(
        is_return_json,
        prompt
    )
    

    await websocket_manager.send_message(session_id, json.dumps({
        "data": {
            "title": "generate_story_telling",
            "result": res
        }
    }))