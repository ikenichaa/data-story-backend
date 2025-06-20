import json
import logging

from services.redis_util import get_description_from_redis
from services.llm_template import get_answer
from ws.websocket import websocket_manager

from services.rag import convert_stat_to_text
from pathlib import Path

logging.basicConfig(level=logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")

positive_emotions = [
   "empathy", 
   "surprise", 
   "joy", 
   "amusement", 
   "contentment", 
   "tenderness", 
   "excitement"
]

negative_emotions = [
   "seriousness", 
   "awe", 
   "sadness", 
   "anger", 
   "fear", 
   "disgust"
]

async def get_appropriate_emotion(session_id):
    logging.info("[prepare_rag] Initialize retriever using Ollama embeddings for queries...")

    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"
    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        field_description = "The dataset contains the columns: "
        for field_name in stat['data']['fields']:
            field_description = field_description + " " + field_name 
    

    logging.info(field_description)
    
    description = get_description_from_redis(session_id)
    res = get_answer(
        True,
        (
            f"You are a data storyteller. Your goal is to recommend the best emotion from the list provided to generate data storytelling that helps users understand and recall data more based on the provided dataset and description."
            f"Description of the dataset: {description}"
            f"{field_description}"

            "Guideline:"
            "- Give high weight to the description when generating an answer, as the user may want to evoke a specific emotion."
            "- First, choose either POSITIVE or NEGATIVE emotion that suits the input"
            f"- Then, if you decide POSITIVE, pick ONE of the positive emotions in the list {positive_emotions} that suits the data narrative for the input best"
            f"- If you choose NEGATIVE, then pick ONE of the POSITIVE emotions in the list {negative_emotions} that suit the data narrative for the input best"
            f"- Give reasoning in ONE sentence."

            "Output:"
            "The response should be in JSON format: ```json {'feeling': 'positive | negative', 'emotion': '...', 'reason': '....'}```"
        )
    )

    await websocket_manager.send_message(session_id, json.dumps({
        "data": {
            "title": "emotion_recommendation",
            "result": res
        }
    }))
    