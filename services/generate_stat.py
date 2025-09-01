import pandas as pd
import logging

from util.date import get_date

logging.basicConfig(level=logging.INFO)

def get_date_field(fields):
    """
    get_date_field
    return the field that store the date 
    """
    possible_date_field = ['date', 'timestamp', 'timestamps', 'Date']
    for field_name in possible_date_field:
        if field_name in fields.keys():
            return field_name
        

def get_correlation(df):
    """
    get_correlation
    return the correlation
    """
    correlation = {}
    cor = df.corr(method="pearson", numeric_only=True)

    all_fields = cor.index
    for field in cor:
        correlation[field] = {}
        for other_fields in all_fields:
            if field == other_fields:
                continue
            correlation[field][other_fields] = round(cor[field].loc[other_fields], 2)

    return correlation

def get_summary_by_year(df, date_field):
    all_types = df.dtypes
    field_names = all_types.index
    numerical_fields = []

    logging.info("All Typses: %s", all_types)
    logging.info("Shape of DataFrame: %s", df.shape[1])

    # Ensure 'date' column is in datetime format
    df[date_field] = pd.to_datetime(df[date_field])
    for i in range(df.shape[1]):
        field_type = str(all_types.iloc[i])
        if pd.api.types.is_numeric_dtype(field_type):
            numerical_fields.append(field_names[i])

    # Create 'year' column for grouping
    df['year'] = df[date_field].dt.year

    # Group by year, then aggregate
    summary_df = df.groupby(['year'])[numerical_fields].agg(['mean', 'max', 'min', 'std'])
    summary_df.columns = ['_'.join(col).strip() for col in summary_df.columns.values]
    summary_df = summary_df.reset_index()

    summary_by_year = []
    for _, row in summary_df.iterrows():
        entry = {
            "year": int(row["year"]),
            "metrics": {}
        }

        
        for field in numerical_fields:
            mean_value = row[f"{field}_mean"]
            max_value = row[f"{field}_max"]
            min_value = row[f"{field}_min"]
            std_value = row[f"{field}_std"]

            entry["metrics"][field] = {
                "mean": str(round(mean_value, 2)) if pd.notnull(mean_value) else 0,
                "max": str(round(max_value, 2)) if pd.notnull(max_value) else 0,
                "min": str(round(min_value, 2)) if pd.notnull(min_value) else 0,
                "std": str(round(mean_value, 2)) if pd.notnull(std_value) else 0
            }

        summary_by_year.append(entry)


    return summary_by_year



def generate_descriptive_stats(df: pd.DataFrame):
    """
    generate_descriptive_stats
    return fields, descriptive stat, and correlation
    """

    """
    Fields
    """
    fields = {}
    fields_type = df.dtypes
    fields_name = fields_type.index
    num_total_fields = len(fields_name)
    logging.info("Field Type: %s", fields_type)

    for i in range (0, num_total_fields):
        fields[fields_name[i]] = str(fields_type.iloc[i])
    
    """
    Start and End
    """
    date = {}
    date_field = get_date_field(fields)
    df["date_with_format"] = df[date_field].map(lambda x: get_date(x))

    start_date = min(df["date_with_format"])
    end_date = max(df["date_with_format"])

    date["start_date"] = str(start_date)
    date["end_date"] = str(end_date)

    """
    Correlation
    """
    cor = get_correlation(df)

    """
    Group By
    """
    by_year = get_summary_by_year(df, date_field)


    """
    Format final data
    """
    data = {}
    data["fields"] = fields
    data["date"] = date
    data["correlation"] = cor
    data["summary_by_year"] = by_year
    
    final = {"data": data}

    return final