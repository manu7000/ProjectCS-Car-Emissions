import streamlit as st
import openrouteservice
from openrouteservice import convert
import os

# ---- PAGE SETUP ----
st.set_page_config(page_title="🖕🏾Car Journey CO₂ Emission Calculator", page_icon="🚗", layout="centered")

# ---- HEADER ----
st.title("🥸Car Journey CO₂ Emission Calculator")
st.write("Welcome! This app will help you calculate and compare the carbon emissions of your trips.")

# ---- SIDEBAR ----
st.sidebar.header("Journey Details")

start = st.sidebar.text_input("Enter start address")
end = st.sidebar.text_input("Enter destination address")

vehicle_type = st.sidebar.selectbox(
    "Select vehicle type", 
    ["Petrol", "Diesel", "Electric", "Hybrid"]
)

compare_public_transport = st.sidebar.checkbox("Compare with public transport")
show_alternatives = st.sidebar.checkbox("Show alternative vehicles")

# ---- OPENROUTESERVICE SETUP ----
API_KEY = "YOUR_OPENROUTESERVICE_API_KEY"  # Replace with your actual API key
client = openrouteservice.Client(key=API_KEY)

# ---- MAIN SECTION ----
st.header("Your Journey Summary")

if st.button("Calculate Emissions"):
    if start and end:
        try:
            # Geocode the addresses
            geocode_start = client.pelias_search(text=start)["features"][0]["geometry"]["coordinates"]
            geocode_end = client.pelias_search(text=end)["features"][0]["geometry"]["coordinates"]

            # Get route
            route = client.directions(
                coordinates=[geocode_start, geocode_end],
                profile='driving-car',
                format='geojson'
            )

            distance_meters = route['features'][0]['properties']['segments'][0]['distance']
            duration_seconds = route['features'][0]['properties']['segments'][0]['duration']

            distance_km = distance_meters / 1000
            duration_minutes = duration_seconds / 60

            st.success(f"Route from **{start}** to **{end}** calculated successfully!")
            st.info(f"Distance: **{distance_km:.2f} km**")
            st.info(f"Estimated duration: **{duration_minutes:.1f} minutes**")

            # Emissions calculation placeholder
            st.info("CO₂ Emissions: _to be calculated based on vehicle type and distance_")

            # Placeholder for chart
            st.subheader("Comparison Chart")
            st.write("_Chart will appear here after calculation_")

        except Exception as e:
            st.error(f"An error occurred while calculating the route: {e}")

    else:
        st.error("Please enter both a start and destination address.")

# ---- FOOTER ----
st.markdown("""---""")
st.caption("Data sources: OpenRouteService, Carbon Interface API, Kaggle CO₂ dataset.")
