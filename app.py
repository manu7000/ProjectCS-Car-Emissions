import streamlit as st
import pandas as pd
import pydeck as pdk
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import LabelEncoder
import numpy as np
import plotly.graph_objects as go
from Map_API import autocomplete_address, get_coordinates, get_route_info

# ── PAGE CONFIGURATION ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="CO₂ Emission Calculator",
    page_icon="🚗",
    layout="wide"
)

# ── DONUT CHART FUNCTION ─────────────────────────────────────────────────────
def draw_donut(value, label, color):
    # Clamp value between 0 and 100
    val = max(min(value, 100), 0)
    fig = go.Figure(data=[go.Pie(
        values=[val, 100 - val if 100 - val > 0 else 0.01],
        hole=0.7,
        marker_colors=[color, "#e8e8e8"],
        textinfo="none"
    )])
    fig.update_layout(
        showlegend=False,
        annotations=[{
            "text": f"<b>{value:.2f}</b><br>{label}",
            "font": {"size": 16},
            "showarrow": False
        }],
        margin=dict(t=0, b=0, l=0, r=0),
        height=220,
        width=220
    )
    return fig

# ── HEADER ───────────────────────────────────────────────────────────────────
st.title("Car Journey CO₂ Emission Calculator")
st.write("This tool helps you calculate and compare the CO₂ emissions of your car trips.")

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.header("Enter Your Trip Information")

# Address inputs
start_input = st.sidebar.text_input("From:")
start_suggestions, selected_start = [], None
if start_input:
    try:
        start_suggestions = autocomplete_address(start_input)
        selected_start = st.sidebar.selectbox("Select Starting Point:", start_suggestions)
    except Exception as e:
        st.sidebar.error(f"Error getting suggestions: {e}")

end_input = st.sidebar.text_input("To:")
end_suggestions, selected_end = [], None
if end_input:
    try:
        end_suggestions = autocomplete_address(end_input)
        selected_end = st.sidebar.selectbox("Select Destination:", end_suggestions)
    except Exception as e:
        st.sidebar.error(f"Error getting suggestions: {e}")

st.sidebar.header("Select Your Vehicle")

# Load vehicle data
try:
    vehicle_df = pd.read_csv(
        "all-vehicles-model@public.csv",
        sep=";", encoding="utf-8-sig", engine="python"
    )
    vehicle_df.columns = vehicle_df.columns.str.strip().str.replace(" ", "_")
    vehicle_df = vehicle_df.dropna(
        subset=["Make","Fuel_Type1","Model","Year","Co2__Tailpipe_For_Fuel_Type1"]
    )
except Exception as e:
    st.error(f"Failed to load vehicle data: {e}")
    st.stop()

# Optional custom car entry
car_not_listed = st.sidebar.checkbox("My car is not listed")
if car_not_listed:
    st.sidebar.markdown("### Enter your car details")
    fuel_type = st.sidebar.selectbox("Fuel Type", vehicle_df["Fuel_Type1"].dropna().unique())
    cylinders = st.sidebar.number_input("Cylinders", min_value=3, max_value=16)
    year = st.sidebar.number_input("Year", min_value=1980, max_value=2025)

    # Train a simple Decision Tree to predict CO₂
    model_data = vehicle_df.dropna(subset=[
        "Fuel_Type1","Cylinders","Year","Co2__Tailpipe_For_Fuel_Type1"
    ]).copy()
    le = LabelEncoder()
    model_data["Fuel_Type1_Encoded"] = le.fit_transform(model_data["Fuel_Type1"])
    X = model_data[["Fuel_Type1_Encoded","Cylinders","Year"]]
    y = model_data["Co2__Tailpipe_For_Fuel_Type1"]
    dt_model = DecisionTreeRegressor(random_state=42)
    dt_model.fit(X, y)

    inp = pd.DataFrame([[fuel_type,cylinders,year]],
                       columns=["Fuel_Type1","Cylinders","Year"])
    inp["Fuel_Type1_Encoded"] = le.transform(inp["Fuel_Type1"])
    predicted_co2 = dt_model.predict(inp[["Fuel_Type1_Encoded","Cylinders","Year"]])[0]

    selected_make = "Custom"
    selected_model = "Custom Entry"
    selected_year = year
    selected_fuel = fuel_type
    final_row = pd.Series({"Co2__Tailpipe_For_Fuel_Type1": predicted_co2})
else:
    # Standard vehicle selection
    makes = sorted(vehicle_df['Make'].dropna().unique())
    selected_make = st.sidebar.selectbox("Make", makes)

    df_m = vehicle_df[vehicle_df['Make'] == selected_make]
    fuel_types = sorted(df_m['Fuel_Type1'].dropna().unique())
    selected_fuel = st.sidebar.selectbox("Fuel Type", fuel_types)

    df_f = df_m[df_m['Fuel_Type1'] == selected_fuel]
    models = sorted(df_f['Model'].dropna().unique())
    selected_model = st.sidebar.selectbox("Model", models)

    df_mod = df_f[df_f['Model'] == selected_model]
    years = sorted(df_mod['Year'].dropna().unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Year", years)

    final_row = vehicle_df[
        (vehicle_df['Make'] == selected_make) &
        (vehicle_df['Fuel_Type1'] == selected_fuel) &
        (vehicle_df['Model'] == selected_model) &
        (vehicle_df['Year'] == selected_year)
    ]

compare_public_transport = st.sidebar.checkbox("Compare with public transport")

# ── MAIN SECTION ──────────────────────────────────────────────────────────────
if selected_start and selected_end and st.sidebar.button("Calculate Route"):
    try:
        # Get route info
        start_coords = get_coordinates(selected_start)
        end_coords = get_coordinates(selected_end)
        route = get_route_info(start_coords, end_coords)
        distance_km = route['distance_km']
        duration_min = route['duration_min']

        # Retrieve vehicle data
        if isinstance(final_row, pd.Series):
            row = final_row
        else:
            row = final_row.iloc[0]

        co2_g_mile = row['Co2__Tailpipe_For_Fuel_Type1']
        mpg = row.get('Combined_Mpg_For_Fuel_Type1', np.nan)
        ghg_score = row.get('GHG_Score', np.nan)
        car_emission_kg = (co2_g_mile / 1.60934) * distance_km / 1000

        # Display impact with donuts
        st.header("Estimated Impact")
        cols = st.columns(3)
        cols[0].plotly_chart(draw_donut(car_emission_kg, "kg CO₂ / car", "#264653"), use_container_width=True)
        if compare_public_transport:
            train_kg = (41 * distance_km) / 1000
            bus_kg = (105 * distance_km) / 1000
            cols[1].plotly_chart(draw_donut(train_kg, "kg CO₂ / train", "#2a9d8f"), use_container_width=True)
            cols[2].plotly_chart(draw_donut(bus_kg, "kg CO₂ / bus", "#e9c46a"), use_container_width=True)

        st.info(f"📏 Distance: **{distance_km:.2f} km**")
        if duration_min >= 60:
            h, m = divmod(int(duration_min), 60)
            st.info(f"🕒 Travel time: **{h}h {m} min**")
        else:
            st.info(f"🕒 Travel time: **{duration_min:.1f} min**")

        if pd.notna(mpg) and mpg > 0:
            l100 = 235.21 / mpg
            trip_l = (l100 * distance_km) / 100
            st.metric("⛽ Fuel Consumption", f"{trip_l:.2f} L")

        if pd.notna(ghg_score) and ghg_score > 0:
            color = "#2ECC71" if ghg_score >= 8 else "#F39C12" if ghg_score >= 5 else "#E74C3C"
            st.markdown(
                f"<div style='padding:10px; background-color:{color}; border-radius:8px; color:white;'>"
                f"🌿 GHG Score: **{int(ghg_score)}** (out of 10)</div>",
                unsafe_allow_html=True
            )

        # Display map last
        st.header("Route Map")
        rcoords = [[lat, lon] for lon, lat in route['geometry']]
        rdf = pd.DataFrame(rcoords, columns=["lat","lon"])
        rdf["lon2"] = rdf["lon"].shift(-1)
        rdf["lat2"] = rdf["lat"].shift(-1)
        rdf = rdf.dropna()

        view = pdk.ViewState(
            latitude=(rdf["lat"].min() + rdf["lat"].max())/2,
            longitude=(rdf["lon"].min() + rdf["lon"].max())/2,
            zoom=7
        )
        layer = pdk.Layer(
            "LineLayer", data=rdf,
            get_source_position=["lon","lat"],
            get_target_position=["lon2","lat2"],
            get_color=[0,0,255], get_width=4
        )
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view,
                                 map_style='mapbox://styles/mapbox/satellite-streets-v11'))

    except Exception as e:
        st.error("❌ An error occurred during route calculation.")
        st.exception(e)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("CS Project by Kaïs, Manu, Emmanuel & Yannick. Data sources: OpenRouteService, EEA, EPA")
