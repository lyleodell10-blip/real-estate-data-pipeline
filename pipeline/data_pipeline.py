import pandas as pd
from sqlalchemy import create_engine

def run_pipeline():

    df = pd.read_csv("data/raw/real_estate.csv")

    df = df.dropna()

    engine = create_engine(
        "postgresql://user:password@localhost:5432/realestate"
    )

    df.to_sql(
        "housing_data",
        engine,
        if_exists="replace",
        index=False
    )

    print("Pipeline completed")