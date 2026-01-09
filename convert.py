import requests
import json

def convert_to_geojson(url, output_filename):
    # 1. Fetch the original JSON
    print(f"Downloading from {url}...")
    response = requests.get(url)
    data = response.json()
    
    # 2. Extract points (assuming the structure is {"data": [...]})
    points = data.get('data', [])
    
    # 3. Construct GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    for point in points:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [point['lon'], point['lat']]  # GeoJSON is [Lon, Lat]
            },
            "properties": {
                "depth_mm": point['depth_mm']
            }
        }
        geojson["features"].append(feature)
    
    # 4. Save to file
    with open(output_filename, 'w') as f:
        json.dump(geojson, f)
    
    print(f"Success! Saved {len(points)} points to {output_filename}")

# Run the converter
s3_url = "https://cloudkj.s3.us-east-1.amazonaws.com/snow_depth.json"
convert_to_geojson(s3_url, "snow_depth.geojson")
