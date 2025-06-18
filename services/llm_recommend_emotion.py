import json
import logging

from services.redis_util import get_description_from_redis
from services.llm_template import get_answer
from ws.websocket import websocket_manager 

logging.basicConfig(level=logging.INFO)

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
    
    description = get_description_from_redis(session_id)
    res = get_answer(
        session_id,
        True,
        (
            f"You are a data story-teller. Your goal is to recommend the best emotion from the list provided to generate data storytelling that help user to understand and recall data more based on the provided dataset and description"
            f"Description of the dataset: {description}"
            "Give weight more to the description as the user may want to get some specific emotion"
            "First, choose either POSITIVE or NEGATIVE emotion that suit the input"
            f"Then, If you choose POSITIVE then pick ONE of the POSTIVIE emotions in the list {positive_emotions} that suit the data narrative for the input best"
            f"If you choose NEGTIVE then pick ONE of the POSTIVIE emotions in the list {negative_emotions} that suit the data narrative for the input best"
            f"Give reasoning in ONE sentence"
            "The response should be in json format: ```json{'feeling': 'positive | negative', 'emotion': '...', 'reason': '....'}```"
        )
    )
    

    await websocket_manager.send_message(session_id, json.dumps({
        "data": {
            "title": "emotion_recommendation",
            "result": res
        }
    }))
    