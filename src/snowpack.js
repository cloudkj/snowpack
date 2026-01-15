import L from 'leaflet';
import togeojson from 'togeojson';
import 'leaflet-geojson-vt';

let renderer = L.canvas();
let map;
let kmlLayerGroup = null;
let geoJsonLayer = null;
let heatLayer = null;

function info(message) {
    const msgDiv = document.getElementById("log");
    msgDiv.innerHTML += `<div>${message}</div>`;
    console.log(message);
}

function error(message, err) {
    console.error(message, err);
    document.getElementById("log").innerHTML += `<div style="color:red;">Error: ${message}</div>`;
}

async function loadKML() {
    const url = document.getElementById("kmlUrl").value.trim();
    if (!url) {
        error("Invalid URL");
        return;
    }

    if (kmlLayerGroup) {
        map.removeLayer(kmlLayerGroup);
    }

    info("Fetching KML...");
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
    kmlLayerGroup = layer;
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

    geoJsonLayer = L.geoJson.vt(data, {
        debug: 1,
        maxZoom: 20,
        indexMaxPoints: 200000,
        tolerance: 3,
        style: function (properties) {
            return {
                color: properties.c,
                fill: true,
                fillColor: properties.c,
                fillOpacity: 0.7,
                weight: 1,
                stroke: true
            };
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
