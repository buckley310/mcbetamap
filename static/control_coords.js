L.control.coords = function (opts) {
	let ctrl = L.Control.extend({
		onAdd: (map) => {
			// TODO: make this not a button
			let c = L.DomUtil.create("button");
			c.innerHTML = "(&nbsp;&nbsp;&nbsp;&nbsp;)";

			let update = (e) =>
				(c.textContent = `(${parseInt(e.latlng.lng)}, ${parseInt(
					-e.latlng.lat,
				)})`);

			L.DomEvent.on(map, "mousemove", update);
			return c;
		},
	});

	return new ctrl(opts);
};
