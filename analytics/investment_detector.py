import pandas as pd

def find_investment_opportunities(df):

    city_avg = df.groupby("city")["price"].mean().to_dict()

    opportunities = []

    for _, row in df.iterrows():

        city_avg_price = city_avg[row["city"]]

        if row["price"] < city_avg_price * 0.8:

            opportunities.append({
                "city": row["city"],
                "price": row["price"],
                "bedrooms": row["bedrooms"],
                "sqft": row["sqft"]
            })

    return pd.DataFrame(opportunities)