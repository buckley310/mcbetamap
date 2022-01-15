(function () {

    let initMap = function (landmarks) {
        let map = L.map('map', { crs: L.CRS.Simple }).setView([0, 0], 0);
        addEventListener('resize', () => map.invalidateSize());

        L.tileLayer('./data/tiles_{z}/r.{x}.{y}.png', {
            tileSize: 512,
            maxNativeZoom: 0,
            maxZoom: 4,
            minNativeZoom: -7,
            minZoom: -7,
        }).addTo(map);

        L.control.scale().addTo(map);
        L.control.spawn().addTo(map);
    };

    addEventListener('load', function () {
        fetch('./data/data.json')
            .then(r => r.json())
            .then(initMap);
    });

})();
