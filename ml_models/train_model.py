import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

df = pd.read_csv("real_estate_data.csv")

features = ["GrLivArea","LotArea","OverallQual","YearBuilt"]
target = "SalePrice"

X = df[features]
y = df[target]

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2)

model = RandomForestRegressor(n_estimators=200)

model.fit(X_train,y_train)

joblib.dump(model,"ml_models/price_model.pkl")

print("Model trained and saved.")

