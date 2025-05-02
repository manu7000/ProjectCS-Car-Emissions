import streamlit as st
import pandas as pd
from routing import get_coordinates, get_route_info

# ---- LOAD VEHICLE DATABASE ----
@st.cache_data
def load_vehicle_data():
    df = pd.read_csv("Euro_6_latest.csv", encoding="latin1")
    df = df[["Manufacturer", "Model", "Description", "Fuel Type", "WLTP CO2"]].dropna(subset=["WLTP CO2"])
    df["Vehicle Label"] = (
        df["Manufacturer"] + " | " +
        df["Model"] + " | " +
        df["Description"] + " | " +
        df["Fuel Type"]
    )
    df = df.drop_duplicates(subset=["Vehicle Label"]).reset_index(drop=True)
    return df[["Vehicle Label", "WLTP CO2"]]

vehicle_df = load_vehicle_data()

# ---- PAGE SETUP ----
st.set_page_config(page_title="🖕🏾Car Journey CO₂ Emission Calculator", page_icon="🚗", layout="centered")
st.title("🥸Car Journey CO₂ Emission Calculator")
st.write("Welcome! This app helps calculate carbon emissions based on your car journey.")

# ---- SIDEBAR ----
st.sidebar.header("Journey Details")

selected_vehicle = st.sidebar.selectbox("Select your vehicle", vehicle_df["Vehicle Label"].tolist())
start = st.sidebar.text_input("Enter start address")
end = st.sidebar.text_input("Enter destination address")

# ---- MAIN SECTION ----
st.header("Your Journey Summary")

if st.button("Calculate Emissions"):
    if start and end and selected_vehicle:
        try:
            # Extract selected vehicle's CO₂ per km
            co2_per_km = vehicle_df.loc[
                vehicle_df["Vehicle Label"] == selected_vehicle, "WLTP CO2"
            ].values[0]

            # Geocode and get route info
            start_coords = get_coordinates(start)
            end_coords = get_coordinates(end)
            route_data = get_route_info(start_coords, end_coords)

            distance_km = route_data["distance_km"]
            co2_total_grams = co2_per_km * distance_km
            co2_total_kg = co2_total_grams / 1000

            st.success(f"Route from **{start}** to **{end}** calculated!")
            st.info(f"Distance: **{distance_km:.2f} km**")
            st.info(f"Estimated duration: **{route_data['duration_min']:.1f} minutes**")
            st.info(f"Vehicle: **{selected_vehicle}**")
            st.success(f"🌱 Total CO₂ emissions: **{co2_total_kg:.2f} kg**")

            # Optional: Display route on map (add this block if you want it too)
            import pydeck as pdk
            route_coords = [[lat, lon] for lon, lat in route_data["geometry"]]
            df_route = pd.DataFrame(route_coords, columns=["lat", "lon"])
            midpoint = df_route.iloc[len(df_route) // 2]
            layer = pdk.Layer(
                "LineLayer",
                data=df_route,
                get_source_position="[lon, lat]",
                get_target_position="[lon, lat]",
                get_color=[255, 0, 0],
                get_width=5
            )
            view_state = pdk.ViewState(
                latitude=midpoint["lat"],
                longitude=midpoint["lon"],
                zoom=10
            )
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Please fill out all fields.")

# ---- FOOTER ----
st.markdown("---")
st.caption("Data sources: OpenRouteService, Euro 6 Vehicle Database")
