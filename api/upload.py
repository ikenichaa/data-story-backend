import logging
import uuid
import json

import pandas as pd

from fastapi import APIRouter, UploadFile, File, Form, Response, status, BackgroundTasks

from pathlib import Path
from redis_manager import RedisManager
from services.generate_stat import generate_descriptive_stats
from services.rag import prepare_rag


router = APIRouter()

logging.basicConfig(level = logging.INFO)
UPLOAD_ROOT = Path("uploaded_files")

# TODO: Delete this API
@router.post("/test-rag-json")
async def test_rag_json():
    session_dir = UPLOAD_ROOT/"ff1bc445-861f-4cc0-96fc-c74a84e4ec18/stat.json"
    with open(session_dir) as json_data:
        stat = json.load(json_data)
        logging.info(stat['data'])

        info = []
        for key in stat['data']:
            logging.info(key)
            logging.info(stat['data'][key])
            if key == "fields":
                text = "The dataset contains the columns: "
                for field_name in stat['data'][key]:
                    text = text + " " + field_name 
                info.append(text)

            if key == "date":
                text = f"The dataset consists of the data from {stat['data'][key]['start_date']} to {stat['data'][key]['end_date']}" 
                info.append(text)
            
            if key == "stat":
                for field in stat["data"]["stat"]:
                    s = stat["data"]["stat"][field] 
                    text = (f"""For the whole period, This is the summary statistics: """ 
                    f"""the mean value of {field} is {s["mean"]}, """
                    f"""the min value of {field} is {s["min"]}, """
                    f"""the max value of {field} is {s["max"]}, """
                    f"""the median value of {field} is {s["median"]}, """
                    f"""the sd value of {field} is {s["sd"]}""") 

                    info.append(text.rstrip())
            
            if key == "correlation":
                text = "The correlation between each fields are as follow, "
                content = ""
                for field in stat["data"]["correlation"]:
                    c = stat["data"]["correlation"][field]
                    for other_field in c:
                        content = content + f"{field} and {other_field} is {c[other_field]}. "

                info.append(text+content)
            
            if key == "summary_by_month":
                for monthly_stat in stat["data"]["summary_by_month"]:
                    text = f"This is the statistics summary of the month: {monthly_stat['month']}, year: {monthly_stat['year']}. "
                    content = ""
                    for key_field in monthly_stat["metrics"]:
                        content = content + (
                            f"""The {key_field}: max is {monthly_stat["metrics"][key_field]["max"]}, """
                            f"""mean is {monthly_stat["metrics"][key_field]["mean"]}, """ 
                            f"""min is {monthly_stat["metrics"][key_field]["min"]}, """ 
                            f"""sd is {monthly_stat["metrics"][key_field]["std"]}. """ 
                         )
                    
                    info.append(text+content)    
            
            if key == "summary_by_year":
                for yearly_stat in stat["data"]["summary_by_year"]:
                    text = f"This is the statistics summary of the whole year: {yearly_stat['year']}. "
                    content = ""
                    for key_field in yearly_stat["metrics"]:
                        content = content + (
                            f"""The {key_field}: max is {yearly_stat["metrics"][key_field]["max"]}, """
                            f"""mean is {yearly_stat["metrics"][key_field]["mean"]}, """ 
                            f"""min is {yearly_stat["metrics"][key_field]["min"]}, """ 
                            f"""sd is {yearly_stat["metrics"][key_field]["std"]}. """ 
                         )
                    
                    info.append(text+content)   


        

def prepare_stat_and_rag(df: pd.DataFrame, session_dir, session_id):
    res = generate_descriptive_stats(df)
    json_file_path = session_dir / "stat.json"

    with open(json_file_path, "w") as f:
        f.write(json.dumps(res, indent=4))

    csv_file_path = session_dir/ "data.csv" 
    prepare_rag(csv_file_path, json_file_path, session_id) 


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file_and_description(
    response: Response,
    background_tasks: BackgroundTasks,
    description: str = Form(None),
    file: UploadFile = File(None)
):
    ## Check the input
    if file is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "missing file"}
    if description is None:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "missing description"}
    if file.content_type != "text/csv":
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "accept only CSV file"}
    
    ## Create session id
    session_id = str(uuid.uuid4())

    session_dir = UPLOAD_ROOT/session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    csv_file_path = session_dir / "data.csv"
    json_file_path = session_dir / "stat.json"

    ## Save to temp folder
    with open(csv_file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    value = {
        "status": "processing",
        "description": description
    }
    redis_client = RedisManager.get_client()
    redis_client.set(session_id, json.dumps(value))

    logging.info("[API] Upload the file and description")

    # Add some background tasks
    background_tasks.add_task(prepare_stat_and_rag,pd.read_csv(csv_file_path), session_dir, session_id)
    
    return {
        "session_id": session_id,
    }