import streamlit as st
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import LabelEncoder

# Das speichert das Machine-Learning-Modell im Cache, damit es nicht jedes Mal neu trainiert wird
@st.cache_resource
def train_model(df: pd.DataFrame):  # Wandle Kraftstoffart (ein Wort) in Zahlen um, die das Modell versteht
    """
    Train a Decision Tree Regressor on vehicle data to predict CO2 emissions.

    Parameters:
        df (pd.DataFrame): Cleaned vehicle dataset.

    Returns:
        model (DecisionTreeRegressor): Trained decision tree model.
        le (LabelEncoder): Label encoder for fuel type.
    """
    # Entferne Zeilen, bei denen wichtige Daten fehlen
    data = df.dropna(
        subset=["Fuel_Type1", "Cylinders", "Year", "Co2__Tailpipe_For_Fuel_Type1"]   
    ).copy()
    # Wandle Kraftstoffart (ein Wort) in Zahlen um, die das Modell versteht
    le = LabelEncoder()
    data["Fuel_Type1_Encoded"] = le.fit_transform(data["Fuel_Type1"])
    X = data[["Fuel_Type1_Encoded", "Cylinders", "Year"]]     # Setze die Eingabemerkmale (Kraftstoff, Zylinderanzahl, Baujahr)
    y = data["Co2__Tailpipe_For_Fuel_Type1"]    # Setze das Ziel, das wir vorhersagen wollen (CO2-Ausstoß)
    model = DecisionTreeRegressor(random_state=42)     # Erstelle das Decision-Tree-Modell
    model.fit(X, y)    # Trainiere das Modell mit unseren Daten
    return model, le    # Gib das trainierte Modell und den Encoder zurück

def predict_co2_emission(model, le, fuel_type, cylinders, year) -> float:
    """
    Predict CO2 emissions based on user input using the trained model.

    Parameters:
        model: Trained DecisionTreeRegressor.
        le: LabelEncoder for encoding fuel types.
        fuel_type (str): Type of fuel.
        cylinders (int): Number of engine cylinders.
        year (int): Vehicle model year.

    Returns:
        float: Predicted CO2 emission value.
    """
    # Erstelle ein kleines DataFrame (1 Zeile) mit den Autodaten des Nutzers
    inp = pd.DataFrame(
        [[fuel_type, cylinders, year]],
        columns=["Fuel_Type1", "Cylinders", "Year"]
    )
    # Verschlüssele die Kraftstoffart, damit das Modell sie versteht
    inp["Fuel_Type1_Encoded"] = le.transform(inp["Fuel_Type1"])
     # Frage das Modell, den CO2-Ausstoß für dieses Auto vorherzusagen
    return model.predict(inp[["Fuel_Type1_Encoded", "Cylinders", "Year"]])[0] 