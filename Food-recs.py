import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(page_title="🍽️ Find Best Places to Eat Nearby", layout="wide")
st.title("🍽️ Best Places to Eat Near You")

# Sidebar for input
st.sidebar.header("🔍 Search Parameters")
place_query = st.sidebar.text_input("Enter your location:", "Delhi, India")
radius = st.sidebar.slider("Search radius (in meters):", 500, 5000, 1500)
cuisine = st.sidebar.text_input("Preferred cuisine keyword (optional):", "")

API_KEY = st.secrets["GEOAPIFY_API_KEY"]

# Geocode location to lat/lon
def geocode_location(place):
    geolocator = Nominatim(user_agent="streamlit-app")
    location = geolocator.geocode(place)
    if location:
        return location.latitude, location.longitude
    return None, None

# Fetch restaurants using Geoapify Places API
def get_places(lat, lon, radius, keyword=""):
    endpoint = "https://api.geoapify.com/v2/places"
    params = {
        "categories": "catering.restaurant",
        "filter": f"circle:{lon},{lat},{radius}",
        "bias": f"proximity:{lon},{lat}",
        "limit": 30,
        "apiKey": API_KEY
    }
    if keyword:
        params["name"] = keyword

    response = requests.get(endpoint, params=params)
    return response.json().get("features", [])

# On search button click
if st.sidebar.button("Search"):
    with st.spinner("Searching for restaurants..."):
        lat, lon = geocode_location(place_query)
        if lat is None:
            st.error("Couldn't find the location. Try a more specific place.")
        else:
            st.session_state["results"] = get_places(lat, lon, radius, cuisine)
            st.session_state["location"] = (lat, lon)

# Render map + list from session_state
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    lat, lon = st.session_state["location"]

    st.success(f"Found {len(results)} restaurants near {place_query}!")

    m = folium.Map(location=[lat, lon], zoom_start=14)
    for r in results:
        props = r.get("properties", {})
        name = props.get("name", "Unnamed")
        address = props.get("formatted", "")
        lon_r, lat_r = r["geometry"]["coordinates"]

        folium.Marker(
            location=[lat_r, lon_r],
            popup=f"{name}\n{address}",
            icon=folium.Icon(color="blue", icon="cutlery", prefix="fa")
        ).add_to(m)

    st.markdown("### 🗺️ Map of Restaurants")
    st_folium(m, width=900, height=500)

    st.markdown("### 📋 Restaurant List")
    for r in results:
        props = r["properties"]
        name = props.get("name", "Unnamed")
        address = props.get("formatted", "")
        distance = props.get("distance", "")
        st.markdown(f"**{name}** — {address} ({distance}m away)")
        st.divider()

elif "results" in st.session_state and not st.session_state["results"]:
    st.warning("No restaurants found in this area.")
    st.info("Try increasing the radius or using a broader location like 'Delhi' or 'Andheri, Mumbai'.")
