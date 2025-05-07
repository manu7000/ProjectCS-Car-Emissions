import streamlit as st
import pandas as pd
import pydeck as pdk

# Import custom map API functions
from Map_API import autocomplete_address, get_coordinates, get_route_info

###### PAGE SETUP ######
st.set_page_config(page_title="CO₂ Emission Calculator", page_icon="🚗", layout="centered")

##### HEADER #####
st.title("Car Journey CO₂ Emission Calculator")
st.write("Welcome! This app will help you calculate and compare the carbon emissions of your trips.")

##### SIDEBAR ####
st.sidebar.header("Select Your Vehicle")

# Load car data
try:
    vehicle_df = pd.read_csv("all-vehicles-model@public.csv", sep=";", encoding="utf-8-sig", engine="python")
    vehicle_df.columns = vehicle_df.columns.str.strip().str.replace(" ", "_")
    vehicle_df = vehicle_df.dropna(subset=["Make", "Fuel_Type1", "Model", "Year", "Co2__Tailpipe_For_Fuel_Type1"])
except Exception as e:
    st.error(f"Failed to load vehicle data: {e}")
    st.stop()

# Step-by-step sidebar filters
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

compare_public_transport = st.sidebar.checkbox("Compare with public transport")
show_alternatives = st.sidebar.checkbox("Show alternative vehicles")

########## USER INPUT ##########
start_input = st.text_input("From:")
start_suggestions = []
selected_start = None
if start_input:
    try:
        start_suggestions = autocomplete_address(start_input)
        selected_start = st.selectbox("Select starting location:", start_suggestions)
    except Exception as e:
        st.error(f"Could not get start location suggestions: {e}")

end_input = st.text_input("To:")
end_suggestions = []
selected_end = None
if end_input:
    try:
        end_suggestions = autocomplete_address(end_input)
        selected_end = st.selectbox("Select destination:", end_suggestions)
    except Exception as e:
        st.error(f"Could not get destination suggestions: {e}")

########## CALCULATE ROUTE ##########
if selected_start and selected_end and st.button("Calculate Route"):
    try:
        st.write("✅ Le calcul de la route commence")
        start_coords = get_coordinates(selected_start)
        end_coords = get_coordinates(selected_end)

        route = get_route_info(start_coords, end_coords)
        distance_km = route['distance_km']

        st.info(f"*Distance:* **{route['distance_km']:.2f} km**")

        travel_time_min = route['duration_min']
        if travel_time_min >= 60:
            hours = int(travel_time_min // 60)
            minutes = int(travel_time_min % 60)
            st.info(f"*Travel time:* **{hours}h {minutes} min**")
        else:
            st.info(f"*Travel time:* **{travel_time_min:.1f} minutes**")

        # Map
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
            get_width=5
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style='mapbox://styles/mapbox/satellite-streets-v11'
        ))

        ##### MAIN DISPLAY AFTER ROUTE #####
        st.header("Estimated Impact")

        final_row = vehicle_df[
            (vehicle_df['Make'] == selected_make) &
            (vehicle_df['Fuel_Type1'] == selected_fuel) &
            (vehicle_df['Model'] == selected_model) &
            (vehicle_df['Year'] == selected_year)
        ]

        if not final_row.empty:
            row = final_row.iloc[0]
            co2_g_per_mile = row['Co2__Tailpipe_For_Fuel_Type1']
            mpg = row.get('Combined_Mpg_For_Fuel_Type1')
            ghg_score = row.get('GHG_Score')

            st.success(f"{selected_make} {selected_model} ({selected_year}) - {selected_fuel}")

            if pd.notna(co2_g_per_mile) and co2_g_per_mile > 0:
                co2_g_per_km = co2_g_per_mile / 1.60934
                total_emissions_grams = co2_g_per_km * distance_km
                st.metric("💨 CO₂ Emissions", f"{total_emissions_grams / 1000:.2f} kg")
            else:
                st.warning("💨 CO₂ emissions could not be calculated for the selected vehicle.")

            if pd.notna(mpg) and mpg > 0:
                l_per_100km = 235.21 / mpg
                fuel_for_trip = (l_per_100km * distance_km) / 100
                st.metric("⛽ Fuel Consumption", f"{fuel_for_trip:.2f} liters")
            else:
                st.warning("⛽ Fuel consumption could not be calculated.")

            if pd.notna(ghg_score) and ghg_score > 0:
                if ghg_score >= 8:
                    color = "#2ECC71"
                elif ghg_score >= 5:
                    color = "#F39C12"
                else:
                    color = "#E74C3C"

                st.markdown(
                    f"<div style='padding: 10px; background-color: {color}; border-radius: 8px; color: white; font-size: 18px;'>"
                    f"🌿 GHG Score: <strong>{int(ghg_score)}</strong> (out of 10)</div>",
                    unsafe_allow_html=True
                )
            else:
                st.warning("🌿 GHG score not available.")
        else:
            st.info("No matching vehicle found. Please adjust your selection.")

    except Exception as e:
        st.error("❌ Une erreur s'est produite lors du calcul de la route.")
        st.exception(e)  # 👉 Montre l'erreur complète dans Streamlit

########## FOOTER ##########
st.markdown("""---""")
st.caption("CS Project. Designed by Aymeric, Kaïs, Manu and Yannick. Group 2.06. "
           "Data sources: OpenRouteService, Environmental Protection Agency's National Vehicle and Fuel Emissions Laboratory.")
