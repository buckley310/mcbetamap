(function () {
	let initMap = function (landmarks) {
		let map = L.map("map", { crs: L.CRS.Simple }).setView([0, 0], 0);
		addEventListener("resize", () => map.invalidateSize());

		L.tileLayer("./data/tiles_{z}/r.{x}.{y}.png", {
			tileSize: 512,
			maxNativeZoom: 0,
			maxZoom: 4,
			minNativeZoom: -7,
			minZoom: -7,
		}).addTo(map);

		L.control.scale().addTo(map);
		L.control.signs({ signs: landmarks.signs }).addTo(map);
		L.control.beds({ beds: landmarks.beds }).addTo(map);
		L.control.spawn().addTo(map);
		L.control.coords({ position: "bottomleft" }).addTo(map);

		for (let b of landmarks.beds)
			L.marker([-b.z, b.x]).addTo(map)._icon.classList.add("huechange");

		for (let s of landmarks.signs)
			L.marker([-s.z, s.x], { title: s.text }).addTo(map);
	};

	addEventListener("load", function () {
		fetch("./data/data.json")
			.then((r) => r.json())
			.then(initMap);
	});
})();
