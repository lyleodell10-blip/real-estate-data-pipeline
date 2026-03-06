import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import joblib
import pandas as pd
import plotly.express as px

# Load dataset
df = pd.read_csv("real_estate_data.csv")

# Load trained ML model
model = joblib.load("ml_models/price_model.pkl")

features = ["GrLivArea", "LotArea", "OverallQual", "YearBuilt"]

# Feature importance chart
importance_df = pd.DataFrame({
    "Feature": features,
    "Importance": model.feature_importances_
})

importance_fig = px.bar(
    importance_df,
    x="Feature",
    y="Importance",
    title="Feature Importance for House Price Prediction"
)

# Price distribution
price_hist = px.histogram(
    df,
    x="SalePrice",
    nbins=40,
    title="House Price Distribution"
)

# Living area vs price
scatter_fig = px.scatter(
    df,
    x="GrLivArea",
    y="SalePrice",
    title="Living Area vs House Price",
)

# Average price by quality
quality_df = df.groupby("OverallQual")["SalePrice"].mean().reset_index()

quality_fig = px.bar(
    quality_df,
    x="OverallQual",
    y="SalePrice",
    title="Average House Price by Quality"
)

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([

    html.H1("Real Estate Analytics & AI Valuation Dashboard"),

    html.H2("Market Analysis"),

    dcc.Graph(figure=price_hist),

    dcc.Graph(figure=scatter_fig),

    dcc.Graph(figure=quality_fig),

    html.H2("AI Home Price Predictor"),

    html.Div([

        dcc.Input(
            id="grlivarea",
            type="number",
            placeholder="Living Area (sqft)",
            style={"margin": "10px"}
        ),

        dcc.Input(
            id="lotarea",
            type="number",
            placeholder="Lot Area",
            style={"margin": "10px"}
        ),

        dcc.Input(
            id="overallqual",
            type="number",
            placeholder="Quality (1-10)",
            style={"margin": "10px"}
        ),

        dcc.Input(
            id="yearbuilt",
            type="number",
            placeholder="Year Built",
            style={"margin": "10px"}
        ),

    ]),

    html.Button(
        "Predict Price",
        id="predict_button",
        n_clicks=0,
        style={"margin": "20px"}
    ),

    html.H3(id="prediction_output"),

    html.H2("Prediction Visualization"),

    dcc.Graph(id="prediction_graph"),

    html.H2("Model Insights"),

    dcc.Graph(figure=importance_fig)

])


@app.callback(
    Output("prediction_output", "children"),
    Output("prediction_graph", "figure"),
    Input("predict_button", "n_clicks"),
    State("grlivarea", "value"),
    State("lotarea", "value"),
    State("overallqual", "value"),
    State("yearbuilt", "value")
)
def predict_price(n_clicks, grlivarea, lotarea, overallqual, yearbuilt):

    if n_clicks == 0:
        return "", {}

    if None in [grlivarea, lotarea, overallqual, yearbuilt]:
        return "Please enter all house details.", {}

    input_data = [[grlivarea, lotarea, overallqual, yearbuilt]]

    prediction = model.predict(input_data)[0]

    lower = prediction * 0.9
    upper = prediction * 1.1

    prediction_text = (
        f"Estimated House Price: ${prediction:,.0f} "
        f"(Range: ${lower:,.0f} - ${upper:,.0f})"
    )

    graph_df = pd.DataFrame({
        "Estimate": ["Low", "Predicted", "High"],
        "Price": [lower, prediction, upper]
    })

    fig = px.bar(
        graph_df,
        x="Estimate",
        y="Price",
        title="AI Price Prediction Range"
    )

    return prediction_text, fig


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

# Expose server for Gunicorn
server = app.server