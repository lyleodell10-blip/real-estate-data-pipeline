import pandas as pd

def generate_market_insights(df):

    insights = {}

    # Average price
    insights["avg_price"] = round(df["price"].mean(), 2)

    # Median price
    insights["median_price"] = round(df["price"].median(), 2)

    # Average bedrooms
    insights["avg_bedrooms"] = round(df["bedrooms"].mean(), 2)

    # Most expensive city
    city_prices = df.groupby("city")["price"].mean()
    insights["top_city"] = city_prices.idxmax()

    # Cheapest city
    insights["cheap_city"] = city_prices.idxmin()

    return insights