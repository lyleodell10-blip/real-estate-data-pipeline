import pandas as pd
import numpy as np

from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go

from flask import jsonify

# -------------------------------
# LOAD DATA
# -------------------------------

DATA_FILE = "real_estate_data.csv"

df = pd.read_csv(DATA_FILE)

# -------------------------------
# BASIC CLEANING
# -------------------------------

# Fill numeric NaNs with median
numeric_cols = df.select_dtypes(include=np.number).columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

# Ensure SalePrice exists
if "SalePrice" not in df.columns:
    raise Exception("Dataset must include SalePrice column")

# Create price per sqft
if "GrLivArea" in df.columns:
    df["PricePerSqft"] = df["SalePrice"] / df["GrLivArea"]
else:
    df["PricePerSqft"] = df["SalePrice"]

# -------------------------------
# MARKET INSIGHTS ENGINE
# -------------------------------

def generate_market_insights(data):

    insights = []

    avg_price = int(data["SalePrice"].mean())
    median_price = int(data["SalePrice"].median())

    insights.append(f"Average home price: ${avg_price:,}")
    insights.append(f"Median home price: ${median_price:,}")

    if "Neighborhood" in data.columns:

        top_neighborhood = (
            data.groupby("Neighborhood")["SalePrice"]
            .mean()
            .sort_values(ascending=False)
            .index[0]
        )

        insights.append(f"Highest value neighborhood: {top_neighborhood}")

    if "YrSold" in data.columns:

        yearly = data.groupby("YrSold")["SalePrice"].mean()

        if len(yearly) > 1:

            trend = "increasing" if yearly.iloc[-1] > yearly.iloc[0] else "decreasing"

            insights.append(f"Market trend appears {trend}")

    return insights


# -------------------------------
# INVESTMENT DEAL DETECTOR
# -------------------------------

def find_investment_deals(data):

    median_ppsqft = data["PricePerSqft"].median()

    deals = data[data["PricePerSqft"] < median_ppsqft * 0.8]

    deals = deals.sort_values("PricePerSqft").head(10)

    return deals


# -------------------------------
# DASH APP
# -------------------------------

app = Dash(__name__)
server = app.server

# -------------------------------
# DROPDOWN OPTIONS
# -------------------------------

def dropdown_options(column):

    if column in df.columns:

        values = sorted(df[column].dropna().unique())

        return [{"label": str(v), "value": v} for v in values]

    return []


# -------------------------------
# LAYOUT
# -------------------------------

app.layout = html.Div([

    html.H1("Real Estate Analytics Dashboard"),

    html.Div([

        dcc.Dropdown(
            id="neighborhood_filter",
            options=dropdown_options("Neighborhood"),
            multi=True,
            placeholder="Filter by Neighborhood"
        ),

        dcc.Dropdown(
            id="year_filter",
            options=dropdown_options("YrSold"),
            multi=True,
            placeholder="Filter by Year Sold"
        ),

        dcc.Dropdown(
            id="zoning_filter",
            options=dropdown_options("MSZoning"),
            multi=True,
            placeholder="Filter by Zoning"
        )

    ], style={"width": "50%"}),

    html.Hr(),

    html.H2("Automated Market Insights"),

    html.Div(id="market_insights"),

    html.Hr(),

    html.H2("Investment Opportunities"),

    html.Div(id="investment_table"),

    html.Hr(),

    dcc.Graph(id="saleprice_histogram"),
    dcc.Graph(id="lotarea_histogram"),
    dcc.Graph(id="correlation_heatmap"),
    dcc.Graph(id="sales_trend"),
    dcc.Graph(id="monthly_sales_trend"),
    dcc.Graph(id="price_per_sqft_neighborhood"),
    dcc.Graph(id="price_per_sqft_zoning")

])


# -------------------------------
# DASH CALLBACK
# -------------------------------

@app.callback(

    Output("saleprice_histogram", "figure"),
    Output("lotarea_histogram", "figure"),
    Output("correlation_heatmap", "figure"),
    Output("sales_trend", "figure"),
    Output("monthly_sales_trend", "figure"),
    Output("price_per_sqft_neighborhood", "figure"),
    Output("price_per_sqft_zoning", "figure"),
    Output("market_insights", "children"),
    Output("investment_table", "children"),

    Input("neighborhood_filter", "value"),
    Input("year_filter", "value"),
    Input("zoning_filter", "value")

)

def update_dashboard(neighborhoods, years, zoning):

    filtered = df.copy()

    if neighborhoods and "Neighborhood" in filtered.columns:
        filtered = filtered[filtered["Neighborhood"].isin(neighborhoods)]

    if years and "YrSold" in filtered.columns:
        filtered = filtered[filtered["YrSold"].isin(years)]

    if zoning and "MSZoning" in filtered.columns:
        filtered = filtered[filtered["MSZoning"].isin(zoning)]

    # ---------------------------
    # CHARTS
    # ---------------------------

    saleprice_hist = px.histogram(filtered, x="SalePrice", nbins=40)

    if "LotArea" in filtered.columns:
        lotarea_hist = px.histogram(filtered, x="LotArea", nbins=40)
    else:
        lotarea_hist = px.histogram(filtered, x="SalePrice")

    corr = filtered.select_dtypes(include=np.number).corr()

    heatmap = px.imshow(corr)

    if "YrSold" in filtered.columns:

        sales_trend = px.line(
            filtered.groupby("YrSold")["SalePrice"].mean().reset_index(),
            x="YrSold",
            y="SalePrice"
        )

    else:
        sales_trend = go.Figure()

    if "MoSold" in filtered.columns:

        monthly_sales_trend = px.line(
            filtered.groupby("MoSold")["SalePrice"].mean().reset_index(),
            x="MoSold",
            y="SalePrice"
        )

    else:
        monthly_sales_trend = go.Figure()

    if "Neighborhood" in filtered.columns:

        price_neighborhood = px.bar(
            filtered.groupby("Neighborhood")["PricePerSqft"].mean().reset_index(),
            x="Neighborhood",
            y="PricePerSqft"
        )

    else:
        price_neighborhood = go.Figure()

    if "MSZoning" in filtered.columns:

        price_zoning = px.bar(
            filtered.groupby("MSZoning")["PricePerSqft"].mean().reset_index(),
            x="MSZoning",
            y="PricePerSqft"
        )

    else:
        price_zoning = go.Figure()

    # ---------------------------
    # MARKET INSIGHTS
    # ---------------------------

    insights = generate_market_insights(filtered)

    insights_html = html.Ul([html.Li(i) for i in insights])

    # ---------------------------
    # INVESTMENT DEALS TABLE
    # ---------------------------

    deals = find_investment_deals(filtered)

    table = html.Table([

        html.Thead(
            html.Tr([
                html.Th("Neighborhood"),
                html.Th("Price"),
                html.Th("Price per Sqft")
            ])
        ),

        html.Tbody([

            html.Tr([

                html.Td(row.get("Neighborhood", "")),
                html.Td(f"${int(row['SalePrice']):,}"),
                html.Td(f"${round(row['PricePerSqft'],2)}")

            ])

            for _, row in deals.iterrows()

        ])

    ])

    return (
        saleprice_hist,
        lotarea_hist,
        heatmap,
        sales_trend,
        monthly_sales_trend,
        price_neighborhood,
        price_zoning,
        insights_html,
        table
    )


# -------------------------------
# API ENDPOINT
# -------------------------------

@server.route("/api/market-insights")

def api_market_insights():

    insights = generate_market_insights(df)

    return jsonify({"insights": insights})


# -------------------------------
# RUN APP
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True)
```
