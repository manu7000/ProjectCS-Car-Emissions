import streamlit as st

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

# Example hardcoded models by vehicle type (we will later load this from CSV or API)
vehicle_models = {
    "Petrol": ["Toyota Corolla", "VW Golf", "Ford Fiesta"],
    "Diesel": ["BMW 320d", "Audi A4", "Renault Megane"],
    "Electric": ["Tesla Model 3", "Renault Zoe", "BMW i3"],
    "Hybrid": ["Toyota Prius", "Honda Insight", "Hyundai Ioniq"]
}

model_options = vehicle_models[vehicle_type]
selected_model = st.sidebar.selectbox("Choose car model", model_options)
compare_public_transport = st.sidebar.checkbox("Compare with public transport")
show_alternatives = st.sidebar.checkbox("Show alternative vehicles")

# ---- MAIN SECTION ----
st.header("Your Journey Summary")

if st.button("Calculate Emissions"):
    if start and end:
        st.success(f"Calculating emissions from **{start}** to **{end}** using a **{vehicle_type}** vehicle...")
        st.info("Distance: _to be calculated_")
        st.info("CO₂ Emissions: _to be calculated_")

        # Placeholders for future charts
        st.subheader("Comparison Chart")
        st.write("_Chart will appear here after calculation_")

    else:
        st.error("Please enter both a start and destination address.")

# ---- FOOTER ----
st.markdown("""---""")
st.caption("Data sources: OpenRouteService, Carbon Interface API, Kaggle CO₂ dataset.")
