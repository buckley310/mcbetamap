let map = L.map('map', { crs: L.CRS.Simple }).setView([0, 0], 0);
addEventListener('resize', () => map.invalidateSize());

L.control.scale().addTo(map);

L.tileLayer('./data/tiles_{z}/r.{x}.{y}.png', {
    maxNativeZoom: 0,
    maxZoom: 4,
    minNativeZoom: -7,
    minZoom: -7,
    tileSize: 512,
}).addTo(map);
