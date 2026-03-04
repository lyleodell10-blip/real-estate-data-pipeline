# ingest.py
import pandas as pd
import sqlite3

# 1. Load CSV data
file_path = "data/real_estate.csv"  # put your CSV in a folder named 'data'
df = pd.read_csv(file_path)

# 2. Quick data overview
print("First 5 rows:")
print(df.head())
print("\nColumns and types:")
print(df.dtypes)

# 3. Basic cleaning
df = df.drop_duplicates()           # remove duplicates
df = df.dropna(subset=['SalePrice'])    # remove rows with missing price

# 4. Connect to SQLite (SQL folder)
conn = sqlite3.connect("sql/real_estate.db")

# 5. Write cleaned data to SQL
df.to_sql("properties", conn, if_exists="replace", index=False)

print("\nData successfully ingested to SQL!")
conn.close()