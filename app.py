import streamlit as st
import pandas as pd
import pydeck as pdk
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import LabelEncoder
import numpy as np
from Map_API import autocomplete_address, get_coordinates, get_route_info

# -----------------------------------
# PAGE CONFIGURATION 
# -----------------------------------
st.set_page_config(
    page_title="CO₂ Emission Calculator",
    page_icon="🚗",
    layout="centered"
)

# -----------------------------------
# UTILITY FUNCTIONS ---- YANNICK -----
# -----------------------------------

@st.cache_data
def load_vehicle_data(path: str) -> pd.DataFrame:
    """
    Load and clean vehicle dataset from a CSV file.
    Drops rows missing critical fields.
    """
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", engine="python")
    df.columns = df.columns.str.strip().str.replace(" ", "_")
    return df.dropna(
        subset=[
            "Make",
            "Fuel_Type1",
            "Model",
            "Year",
            "Co2__Tailpipe_For_Fuel_Type1"
        ]
    )

@st.cache_resource
def train_model(df: pd.DataFrame):
    """
    Train a Decision Tree on known vehicles to predict CO2 for custom entries.
    Returns the trained model and the label encoder.
    """
    data = df.dropna(
        subset=["Fuel_Type1", "Cylinders", "Year", "Co2__Tailpipe_For_Fuel_Type1"]
    ).copy()
    le = LabelEncoder()
    data["Fuel_Type1_Encoded"] = le.fit_transform(data["Fuel_Type1"])
    X = data[["Fuel_Type1_Encoded", "Cylinders", "Year"]]
    y = data["Co2__Tailpipe_For_Fuel_Type1"]
    model = DecisionTreeRegressor(random_state=42)
    model.fit(X, y)
    return model, le

def predict_co2_emission(model, le, fuel_type, cylinders, year) -> float:
    """
    Given user-specified fuel type, cylinder count, and year,
    predict CO2 tailpipe emissions using the trained model.
    """
    inp = pd.DataFrame(
        [[fuel_type, cylinders, year]],
        columns=["Fuel_Type1", "Cylinders", "Year"]
    )
    inp["Fuel_Type1_Encoded"] = le.transform(inp["Fuel_Type1"])
    return model.predict(inp[["Fuel_Type1_Encoded", "Cylinders", "Year"]])[0]

def display_route_map(route: dict):
    """
    Render the route geometry on a PyDeck map.
    Expects 'geometry' key: list of [lon, lat] points.
    """
    # Prepare coordinate DataFrame
    coords = [[lat, lon] for lon, lat in route["geometry"]]
    df = pd.DataFrame(coords, columns=["lat", "lon"])
    df["lon_next"] = df["lon"].shift(-1)
    df["lat_next"] = df["lat"].shift(-1)
    df = df.dropna()

    # Center map
    center_lat = (df["lat"].min() + df["lat"].max()) / 2
    center_lon = (df["lon"].min() + df["lon"].max()) / 2
    view = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7)

    # Line layer for route
    layer = pdk.Layer(
        "LineLayer",
        data=df,
        get_source_position=["lon", "lat"],
        get_target_position=["lon_next", "lat_next"],
        get_color=[0, 0, 255],
        get_width=4
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            map_style="mapbox://styles/mapbox/satellite-streets-v11"
        )
    )

# -----------------------------------
# UI LAYOUT: HEADER + SIDEBAR ----- KAIS-------
# -----------------------------------

st.title("Car Journey CO₂ Emission Calculator")  #display main app title
st.write("Welcome! This app will help you calculate and compare the carbon emissions of your trips.")  #subtitle

# Sidebar: Trip address inputs
st.sidebar.header("Enter your trip information")  #sidebar section header text
start_input = st.sidebar.text_input("From:")  #text box for departure address
selected_start = st.sidebar.selectbox(  
    "Select starting location:",  
    autocomplete_address(start_input)  
) if start_input else None  #show autocomplete dropdown only after typing. Only show the sropdown if there is an input

end_input = st.sidebar.text_input("To:")  #text box for destination address
selected_end = st.sidebar.selectbox(  
    "Select destination:",  
    autocomplete_address(end_input)  
) if end_input else None  # show autocomplete dropdown only after typing. Only show the sropdown if there is an input

# Load and train vehicle data
try:  
    vehicle_df = load_vehicle_data("all-vehicles-model@public.csv")  # read & clean CSV
except Exception:  
    st.error("Could not load vehicle database.")  # show error if load fails
    st.stop()  # stop app execution on failure

model, le = train_model(vehicle_df)  # train ML model + encoder for custom CO₂ predictions

# Sidebar: Vehicle selection or custom entry
st.sidebar.header("Select Your Vehicle")  # sidebar section header
car_not_listed = st.sidebar.checkbox("My car is not listed")  # checkbox for car not listed

# What is showed on the interface depending on if the car is listed or not
# If car is not listed checkbox is selected a different dropdown menu appears
if car_not_listed:
    fuel_type = st.sidebar.selectbox("Fuel Type", vehicle_df["Fuel_Type1"].unique())  # fuel dropdown
    cylinders = st.sidebar.number_input("Number of Cylinders", min_value=3, max_value=16, step=1)  # cylinders input
    year = st.sidebar.number_input("Year", min_value=1980, max_value=2025, step=1)  # year input
    predicted_co2 = predict_co2_emission(model, le, fuel_type, cylinders, year)  # predict CO2 via ML
    st.sidebar.success(f"Predicted CO₂ Emission: {(predicted_co2/1.60934):.2f} g/km")  # show CO2 prediction on the screen (divided by 1.6 because it's in mile in the csv file)
    final_row = pd.Series({"Co2__Tailpipe_For_Fuel_Type1": predicted_co2})  # single‐row fallback for the code to work with ML prediction otherwise it will go check for final row on line 159
    selected_make, selected_model, selected_year, selected_fuel = "Custom", "Custom Entry", year, fuel_type  # gives placeholder values for make and model so that the code can treat it as normal selection
else:
    selected_make = st.sidebar.selectbox("Brand", sorted(vehicle_df["Make"].unique()))  # choose brand text on the sidebar
    df_m = vehicle_df[vehicle_df["Make"] == selected_make]  # filter by brand
    selected_fuel = st.sidebar.selectbox("Fuel Type", sorted(df_m["Fuel_Type1"].unique()))  # choose fuel text on the sidebar
    df_f = df_m[df_m["Fuel_Type1"] == selected_fuel]  # filter by fuel
    selected_model = st.sidebar.selectbox("Model", sorted(df_f["Model"].unique()))  # choose model text on the sidebar
    df_mod = df_f[df_f["Model"] == selected_model]  # filter by model
    selected_year = st.sidebar.selectbox(  
        "Year",  
        sorted(df_mod["Year"].unique(), reverse=True)  
    )  # to choose year in the sidebar
    final_row = vehicle_df[  
        (vehicle_df["Make"] == selected_make) &  
        (vehicle_df["Fuel_Type1"] == selected_fuel) &  
        (vehicle_df["Model"] == selected_model) &  
        (vehicle_df["Year"] == selected_year)  
    ]  # lookup at the selected row

# Option to compare public transport
compare_public_transport = st.sidebar.checkbox("Compare with public transport")  # checkbox for bus/train comparison
# -----------------------------------
# MAIN LOGIC: CALCULATION + DISPLAY ----- AYMERIC -------
# -----------------------------------
if selected_start and selected_end and st.sidebar.button("Calculate Route"):
    try:
        # 1) Compute route info via OpenRouteService
        with st.spinner("Calculating route and emissions..."):
            sc = get_coordinates(selected_start)
            ec = get_coordinates(selected_end)
            route = get_route_info(sc, ec)
        distance_km = route["distance_km"]
        duration_min = route["duration_min"]

        # 2) Retrieve CO₂ and MPG data
        row = final_row.iloc[0] if not car_not_listed else final_row
        co2_g_mile = row["Co2__Tailpipe_For_Fuel_Type1"]
        mpg = row.get("Combined_Mpg_For_Fuel_Type1", np.nan)
        ghg_score = row.get("GHG_Score", np.nan)
        car_emission_kg = (co2_g_mile / 1.60934) * distance_km / 1000

        # -----------------------------------
        # 3) Estimated Impact Dashboard
        # -----------------------------------
        st.header("Estimated Impact")

        # Contextual info about per-person budget
        st.info(
            "💡 To halt climate change, max CO₂ per person per year ≈ **600 kg**."
        )

        # Format travel time string
        if duration_min >= 60:
            h, m = divmod(int(duration_min), 60)
            travel_str = f"{h}h {m}m"
        else:
            travel_str = f"{duration_min:.0f}m"

        # Compute liters of fuel for trip if MPG known
        trip_L = (
            (235.21 / mpg) * distance_km / 100
            if pd.notna(mpg) and mpg > 0 else np.nan
        )

        # Row of four cards: Distance, Time, Emissions, Fuel
        labels = ["Distance", "Travel Time", "CO₂ Emissions", "Fuel Consumption"]
        icons = ["📏", "🕒", "💨", "⛽"]
        vals = [
            f"{distance_km:.2f} km",
            travel_str,
            f"{car_emission_kg:.2f} kg",
            f"{trip_L:.2f} L"
        ]
        cards = st.columns(4, gap="small")
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
            """, unsafe_allow_html=True)
# ---------------- MANU -----------------------------------------------------------------------
        # Add vertical spacing before next cards row
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # Second row: GHG score & public transport comparison
        g1, g2 = st.columns(2, gap="small")

        # GHG score card (always shown)
        with g1:
            if pd.notna(ghg_score):
                col = "#2ECC71" if ghg_score >= 8 else "#F39C12" if ghg_score >= 5 else "#E74C3C"
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
                # Fallback when no score
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

        # Public transport card (only if checkbox)
        with g2:
            if compare_public_transport:
                train_kg = 41 * distance_km / 1000
                bus_kg = 105 * distance_km / 1000
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

        # Add extra space before the info box about percent changes
        if compare_public_transport:
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            # Calculate percentage savings
            percent_train = (
                (car_emission_kg - train_kg) / car_emission_kg * 100
                if car_emission_kg > train_kg else 0
            )
            percent_bus = (
                (car_emission_kg - bus_kg) / car_emission_kg * 100
                if car_emission_kg > bus_kg else 0
            )
            st.info(
                f"🚄 Taking the train would reduce emissions by {percent_train:.1f}%\n\n"
                f"🚌 Taking the bus would reduce emissions by {percent_bus:.1f}%"
            )

        # -----------------------------------
        # 4) Route Map
        # -----------------------------------
        st.header("Route Map")
        display_route_map(route)

    except Exception as e:
        st.error("❌ An error occurred during route calculation.")
        st.exception(e)

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("---")
st.caption(
    "CS Project by Aymeric, Kaïs, Emmanuel and Yannick. Group 2.06. "
    "Data sources: OpenRouteService, EEA, EPA."
)