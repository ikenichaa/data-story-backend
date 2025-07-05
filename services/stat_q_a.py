import logging

from pathlib import Path


UPLOAD_ROOT = Path("uploaded_files")
logging.basicConfig(level = logging.INFO)


def data_change_through_out_year(stat_summary_by_year, field):
    question = f"What is the value of {field} change throughout the whole period"
    full_summary = ""
    for stat in stat_summary_by_year:
        year = stat["year"]
        average = stat["metrics"][field]["mean"]

        summary_text = f"In {year}, the average {field} is {average}. "
        full_summary = full_summary + summary_text

    return {
        "Q": question,
        "A": full_summary
    }
