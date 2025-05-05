import streamlit as st
import pandas as pd

###### PAGE SETUP ######
st.set_page_config(page_title="CO₂ Emission Calculator", page_icon="🚗", layout="centered")

##### HEADER #####
st.title("Car Journey CO₂ Emission Calculator")
st.write("Welcome! This app will help you calculate and compare the carbon emissions of your trips.")

##### SIDEBAR ####
#Loading data from the CSV file for sidebar
df = pd.read_csv("all-vehicles-model@public.csv", sep=";", encoding="ISO-8859-1", engine="python")
df.columns = df.columns.str.strip().str.replace(" ", "_")

# Drop rows with missing critical fields
df = df.dropna(subset=["Make", "Fuel_Type1", "Model", "Year", "Co2__Tailpipe_For_Fuel_Type1"])

# ---- SIDEBAR: FULL CAR SELECTION ----
st.sidebar.header("Select Your Vehicle")

# Step 1: Make
makes = sorted(df['Make'].dropna().unique())
selected_make = st.sidebar.selectbox("Make", makes)

# Step 2: Fuel Type
filtered_df = df[df['Make'] == selected_make]
fuel_types = sorted(filtered_df['Fuel_Type1'].dropna().unique())
selected_fuel = st.sidebar.selectbox("Fuel Type", fuel_types)

# Step 3: Model
filtered_df = filtered_df[filtered_df['Fuel_Type1'] == selected_fuel]
models = sorted(filtered_df['Model'].dropna().unique())
selected_model = st.sidebar.selectbox("Model", models)

# Step 4: Year
filtered_df = filtered_df[filtered_df['Model'] == selected_model]
years = sorted(filtered_df['Year'].dropna().unique(), reverse=True)
selected_year = st.sidebar.selectbox("Year", years)

# Step 5: Trip Distance
distance_km = st.sidebar.number_input("Trip Distance (km)", min_value=1)

# ---- MAIN DISPLAY ----
st.header("Estimated Impact")

# Final filter based on all four selections
final_row = df[
    (df['Make'] == selected_make) &
    (df['Fuel_Type1'] == selected_fuel) &
    (df['Model'] == selected_model) &
    (df['Year'] == selected_year)
]

if not final_row.empty:
    row = final_row.iloc[0]

    co2_g_per_mile = row['Co2__Tailpipe_For_Fuel_Type1']
    mpg = row.get('Combined_Mpg_For_Fuel_Type1')
    ghg_score = row.get('GHG_Score')

    st.success(f"{selected_make} {selected_model} ({selected_year}) - {selected_fuel}")

    # --- CO₂ Emissions Calculation ---
    if pd.notna(co2_g_per_mile) and co2_g_per_mile > 0:
        co2_g_per_km = co2_g_per_mile / 1.60934
        total_emissions_grams = co2_g_per_km * distance_km
        total_emissions_kg = total_emissions_grams / 1000
        st.metric("💨 CO₂ Emissions", f"{total_emissions_kg:.2f} kg")
    else:
        st.warning("💨 CO₂ emissions could not be calculated for the selected vehicle.")

    # --- Fuel Consumption Calculation ---
    if pd.notna(mpg) and mpg > 0:
        l_per_100km = 235.21 / mpg
        fuel_for_trip = (l_per_100km * distance_km) / 100
        st.metric("⛽ Fuel Consumption", f"{fuel_for_trip:.2f} liters")
    else:
        st.warning("⛽ Fuel consumption could not be calculated for the selected vehicle.")

    # --- GHG Score Display ---
    if pd.notna(ghg_score) and ghg_score > 0:
        if ghg_score >= 8:
            color = "#2ECC71"  # green
        elif ghg_score >= 5:
            color = "#F39C12"  # orange
        else:
            color = "#E74C3C"  # red

        st.markdown(
            f"<div style='padding: 10px; background-color: {color}; border-radius: 8px; color: white; font-size: 18px;'>"
            f"🌿 GHG Score: <strong>{int(ghg_score)}</strong> (out of 10)"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.warning("🌿 GHG score could not be calculated for the selected vehicle.")
else:
    st.info("No matching vehicle found. Please adjust your selection.")


compare_public_transport = st.sidebar.checkbox("Compare with public transport")
show_alternatives = st.sidebar.checkbox("Show alternative vehicles")

########### MAIN SECTION ##############

import pydeck as pdk

# Import your functions
from Map_API import autocomplete_address, get_coordinates, get_route_info

########## USER INPUT ##########
# START LOCATION 
#enter a starting address
start_input = st.text_input("From:")

# Create an empty list to hold suggestions
start_suggestions = []

# Create a variable for the selected starting address
selected_start = None

# If the user types something and presses Enter
if start_input:
    try:
        # Call the autocomplete_address function to get suggestions
        start_suggestions = autocomplete_address(start_input)
        # Show the suggestions in a dropdown
        selected_start = st.selectbox("Select starting location:", start_suggestions)

    except Exception as e:
        st.error(f"Could not get start location suggestions: {e}")

# END LOCATION 
# Same coding logic as for the start location 
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

#User must have selected both start and end destinations in order to calculate route 
if selected_start and selected_end and st.button("Calculate Route"):
    try:
        ########## GET COORDINATES ##########

        # Get the coordinates (latitude and longitude) of the selected start location
        start_coords = get_coordinates(selected_start)

        # Get the coordinates of the selected destination
        end_coords = get_coordinates(selected_end)

        ########## GET ROUTE DATA ##########

        # Call the get_route_info function to get route distance, duration, and geometry
        route = get_route_info(start_coords, end_coords)

        ########## SHOW ROUTE INFO ##########

        # Show a success message
        st.success("Your route has been calculated successfully.")

        # Show the distance in kilometers
        st.info(f"*Distance:* **{route['distance_km']:.2f} km**") # * for itallic and ** for bold text 

        ########## FORMAT TRAVEL TIME ##########

        travel_time_min = route['travel_time_min']

        # If the trip is longer than 60 minutes, show hours and minutes
        if travel_time_min >= 60:
            hours = int(travel_time_min // 60)
            minutes = int(travel_time_min % 60)
            st.info(f"*Travel time:* **{hours}h {minutes} min**")
        else:
            # Otherwise, just show minutes
            st.info(f"*Travel time:* **{travel_time_min:.1f} minutes**")


        ######### MAP DATA ########## ----> I don't understand shit, GPT made it 

        # The API gives coordinates as [longitude, latitude].
        # For mapping, must reverse them to [latitude, longitude].

        route_coords = [[lat, lon] for lon, lat in route['geometry']]

        # Create a DataFrame with latitude and longitude columns
        df = pd.DataFrame(route_coords, columns=["lat", "lon"])

        # Create two new columns for the next point in the line (to draw segments)
        df["lon_next"] = df["lon"].shift(-1)
        df["lat_next"] = df["lat"].shift(-1)

        # Remove any rows where the next point is missing (last row)
        df = df.dropna()

        ##### MAP VIEW #####

        # Find the smallest and largest latitude and longitude values
        min_lat = df["lat"].min()
        max_lat = df["lat"].max()
        min_lon = df["lon"].min()
        max_lon = df["lon"].max()

        # Calculate the center point between the minimum and maximum values
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2

        # Set the initial view of the map
        # Zoom level 7 means fairly zoomed out — adjust if needed
        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=7
        )

        #### MAP LAYER #### ---> Also don't understand shit, GPT did 

        # Create a line layer to draw the route
        layer = pdk.Layer(
            "LineLayer",
            data=df,
            get_source_position=["lon", "lat"],  # Starting points
            get_target_position=["lon_next", "lat_next"],  # Ending points
            get_color=[0, 0, 255],  # Orange line
            get_width=5
        )

        ###### DISPLAY MAP ####### ----> Made by GPT 

        # Show the map with the route
        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style= 'mapbox://styles/mapbox/satellite-streets-v11' # Adding satellite view because looks really cool 
        ))

    except Exception as e:
        st.error(f"Error computing route: {e}")

########## FOOTER #########
st.markdown("""---""")
st.caption("CS Project. Designed by Aymeric, Kaïs, Manu adn Yannick. Group 2.06" \
           "Data sources: OpenRouteService, Carbon Interface API,.")
