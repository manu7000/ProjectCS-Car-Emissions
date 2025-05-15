import streamlit as st
import pandas as pd
import pydeck as pdk
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import LabelEncoder
import numpy as np
from Map_API import autocomplete_address, get_coordinates, get_route_info

# SEITENKONFIGURATION
st.set_page_config(
    page_title="CO₂ Emission Calculator",
    page_icon="🚗",
    layout="centered"
)

# Titel
st.title("Car Journey CO₂ Emission Calculator")  # Haupttitel der App anzeigen
st.write("Welcome! This app will help you calculate and compare the carbon emissions of your trips.")  # Untertitel


# HILFSFUNKTIONEN 
# Dieser Dekorator sagt Streamlit, das Ergebnis der Funktion zwischenzuspeichern, damit es beim erneuten Aufruf schneller geht
@st.cache_data
def load_vehicle_data(path: str) -> pd.DataFrame:
    """
    Load and clean vehicle dataset from a CSV file.
    Drops rows missing critical fields.
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

# Das speichert das Machine-Learning-Modell im Cache, damit es nicht jedes Mal neu trainiert wird
@st.cache_resource
def train_model(df: pd.DataFrame):  # Wandle Kraftstoffart (ein Wort) in Zahlen um, die das Modell versteht
    """
    Train a Decision Tree on known vehicles to predict CO2 for custom entries.
    Returns the trained model and the label encoder.
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
    Given user-specified fuel type, cylinder count, and year,
    predict CO2 tailpipe emissions using the trained model.
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
    

#-------------------------------------------------------------------------------------------------GPT??????
def display_route_map(route: dict):
    """
    Render the route geometry on a PyDeck map.
    Expects 'geometry' key: list of [lon, lat] points.
    """
    if route is None:
        st.error("Unable to retrieve a route. Please check the addresses and try again.")
        st.stop()
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
    
    

# Seitenleiste: Eingabe der Reisedaten
st.sidebar.header("Enter your trip information")  # Überschrift für den Seitenleistenabschnitt
start_input = st.sidebar.text_input("From:")  # Textfeld für Startadresse
selected_start = st.sidebar.selectbox(  
    "Select starting location:",  
    autocomplete_address(start_input)  
) if start_input else None  # Autovervollständigung nur nach Eingabe anzeigen. Nur anzeigen, wenn Eingabe vorhanden ist

end_input = st.sidebar.text_input("To:")  # Textfeld für Zieladresse
selected_end = st.sidebar.selectbox(  
    "Select destination:",  
    autocomplete_address(end_input)  
) if end_input else None  # Autovervollständigung nur nach Eingabe anzeigen. Nur anzeigen, wenn Eingabe vorhanden ist

# Fahrzeugdaten laden und trainieren
try:  
    vehicle_df = load_vehicle_data("all-vehicles-model@public.csv")  # Lese & bereinige CSV
except Exception:  
    st.error("Could not load vehicle database.")  # Zeige Fehler, falls Laden fehlschlägt
    st.stop()  # Beende die App bei Fehler

model, le = train_model(vehicle_df)  # Trainiere ML-Modell + Encoder für eigene CO₂-Vorhersagen

# Seitenleiste: Fahrzeugauswahl oder eigene Eingabe
st.sidebar.header("Select Your Vehicle")  # Überschrift für Fahrzeugauswahl
car_not_listed = st.sidebar.checkbox("My car is not listed")  # Checkbox für "Auto nicht gelistet"

# Was auf der Oberfläche angezeigt wird, je nachdem, ob das Auto gelistet ist oder nicht
# Wenn die Checkbox "My car is not listed" ausgewählt ist, erscheint ein anderes Dropdown-Menü
if car_not_listed:
    fuel_type = st.sidebar.selectbox("Fuel Type", vehicle_df["Fuel_Type1"].unique())  
    cylinders = st.sidebar.number_input("Number of Cylinders", min_value=3, max_value=16, step=1)  
    year = st.sidebar.number_input("Year", min_value=1980, max_value=2025, step=1) 
    predicted_co2 = predict_co2_emission(model, le, fuel_type, cylinders, year)  # CO2 mit ML vorhersagen
    st.sidebar.success(f"Predicted CO₂ Emission: {(predicted_co2/1.60934):.2f} g/km")  # Zeige CO2-Vorhersage an (geteilt durch 1,6, weil in der CSV pro Meile)
    final_row = pd.Series({"Co2__Tailpipe_For_Fuel_Type1": predicted_co2})  # Einzelzeilen-Fallback, damit der Code mit ML-Vorhersage funktioniert, sonst würde er weiter unten nach final_row suchen
    selected_make, selected_model, selected_year, selected_fuel = "Custom", "Custom Entry", year, fuel_type  # Platzhalterwerte für Marke und Modell, damit der Code wie bei normaler Auswahl funktioniert
else:
    selected_make = st.sidebar.selectbox("Brand", sorted(vehicle_df["Make"].unique()))  # Auswahl der Marke in der Seitenleiste
    df_m = vehicle_df[vehicle_df["Make"] == selected_make]  # Nach Marke filtern
    selected_fuel = st.sidebar.selectbox("Fuel Type", sorted(df_m["Fuel_Type1"].unique()))  # Auswahl des Kraftstoffs in der Seitenleiste
    df_f = df_m[df_m["Fuel_Type1"] == selected_fuel]  # Nach Kraftstoff filtern
    selected_model = st.sidebar.selectbox("Model", sorted(df_f["Model"].unique()))  # Auswahl des Modells in der Seitenleiste
    df_mod = df_f[df_f["Model"] == selected_model]  # Nach Modell filtern
    selected_year = st.sidebar.selectbox(  
        "Year",  
        sorted(df_mod["Year"].unique(), reverse=True)  
    )  # Auswahl des Baujahrs in der Seitenleiste
    final_row = vehicle_df[  
        (vehicle_df["Make"] == selected_make) &  
        (vehicle_df["Fuel_Type1"] == selected_fuel) &  
        (vehicle_df["Model"] == selected_model) &  
        (vehicle_df["Year"] == selected_year)  
    ]  # Suche nach der ausgewählten Zeile

# Option zum Vergleich mit öffentlichen Verkehrsmitteln
compare_public_transport = st.sidebar.checkbox("Compare with public transport")  
if selected_start and selected_end and st.sidebar.button("Calculate Route"):
    try:
        # Berechne Routendaten über OpenRouteService
        with st.spinner("Calculating route and emissions..."): # Ladeanimation während der Berechnung
            sc = get_coordinates(selected_start) 
            ec = get_coordinates(selected_end)
            route = get_route_info(sc, ec) # Ruft OpenRouteService-Funktion auf, um die Route für die angegebenen Adressen zu berechnen
        if route is None:
            st.exception()
            distance_km = 0
            duration_min = 0
        else:
            distance_km = route["distance_km"]
            duration_min = route["duration_min"] # min Dauer von OpenRouteService

        # Hole CO₂- und MPG-(Meilen pro Gallone)-Daten
        row = final_row.iloc[0] if not car_not_listed else final_row 
        co2_g_mile = row["Co2__Tailpipe_For_Fuel_Type1"] # Suche CO₂-Wert für das ausgewählte Auto
        mpg = row.get("Combined_Mpg_For_Fuel_Type1", np.nan) # Hole MPG-Wert, falls verfügbar, sonst NaN
        ghg_score = row.get("GHG_Score", np.nan) # Hole GHG-Score, falls verfügbar, sonst NaN
        car_emission_kg = (co2_g_mile / 1.60934) * distance_km / 1000 # Berechne Emission in kg: 1 Meile = 1,60934 km und /1000 für kg

        # Geschätzte Auswirkungen
        st.header("Estimated Impact")
        st.info(
            "💡 To halt climate change, the max CO₂ consumption per person per year should be ≈ **600 kg**."
        ) # Kleines Info-Feld für den Nutzer

        # Reisezeit-String formatieren
        if duration_min >= 60:
            h, m = divmod(int(duration_min), 60)  # Teile durch 60 für Stunden und Minuten, wenn über 60 Minuten
            travel_str = f"{h}h {m}m" 
        else:
            travel_str = f"{duration_min:.0f}m" # Wenn unter 60 Minuten, in Minuten belassen

        # Berechne Literverbrauch, falls MPG bekannt
        trip_L = (
            (235.21 / mpg) * distance_km / 100
            if pd.notna(mpg) and mpg > 0 else np.nan
        )

#--------------------------------------------------------------------------------------------------------------------GPT ?????????
        # Info-Felder
        labels = ["Distance", "Travel Time", "CO₂ Emissions", "Fuel Consumption"]
        icons = ["📏", "🕒", "💨", "⛽"]
        vals = [
            f"{distance_km:.2f} km",
            travel_str,
            f"{car_emission_kg:.2f} kg",
            f"{trip_L:.2f} L" # Nutze die oben berechneten Werte und zeige sie mit f-Strings in den Boxen an
        ]
        cards = st.columns(4, gap="small") # Erzeuge eine Reihe von vier gestalteten Karten  
        for col, icon, lab, val in zip(cards, icons, labels, vals):
            col.markdown(f"""
                <div style=" 
                    padding:20px;
                    background:white;
                    border-radius:8px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.1);
                    text-align:center; 
                ">
                  <div style="font-size:28px;">{icon}</div>
                  <div style="font-size:24px; font-weight:bold; margin:4px 0;">{val}</div>
                  <div style="font-size:14px; color:#666;">{lab}</div>
                </div>
            """, unsafe_allow_html=True) # Box-Gestaltung 

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)  # Füge vertikalen Abstand vor der nächsten Kartenreihe hinzu
        
        g1, g2 = st.columns(2, gap="small")     # Erstelle zwei Spalten für Anzeige von GHG-Score (g1) und ÖPNV-Emissionen (g2)


        #--------------------------------------------------------------------------------------------------------------------GPT ?????????
        # GHG-Score-Karte
        with g1:
            if pd.notna(ghg_score):     # Prüfe, ob ein GHG-Score für das gewählte Auto existiert
                col = "#2ECC71" if ghg_score >= 8 else "#F39C12" if ghg_score >= 5 else "#E74C3C"   # Bestimme die Farbe anhand des GHG-Scores (grün = gut, orange = mittel, rot = schlecht)
                
                # Zeige den GHG-Score als farbige Karte an
                g1.markdown(f"""
                    <div style="
                        padding:20px;
                        background:{col};
                        border-radius:8px;
                        color:white;
                        text-align:center;
                    ">
                      <div style="font-size:24px; font-weight:bold;">{int(ghg_score)}/10</div>
                      <div style="font-size:14px; margin-top:4px;">GHG Score</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Zeige Ersatztext, wenn kein GHG-Score vorhanden ist
                g1.markdown(f"""
                    <div style="
                        padding:20px;
                        background:#cccccc;
                        border-radius:8px;
                        color:white;
                        text-align:center;
                    ">
                      <div style="font-size:24px; font-weight:bold;">–</div>
                      <div style="font-size:14px; margin-top:4px;">
                        GHG score is not available for this model of car
                      </div>
                    </div>
                """, unsafe_allow_html=True)

        # Karte für öffentlichen Verkehr (nur wenn Checkbox aktiviert)
        with g2:
            if compare_public_transport:
                train_kg = 41 * distance_km / 1000  # 41g CO2/km als Richtwert (Quelle: EEA), /1000 für kg
                bus_kg = 105 * distance_km / 1000   # 105g CO2/km als Richtwert (Quelle: EEA), /1000 für kg
                
                # Zeige Vergleichskarte für Emissionen an
                g2.markdown(f"""
                    <div style="
                        padding:20px;
                        background:white;
                        border-radius:8px;
                        box-shadow:0 1px 4px rgba(0,0,0,0.1);
                        text-align:center;
                    ">
                      <div style="font-size:24px; font-weight:bold;">
                        🚄 {train_kg:.2f} kg &nbsp; 🚌 {bus_kg:.2f} kg
                      </div>
                      <div style="font-size:14px; color:#666; margin-top:4px;">
                        Public Transport Emissions Comparison
                      </div>
                    </div>
                """, unsafe_allow_html=True)
        
        # Info-Box über die prozentuale Emissionsreduktion durch ÖPNV (nur wenn Checkbox aktiviert)
        if compare_public_transport:
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)  # Füge extra Abstand vor der Info-Box über Prozentänderungen hinzu
            
            # Berechne prozentuale Emissionsersparnis, wenn Zug oder Bus statt Auto genommen wird
            percent_train = (
                (car_emission_kg - train_kg) / car_emission_kg * 100
                if car_emission_kg > train_kg else 0
            )
            percent_bus = (
                (car_emission_kg - bus_kg) / car_emission_kg * 100
                if car_emission_kg > bus_kg else 0
            )
            
            # Zeige die berechneten Ersparnisse in einer Info-Box an
            st.info(
                f"🚄 Taking the train would reduce emissions by {percent_train:.1f}%\n\n"
                f"🚌 Taking the bus would reduce emissions by {percent_bus:.1f}%"
            )

        
        # Routenkartenanzeige

        st.header("Route Map")
        display_route_map(route)    # Zeige die Routenkarte mit der berechneten Route an

    # Zeige Fehlermeldung, falls keine Route gefunden wurde
    except Exception as e:
        st.error("❌ An error occurred during route calculation.")
        st.exception(e)


# FUSSZEILE
st.markdown("---")
st.caption(
    "CS Project by Aymeric, Kaïs, Emmanuel and Yannick. Group 2.06. "
    "Data sources: OpenRouteService, EEA, EPA."
)