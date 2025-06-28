import json
import logging

from pathlib import Path
from pydantic import BaseModel, Field

from ws.websocket import websocket_manager

from langchain_core.prompts import PromptTemplate 
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableParallel
from langchain_ollama import OllamaLLM
# from langchain.globals import set_debug

# set_debug(True)
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

model = OllamaLLM(
    model="llama3.1:8b",
    base_url="http://host.docker.internal:11434" 
)

# Define your desired data structure.
class EmotionRecommendation(BaseModel):
    emotion: str = Field(description="the recommended emotion for the data narrative")
    reason: str = Field(description="the reason for the recommendation")

class InAppropriateEmotion(BaseModel):
    is_there_inappropriate_emotion: bool = Field(description="whether there is an inappropriate emotion for the data narrative")
    inappropriate_emotion: str = Field(description="the inappropriate emotion for the data narrative")
    reason: str = Field(description="the reason for the inappropriate emotion recommendation")

def recommended_emotion_chain_generator():
    recommended_emotion_parser = JsonOutputParser(pydantic_object=EmotionRecommendation)
    recommended_emotion_template = (
        "You are a data storyteller. Your goal is to recommend the best emotion from the list provided to generate data storytelling that helps users understand and recall data more based on the provided dataset and description.\n"
        "Description of the dataset: {description}\n"
        "{field_summary}\n"

        "Guideline:"
        "- Give high weight to the description when generating an answer, as the user may want to evoke a specific emotion.\n"
        "- First, choose either POSITIVE or NEGATIVE emotion that suits the input.\n"
        "- Then, if you decide POSITIVE, pick ONE of the positive emotions in the list {positive_emotions} that suits the data narrative for the input best.\n"
        "- If you choose NEGATIVE, then pick ONE of the POSITIVE emotions in the list {negative_emotions} that suit the data narrative for the input best.\n"
        "- Give reasoning in ONE sentence.\n"

        "{format_instructions}\n"
    )

    recommended_emotion_prompt = PromptTemplate(
        template=recommended_emotion_template,
        input_variables=["description", "field_summary", "positive_emotions", "negative_emotions"],
        partial_variables={"format_instructions": recommended_emotion_parser.get_format_instructions()},
    )

    return recommended_emotion_prompt | model | recommended_emotion_parser

def inappropriate_emotion_chain_generator():
    inappropriate_emotion_parser = JsonOutputParser(pydantic_object=InAppropriateEmotion)
    inappropriate_emotion_template = (
        "You are a data storyteller. Your role is to ensure that users do not select inappropriate emotions when crafting a narrative based on the dataset.\n"
        "Description of the dataset: {description}\n"
        "{field_summary}\n"

        "Guideline:"
        "- First, determine whether the dataset is emotionally sensitive.\n"
        "- A dataset is considered sensitive if it involves topics such as tragic events, trauma, loss, or other serious human experiences..\n"
        "- If the dataset is sensitive, advise against using certain emotions that may be inappropriate (e.g., avoid positive emotions for tragic data, or avoid negative emotions for celebratory data).\n"
        "- If the dataset is **NOT** sensitive, respond that there are no inappropriate emotions, and leave the Emotion and Reason fields blank.\n"
        "- If the dataset is **SENSITIVE**, specify whether it is inappropriate to recommend positive or negative emotions.\n"
        "- Provide a brief reason (in one sentence) explaining your decision.\n"

        "{format_instructions}\n"
    )

    inappropriate_emotion_prompt = PromptTemplate(
        template=inappropriate_emotion_template,
        input_variables=["description", "field_summary"],
        partial_variables={"format_instructions": inappropriate_emotion_parser.get_format_instructions()},
    )

    return inappropriate_emotion_prompt | model | inappropriate_emotion_parser

def field_name_summary(session_id: str):
    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"
    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        field_description = "The dataset contains the columns: "
        for field_name in stat['data']['fields']:
            field_description = field_description + " " + field_name
    
    field_description = field_description + ". "
    logging.info(f"Field description: {field_description}")

    return field_description

async def llm_emotion_recommendation(session_id: str, description: str):
    logging.info("Starting emotion recommendation process...")
    field_summary = field_name_summary(session_id)

    recommended_emotion_chain = recommended_emotion_chain_generator()
    inappropriate_emotion_chain = inappropriate_emotion_chain_generator()

    runnable = RunnableParallel(
        recommend_emotion=recommended_emotion_chain, 
        inappropriate_emotion=inappropriate_emotion_chain
    )

    res = runnable.invoke({
        "description": description,
        "field_summary": field_summary,
        "positive_emotions": positive_emotions,
        "negative_emotions": negative_emotions
    })

    logging.info(f"Emotion recommendation result------->: {res}")

    if "properties" in res['recommend_emotion']:
        recommended_emotion_result = res['recommend_emotion']["properties"]
    else:
        recommended_emotion_result = res['recommend_emotion']

    # Send the results back to the websocket
    await websocket_manager.send_message(session_id, json.dumps({
        "data": {
            "title": "recommended_emotion",
            "result": recommended_emotion_result
        }
    }))

    if "properties" in res['inappropriate_emotion']:
        inappropriate_emotion_result = res['inappropriate_emotion']["properties"]
    else:
        inappropriate_emotion_result = res['inappropriate_emotion']

    await websocket_manager.send_message(session_id, json.dumps({
        "data": {
            "title": "inappropriate_emotion",
            "result": inappropriate_emotion_result
        }
    }))
    