import streamlit as st
import pandas as pd
import pydeck as pdk

# HILFSFUNKTIONEN 
# Dieser Dekorator sagt Streamlit, das Ergebnis der Funktion zwischenzuspeichern, damit es beim erneuten Aufruf schneller geht
@st.cache_data
def load_vehicle_data(path: str) -> pd.DataFrame:
    """
    Load and clean a vehicle dataset from a CSV file.

    Parameters:
        path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Cleaned DataFrame with essential columns retained.
    """
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", engine="python")     # Lese die CSV-Datei in ein DataFrame (wie eine Tabelle im Code)
    df.columns = df.columns.str.strip().str.replace(" ", "_")    # Bereinige die Spaltennamen: entferne Leerzeichen und ersetze sie durch Unterstriche
    return df.dropna(    # Entferne Zeilen, bei denen wichtige Informationen fehlen
        subset=[
            "Make",     
            "Fuel_Type1",   
            "Model",     
            "Year",    
            "Co2__Tailpipe_For_Fuel_Type1"    
        ]
    )

#-------------------------------------------------------------------------------------------------GPT??????
def display_route_map(route: dict):
    """
    Visualize a route using PyDeck with line segments between coordinates.

    Parameters:
        route (dict): Dictionary containing route geometry with 'geometry' key
                      as a list of [longitude, latitude] points.
    """
    # Bereite das Koordinaten-DataFrame vor
    coords = [[lat, lon] for lon, lat in route["geometry"]]
    df = pd.DataFrame(coords, columns=["lat", "lon"])    # Lege die Koordinaten in ein DataFrame, damit PyDeck sie nutzen kann
    
    # Erstelle neue Spalten mit dem nächsten Punkt auf der Route, um Linien zwischen den Punkten zu zeichnen
    df["lon_next"] = df["lon"].shift(-1)
    df["lat_next"] = df["lat"].shift(-1)
    df = df.dropna() # Entferne alle Zeilen mit fehlenden Daten

    # Karte zentrieren
    center_lat = (df["lat"].min() + df["lat"].max()) / 2    # Finde den Mittelpunkt der Route für korrekten Zoom (Breite)
    center_lon = (df["lon"].min() + df["lon"].max()) / 2    # Finde den Mittelpunkt der Route für korrekten Zoom (Länge)
    view = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7)

    # Linien-Layer für Route
    layer = pdk.Layer(   
        "LineLayer",    # Sagt PyDeck, Linien zu zeichnen
        data=df,     # Nutze unsere Routendaten
        get_source_position=["lon", "lat"],    # Start jeder Linie
        get_target_position=["lon_next", "lat_next"],    # Ende jeder Linie
        get_color=[0, 0, 255],    # Blaue Linien (RGB)
        get_width=4     # Liniendicke
    )

    # Zeige die Karte in der Streamlit-App
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],     # Der Layer zum Zeichnen der Route
            initial_view_state=view,     # Mittelpunkt und Zoomstufe der Karte
            map_style="mapbox://styles/mapbox/satellite-streets-v11"     # Kartenstil
        )
    )
    