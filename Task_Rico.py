map_key = "5b3ce3597851110001cf62485f6755d74d604274b66428ddcf0f7c26"
import openrouteservice

# Function to get distance between two places using OpenRouteService
def get_distance(start_coords, end_coords):
    client = openrouteservice.Client(key=map_key)

    # Request directions
    route = client.directions(
        coordinates=[start_coords, end_coords],
        profile='driving-car',
        format='geojson'
    )

    # Extract the distance (in meters)
    distance_meters = route['features'][0]['properties']['segments'][0]['distance']

    # Convert to kilometers
    distance_km = distance_meters / 1000

    return distance_km

if __name__ == "__main__":
    # Example coordinates (longitude, latitude)
    # London: -0.1257, 51.5085
    # Paris: 2.3522, 48.8566

    start = [-0.1257, 51.5085]  # London
    end = [2.3522, 48.8566]     # Paris

    distance = get_distance(start, end)
    print(f"The distance between London and Paris is approximately {distance:.2f} km.")

