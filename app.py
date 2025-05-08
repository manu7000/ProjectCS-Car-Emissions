import streamlit as st
import pandas as pd
import pydeck as pdk
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import LabelEncoder
import numpy as np
from Map_API import autocomplete_address, get_coordinates, get_route_info

# Set page configuration
st.set_page_config(page_title="CO₂ Emission Calculator", page_icon="🚗", layout="centered")

# -----------------------------------
# Utility Functions YANNICK
# -----------------------------------

@st.cache_data
def load_vehicle_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", engine="python")
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    return df.dropna(subset=["Make", "Fuel_Type1", "Model", "Year", "Co2__Tailpipe_For_Fuel_Type1"])

@st.cache_resource
def train_model(df):
    df = df.dropna(subset=["Fuel_Type1", "Cylinders", "Year", "Co2__Tailpipe_For_Fuel_Type1"]).copy()
    le = LabelEncoder()
    df["Fuel_Type1_Encoded"] = le.fit_transform(df["Fuel_Type1"])
    X = df[["Fuel_Type1_Encoded", "Cylinders", "Year"]]
    y = df["Co2__Tailpipe_For_Fuel_Type1"]
    model = DecisionTreeRegressor(random_state=42)
    model.fit(X, y)
    return model, le

def predict_co2_emission(model, le, fuel_type, cylinders, year):
    user_input = pd.DataFrame([[fuel_type, cylinders, year]], columns=["Fuel_Type1", "Cylinders", "Year"])
    user_input["Fuel_Type1_Encoded"] = le.transform(user_input["Fuel_Type1"])
    return model.predict(user_input[["Fuel_Type1_Encoded", "Cylinders", "Year"]])[0]

def display_route_map(route):
    route_coords = [[lat, lon] for lon, lat in route['geometry']]
    df = pd.DataFrame(route_coords, columns=["lat", "lon"])
    df["lon_next"] = df["lon"].shift(-1)
    df["lat_next"] = df["lat"].shift(-1)
    df = df.dropna()

    center_lat = (df["lat"].min() + df["lat"].max()) / 2
    center_lon = (df["lon"].min() + df["lon"].max()) / 2
    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7)

    layer = pdk.Layer(
        "LineLayer",
        data=df,
        get_source_position=["lon", "lat"],
        get_target_position=["lon_next", "lat_next"],
        get_color=[0, 0, 255],
        get_width=4
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style='mapbox://styles/mapbox/satellite-streets-v11'
    ))

# -----------------------------------
# UI Elements
# -----------------------------------

st.title("Car Journey CO₂ Emission Calculator")
st.write("Welcome! This app will help you calculate and compare the carbon emissions of your trips.")

st.sidebar.header("Enter your trip information")

# Address inputs
start_input = st.sidebar.text_input("From:")
selected_start = st.sidebar.selectbox("Select starting location:", autocomplete_address(start_input)) if start_input else None

end_input = st.sidebar.text_input("To:")
selected_end = st.sidebar.selectbox("Select destination:", autocomplete_address(end_input)) if end_input else None

# Load vehicle data
try:
    vehicle_df = load_vehicle_data("all-vehicles-model@public.csv")
except Exception:
    st.error("Could not load vehicle database.")
    st.stop()

model, le = train_model(vehicle_df)

# ---------------- KAIS -----------------------------------------------------------------------

st.sidebar.header("Select Your Vehicle")
car_not_listed = st.sidebar.checkbox("My car is not listed")

if car_not_listed:
    fuel_type = st.sidebar.selectbox("Fuel Type", vehicle_df["Fuel_Type1"].dropna().unique())
    cylinders = st.sidebar.number_input("Number of Cylinders", min_value=3, max_value=16, step=1)
    year = st.sidebar.number_input("Year", min_value=1980, max_value=2025, step=1)
    predicted_co2 = predict_co2_emission(model, le, fuel_type, cylinders, year)
    st.sidebar.success(f"Predicted CO₂ Emission: {(predicted_co2 / 1.60934):.2f} g/km")

    final_row = pd.Series({"Co2__Tailpipe_For_Fuel_Type1": predicted_co2})
    selected_make, selected_model, selected_year, selected_fuel = "Custom", "Custom Entry", year, fuel_type
else:
    selected_make = st.sidebar.selectbox("Make", sorted(vehicle_df['Make'].dropna().unique()))
    df_filtered = vehicle_df[vehicle_df['Make'] == selected_make]
    selected_fuel = st.sidebar.selectbox("Fuel Type", sorted(df_filtered['Fuel_Type1'].dropna().unique()))
    df_filtered = df_filtered[df_filtered['Fuel_Type1'] == selected_fuel]
    selected_model = st.sidebar.selectbox("Model", sorted(df_filtered['Model'].dropna().unique()))
    df_filtered = df_filtered[df_filtered['Model'] == selected_model]
    selected_year = st.sidebar.selectbox("Year", sorted(df_filtered['Year'].dropna().unique(), reverse=True))

    final_row = vehicle_df[
        (vehicle_df['Make'] == selected_make) &
        (vehicle_df['Fuel_Type1'] == selected_fuel) &
        (vehicle_df['Model'] == selected_model) &
        (vehicle_df['Year'] == selected_year)
    ]

compare_public_transport = st.sidebar.checkbox("Compare with public transport")

# -----------------------------------
# MAIN LOGIC
# -----------------------------------
if selected_start and selected_end and st.sidebar.button("Calculate Route"):
    try:
        with st.spinner("Calculating route and emissions..."):
            start_coords = get_coordinates(selected_start)
            end_coords   = get_coordinates(selected_end)
            route        = get_route_info(start_coords, end_coords)
            distance_km  = route['distance_km']
            duration_min = route['duration_min']

        # retrieve vehicle/co2 info
        row = final_row.iloc[0] if not car_not_listed else final_row
        co2_g_mile       = row['Co2__Tailpipe_For_Fuel_Type1']
        mpg              = row.get('Combined_Mpg_For_Fuel_Type1', np.nan)
        ghg_score        = row.get('GHG_Score', np.nan)
        car_emission_kg  = (co2_g_mile / 1.60934) * distance_km / 1000

        # ---------------- MANU-------------------------------------------------------------------------
        # Dashboard‐style layout for Estimated Impact
        st.header("Estimated Impact")

        # Row 1: Vehicle / Distance / Time
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.success(f"{selected_make} {selected_model} ({selected_year})")
        with c2:
            st.metric("📏 Distance", f"{distance_km:.2f} km")
        with c3:
            if duration_min >= 60:
                h, m = divmod(int(duration_min), 60)
                st.metric("🕒 Travel Time", f"{h}h {m}m")
            else:
                st.metric("🕒 Travel Time", f"{duration_min:.0f} min")

        # Row 2: CO₂ / Fuel / GHG
        d1, d2, d3 = st.columns(3)
        with d1:
            st.metric("💨 CO₂ Emissions", f"{car_emission_kg:.2f} kg")
        with d2:
            if pd.notna(mpg) and mpg > 0:
                liters = (235.21 / mpg) * distance_km / 100
                st.metric("⛽ Fuel Consumption", f"{liters:.2f} L")
        with d3:
            if pd.notna(ghg_score):
                color = "#2ECC71" if ghg_score >= 8 else "#F39C12" if ghg_score >= 5 else "#E74C3C"
                st.markdown(
                    f"<div style='padding:8px; background:{color}; border-radius:6px; color:white; text-align:center;'>"
                    f"🌿 GHG Score: {int(ghg_score)}/10</div>",
                    unsafe_allow_html=True
                )

        # (Optional) Public transport comparison
        if compare_public_transport:
            st.subheader("Public Transport Comparison")
            t1, t2, t3 = st.columns(3)
            train_kg = 41 * distance_km / 1000
            bus_kg   = 105 * distance_km / 1000
            t1.metric("🚄 Train", f"{train_kg:.2f} kg")
            t2.metric("🚌 Bus",   f"{bus_kg:.2f} kg")
            t3.write("")

        # Route Map
        st.header("Route Map")
        display_route_map(route)

    except Exception as e:
        st.error("❌ An error occurred during route calculation.")
        st.exception(e)

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("---")
st.caption("CS Project by Aymeric, Kaïs, Emmanuel and Yannick. Group 2.06. Data sources: OpenRouteService, EEA, EPA.")