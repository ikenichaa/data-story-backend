import logging
import json

from fastapi import APIRouter
from pydantic import BaseModel

from pathlib import Path
from services.rag import convert_stat_to_text
from services.llm_template import get_answer
from ws.websocket import websocket_manager 

router = APIRouter()

logging.basicConfig(level = logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")


class Item(BaseModel):
    question: str

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
        item: Item,
    ):
    q_and_a = [
  {
    "question": "What are the main columns or features in the dataset, and what do they represent?",
    "answer": "The dataset contains the following columns: date, meantemp, humidity, wind_speed, and meanpressure. These represent daily weather data including temperature, humidity level, wind speed, and atmospheric pressure."
  },
  {
    "question": "What is the time range covered in the dataset (start and end date)?",
    "answer": "The dataset covers data from 2013-01-01 to 2017-12-31."
  },
  {
    "question": "What is the frequency of the data (daily, weekly, monthly)? Are there any missing dates or gaps?",
    "answer": "The data is recorded daily. There are 11 missing days out of the total expected 1826 days over 5 years."
  },
  {
    "question": "What are the overall trends in key variables over time?",
    "answer": "Over the years, meantemp shows a steady seasonal pattern without a strong upward or downward long-term trend. Humidity and meanpressure also remain relatively stable, while wind_speed fluctuates seasonally."
  },
  {
    "question": "Are there any clear seasonal patterns, periodic behavior, or recurring cycles?",
    "answer": "Yes, meantemp shows a clear seasonal pattern peaking in the summer months and dipping in winter, consistent each year. Similar seasonality is observed in humidity and wind_speed."
  },
  {
    "question": "What is the average, minimum, and maximum value for each numeric variable?",
    "answer": "For meantemp: mean=24.6°C, min=5.1°C, max=39.2°C. For humidity: mean=68.4%, min=28.3%, max=98.0%. For wind_speed: mean=5.2 km/h, min=0.0 km/h, max=13.7 km/h. For meanpressure: mean=1009.8 hPa, min=1001.3 hPa, max=1018.2 hPa."
  },
  {
    "question": "Are there any noticeable outliers or anomalies in the data? What might have caused them?",
    "answer": "Yes, there are a few outlier days with extremely high wind_speed (above 13 km/h) and extremely low pressure readings below 1002 hPa, which could be due to storm events or recording errors."
  },
  {
    "question": "How are different variables correlated with each other over time?",
    "answer": "Meantemp is negatively correlated with humidity (r = -0.54) and positively correlated with wind_speed (r = 0.41). Meanpressure has a weak correlation with other variables."
  },
  {
    "question": "How do the statistics (mean, std, min, max) of key variables vary by month or year?",
    "answer": "Monthly analysis shows that meantemp peaks in May and June (avg 34.2°C) and is lowest in January (avg 12.4°C). Humidity is highest during the monsoon months (July–August). Wind_speed is most variable during winter months."
  },
  {
    "question": "What are the most significant changes or events in the dataset? When did they occur?",
    "answer": "A sharp drop in meanpressure was observed around July 2015, possibly indicating a storm or weather anomaly. Additionally, there were several unusually high temperature days in May 2016."
  }
]

    prompt = (
            "We have provided context information below" 
            f"{q_and_a}" 
            "Given this information, please answer the question: "
            f"{item.question}"
            "Don't give an answer unless it is supported by the context above."
        )
    
    logging.info(f"Prompt: {prompt}")

    is_return_json = False
    res = get_answer(
        is_return_json,
        prompt
    )
    

    return {
        "data": {
            "title": "ask_question_from_json",
            "result": res
        }
    }