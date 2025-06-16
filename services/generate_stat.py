import pandas as pd
import logging
import json

def get_date_field(fields):
    """
    get_date_field
    return the field that store the date 
    """
    possible_date_field = ['date', 'timestamp', 'timestamps', 'Date']
    for field_name in possible_date_field:
        if field_name in fields.keys():
            return field_name
        

def descriptive_stat(df: pd.DataFrame):
    """
    descriptive_stat
    return the stat of the dataframe
    """
    stat = {}
    mean = df.mean(numeric_only=True) 
    for index, field in enumerate(mean.index):
        stat[field] = {}
        stat[field]["mean"] = round(mean.iloc[index], 2)
    
    median = df.median(numeric_only=True)
    for index, field in enumerate(median.index):
        stat[field]["median"] = round(median.iloc[index], 2)
    
    min = df.min(numeric_only=True)
    for index, field in enumerate(min.index):
        stat[field]["min"] = round(min.iloc[index], 2)
    
    max = df.max(numeric_only=True)
    for index, field in enumerate(max.index):
        stat[field]["max"] = round(max.iloc[index], 2)
    
    sd = df.std(numeric_only=True)
    for index, field in enumerate(sd.index):
        stat[field]["sd"] = round(sd.iloc[index], 2)

    return stat

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

def get_summary_by_time(df, date_field):
    all_types = df.dtypes
    field_names = all_types.index
    numerical_fields = []

    for i in range(df.shape[1]):
        field_type = str(all_types.iloc[i])
        if ("int" in field_type) or ("float" in field_type):
            numerical_fields.append(field_names[i])

    # Ensure 'date' column is in datetime format
    df[date_field] = pd.to_datetime(df[date_field])

    # Create 'year' and 'month' columns
    df['year'] = df[date_field].dt.year
    df['month'] = df[date_field].dt.month

    # Group by year and month, then aggregate
    summary_df = df.groupby(['year', 'month'])[numerical_fields].agg(['mean', 'max', 'min', 'std'])
    summary_df.columns = ['_'.join(col).strip() for col in summary_df.columns.values]
    summary_df = summary_df.reset_index()

    summary_by_month = []

    for _, row in summary_df.iterrows():
        entry = {
            "year": int(row["year"]),
            "month": int(row["month"]),
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

        summary_by_month.append(entry)
    
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


    return summary_by_month, summary_by_year



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

    for i in range (0, num_total_fields):
        fields[fields_name[i]] = str(fields_type.iloc[i])
    
    """
    Start and End
    """
    date = {}
    date_field = get_date_field(fields)

    start_date = min(df[date_field])
    end_date = max(df[date_field])

    date["start_date"] = start_date
    date["end_date"] = end_date

    """
    Descriptive stat
    """
    stat = descriptive_stat(df)

    """
    Correlation
    """
    cor = get_correlation(df)

    """
    Group By
    """
    by_month, by_year = get_summary_by_time(df, date_field)


    """
    Format final data
    """
    data = {}
    data["fields"] = fields
    data["date"] = date
    data["stat"] = stat
    data["correlation"] = cor
    data["summary"] = {
        "summary_by_month": by_month,
        "summary_by_year": by_year
    }

    final = {"data": data}

    return final

if __name__ == "__main__":
    df = pd.read_csv("full_climate.csv")
    res = generate_descriptive_stats(df)
    print(json.dumps(res, indent = 4))