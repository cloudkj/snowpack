import L from 'leaflet';
import togeojson from 'togeojson';
import 'leaflet.vectorgrid';

let renderer = L.canvas();
let map;
let kmlLayer = null;
let geoJsonLayer = null;

function info(message) {
    const msgDiv = document.getElementById("log");
    msgDiv.innerHTML += `<div>${message}</div>`;
    console.log(message);
}

async function loadKML() {
    const url = document.getElementById("kmlUrl").value.trim();
    if (kmlLayer) {
        map.removeLayer(kmlLayer);
    }

    info("Loading " + url);
    const response = await fetch(url);
    const text = await response.text();

    const parser = new DOMParser();
    const kmlDom = parser.parseFromString(text, 'text/xml');
    const kmlData = togeojson.kml(kmlDom);

    const layer = L.geoJSON(kmlData, {
        onEachFeature: function(f, l) {
            if (f.properties && f.properties.name) {
                l.bindPopup(f.properties.name);
            }
        }
    }).addTo(map);
    map.fitBounds(layer.getBounds());
    kmlLayer = layer;
}

async function loadGeoJSON() {
    const url = document.getElementById("geoJsonUrl").value.trim();
    if (geoJsonLayer) {
        map.removeLayer(geoJsonLayer);
    }

    info("Loading " + url);
    const response = await fetch(url);
    const data = await response.json();
    info("Loaded " + data.features.length + " features");

    geoJsonLayer = L.vectorGrid.slicer(data, {
        vectorTileLayerStyles: {
            sliced: function(properties, zoom) {
                return {
                    color: properties.c,
                    fill: true,
                    fillColor: properties.c,
                    fillOpacity: 0.7,
                    stroke: false
                };
            }
        }
    }).addTo(map);
}

map = L.map('map', { renderer: renderer, preferCanvas: true }).setView([38.5, -120.0], 8);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);
info("Map initialized");

document.getElementById('loadKML').addEventListener('click', loadKML);
document.getElementById('loadGeoJSON').addEventListener('click', loadGeoJSON);
