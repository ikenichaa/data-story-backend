import logging
import datetime

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

def get_date(date):
    for fmt in date_time_common_formats:
        try:
            datetime_object = datetime.datetime.strptime(date, fmt)
            return datetime_object
        except ValueError:
            continue
    
    logging.ERROR("[get_date] Cannot find matching format")