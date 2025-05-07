import streamlit as st
import pandas as pd
import pydeck as pdk
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import LabelEncoder
import numpy as np

# Custom API functions
from Map_API import autocomplete_address, get_coordinates, get_route_info

###### PAGE SETUP ######
st.set_page_config(page_title="CO₂ Emission Calculator", page_icon="🚗", layout="centered")


##### HEADER #####
st.title("Car Journey CO₂ Emission Calculator")
st.write("Welcome! This app will help you calculate and compare the carbon emissions of your trips.")

##### SIDEBAR #####
st.sidebar.header("Enter your trip information")

# --- Start/End addresses ---
start_input = st.sidebar.text_input("From:")
start_suggestions, selected_start = [], None
if start_input:
    try:
        start_suggestions = autocomplete_address(start_input)
        selected_start = st.sidebar.selectbox("Select starting location:", start_suggestions)
    except Exception as e:
        st.sidebar.error(f"Could not get start location suggestions: {e}")

end_input = st.sidebar.text_input("To:")
end_suggestions, selected_end = [], None
if end_input:
    try:
        end_suggestions = autocomplete_address(end_input)
        selected_end = st.sidebar.selectbox("Select destination:", end_suggestions)
    except Exception as e:
        st.sidebar.error(f"Could not get destination suggestions: {e}")

st.sidebar.header("Select Your Vehicle")

# --- Load car data ---
try:
    vehicle_df = pd.read_csv("all-vehicles-model@public.csv", sep=";", encoding="utf-8-sig", engine="python")
    vehicle_df.columns = vehicle_df.columns.str.strip().str.replace(" ", "_")
    vehicle_df = vehicle_df.dropna(subset=["Make", "Fuel_Type1", "Model", "Year", "Co2__Tailpipe_For_Fuel_Type1"])
except Exception as e:
    st.error(f"Failed to load vehicle data: {e}")
    st.stop()

car_not_listed = st.sidebar.checkbox("My car is not listed")

if car_not_listed:
    st.sidebar.markdown("### Enter your car details")
    fuel_type = st.sidebar.selectbox("Fuel Type", vehicle_df["Fuel_Type1"].dropna().unique())
    cylinders = st.sidebar.number_input("Number of Cylinders", min_value=3, max_value=16, step=1)
    year = st.sidebar.number_input("Year", min_value=1980, max_value=2025, step=1)

    # Train a decision tree model to predict CO2
    model_data = vehicle_df.dropna(subset=["Fuel_Type1", "Cylinders", "Year", "Co2__Tailpipe_For_Fuel_Type1"]).copy()
    le = LabelEncoder()
    model_data["Fuel_Type1_Encoded"] = le.fit_transform(model_data["Fuel_Type1"])
    X = model_data[["Fuel_Type1_Encoded", "Cylinders", "Year"]]
    y = model_data["Co2__Tailpipe_For_Fuel_Type1"]

    dt_model = DecisionTreeRegressor(random_state=42)
    dt_model.fit(X, y)

    user_input = pd.DataFrame([[fuel_type, cylinders, year]], columns=["Fuel_Type1", "Cylinders", "Year"])
    user_input["Fuel_Type1_Encoded"] = le.transform(user_input["Fuel_Type1"])
    predicted_co2 = dt_model.predict(user_input[["Fuel_Type1_Encoded", "Cylinders", "Year"]])[0]

    st.sidebar.success(f"Predicted CO₂ Emission: {(predicted_co2/1.60934):.2f} g/km")

    selected_make = "Custom"
    selected_model = "Custom Entry"
    selected_year = year
    selected_fuel = fuel_type
    co2_g_per_mile = predicted_co2
    final_row = pd.Series({"Co2__Tailpipe_For_Fuel_Type1": predicted_co2})
else:
    # --- Car selection ---
    makes = sorted(vehicle_df['Make'].dropna().unique())
    selected_make = st.sidebar.selectbox("Make", makes)

    filtered_df = vehicle_df[vehicle_df['Make'] == selected_make]
    fuel_types = sorted(filtered_df['Fuel_Type1'].dropna().unique())
    selected_fuel = st.sidebar.selectbox("Fuel Type", fuel_types)

    filtered_df = filtered_df[filtered_df['Fuel_Type1'] == selected_fuel]
    models = sorted(filtered_df['Model'].dropna().unique())
    selected_model = st.sidebar.selectbox("Model", models)

    filtered_df = filtered_df[filtered_df['Model'] == selected_model]
    years = sorted(filtered_df['Year'].dropna().unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Year", years)

    final_row = vehicle_df[
        (vehicle_df['Make'] == selected_make) &
        (vehicle_df['Fuel_Type1'] == selected_fuel) &
        (vehicle_df['Model'] == selected_model) &
        (vehicle_df['Year'] == selected_year)
    ]

compare_public_transport = st.sidebar.checkbox("Compare with public transport")

########## MAIN LOGIC ##########
if selected_start and selected_end and st.sidebar.button("Calculate Route"):
    try:
        start_coords = get_coordinates(selected_start)
        end_coords = get_coordinates(selected_end)

        route = get_route_info(start_coords, end_coords)
        distance_km = route['distance_km']

        st.header("Estimated Impact")

        if not final_row.empty:
            row = final_row.iloc[0] if not car_not_listed else final_row

            co2_g_per_mile = row['Co2__Tailpipe_For_Fuel_Type1']
            mpg = row.get('Combined_Mpg_For_Fuel_Type1', np.nan)
            ghg_score = row.get('GHG_Score', np.nan)

            st.success(f"{selected_make} {selected_model} ({selected_year}) - {selected_fuel}")
            st.info(f"📏 Distance: **{distance_km:.2f} km**")

            travel_time_min = route['duration_min']
            if travel_time_min >= 60:
                h, m = int(travel_time_min // 60), int(travel_time_min % 60)
                st.info(f"🕒 Travel time: **{h}h {m} min**")
            else:
                st.info(f"🕒 Travel time: **{travel_time_min:.1f} minutes**")

            if pd.notna(co2_g_per_mile) and co2_g_per_mile > 0:
                co2_g_per_km = co2_g_per_mile / 1.60934
                total_emissions_grams = co2_g_per_km * distance_km
                st.metric("💨 CO₂ Emissions", f"{total_emissions_grams / 1000:.2f} kg")
                ###### PUBLIC TRANSPORT COMPARISON (BUS VS TRAIN) ######
                if compare_public_transport:
                    st.subheader("🚆 Public Transport CO₂ Comparison")

                    # Average emissions (European data)
                    train_co2_g_per_km = 41     # g/km
                    bus_co2_g_per_km = 105      # g/km

                    train_emission_kg = (train_co2_g_per_km * distance_km) / 1000
                    bus_emission_kg = (bus_co2_g_per_km * distance_km) / 1000

                    st.metric("🚄 Train Emissions", f"{train_emission_kg:.2f} kg")
                    st.metric("🚌 Bus Emissions", f"{bus_emission_kg:.2f} kg")

                    if total_emissions_grams > 0:
                        car_emission_kg = total_emissions_grams / 1000

                        train_savings = car_emission_kg - train_emission_kg
                        bus_savings = car_emission_kg - bus_emission_kg

                        if train_savings > 0:
                            st.success(f"🌿 By taking the **train**, you could save ~{train_savings:.2f} kg CO₂ (-{(train_savings/car_emission_kg * 100):.2f}%).")
                        else:
                            st.info("🚗 Your car is more efficient than the average train on this route.")

                        if bus_savings > 0:
                            st.success(f"🌿 By taking the **bus**, you could save ~{bus_savings:.2f} kg CO₂.")
                        else:
                            st.info("🚗 Your car is more efficient than the average bus on this route.")

            else:
                st.warning("💨 CO₂ emissions could not be calculated.")

            if pd.notna(mpg) and mpg > 0:
                l_per_100km = 235.21 / mpg
                fuel_for_trip = (l_per_100km * distance_km) / 100
                st.metric("⛽ Fuel Consumption", f"{fuel_for_trip:.2f} liters")
            else:
                st.warning("⛽ Fuel consumption could not be calculated.")

            if pd.notna(ghg_score) and ghg_score > 0:
                color = "#2ECC71" if ghg_score >= 8 else "#F39C12" if ghg_score >= 5 else "#E74C3C"
                st.markdown(
                    f"<div style='padding: 10px; background-color: {color}; border-radius: 8px; color: white; font-size: 18px;'>"
                    f"🌿 GHG Score: <strong>{int(ghg_score)}</strong> (out of 10)</div>",
                    unsafe_allow_html=True
                )
            else:
                st.warning("🌿 GHG score not available.")
        else:
            st.info("No matching vehicle found. Please adjust your selection.")

        ########## MAP DISPLAY ##########
        st.header("Route Map")

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
            get_color=[0, 0, 255], # = blue color for route line 
            get_width=4
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style='mapbox://styles/mapbox/satellite-streets-v11' #link from ChatGPT to get sat view + cities & routes 
        ))

    except Exception as e:
        st.error("❌ An error occurred during route calculation.")
        st.exception(e)

########## FOOTER ##########
st.markdown("""---""")
st.caption("CS Project. Designed by Aymeric, Kaïs, Emmanuel and Yannick. Group 2.06. "
           "Data sources: OpenRouteService, European Environment Agency, " \
           "Environmental Protection Agency's National Vehicle and Fuel Emissions Laboratory.")