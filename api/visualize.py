import logging
import os
import zipfile
import random

from fastapi import APIRouter, status, Body
from fastapi.responses import FileResponse
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

logging.basicConfig(level = logging.INFO)
router = APIRouter()

UPLOAD_ROOT = Path("uploaded_files")

def timeseries_graph(df, session_id, date_field, column, colors_list):
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot using Seaborn on the given axes
    if colors_list:
        # randomly select a color for single line plots
        random_color = random.randint(0, len(colors_list) - 1)
        sns.lineplot(ax=ax, x=date_field, y=column, data=df, color=colors_list[random_color])  # Use first color for single line
    else:
        sns.lineplot(ax=ax, x=date_field, y=column, data=df)

    # Add title and format x-axis
    ax.set_title(f"Daily {column} Over Time", fontsize=16)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)

    # Save to file
    output_path = f"./uploaded_files/{session_id}/graph/{column}.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)  # Close this specific figure

def generate_graph_from_files(session_dir, session_id, colors_list):
    # Ensure date column is datetime
    data_dir = session_dir/"data.csv"
    df = pd.read_csv(data_dir)

    possible_date_field = ['date', 'timestamp', 'timestamps', 'Date']
    fields = df.dtypes.index
    for field_name in possible_date_field:
        if field_name in fields:
            date_field = field_name

    df[date_field] = pd.to_datetime(df[date_field], errors="coerce")
    for col_name, col_type in df.dtypes.items():
        logging.info(f"Col type: {col_type}")
        logging.info(pd.api.types.is_numeric_dtype(col_type))


        if pd.api.types.is_numeric_dtype(col_type):
            logging.info(f"Generating graph for column: {col_name}")
            timeseries_graph(df, session_id, date_field, col_name, colors_list)


@router.post("/visualization/{session_id}", status_code=status.HTTP_202_ACCEPTED)
def visualization(session_id: str, colors: str = Body(..., embed=True)):
    session_dir = UPLOAD_ROOT/session_id
    graph_dir = session_dir/"graph" 
    graph_dir.mkdir(parents=True, exist_ok=True)

    colors_list = [color.strip() for color in colors.split(',')]

    generate_graph_from_files(session_dir, session_id, colors_list)

    image_paths = [os.path.join(graph_dir, f) for f in os.listdir(graph_dir) if f.endswith(".png")]
    zip_path = "/tmp/images_bundle.zip"

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for path in image_paths:
            zipf.write(path, arcname=os.path.basename(path))  # arcname removes folder path in ZIP

    return FileResponse(zip_path, media_type='application/zip', filename="data_visualizations.zip")
