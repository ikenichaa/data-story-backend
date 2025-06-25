import json
import logging

from pathlib import Path

from dateutil.relativedelta import relativedelta
import datetime

UPLOAD_ROOT = Path("uploaded_files")
logging.basicConfig(level = logging.INFO)

date_time_common_formats = [
    "%m/%d/%Y %H:%M:%S",  # e.g., "1/10/2017 16:00:00"
    "%m/%d/%Y %H:%M",     # e.g., "1/10/2017 16:00"
    "%Y-%m-%d %H:%M:%S",  # e.g., "2023-01-25 10:30:00"
    "%Y-%m-%d %H:%M",     # e.g., "2023-01-25 10:30"
    "%Y-%m-%dT%H:%M:%S",  # e.g., "2023-01-25T10:30:00" (ISO 8601 without timezone)
    "%Y-%m-%dT%H:%M:%SZ", # e.g., "2023-01-25T10:30:00Z" (ISO 8601 UTC)
    "%Y-%m-%d",           # e.g., "2023-01-25"
    "%m/%d/%Y",           # e.g., "01/25/2023"
    "%d-%m-%Y",           # e.g., "25-01-2023"
    "%b %d %Y %H:%M:%S",  # e.g., "Jan 25 2023 10:30:00"
    "%d %b %Y %H:%M:%S",  # e.g., "25 Jan 2023 10:30:00"
    "%A, %B %d, %Y %H:%M:%S", # e.g., "Wednesday, January 25, 2023 10:30:00"
]

month_mapping = {
    "1": "January",
    "2": "February",
    "3": "March",
    "4": "April",
    "5": "May",
    "6": "June",
    "7": "July",
    "8": "August",
    "9": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}

def get_date(date):
    for fmt in date_time_common_formats:
        try:
            datetime_object = datetime.datetime.strptime(date, fmt)
            return datetime_object
        except ValueError:
            continue
    
    logging.ERROR("[get_date] Cannot find matching format")


def time_period_data_capture(stat_date):
    question = "What is the time period where the data was captured?"
    start_date, end_date = start_end_period(stat_date) 

    difference_in_years = relativedelta(end_date, start_date).years

    return {
        "Q": question,
        "A": f"The data spans about {difference_in_years} years, from {start_date} to {end_date}." 
    }

def start_end_period(stat_date):
    start_date = get_date(stat_date["start_date"])
    end_date = get_date(stat_date["end_date"])

    return start_date, end_date


def find_missing_month(stat_summary_by_month):
    question = "Are there any months or years with missing or partial data?"
    whole_duration = {}
    for info in stat_summary_by_month:
        year = info["year"]
        month = info["month"]
        if year in whole_duration:   
            whole_duration[year].append(month)
        else:
           whole_duration[year] = [month]

    answer = "No"
    year_with_missing_data = []
    for year in whole_duration:
        if len(whole_duration[year]) < 12:
            answer = "Yes"
            year_with_missing_data.append(year)
        else:
            continue
    
    if answer == "No":
        return {
            "Q": question,
            "A": answer
        }
    
    years_joined_string = ", ".join(map(str, year_with_missing_data))
    answer = f"Yes, There are {len(year_with_missing_data)} year(s) with missing months - {years_joined_string}."
    for year in year_with_missing_data:
        logging.info(whole_duration)
        month_in_that_year = whole_duration[year]
        text = f" Year {year} has data for only {len(month_in_that_year)} month(s). In {year}, data is missing for "
        for i in range(1,13):
            if i in month_in_that_year:
                continue
            else:
                text = text + month_mapping[str(i)] + ", "
        text = text[:-2]
        
        answer = answer + text + "."

    return {
        "Q": question,
        "A": answer
    }

# Keep only mean for now
def data_change_throughout_month(summary_by_month, year, field):
    question = f"What is the value for {field} change throughout the year {year}?"
    answer = ""
    for s_month in summary_by_month:
        if str(s_month["year"]) != str(year):
            continue
        else:
            month = s_month["month"]
            month_text = month_mapping[str(month)] 
            avg = s_month["metrics"][field]["mean"]
            answer = answer + f"In {month_text}, the average {field} is {avg}. "

    return {
        "Q": question,
        "A": answer
    } 

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
# TEST
def generate_q_a_getting_to_know_data(stat_file_path):
    q_a = []
    with open(stat_file_path) as json_data:
        stat = json.load(json_data)

        # Q1. Time period
        q_a.append(time_period_data_capture(stat["data"]["date"]))

        return q_a

# TEST
def getting_to_know_field(stat_file_path, field):
    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        return data_change_through_out_year(stat["data"]["summary_by_year"], field)

def getting_to_know_the_correlation(stat_file_path):
    with open(stat_file_path) as json_data:
        stat = json.load(json_data)
        text = "The correlation between each fields are as follow, "
        content = ""
        for field in stat["data"]["correlation"]:
            c = stat["data"]["correlation"][field]
            for other_field in c:
                content = content + f"{field} and {other_field} is {c[other_field]}. "

    return text+content

def generate_stat_q_and_a(stat_file_path):
    q_a = []
    with open(stat_file_path) as json_data:
        stat = json.load(json_data)

        # Q1. Time period
        q_a.append(time_period_data_capture(stat["data"]["date"]))

        # Q2. Missing data
        q_a.append(find_missing_month(stat["data"]["summary_by_month"]))

        # Q3. Change of each fields in each month by year
        start, end = start_end_period(stat["data"]["date"])
        start_year, end_year = start.year, end.year
        fields = [field for field in stat["data"]["stat"]]
        logging.info(f"Start Year: {start_year}, End Year: {end_year}")
        logging.info(f"Fields: {fields}")

        for year in range(start_year, end_year):
            for field in fields:
                q_a.append(data_change_throughout_month(stat["data"]["summary_by_month"], str(year), field))
        
        # Q4. Overall trend of each field throughout the years
        for field in fields:
            q_a.append(data_change_through_out_year(stat["data"]["summary_by_year"], field)) 

        return json.dumps({
            "data": q_a
        })


if __name__ == "__main__":
    print("---- Hello ----")

    session_id = "test_3"
    session_dir = UPLOAD_ROOT/session_id
    stat_file_path = session_dir / "stat.json"

    generate_stat_q_and_a(stat_file_path)


