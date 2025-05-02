# Project CS
This is the description of the Group number 02.06


Project idea :
Many people want to understand and reduce their carbon footprint, but it’s difficult to know the environmental impact of everyday actions like driving a car from point A to point B. We propose to build a web application that allows users to:
1.	Calculate the carbon emissions of any car journey
o	Users enter a departure and destination address, and select their vehicle type or specific car model.
o	The app uses mapping APIs to calculate the journey distance and emission factor APIs to compute the CO₂ emissions for that trip.
2.	Compare emissions for different vehicles and transport modes
o	Users can see how different car models, electric cars, or even public transport would change the emissions for the same journey.
3.	Visualize the environmental impact
o	Emissions are shown in easy-to-understand charts and graphics, allowing users to compare options at a glance.
4.	Suggest alternative or more eco-friendly travel options (future feature)
o	The app can recommend public transport, carpooling, or carbon offsetting for high-emission journeys.

Key Features
•	Distance calculation using mapping API (e.g., OpenRouteService)
•	Emission calculation using vehicle-specific emission factors (e.g., Carbon Interface API)
•	Data visualization: Emissions displayed in charts and maps
•	User interaction: Select journey, vehicle, and transport mode
•	Machine learning: Predict emissions for vehicles based on features (engine size, fuel type, etc.)
•	Comparison tools: Compare emissions for various vehicles and transport modes

User Interface
•	Input: Start address, destination, car model/type
•	Output: Distance, CO₂ emissions (kg), comparison with other vehicle types or public transport, charts

User Interface in details 
1. Main Page Structure (Streamlit App Layout)
A. Header
•	App name: “Car Journey CO₂ Emission Calculator”
•	Short intro text: Explains the purpose in 1-2 sentences
B. Input Section (Sidebar or top of the main page)
•	Departure address (Text input or autocomplete)
•	Arrival address (Text input or autocomplete)
•	Car selection
o	Dropdown: Select a vehicle type (Petrol/Diesel/Electric/Hybrid)
o	Optional: Dropdown or search to select a specific car model (e.g., from a dataset or API)
•	Advanced options (optional, for future features)
o	Checkbox: “Compare with public transport”
o	Checkbox: “Show alternative vehicles”
C. Action Button
•	Button: “Calculate Emissions”
D. Results Section (Main page, appears after calculation)
•	Journey distance (Display the calculated distance, e.g., “112 km”)
•	CO₂ emissions result (e.g., “Your journey emits 19.2 kg of CO₂”)
•	Visualization
o	Bar chart comparing selected vehicle with other types (e.g., Petrol, Diesel, Electric, Public Transport)
o	Map showing the journey route (optional, can be a static map or just start/end points)
•	Suggestions/Comparisons (Optional)
o	Text or icon-based suggestions for lower-carbon alternatives or carbon offsetting
E. Footer
•	Info about the data sources/APIs
•	Team/project info


User Flow (Step-by-Step)
1.	User visits app: Sees header and input form.
2.	User enters journey details: Types addresses, picks vehicle.
3.	User clicks 'Calculate': App queries APIs, calculates and predicts emissions.
4.	App displays results: Distance, CO₂, charts, map, suggestions.
5.	User tries comparisons: Changes vehicle, toggles “compare” options, sees updated visualizations.

How to Integrate Machine Learning:
Let’s use ML to predict the CO₂ emissions of a car journey based on vehicle features, instead of just using a fixed lookup value for each car.
This is actually what some CO₂ calculators do behind the scenes—using a regression model trained on car data (engine size, fuel type, weight, etc.).

ML in the workflow
1.	User inputs journey details (from/to, vehicle features)
2.	App gets journey distance (from mapping API)
3.	App uses ML model to predict emissions (based on distance and car features)
4.	Display:
o	ML prediction
o	(Optional) Compare with other methods or vehicles

ML model
•	Linear Regression (simple, easy to explain, and works well for this kind of numeric prediction)
•	Features: engine size, fuel type, transmission, cylinders, vehicle class, etc
