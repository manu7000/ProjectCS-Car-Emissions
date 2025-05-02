import openrouteservice

client = openrouteservice.Client(key="5b3ce3597851110001cf624863c2387f20a145d69082b4da269112fa") 

def get_coordinates(address):
    """Get coordinates for a given address using Pelias geocoding."""
    try:
        response = client.pelias_search(text=address)
        return response["features"][0]["geometry"]["coordinates"]
    except Exception as e:
        raise RuntimeError(f"Could not get coordinates for '{address}': {e}")

def get_route_info(start_coords, end_coords):
    """Get distance and duration between two coordinates."""
    try:
        route = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='geojson'
        )
        segment = route['features'][0]['properties']['segments'][0]
        return {
            "distance_km": segment['distance'] / 1000,
            "duration_min": segment['duration'] / 60
        }
    except Exception as e:
        raise RuntimeError(f"Could not get route information: {e}")
