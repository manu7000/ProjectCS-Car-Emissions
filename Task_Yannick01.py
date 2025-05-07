###### PUBLIC TRANSPORT COMPARISON ######
if compare_public_transport:
    avg_co2_public = 70  # grams per km (adjust if needed)
    public_emission_kg = (avg_co2_public * distance_km) / 1000
    st.metric("🚆 Estimated CO₂ by Public Transport", f"{public_emission_kg:.2f} kg")

    if total_emissions_grams > 0:
        reduction = total_emissions_grams / 1000 - public_emission_kg
        if reduction > 0:
            st.success(f"🌱 You could save ~{reduction:.2f} kg CO₂ by using public transport.")
        else:
            st.info("🚗 Your car is more efficient than average public transport for this route.")

###### ALTERNATIVE VEHICLE SUGGESTIONS ######
if show_alternatives and not car_not_listed:
    st.subheader("🚘 Lower Emission Alternatives")
    similar_cars = vehicle_df[
        (vehicle_df['Fuel_Type1'] == selected_fuel) &
        (vehicle_df['Year'].between(selected_year - 2, selected_year + 2)) &
        (vehicle_df['Co2__Tailpipe_For_Fuel_Type1'] < co2_g_per_mile)
    ].sort_values("Co2__Tailpipe_For_Fuel_Type1").drop_duplicates(["Make", "Model"]).head(3)

    if not similar_cars.empty:
        for _, row in similar_cars.iterrows():
            alt_name = f"{row['Make']} {row['Model']} ({int(row['Year'])})"
            alt_co2 = row['Co2__Tailpipe_For_Fuel_Type1'] / 1.60934
            st.markdown(f"- **{alt_name}**: {alt_co2:.1f} g/km")
    else:
        st.info("No lower-emission alternatives found for your selection.")

