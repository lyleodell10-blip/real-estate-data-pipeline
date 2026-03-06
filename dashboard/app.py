# dashboard/app.py
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv("real_estate_data.csv")

# -----------------------------
# Train model (or load existing)
# -----------------------------
try:
    model = joblib.load("ml_models/price_model.pkl")
except:
    features = ["GrLivArea", "LotArea", "OverallQual", "YearBuilt"]
    target = "SalePrice"
    X = df[features]
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = RandomForestRegressor(n_estimators=200)
    model.fit(X_train, y_train)
    joblib.dump(model, "ml_models/price_model.pkl")

# -----------------------------
# Dash app setup
# -----------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Real Estate Price Dashboard"),
    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.Label("Above Ground Living Area (sq ft)"),
            dcc.Input(id="GrLivArea", type="number", value=1500),
            html.Br(),

            html.Label("Lot Area (sq ft)"),
            dcc.Input(id="LotArea", type="number", value=5000),
            html.Br(),

            html.Label("Overall Quality (1-10)"),
            dcc.Input(id="OverallQual", type="number", value=5),
            html.Br(),

            html.Label("Year Built"),
            dcc.Input(id="YearBuilt", type="number", value=2000),
            html.Br(),

            html.Br(),
            html.Button("Predict Price", id="predict-button", n_clicks=0),
            html.H4(id="prediction-output")
        ], width=4),

        dbc.Col([
            dcc.Graph(
                id="scatter-plot",
                figure=px.scatter(
                    df,
                    x="GrLivArea",
                    y="SalePrice",
                    color="OverallQual",
                    trendline="ols",
                    title="GrLivArea vs SalePrice"
                )
            )
        ], width=8)
    ])
], fluid=True)

# -----------------------------
# Callbacks
# -----------------------------
@app.callback(
    Output("prediction-output", "children"),
    Input("predict-button", "n_clicks"),
    Input("GrLivArea", "value"),
    Input("LotArea", "value"),
    Input("OverallQual", "value"),
    Input("YearBuilt", "value")
)
def predict_price(n_clicks, gr_liv, lot, qual, year):
    if n_clicks == 0:
        return ""
    features = [[gr_liv, lot, qual, year]]
    pred = model.predict(features)[0]
    return f"Predicted Sale Price: ${pred:,.0f}"

# -----------------------------
# Expose server for Gunicorn
# -----------------------------
server = app.server

# Optional: run locally
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)