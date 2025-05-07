# ──────── IMPORTS ───────────────────────────────────────────────

import streamlit as st  
# We bring in Streamlit (aliased as `st`) so we can build web app elements 
# like text, buttons, maps, and sidebars just by calling `st.*` functions.

import pandas as pd  
# Pandas (aliased as `pd`) lets us read CSV files and work with tables of data 
# as DataFrames, which are like Excel spreadsheets inside Python.

import pydeck as pdk  
# PyDeck (alias `pdk`) lets us draw interactive maps in Streamlit by describing 
# data layers (lines, points) and view settings (center, zoom).

from sklearn.tree import DecisionTreeRegressor  
# We import a DecisionTreeRegressor from scikit-learn to train a simple model 
# that predicts CO₂ emissions when the user’s car isn’t in our database.

from sklearn.preprocessing import LabelEncoder  
# LabelEncoder converts text labels (like “Gasoline”) into numbers (0, 1, 2) 
# so our machine-learning model can understand them.

import numpy as np  
# NumPy (alias `np`) gives us fast array and math functions, and handles 
# missing values (`np.nan`) conveniently.

from Map_API import autocomplete_address, get_coordinates, get_route_info  
# We bring in three helper functions you wrote in Map_API.py:
# 1) `autocomplete_address(text)` returns a list of address suggestions
# 2) `get_coordinates(address)` returns a [lon, lat] pair for a chosen address
# 3) `get_route_info(start, end)` returns distance, duration, and route shape

# ──────── PAGE SETUP ─────────────────────────────────────────────

st.set_page_config(
    page_title="CO₂ Emission Calculator",   # The title in your browser tab
    page_icon="🚗",                         # A little car emoji in the tab
    layout="centered"                       # Center the main content on the page
)
# We call this once at the top so Streamlit knows how to display our app.

st.title("Car Journey CO₂ Emission Calculator")  
# This big headline appears at the top of the page in large text.

st.write(
    "Welcome! This student-built app helps you calculate and compare "
    "the carbon emissions of your trips."
)
# A friendly introduction just below the title, explaining the app’s purpose.

# ──────── SIDEBAR: TRIP INPUTS ───────────────────────────────────

st.sidebar.header("Enter your trip information")  
# In the sidebar (left panel), show this header above our address fields.

start_input = st.sidebar.text_input("From:")  
# Create a text box labeled “From:” where the user types their starting address.
# The typed text is stored in the variable `start_input`.

start_suggestions = []  
# Before we call any autocomplete API, initialize an empty list to hold suggestions.

selected_start = None  
# Also initialize a placeholder for whichever suggestion the user picks.

if start_input:  
    # Only try to autocomplete if the user has typed something non-empty.
    try:
        start_suggestions = autocomplete_address(start_input)
        # Call the autocomplete function to get a list of address strings.

        selected_start = st.sidebar.selectbox(
            "Select starting location:", start_suggestions
        )
        # Show those suggestions in a dropdown; store the user’s choice.
    except Exception as e:
        st.sidebar.error(
            f"Could not get start location suggestions: {e}"
        )
        # If the API call fails, show an error message in the sidebar.

end_input = st.sidebar.text_input("To:")  
# Another text box labeled “To:” for the destination address.
# The user’s entry is stored in `end_input`.

end_suggestions = []  
# Initialize an empty list for destination autocomplete suggestions.

selected_end = None  
# Placeholder for whichever destination the user selects.

if end_input:
    # Only run if the user typed something for the “To:” field.
    try:
        end_suggestions = autocomplete_address(end_input)
        # Get suggestions just like we did above.

        selected_end = st.sidebar.selectbox(
            "Select destination:", end_suggestions
        )
        # Let the user pick one and store it.
    except Exception as e:
        st.sidebar.error(
            f"Could not get destination suggestions: {e}"
        )
        # Show error if that call fails.

st.sidebar.header("Select Your Vehicle")  
# Add another header in the sidebar for choosing the car info.

# ──────── LOAD VEHICLE DATA ──────────────────────────────────────

try:
    vehicle_df = pd.read_csv(
        "all-vehicles-model@public.csv",  # The CSV file name
        sep=";",                          # Semicolon used as the column separator
        encoding="utf-8-sig",             # Handles any extra BOM characters
        engine="python"                   # Use the Python CSV engine
    )
    # Load the CSV into a DataFrame called `vehicle_df`.

    vehicle_df.columns = (
        vehicle_df.columns
        .str.strip()                       # Remove extra spaces around column names
        .str.replace(" ", "_")            # Replace spaces with underscores
    )
    # We clean up the column names so we can refer to them easily.

    vehicle_df = vehicle_df.dropna(subset=[
        "Make", "Fuel_Type1", "Model", "Year",
        "Co2__Tailpipe_For_Fuel_Type1"
    ])
    # Remove any rows that are missing one of these key columns.
except Exception as e:
    st.error(f"Failed to load vehicle data: {e}")
    # If reading the CSV fails for any reason, show an error banner on the main page.

    st.stop()
    # Stop running the rest of the app since we can’t continue without vehicle data.

# ──────── CUSTOM CAR OPTION ──────────────────────────────────────

car_not_listed = st.sidebar.checkbox("My car is not listed")  
# Give the user a checkbox to say “I don’t see my car in your list.”

if car_not_listed:
    # If they check that box, we’ll let them enter custom details.
    st.sidebar.markdown("### Enter your car details")
    # A sub-header above the custom inputs.

    fuel_type = st.sidebar.selectbox(
        "Fuel Type",
        vehicle_df["Fuel_Type1"].dropna().unique()
    )
    # Dropdown of all fuel types we have in the DataFrame (e.g. Gasoline, Diesel).

    cylinders = st.sidebar.number_input(
        "Number of Cylinders", min_value=3, max_value=16, step=1
    )
    # A numeric input field for how many cylinders—only whole numbers between 3 and 16.

    year = st.sidebar.number_input(
        "Year", min_value=1980, max_value=2025, step=1
    )
    # Numeric input for the car’s model year—between 1980 and 2025.

    # ──────── TRAIN A SIMPLE MODEL ───────────────────────────────
    # Filter out any rows still missing data for those four columns:
    model_data = vehicle_df.dropna(subset=[
        "Fuel_Type1", "Cylinders", "Year", "Co2__Tailpipe_For_Fuel_Type1"
    ]).copy()

    le = LabelEncoder()
    # Create an encoder instance to turn text labels into numbers.

    model_data["Fuel_Type1_Encoded"] = le.fit_transform(
        model_data["Fuel_Type1"]
    )
    # Learn how to map each fuel type (Gasoline→0, Diesel→1, etc.) and transform.

    X = model_data[[
        "Fuel_Type1_Encoded", "Cylinders", "Year"
    ]]
    # Features we’ll use to predict CO₂: encoded fuel type, cylinder count, year.

    y = model_data["Co2__Tailpipe_For_Fuel_Type1"]
    # The target variable we want to predict (actual CO₂ from the data).

    dt_model = DecisionTreeRegressor(random_state=42)
    # Create the decision tree model; `random_state=42` makes results reproducible.

    dt_model.fit(X, y)
    # Train (fit) the model on all our historical vehicle data.

    # Build a one-row DataFrame from the user’s custom inputs:
    user_input = pd.DataFrame(
        [[fuel_type, cylinders, year]],
        columns=["Fuel_Type1", "Cylinders", "Year"]
    )

    user_input["Fuel_Type1_Encoded"] = le.transform(
        user_input["Fuel_Type1"]
    )
    # Encode the user’s chosen fuel type using the same mapping.

    predicted_co2 = dt_model.predict(
        user_input[["Fuel_Type1_Encoded", "Cylinders", "Year"]]
    )[0]
    # Predict the CO₂ emission (in grams per mile) for these custom inputs.

    st.sidebar.success(
        f"Predicted CO₂ Emission: {(predicted_co2/1.60934):.2f} g/km"
    )
    # Show the prediction in the sidebar, converting from g/mile to g/km.

    # Save these custom selections so we can use them later:
    selected_make = "Custom"
    selected_model = "Custom Entry"
    selected_year = year
    selected_fuel = fuel_type
    co2_g_per_mile = predicted_co2
    final_row = pd.Series({"Co2__Tailpipe_For_Fuel_Type1": predicted_co2})
else:
    # ──────── STANDARD VEHICLE SELECTION ────────────────────────

    makes = sorted(vehicle_df["Make"].dropna().unique())
    # Get an alphabetical list of all makes (brands) in our data.

    selected_make = st.sidebar.selectbox("Make", makes)
    # Let the user choose a make from that list.

    filtered_df = vehicle_df[vehicle_df["Make"] == selected_make]
    # Filter our DataFrame down to only rows of that make.

    fuel_types = sorted(filtered_df["Fuel_Type1"].dropna().unique())
    selected_fuel = st.sidebar.selectbox("Fuel Type", fuel_types)
    # Let the user choose which fuel type their car uses.

    filtered_df = filtered_df[
        filtered_df["Fuel_Type1"] == selected_fuel
    ]
    # Further filter to only the chosen fuel type.

    models = sorted(filtered_df["Model"].dropna().unique())
    selected_model = st.sidebar.selectbox("Model", models)
    # Let the user pick the specific model name.

    filtered_df = filtered_df[
        filtered_df["Model"] == selected_model
    ]
    # Narrow down to that model.

    years = sorted(filtered_df["Year"].dropna().unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Year", years)
    # List available years (newest first) and let the user pick.

    # Finally grab the single row matching all four selections:
    final_row = vehicle_df[
        (vehicle_df["Make"] == selected_make) &
        (vehicle_df["Fuel_Type1"] == selected_fuel) &
        (vehicle_df["Model"] == selected_model) &
        (vehicle_df["Year"] == selected_year)
    ]

# Optional checkboxes for extras:
compare_public_transport = st.sidebar.checkbox(
    "Compare with public transport"
)
show_alternatives = st.sidebar.checkbox("Show alternative vehicles")

# ──────── ROUTE CALCULATION & DISPLAY ──────────────────────────

if selected_start and selected_end and st.sidebar.button("Calculate Route"):
    # Only proceed if we have both start & end AND the user clicked the button.
    try:
        st.write("✅ Route calculation started...")
        # A simple confirmation message so the user knows work is in progress.

        start_coords = get_coordinates(selected_start)
        # Convert the chosen start address string into [lon, lat].

        end_coords = get_coordinates(selected_end)
        # Likewise for the destination.

        route = get_route_info(start_coords, end_coords)
        # Call the routing API and get back a dictionary with:
        #   - 'distance_km': total kilometers
        #   - 'duration_min': total travel minutes
        #   - 'geometry': list of [lon, lat] points along the path

        distance_km = route["distance_km"]
        # Pull out the distance value for later use.

        st.header("Estimated Impact")
        # A new section header where we’ll show emissions, time, etc.

        if not final_row.empty:
            # Make sure we actually found a vehicle row to use.
            row = final_row.iloc[0] if not car_not_listed else final_row
            # If custom, final_row is already a Series; otherwise take the first row.

            co2_g_per_mile = row["Co2__Tailpipe_For_Fuel_Type1"]
            mpg = row.get("Combined_Mpg_For_Fuel_Type1", np.nan)
            ghg_score = row.get("GHG_Score", np.nan)
            # Extract CO₂, MPG, and greenhouse-gas score from our data.

            st.success(
                f"{selected_make} {selected_model} "
                f"({selected_year}) - {selected_fuel}"
            )
            # Remind the user which car we’re calculating for.

            st.info(f"📏 Distance: **{distance_km:.2f} km**")
            # Show the trip distance formatted to two decimal places.

            travel_time_min = route["duration_min"]
            if travel_time_min >= 60:
                hours = int(travel_time_min // 60)
                mins = int(travel_time_min % 60)
                st.info(f"🕒 Travel time: **{hours}h {mins}min**")
            else:
                st.info(
                    f"🕒 Travel time: **{travel_time_min:.1f} minutes**"
                )
            # Convert minutes into hours+minutes if over an hour.

            # ──────── CO₂ EMISSIONS CALCULATION ───────────────────
            if pd.notna(co2_g_per_mile) and co2_g_per_mile > 0:
                co2_g_per_km = co2_g_per_mile / 1.60934
                total_co2 = co2_g_per_km * distance_km
                st.metric(
                    "💨 CO₂ Emissions",
                    f"{total_co2/1000:.2f} kg"
                )
            else:
                st.warning(
                    "💨 CO₂ emissions could not be calculated."
                )
            # Convert grams/mile → grams/km → total grams → kilograms.

            # ──────── FUEL CONSUMPTION CALCULATION ───────────────
            if pd.notna(mpg) and mpg > 0:
                l_per_100km = 235.21 / mpg
                fuel_needed = (l_per_100km * distance_km) / 100
                st.metric(
                    "⛽ Fuel Consumption",
                    f"{fuel_needed:.2f} liters"
                )
            else:
                st.warning(
                    "⛽ Fuel consumption could not be calculated."
                )
            # Convert MPG → L/100km → total liters for the trip.

            # ──────── DISPLAY GHG SCORE ──────────────────────────
            if pd.notna(ghg_score) and ghg_score > 0:
                # Pick a color: green=good, orange=okay, red=poor
                color = (
                    "#2ECC71"
                    if ghg_score >= 8
                    else "#F39C12"
                    if ghg_score >= 5
                    else "#E74C3C"
                )
                st.markdown(
                    f"<div style='background-color:{color};"
                    "padding:10px;border-radius:5px;color:white;'>"
                    f"🌿 GHG Score: <strong>{int(ghg_score)}</strong> "
                    "(out of 10)</div>",
                    unsafe_allow_html=True
                )
            else:
                st.warning("🌿 GHG score not available.")
        else:
            st.info(
                "No matching vehicle found. Please adjust your selection."
            )
            # If our vehicle lookup failed, prompt the user to try again.

        # ──────── ROUTE MAP ────────────────────────────────────
        st.header("Route Map")
        # Show a map of the route below the numbers.

        route_coords = [
            [lat, lon] for lon, lat in route["geometry"]
        ]
        map_df = pd.DataFrame(
            route_coords, columns=["lat", "lon"]
        )
        # Turn the list of [lon,lat] into a DataFrame of [lat,lon].

        map_df["lon_end"] = map_df["lon"].shift(-1)
        map_df["lat_end"] = map_df["lat"].shift(-1)
        map_df = map_df.dropna()
        # Create end-point columns by shifting up; drop the last empty row.

        center_lat = (map_df["lat"].min() + map_df["lat"].max()) / 2
        center_lon = (map_df["lon"].min() + map_df["lon"].max()) / 2
        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=7
        )
        # Calculate the map’s center so the route is nicely framed.

        layer = pdk.Layer(
            "LineLayer",       # We want to draw a line
            data=map_df,       # Data source for the line
            get_source_position=["lon", "lat"],
            get_target_position=["lon_end", "lat_end"],
            get_color=[0, 0, 255],  # Blue line
            get_width=4
        )
        # Define a blue line 4 pixels thick following our route coordinates.

        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                map_style=(
                    "mapbox://styles/mapbox/"
                    "satellite-streets-v11"
                )
            )
        )
        # Render the map using Mapbox’s satellite-streets style.
    except Exception as e:
        st.error("❌ An error occurred during route calculation.")
        st.exception(e)
        # If anything breaks in this whole block, show the error details.

# ──────── FOOTER ────────────────────────────────────────────────

st.markdown("---")
# Draw a horizontal line to separate content from the footer.

st.caption(
    "CS Project. Designed by Aymeric, Kaïs, Manu and Yannick. "
    "Group 2.06. Data sources: OpenRouteService, Carbon Interface API."
)
# Small caption at the very bottom giving credit and data-source info.
