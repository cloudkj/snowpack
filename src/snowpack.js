import L from 'leaflet';
import togeojson from 'togeojson';
import 'leaflet.vectorgrid';

let renderer = L.canvas();
let map;
let kmlLayer = null;
let geoJsonLayer = null;

export async function loadKML(url, propNames) {
    if (kmlLayer) {
        map.removeLayer(kmlLayer);
    }

    const response = await fetch(url);
    const text = await response.text();
    const parser = new DOMParser();
    const kmlDom = parser.parseFromString(text, 'text/xml');
    const kmlData = togeojson.kml(kmlDom);

    const popupPropertyName = propNames.popup;
    const layer = L.geoJSON(kmlData, {
        onEachFeature: function(f, l) {
            if (f.properties && f.properties[popupPropertyName]) {
                l.bindPopup(f.properties[popupPropertyName]);
            }
        }
    }).addTo(map);
    map.fitBounds(layer.getBounds());
    kmlLayer = layer;
}

export async function loadGeoJSON(url, propNames) {
    if (geoJsonLayer) {
        map.removeLayer(geoJsonLayer);
    }

    const response = await fetch(url);
    const data = await response.json();

    const colorPropertyName = propNames.color;
    const popupPropertyName = propNames.popup;
    geoJsonLayer = L.vectorGrid.slicer(data, {
        interactive: true,
        vectorTileLayerStyles: {
            sliced: function(properties, zoom) {
                return {
                    color: properties[colorPropertyName],
                    fill: true,
                    fillColor: properties[colorPropertyName],
                    fillOpacity: 0.7,
                    stroke: false
                };
            }
        }
    }).on('click', function(e) {
        const properties = e.layer.properties;
        if (properties[popupPropertyName]) {
            L.popup()
                .setContent(properties['label'])
                .setLatLng(e.latlng)
                .openOn(map);
        }
    }).addTo(map);
}

export function initMap(containerId, options) {//centerCoords, zoomLevel) {
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
}
