import openrouteservice as ors
import folium

client = ors.Client(key='5b3ce3597851110001cf624863c2387f20a145d69082b4da269112fa') 

def get_coordinates(address):
    response = client.pelias_search(text=address)
    return response["features"][0]["geometry"]["coordinates"]

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

