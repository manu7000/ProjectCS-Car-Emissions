import streamlit as st
from Feature_API import get_coordinates, get_route_info

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

# ---- MAIN SECTION ----
st.header("Your Journey Summary")

if st.button("Calculate Emissions"):
    if start and end:
        try:
            start_coords = get_coordinates(start)
            end_coords = get_coordinates(end)
            route_data = get_route_info(start_coords, end_coords)

            st.success(f"Route from **{start}** to **{end}** calculated successfully!")
            st.info(f"Distance: **{route_data['distance_km']:.2f} km**")
            st.info(f"Estimated duration: **{route_data['duration_min']:.1f} minutes**")

            st.info("CO₂ Emissions: _to be calculated based on vehicle type and distance_")

            st.subheader("Comparison Chart")
            st.write("_Chart will appear here after calculation_")

        except Exception as e:
            st.error(str(e))
    else:
        st.error("Please enter both a start and destination address.")

# ---- FOOTER ----
st.markdown("""---""")
st.caption("Data sources: OpenRouteService, Carbon Interface API, Kaggle CO₂ dataset.")
