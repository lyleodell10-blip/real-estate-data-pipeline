import sqlite3
import pandas as pd

conn = sqlite3.connect("sql/real_estate.db")

df = pd.read_sql("""
SELECT
    MSZoning,
    COUNT(*) AS total_properties,
    AVG(LotArea) AS avg_lot_area
FROM properties
GROUP BY MSZoning
ORDER BY total_properties DESC
""", conn)

print(df)

conn.close()