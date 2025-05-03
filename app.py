import streamlit as st

###### PAGE SETUP ######
st.set_page_config(page_title="🖕🏾Car Journey CO₂ Emission Calculator", page_icon="🚗", layout="centered")

##### HEADER #####
st.title("Car Journey CO₂ Emission Calculator Updated by Rico")
st.write("Welcome! This app will help you calculate and compare the carbon emissions of your trips.")

##### SIDEBAR ####
#Loading data from the CSV file for sidebar
df = pd.read_csv("Euro_6_latest.csv", encoding="ISO-8859-1") #I had to encode it bc it didn't read well the file
df.columns = df.columns.str.strip().str.replace(" ", "_")

# Drop rows with missing key fields
df = df.dropna(subset=['Manufacturer', 'Fuel_Type', 'Model', 'Description'])

#Drop down menu
st.sidebar.header("Select Your Vehicle")

#Manufacturer
manufacturers = sorted(df['Manufacturer'].unique())
selected_manufacturer = st.sidebar.selectbox("Manufacturer", manufacturers)

#Fuel Type (filtered by brand)
filtered_df = df[df['Manufacturer'] == selected_manufacturer]
fuel_types = sorted(filtered_df['Fuel_Type'].unique())
selected_fuel = st.sidebar.selectbox("Fuel Type", fuel_types)

#Model (filtered by brand + fuel)
filtered_df = filtered_df[filtered_df['Fuel_Type'] == selected_fuel]
models = sorted(filtered_df['Model'].unique())
selected_model = st.sidebar.selectbox("Model", models)

#Description (filtered by brand + fuel + model)
filtered_df = filtered_df[filtered_df['Model'] == selected_model]
descriptions = sorted(filtered_df['Description'].unique())
selected_description = st.sidebar.selectbox("Description", descriptions)


compare_public_transport = st.sidebar.checkbox("Compare with public transport")
show_alternatives = st.sidebar.checkbox("Show alternative vehicles")






########### MAIN SECTION ##############
import streamlit as st
import pandas as pd
import pydeck as pdk

# Import your functions
from Map_API import autocomplete_address, get_coordinates, get_route_info

# ------------------ USER INPUT ------------------
# ---- START LOCATION ----
# Ask the user to type a starting address
start_query = st.text_input("From:")

# Create an empty list to hold suggestions
start_suggestions = []

# Create a variable for the selected starting address
selected_start = None

# If the user types something and presses Enter
if start_query:
    try:
        # Call the autocomplete_address function to get suggestions
        start_suggestions = autocomplete_address(start_query)

        # Show the suggestions in a dropdown
        selected_start = st.selectbox("Select starting location:", start_suggestions)

    except Exception as e:
        st.error(f"Could not get start location suggestions: {e}")

# ---- DESTINATION LOCATION ----

# Ask the user to type a destination address
end_query = st.text_input("To:")

# Create an empty list for destination suggestions
end_suggestions = []

# Create a variable for the selected destination address
selected_end = None

# If the user types something and presses Enter
if end_query:
    try:
        # Call the autocomplete_address function to get suggestions
        end_suggestions = autocomplete_address(end_query)

        # Show the suggestions in a dropdown
        selected_end = st.selectbox("Select destination:", end_suggestions)

    except Exception as e:
        st.error(f"Could not get destination suggestions: {e}")

# ------------------ CALCULATE ROUTE ------------------

# If both a start and end location have been selected and the user clicks the button
if selected_start and selected_end and st.button("Calculate Route"):
    try:
        # --- GET COORDINATES ---

        # Get the coordinates (latitude and longitude) of the selected start location
        start_coords = get_coordinates(selected_start)

        # Get the coordinates of the selected destination
        end_coords = get_coordinates(selected_end)

        # --- GET ROUTE DATA ---

        # Call the get_route_info function to get route distance, duration, and geometry
        route = get_route_info(start_coords, end_coords)

        # --- SHOW ROUTE INFO ---

        # Show a success message
        st.success("Your route has been calculated successfully.")

        # Show the distance in kilometers
        st.info(f"Distance: **{route['distance_km']:.2f} km**")

        # --- FORMAT TRAVEL TIME ---

        duration_min = route['duration_min']

        # If the trip is longer than 60 minutes, show hours and minutes
        if duration_min >= 60:
            hours = int(duration_min // 60)
            minutes = int(duration_min % 60)
            st.info(f"Travel time: **{hours}h {minutes} min**")
        else:
            # Otherwise, just show minutes
            st.info(f"Travel time: **{duration_min:.1f} minutes**")

        # ------------------ PREPARE MAP DATA ------------------

        # The API gives coordinates as [longitude, latitude].
        # For mapping, we reverse them to [latitude, longitude].

        route_coords = [[lat, lon] for lon, lat in route['geometry']]

        # Create a DataFrame with latitude and longitude columns
        df = pd.DataFrame(route_coords, columns=["lat", "lon"])

        # Create two new columns for the next point in the line (to draw segments)
        df["lon_next"] = df["lon"].shift(-1)
        df["lat_next"] = df["lat"].shift(-1)

        # Remove any rows where the next point is missing (last row)
        df = df.dropna()

        # ------------------ MAP VIEW ------------------

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

        # ------------------ MAP LAYER ------------------

        # Create a line layer to draw the route
        layer = pdk.Layer(
            "LineLayer",
            data=df,
            get_source_position=["lon", "lat"],  # Starting points
            get_target_position=["lon_next", "lat_next"],  # Ending points
            get_color=[0, 0, 255],  # Blue lines
            get_width=5
        )

        # ------------------ DISPLAY MAP ------------------

        # Show the map with the route
        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state
        ))

    except Exception as e:
        st.error(f"Error computing route: {e}")

########## FOOTER #########
st.markdown("""---""")
st.caption("Data sources: OpenRouteService, Carbon Interface API, Kaggle CO₂ dataset.")
