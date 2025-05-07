###### PUBLIC TRANSPORT COMPARISON (BUS VS TRAIN) ######
if compare_public_transport:
    st.subheader("🚆 Public Transport CO₂ Comparison")

    # Average emissions (European data)
    train_co2_g_per_km = 41     # g/km
    bus_co2_g_per_km = 105      # g/km

    train_emission_kg = (train_co2_g_per_km * distance_km) / 1000
    bus_emission_kg = (bus_co2_g_per_km * distance_km) / 1000

    st.metric("🚄 Train Emissions", f"{train_emission_kg:.2f} kg CO₂")
    st.metric("🚌 Bus Emissions", f"{bus_emission_kg:.2f} kg CO₂")

    if total_emissions_grams > 0:
        car_emission_kg = total_emissions_grams / 1000

        train_savings = car_emission_kg - train_emission_kg
        bus_savings = car_emission_kg - bus_emission_kg

        if train_savings > 0:
            st.success(f"🌿 By taking the **train**, you could save ~{train_savings:.2f} kg CO₂.")
        else:
            st.info("🚗 Your car is more efficient than the average train on this route.")

        if bus_savings > 0:
            st.success(f"🌿 By taking the **bus**, you could save ~{bus_savings:.2f} kg CO₂.")
        else:
            st.info("🚗 Your car is more efficient than the average bus on this route.")


