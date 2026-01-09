import json

def compress_geojson(input_file, output_file, factor=5, precision=3):
    """
    input_file: path to original geojson
    factor: every N-th point to keep (e.g., 5 means 1/25th of data)
    precision: decimal places for coordinates (3 is approx 110m accuracy)
    """
    with open(input_file, 'r') as f:
        data = json.load(f)

    original_features = data['features']
    # Subsample the list
    compressed_features = original_features[::factor]

    for feature in compressed_features:
        # Round coordinates to reduce string length in JSON
        lon, lat = feature['geometry']['coordinates']
        feature['geometry']['coordinates'] = [
            round(lon, precision),
            round(lat, precision)
        ]

    new_geojson = {
        "type": "FeatureCollection",
        "features": compressed_features
    }

    with open(output_file, 'w') as f:
        # separators=(',', ':') removes whitespace for maximum compression
        json.dump(new_geojson, f, separators=(',', ':'))

    print(f"Compressed {len(original_features)} points down to {len(compressed_features)}")

# Usage
compress_geojson('snow_depth.geojson', 'snow_depth_low_res.geojson', factor=10)