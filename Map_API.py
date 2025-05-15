import openrouteservice
from openrouteservice import exceptions

# Initialize OpenRouteService client with API key
client = openrouteservice.Client(key='5b3ce3597851110001cf624863c2387f20a145d69082b4da269112fa')

def get_coordinates(address):
    """
    Geocode a full address into longitude and latitude coordinates.

    Parameters:
        address (str): The full address as a string.

    Returns:
        list: [longitude, latitude] of the address.

    Raises:
        RuntimeError: If the geocoding fails.
    """
    try:
        result = client.pelias_search(text=address)
        coords = result['features'][0]['geometry']['coordinates']
        return coords
    except Exception as e:
        raise RuntimeError(f"Could not geocode address '{address}': {e}")

def autocomplete_address(partial_text):
    """
    Suggest possible address completions for a given partial input.

    Parameters:
        partial_text (str): The beginning of an address or location name.

    Returns:
        list: A list of suggested full address strings.

    Raises:
        RuntimeError: If the autocomplete request fails.
    """
    try:
        result = client.pelias_autocomplete(text=partial_text)
        suggestions = [feature['properties']['label'] for feature in result['features']]
        return suggestions
    except Exception as e:
        raise RuntimeError(f"Autocomplete failed: {e}")

def get_route_info(start_coords, end_coords):
    """
    Calculate routing information between two geographic coordinates.

    Parameters:
        start_coords (list): [longitude, latitude] of the starting point.
        end_coords (list): [longitude, latitude] of the destination.

    Returns:
        dict: A dictionary with route distance in kilometers, 
              duration in minutes, and route geometry (polyline coordinates).

    Returns None if an OpenRouteService API error occurs.
    """
    try:
        route = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',     # Mode of transport
            format='geojson'           # Output format
        )
        segment = route['features'][0]['properties']['segments'][0]
        geometry = route['features'][0]['geometry']['coordinates']
        return {
            "distance_km": segment['distance'] / 1000,     # Convert meters to kilometers
            "duration_min": segment['duration'] / 60,      # Convert seconds to minutes
            "geometry": geometry                           # List of [lon, lat] points along the route
        }
    except exceptions.ApiError as e:
        print(f"OpenRouteService API Error: {e}")
        return None
