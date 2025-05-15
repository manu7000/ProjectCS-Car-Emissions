import openrouteservice
from openrouteservice import exceptions

# OpenRouteService-Client mit API-Schlüssel initialisieren
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
            profile='driving-car',     # Verkehrsmittel
            format='geojson'           # Ausgabeformat
        )
        segment = route['features'][0]['properties']['segments'][0]
        geometry = route['features'][0]['geometry']['coordinates']
        return {
            "distance_km": segment['distance'] / 1000,     # Meter in Kilometer umrechnen
            "duration_min": segment['duration'] / 60,      # Sekunden in Minuten umrechnen
            "geometry": geometry                           # Liste der [lon, lat]-Punkte entlang der Route
        }
    except exceptions.ApiError as e:
        print(f"OpenRouteService API Error: {e}")
        return None
