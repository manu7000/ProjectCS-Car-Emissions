import openrouteservice

client = openrouteservice.Client(key='5b3ce3597851110001cf624863c2387f20a145d69082b4da269112fa') 

def get_coordinates(address):
    try:
        result = client.pelias_search(text=address)
        coords = result['features'][0]['geometry']['coordinates']
        return coords
    except Exception as e:
        raise RuntimeError(f"Could not geocode address '{address}': {e}")
    
def autocomplete_address(partial_text):
    try:
        result = client.pelias_autocomplete(text=partial_text)
        suggestions = [feature['properties']['label'] for feature in result['features']]
        return suggestions
    except Exception as e:
        raise RuntimeError(f"Autocomplete failed: {e}")

def get_route_info(start_coords, end_coords):
    route = client.directions(
        coordinates=[start_coords, end_coords],
        profile='driving-car',
        format='geojson'
    )
    segment = route['features'][0]['properties']['segments'][0]
    geometry = route['features'][0]['geometry']['coordinates']
    return {
        "distance_km": segment['distance'] / 1000,
        "duration_min": segment['duration'] / 60,
        "geometry": geometry
    }

