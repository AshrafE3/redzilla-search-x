import json
import re
import os

# Get the absolute path of the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Open the file using the relative file path
with open(os.path.join(script_dir, 'ZIP_CODES.geojson')) as f:
    data = json.load(f)


def is_valid_zipcode(zipcode):
    zipcode_pattern = r'^\d{5}(?:[-\s]\d{4})?$'
    return bool(re.match(zipcode_pattern, zipcode))


def bounding_rectangle(zip_code):

    # Find the feature with the given zip code
    feature = None
    for feat in data['features']:
        if feat['properties']['ZIP'] == zip_code:
            feature = feat
            break

    if feature is not None:
        # Extract the bounding rectangle coordinates
        coords = feature['geometry']['coordinates'][0]
        lons, lats = zip(*coords)
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        return (min_lon, max_lon, min_lat, max_lat)
    else:
        return None
