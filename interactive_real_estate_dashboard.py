import pandas as pd
import numpy as np
import os
import plotly.express as px

from dash import Dash, dcc, html, Input, Output, State, dash_table
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# -----------------------------
# LOAD DATA
# -----------------------------

csv_file = "real_estate_data.csv"

if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
else:
    np.random.seed(42)
    n = 300

    df = pd.DataFrame({
        "SalePrice": np.random.randint(100000,500000,n),
        "LotArea": np.random.randint(2000,15000,n),
        "GrLivArea": np.random.randint(800,4000,n),
        "BedroomAbvGr": np.random.randint(1,6,n),
        "FullBath": np.random.randint(1,4,n),
        "YrSold": np.random.choice([2018,2019,2020,2021,2022],n),
        "Neighborhood": np.random.choice(["NAmes","CollgCr","OldTown","Edwards"],n),
        "MSZoning": np.random.choice(["RL","RM","FV","C"],n)
    })

    df.to_csv(csv_file,index=False)

# -----------------------------
# DATA PREP
# -----------------------------

df["Price_per_Sqft"] = df["SalePrice"] / df["GrLivArea"]

df["Latitude"] = np.random.uniform(40,41,len(df))
df["Longitude"] = np.random.uniform(-75,-74,len(df))

# Encode categorical variables
df_encoded = pd.get_dummies(df, columns=["Neighborhood","MSZoning"])

features = [c for c in df_encoded.columns if c != "SalePrice"]

X = df_encoded[features]
y = df_encoded["SalePrice"]

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)

# -----------------------------
# MACHINE LEARNING MODEL
# -----------------------------

model = RandomForestRegressor(n_estimators=200,random_state=42)
model.fit(X_train,y_train)

# Predictions
predictions = model.predict(X_test)

# Feature importance
importance = pd.DataFrame({
    "feature":X.columns,
    "importance":model.feature_importances_
}).sort_values("importance",ascending=False)

# -----------------------------
# DASH APP
# -----------------------------

app = Dash(__name__)
app.title = "Real Estate Analytics Platform"

# KPI CARD FUNCTION

def card(title,id_name):
    return html.Div([
        html.H4(title),
        html.H2(id=id_name)
    ],
    style={
        "width":"23%",
        "display":"inline-block",
        "border":"1px solid #ddd",
        "padding":"10px",
        "margin":"5px",
        "textAlign":"center"
    })

# -----------------------------
# LAYOUT
# -----------------------------

app.layout = html.Div([

html.H1("Real Estate Analytics Platform",style={"textAlign":"center"}),

# KPI CARDS
html.Div([
card("Average Price","kpi_avg"),
card("Median Price","kpi_median"),
card("Total Homes","kpi_total"),
card("Avg Price/Sqft","kpi_sqft")
]),

# FILTERS
html.Div([

html.Label("Neighborhood"),

dcc.Dropdown(
options=[{"label":i,"value":i} for i in df["Neighborhood"].unique()],
value=list(df["Neighborhood"].unique()),
multi=True,
id="neighborhood_filter"
),

html.Label("Year Sold"),

dcc.Dropdown(
options=[{"label":i,"value":i} for i in df["YrSold"].unique()],
value=list(df["YrSold"].unique()),
multi=True,
id="year_filter"
)

]),

# HISTOGRAM
dcc.Graph(id="price_histogram"),

# SCATTER
dcc.Graph(id="scatter_chart"),

# BOX
dcc.Graph(id="box_chart"),

# MAP
dcc.Graph(id="map_chart"),

# FEATURE IMPORTANCE
dcc.Graph(
figure=px.bar(
importance.head(10),
x="importance",
y="feature",
orientation="h",
title="Top Predictors of Home Price"
)
),

# MODEL PREDICTION COMPARISON
dcc.Graph(
figure=px.scatter(
x=y_test,
y=predictions,
labels={"x":"Actual Price","y":"Predicted Price"},
title="Model Prediction Accuracy"
)
),

# PRICE PREDICTOR
html.H2("Home Price Predictor"),

html.Div([

html.Label("Living Area (Sqft)"),

dcc.Input(id="input_sqft",type="number",value=2000),

html.Label("Bedrooms"),

dcc.Input(id="input_bedrooms",type="number",value=3),

html.Label("Lot Area"),

dcc.Input(id="input_lot",type="number",value=5000),

html.Button("Predict Price",id="predict_button"),

html.H3(id="prediction_output")

],style={"padding":"20px","border":"1px solid #ddd"}),

# TOP HOMES TABLE

html.H2("Top 10 Most Expensive Homes"),

dash_table.DataTable(
id="top_table",
page_size=10,
sort_action="native"
)

])

# -----------------------------
# DASH CALLBACK
# -----------------------------

@app.callback(

Output("price_histogram","figure"),
Output("scatter_chart","figure"),
Output("box_chart","figure"),
Output("map_chart","figure"),
Output("top_table","data"),
Output("top_table","columns"),
Output("kpi_avg","children"),
Output("kpi_median","children"),
Output("kpi_total","children"),
Output("kpi_sqft","children"),

Input("neighborhood_filter","value"),
Input("year_filter","value")

)

def update_dashboard(neighborhoods,years):

    filtered = df[
        df["Neighborhood"].isin(neighborhoods) &
        df["YrSold"].isin(years)
    ]

# KPI

    avg_price = f"${filtered['SalePrice'].mean():,.0f}"
    median_price = f"${filtered['SalePrice'].median():,.0f}"
    total = len(filtered)
    sqft = f"${filtered['Price_per_Sqft'].mean():,.2f}"

# CHARTS

    hist = px.histogram(filtered,x="SalePrice",title="Price Distribution")

    scatter = px.scatter(
        filtered,
        x="GrLivArea",
        y="SalePrice",
        color="Neighborhood",
        title="Living Area vs Price"
    )

    box = px.box(filtered,x="Neighborhood",y="SalePrice")

    map_chart = px.scatter_mapbox(
        filtered,
        lat="Latitude",
        lon="Longitude",
        color="SalePrice",
        size="GrLivArea",
        mapbox_style="open-street-map",
        zoom=9
    )

# TABLE

    top = filtered.sort_values("SalePrice",ascending=False).head(10)

    data = top.to_dict("records")

    columns=[{"name":i,"id":i} for i in top.columns]

    return hist,scatter,box,map_chart,data,columns,avg_price,median_price,total,sqft

# -----------------------------
# PRICE PREDICTION
# -----------------------------

@app.callback(
Output("prediction_output","children"),
Input("predict_button","n_clicks"),
State("input_sqft","value"),
State("input_bedrooms","value"),
State("input_lot","value"),
prevent_initial_call=True
)

def predict_price(n,sqft,bedrooms,lot):

    row = X.iloc[0].copy()

    row[:] = 0

    if "GrLivArea" in row:
        row["GrLivArea"] = sqft

    if "BedroomAbvGr" in row:
        row["BedroomAbvGr"] = bedrooms

    if "LotArea" in row:
        row["LotArea"] = lot

    predicted = model.predict([row])[0]

    return f"Estimated Price: ${predicted:,.0f}"

# -----------------------------
# RUN APP
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)