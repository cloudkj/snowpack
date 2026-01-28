import L from 'leaflet';
import togeojson from 'togeojson';
import 'leaflet.vectorgrid';

let renderer = L.canvas();
let map;
let kmlLayer = null;
let geoJsonLayer = null;
let heatmapLayer = null;

export async function loadKML(url, options) {
    if (options.singleton && kmlLayer) {
        map.removeLayer(kmlLayer);
    }

    const response = await fetch(url);
    const text = await response.text();
    const parser = new DOMParser();
    const kmlDom = parser.parseFromString(text, 'text/xml');
    const kmlData = togeojson.kml(kmlDom);

    const popupPropertyName = options.popupProperty;
    kmlLayer = L.geoJSON(kmlData, {
        onEachFeature: function(f, l) {
            if (f.properties && f.properties[popupPropertyName]) {
                l.bindPopup(f.properties[popupPropertyName]);
            }
        }
    }).addTo(map);
    map.fitBounds(layer.getBounds());
    return kmlLayer;
}

export async function loadGeoJSON(url, options) {
    if (options.singleton && geoJsonLayer) {
        map.removeLayer(geoJsonLayer);
    }

    const response = await fetch(url);
    const data = await response.json();

    const colorPropertyName = options.colorProperty;
    const popupPropertyName = options.popupProperty;
    geoJsonLayer = L.vectorGrid.slicer(data, {
        interactive: true,
        vectorTileLayerStyles: {
            sliced: function(properties, zoom) {
                return {
                    color: properties[colorPropertyName] || options.color,
                    fill: true,
                    fillColor: properties[colorPropertyName] || options.color,
                    fillOpacity: 0.7,
                    stroke: false
                };
            }
        }
    }).on('click', function(e) {
        const properties = e.layer.properties;
        if (properties[popupPropertyName]) {
            L.popup()
                .setContent(properties[popupPropertyName])
                .setLatLng(e.latlng)
                .openOn(map);
        }
    }).addTo(map);
    return geoJsonLayer;
}

export async function loadHeatmap(url, callback, options) {
    if (options.singleton && heatmapLayer) {
        map.removeLayer(heatmapLayer);
    }

    const response = await fetch(url);
    const data = await response.json();
    let points = data.features.map(callback);

    // Normalize and/or smooth as needed
    let denom = 1;
    if (options.normalize) {
        let maxVal = points.reduce((max, curr) => Math.max(max, curr[2]), 0);
        denom = options.smooth ? Math.log(maxVal) : maxVal;
    }
    points = points.map(([lat, lng, count]) => {
        let numer = options.smooth ? Math.log(count) : count;
        return [lat, lng, options.normalize ? numer / denom : numer];
    });

    heatmapLayer = L.heatLayer(points, {
        maxZoom: 8
    }).addTo(map);
    return heatmapLayer;
}

export function initMap(containerId, options) {
    let maxBounds = null;
    if (options.bounds) {
        maxBounds = L.latLngBounds(
            L.latLng(options.bounds.minLat, options.bounds.minLng),
            L.latLng(options.bounds.maxLat, options.bounds.maxLng));
        
    }
    console.log(maxBounds);
    map = L.map(containerId, {
        maxBounds: maxBounds,
        renderer: renderer,
        preferCanvas: true
    }).setView(options.centerCoords, options.zoomLevel);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    return map;
}
