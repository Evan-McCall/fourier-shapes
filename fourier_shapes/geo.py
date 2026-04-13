"""Country outline loader backed by Natural Earth's 1:110m admin boundaries."""
import os
import urllib.request
import zipfile

import numpy as np


GEO_SHAPES = {
    "united states": "United States of America",
    "usa": "United States of America",
    "united states of america": "United States of America",
    "china": "China",
    "russia": "Russia",
    "brazil": "Brazil",
    "australia": "Australia",
    "india": "India",
    "canada": "Canada",
    "france": "France",
    "germany": "Germany",
    "japan": "Japan",
    "italy": "Italy",
    "spain": "Spain",
    "mexico": "Mexico",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "south africa": "South Africa",
    "argentina": "Argentina",
    "egypt": "Egypt",
    "turkey": "Turkey",
    "nigeria": "Nigeria",
    "indonesia": "Indonesia",
    "thailand": "Thailand",
    "sweden": "Sweden",
    "norway": "Norway",
    "poland": "Poland",
    "ukraine": "Ukraine",
    "iraq": "Iraq",
    "iran": "Iran",
    "saudi arabia": "Saudi Arabia",
    "colombia": "Colombia",
    "peru": "Peru",
    "venezuela": "Venezuela",
    "chile": "Chile",
    "kazakhstan": "Kazakhstan",
    "mongolia": "Mongolia",
    "south korea": "South Korea",
    "north korea": "North Korea",
    "vietnam": "Vietnam",
    "malaysia": "Malaysia",
    "philippines": "Philippines",
    "pakistan": "Pakistan",
    "afghanistan": "Afghanistan",
    "algeria": "Algeria",
    "angola": "Angola",
    "mali": "Mali",
    "ethiopia": "Ethiopia",
    "mozambique": "Mozambique",
    "madagascar": "Madagascar",
    "new zealand": "New Zealand",
    "bolivia": "Bolivia",
    "paraguay": "Paraguay",
    "uruguay": "Uruguay",
    "cuba": "Cuba",
    "portugal": "Portugal",
    "greece": "Greece",
    "romania": "Romania",
    "finland": "Finland",
    "denmark": "Denmark",
}

CACHE_DIR = os.path.expanduser("~/.cache/fourier_shapes")
SHAPEFILE_NAME = "ne_110m_admin_0_countries.shp"
NATURAL_EARTH_URL = (
    "https://naciscdn.org/naturalearth/110m/cultural/"
    "ne_110m_admin_0_countries.zip"
)

_world_data = None


def get_world_data():
    """Load the Natural Earth country shapefile, downloading on first use."""
    global _world_data
    if _world_data is not None:
        return _world_data

    import geopandas as gpd

    os.makedirs(CACHE_DIR, exist_ok=True)
    shp_path = os.path.join(CACHE_DIR, SHAPEFILE_NAME)

    if not os.path.exists(shp_path):
        zip_path = os.path.join(CACHE_DIR, "countries.zip")
        print("Downloading country data (one-time)...")
        urllib.request.urlretrieve(NATURAL_EARTH_URL, zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(CACHE_DIR)
        os.remove(zip_path)

    _world_data = gpd.read_file(shp_path)
    return _world_data


def get_geo_contour(name):
    """Return the largest polygon contour for a country by name, or None."""
    from shapely.geometry import MultiPolygon

    world = get_world_data()
    key = name.lower().strip()
    canonical = GEO_SHAPES.get(key)

    name_cols = [c for c in ["NAME", "NAME_LONG", "ADMIN", "SOVEREIGNT"]
                 if c in world.columns]

    row = None
    if canonical:
        for col in name_cols:
            matches = world[world[col].str.lower() == canonical.lower()]
            if len(matches):
                row = matches.iloc[0]
                break
    if row is None:
        for col in name_cols:
            matches = world[world[col].str.lower().str.contains(key, na=False)]
            if len(matches):
                row = matches.iloc[0]
                break
    if row is None:
        return None

    geom = row.geometry
    if isinstance(geom, MultiPolygon):
        geom = max(geom.geoms, key=lambda g: g.area)

    return np.array(geom.exterior.coords)
